#!/usr/bin/env python

# Author: Sarah Wassermann <sarah.wassermann@student.ulg.ac.be>

import argparse
import subprocess
import datetime
import time
import find_psbox as ps

#global vars - begin
API_KEY = '182abdea-73f4-4844-adc8-e12c44f6945e'
INTERVAL_DEFAULT = 600
#global vars - end

def launch_scheduled_traceroutes(destIP, probes, start, stop, interval, numberOfTraceroutes):
    """
    launch traceroutes.
    The list of probes 'probes' will be used as sources and the destination is 'destIP'
    When no start time is specified, traceroutes will be launched as soon as possible
    It is not possible to specify a start time, but not a stop time and vice-versa
    When no interval is given, a default interval of 600 seconds is used
    Either a stop-time or a number of traceroutes to be scheduled has to be given. When a stop-time
    is indicated, the number of traceroutes will be ignored
    :param destIP:              the IP at which tracroutes should be launched
    :param probes:              the list of RIPE Atlas probes which should be used as sources
    :param start:               the start time (UNIX timestamp) at which first tracroute should be launched
    :param stop:                time (UNIX timestamp) at which no more traceroute should be launched
    :param interval:            time between 2 consecutive traceroutes
    :param numberOfTraceroutes: number of traceroutes to be scheduled
    """
    probes = [probes[i:i + 500] for i in range(0, len(probes), 500)]
    currentTime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
    try:
        logFile = open('../logs/' + currentTime + '_current_scheduled_traceroutes.log', 'w', 0)
    except IOError:
        print "error: Could not open/create '../logs/" + ts + "_current_scheduled_traceroutes.log'!\n"
        return
    nbOfConsecutiveFailures = 0
    giveUp = False

    measurementIDs = list()
    for probesToUse in probes:
        while True:
            try:
                if stop:
                    if start:
                        startTime = start
                    else:
                        startTime = time.time()
                    if interval:
                        i = interval
                    else:
                        i = INTERVAL_DEFAULT
                    udmCreateInfo = subprocess.check_output(['udm-create.pl', '--api', API_KEY, '--type',  'traceroute', '--target',
                                                            destIP, '--probe-list', ','.join(probesToUse), '--start', str(startTime),
                                                            '--stop', str(stop), '--interval', str(i)])
                    nbOfConsecutiveFailures = 0
                elif not start and not interval and not numberOfTraceroutes:
                    udmCreateInfo = subprocess.check_output(['udm-create.pl', '--api', API_KEY, '--type',  'traceroute', '--target',
                                                            destIP, '--probe-list', ','.join(probesToUse)])
                    nbOfConsecutiveFailures = 0
                elif numberOfTraceroutes and interval and not start:
                    startTime = time.time()
                    udmCreateInfo = subprocess.check_output(['udm-create.pl', '--api', API_KEY, '--type',  'traceroute', '--target',
                                                         destIP, '--probe-list', ','.join(probesToUse), '--interval', str(interval), '--start', str(startTime),
                                                         '--stop', str(startTime + numberOfTraceroutes * interval)])
                    nbOfConsecutiveFailures = 0
                elif numberOfTraceroutes and not interval:
                    if start:
                        startTime = start
                    else:
                        startTime = time.time()
                    udmCreateInfo = subprocess.check_output(['udm-create.pl', '--api', API_KEY, '--type',  'traceroute', '--target',
                                                            destIP, '--probe-list', ','.join(probesToUse), '--interval', str(INTERVAL_DEFAULT),
                                                            '--start', str(startTime), '--stop', str(startTime + numberOfTraceroutes * INTERVAL_DEFAULT)])
                    nbOfConsecutiveFailures = 0
                else:
                    break
                udmCreateInfo = udmCreateInfo.rstrip('\r\n')
                if udmCreateInfo:
                    measurementIDs.append(udmCreateInfo)
                break

            except subprocess.CalledProcessError:
                nbOfConsecutiveFailures += 1

                if nbOfConsecutiveFailures == 5:
                    giveUp = True
                    break
        if giveUp:
            break
    if not giveUp:
        logFile.write('\t'.join(measurementIDs) + '\t' + destIP + '\n')
    logFile.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Launch traceroutes from the closest RIPE Atlas boxes'
                                                 ' to a set of IPs to a specified destination')
    parser.add_argument('-v', action="version", version="version 1.0")
    parser.add_argument('-n', action="store", dest="filename", help="Filename of file containing the IPs "
                                                                    "for which traceroutes from the corresponding "
                                                                    "closest RIPE Atlas boxes should be launched to "
                                                                    "the specified destination. The file has to be stored "
                                                                    "in the folder 'input'")
    parser.add_argument('-o', action="store", dest="targetIP", help="The IP for which you want to find the closest box (if not already specified)"
                                                                    "and then launch traceroutes from this box to the specified destination-IP")
    parser.add_argument('-d', action="store", dest="destIP", help="IP which the traceroutes should be launched to", required=True)
    parser.add_argument('-b', action="store", dest="boxID", type=int, help="ID of the closest box to the IP indicated with -o")
    parser.add_argument('-f', action="store", dest="flag", type=int, choices=[0, 1], help="If 1, the closest boxes are specified "
                                                                                          "(via -b when -o used, in the input-file "
                                                                                          "when -n is used). If 0, the closest boxes "
                                                                                          "are computed before launching traceroutes",
                                                                                    required=True)
    parser.add_argument('-m', action="store", dest="nbTraceroutes", type=int, help="Total number of traceroutes to be launched")
    parser.add_argument('-t', action="store", dest="interval", type=int, help="Time between two consecutive traceroutes")
    parser.add_argument('-s', action="store", dest="start", type=int, help="Time when the first traceroute should be launched")
    parser.add_argument('-p', action="store", dest="stop", type=int, help="Time when traceroutes should be stopped")

    arguments = vars(parser.parse_args())

    # check parameters - begin
    if not any(arguments.values()):
        parser.error("error: You must at least specify an IP or a filename of a file containing IPs and a destination-IP!")
        exit(1)
    elif not arguments['filename'] and not arguments['targetIP']:
        parser.error("error: You must either specify an IP or a filename of a file containing IPs!")
        exit(1)
    elif arguments['interval'] and not arguments['nbTraceroutes'] and not arguments['stop']:
        parser.error("error: You must specify the number of traceroutes when setting an interval "
                     "and not indicating the stop-time!")
        exit(1)
    elif arguments['targetIP'] and arguments['flag'] == 1 and not arguments['boxID']:
        parser.error("error: You must specify the RIPE Atlas box to use when setting -f to 1!")
        exit(1)
    elif arguments['flag'] == 0 and arguments['targetIP'] and arguments['boxID']:
        parser.error("error: You cannot specify the RIPE Atlas box to use when setting -f to 0!")
        exit(1)
    elif arguments['stop'] and arguments['nbTraceroutes']:
        parser.error("error: You cannot specify the stop-time when indicating a number of traceroutes to be performed!")
        exit(1)
    # check parameters - end

    flag = arguments['flag']

    # when the user indicated an IP (-o), always go for it
    if arguments['targetIP']:
        targetIP = arguments['targetIP']
        if flag == 1:
            closestBox = str(arguments['boxID'])
        else:
            closestBoxMap = ps.find_psboxes([targetIP], True)
            if closestBoxMap:
                closestBox = closestBoxMap[targetIP]
            elif closestBoxMap == None:
                exit(3)
            else:
                exit(0)
        closestBox = [closestBox]
    else:   # check file
        try:
            IPfile = open('../input/' + arguments['filename'], 'r')
        except IOError:
            print "error: Could not open file '../input/" + arguments['filename'] + "'\n"
            exit(2)

        closestBox = set()

        # load IPs from file
        targetIPs = list()
        for line in IPfile:
            l = line.rstrip('\r\n')
            if l and not l.isspace():
                data = l.split('\t')
                if flag == 1 and data.__len__() < 2:
                    print 'error: You must specify a RIPE Atlas box to use when -f is set to 1, please refer to ' \
                          'the manual\n'
                    IPfile.close()
                    exit(3)
                if ps.checkIP(data[0]) == None:
                    print 'error: The indicated IPs must be in the format <X.X.X.X> where X is an integer >= 0!\n'
                    IPfile.close()
                    exit(4)
                targetIPs.append(data[0])
                if flag == 1:
                    closestBox.add(data[1])
        IPfile.close()

        if flag == 0:
            closestBoxMap = ps.find_psboxes(targetIPs, True, False)
            if closestBoxMap:
                for key in closestBoxMap:
                    closestBox.add(closestBoxMap[key][0])
            elif closestBoxMap == None:
                exit(3)
            else:
                exit(0)
    launch_scheduled_traceroutes(arguments['destIP'], list(closestBox), arguments['start'], arguments['stop'],
                                 arguments['interval'], arguments['nbTraceroutes'])