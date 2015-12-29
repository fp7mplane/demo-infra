#!/usr/bin/env python

# Author: Sarah Wassermann <sarah.wassermann@student.ulg.ac.be>

import argparse
import datetime
import time
import subprocess
import os
import random

import AUX_IP_to_AS_map as IPToAS
import AUX_probe_analysing as pa
import AUX_check_measurements as cm

# constants - begin
# should define the KEY to run RIPE Atlas (Key to create a new user defined measurement)
API_KEY = 'XXXXXXXXXXXXXXXXXXXXXXXX'
# constants - end

# global vars - begin
probeToASMap = dict()
additionalInfoAboutMeasurements = dict()
# global vars - end

def checkIP(ip):
    """
    :param ip: a string representing an IP
    :return: ip converted into an integer, None if ip not a valid IP
    """
    try:
        parts = map(int, ip.split('.'))
        return (16777216 * parts[0]) + (65536 * parts[1]) + (256 * parts[2]) + parts[3]
    except ValueError:
        return None

def getSmallestPingProbe(measurementIDsDict, outputFileName):
    """
    Retrieve closest RIPE atlas boxes to target-IPs and store results
    :param measurementIDsDict:  a dictionary whose keys are RIPE user-defined measurement (udm) IDs and the corresponding
                                values are the targets of the udms
    :param outputFileName:      name of the file to which the results of the analysis should be written to.
                                A line of the file has the format:
                                "<Label> <target-IP> <RIPE probe ID> <RIPE probe IP> <RIPE probe AS> <min RTT>"
                                <Label> is [RANDOM] when the candidate-boxes have been selected randomly,
                                [NO_AS] if no AS could be associated to the target-IP and [OK] associated
    :return: a dictionary whose keys are target-IPs and values are tuples in the form (<probeID>, <probeIP>, <probeAS>, <minRTT>)
    """
    IPToPSBoxMap = dict()
    for IP in measurementIDsDict:
        UDMs = measurementIDsDict[IP]
        pingMeasurements = list()

        for udm in UDMs:
            try:
                resultInfo = subprocess.check_output(['../contrib/udm-result.pl', '--udm', udm])
            except subprocess.CalledProcessError:
                print "Can't get udm-results...\n"
                break

            if not resultInfo:
                continue

            resultInfo = resultInfo.split('\n')
            for line in resultInfo:
                l = line.rstrip('\r\n')
                if l:
                    data = l.split('\t')
                    srcIP = data[2]
                    destIP = data[4]

                    if srcIP == destIP:
                        continue

                    if data[5] != '*':
                        pingMeasurements.append((data[1], data[2], float(data[5]))) #ID/IP/RTT

        if not pingMeasurements: # target unreachable
            continue
        probeMinRTT = min(pingMeasurements, key=lambda tup: tup[2])

        outputFileName.write(IP + '\t' + probeMinRTT[0] + '\t' + probeMinRTT[1] + '\t'
                             + probeToASMap[probeMinRTT[0]] + '\t' + str(probeMinRTT[2]) + '\t'
                             + additionalInfoAboutMeasurements[IP] + '\n')

        IPToPSBoxMap[IP] = (probeMinRTT[0], probeMinRTT[1], probeToASMap[probeMinRTT[0]], str(probeMinRTT[2]))

    return IPToPSBoxMap

def find_psboxes(IPs, verbose, recovery):
    """
    Finds the closest box to each IP in <IPs>, displays the results on the screen and stores them in a file in the
    'output' folder and whose naming-scheme is '<timestamp_of_creation_time>_psbox.txt'
    :param IPs:      a list containing all the IPs a closest box should be found to
    :param verbose:  if true, an error-message gets displayed when an internal problem occurs, otherwise not
    :param recovery: if true, the recovery-modus will be enabled (for more infos, please see the docs in the folder
                     'doc')
    :return:         a dictionary whose values are the IPs and the keys are the corresponding cloesest boxes. If there
                     is not entry for a given IP, no box has been found
    """

    currentTime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
    measurementIDs = set()
    IPsToMeasurementIDs = dict()
    IPsAlreadyAnalysed = set()

    if recovery: # recovery-mode enabled
        # recover ID-to-AS mapping that has been done so far - begin
        try:
            ASMap = open('../logs/ID_To_AS.log', 'r')
        except IOError:
            if verbose:
                print "error: Could not open/create file '../logs/ID_To_AS.log'\n"
            return None

        for line in ASMap:
            l = line.rstrip('\r\n')
            if l:
                data = l.split('\t')
                probeToASMap[data[0]] = data[1]
        ASMap.close()
        # recover ID-to-AS mapping that has been done so far - end

        # recover IPs that have been analysed so far and the corresponding output-file - begin
        try:
            logFile = open('../logs/current_ping_measurementIDs.log', 'r')
        except IOError:
            if verbose:
                print "error: Could not open file '../logs/current_ping_measurementIDs.log'\n"
            return None

        cnt = 0
        timeStamp = ''
        for line in logFile:
            l = line.rstrip('\r\n')
            if l:
                if cnt == 0:
                    timeStamp = l
                else:
                    data = l.split('\t')
                    IPsToMeasurementIDs[data[data.__len__() - 2]] = data[:data.__len__() - 2]
                    measurementIDs.update(data[:data.__len__() - 2])
                    additionalInfoAboutMeasurements[data[data.__len__() - 2]] = data[data.__len__() - 1]
                    IPsAlreadyAnalysed.add(data[data.__len__() - 2])
                cnt += 1
        logFile.close()
        # recover IPs that have been analysed so far and the corresponding output-file - end

    if not recovery:
        try:
            ASMap = open('../logs/ID_To_AS.log', 'w') # clear content of ID-to-AS log
        except IOError:
            if verbose:
                print "error: Could not open/create file '../logs/ID_To_AS.log'\n"
            return None
        ASMap.close()

    # open/create output-file - begin
    try:
        if recovery:
            output = open('../output/' + timeStamp + '_psbox.txt', 'a', 1)
        else:
            output = open('../output/' + currentTime + '_psbox.txt', 'w', 1)
    except IOError:
        if verbose:
            if recovery:
                print "error: Could not open/create file '../output/" + timeStamp  + "_psbox.txt'\n"
            else:
                print "error: Could not open/create file '../output/" + currentTime  + "_psbox.txt'\n"
        return None
    # open/create output-file - end

    # open/create log-file - begin
    try:
        if recovery:
            logFile = open('../logs/current_ping_measurementIDs.log', 'a', 1)
        else:
            logFile = open('../logs/current_ping_measurementIDs.log', 'w', 1)
            logFile.write(currentTime + '\n')
    except IOError:
        if verbose:
            print "error: Could not open/create file '../logs/current_ping_measurementIDs.log'\n"
        return None
    # open/create log-file - end

    # open file containing RIPE Atlas boxes and load data - begin
    try:
        plFile = open('../lib/probelist.txt', 'r')
    except IOError:
        if verbose:
            print "error: Could not open file '../lib/probelist.txt'\n"
        output.close()
        logFile.close()
        return None

    probeList = list() # load list with all currently connected RIPE probes
    for line in plFile:
        l = line.rstrip('\r\n')
        if l:
            probeData = l.split('\t')
            probeList.append((probeData[0], probeData[3]))
    plFile.close()
    # open file containing RIPE Atlas boxes and load data - end

    targetIPs = list(IPs)

    IPToASMap = IPToAS.mapIPtoAS(targetIPs, '../lib/GeoIPASNum2.csv', True)

    if IPToASMap == None:
        output.close()
        logFile.close()
        return None

    encounteredASes = dict()

    # launching measurements to find closest box - start
    for IP in IPToASMap:
        if IP in IPsAlreadyAnalysed:
            continue
        IPsAlreadyAnalysed.add(IP)

        if verbose:
            print 'Starting to do measurements for IP: ' + IP + '...\n'
        AS = IPToASMap[IP]

        if AS == 'NA_MAP':
            additionalInfoAboutMeasurements[IP] = '[NO_AS]'
            idx = random.sample(range(0, probeList.__len__()), 100)
            selectedProbes = [probeList[i][0] for i in idx]

            try:
                ASMap = open('../logs/ID_To_AS.log', 'a', 0)
            except IOError:
                if verbose:
                    print "error: Could not open/create file '../logs/ID_To_AS.log'\n"
                output.close()
                logFile.close()
                return None
            for i in idx:
                ASMap.write(probeList[i][0] + '\t' + probeList[i][1] + '\n')
            ASMap.close()

            probes = [selectedProbes[i:i + 500] for i in range(0, selectedProbes.__len__(), 500)]

        elif not AS in encounteredASes: # check whether we have already retrieved probes for this AS
            # check whether there are probes in IP's AS
            nbOfConsecutiveFailures = 0
            giveUp = False
            while True:
                try:
                    probeListInfo = subprocess.check_output(['../contrib/probe-list.pl', '--asn', IPToASMap[IP]])
                    nbOfConsecutiveFailures = 0
                    break
                except subprocess.CalledProcessError:
                    nbOfConsecutiveFailures += 1
                    time.sleep(120)

                    # if download-attempt fails for 5 consecutive times, abord
                    if nbOfConsecutiveFailures == 5:
                        giveUp = True
                        break
            if giveUp:
                break # proceed to closest-box analysis

            # if not, look at the neighbour-ASes
            if not probeListInfo:
                neighbours = pa.findASNeighbourhood(IPToASMap[IP], True)
                if neighbours == None:
                    output.close()
                    logFile.close()
                    return None

                giveUp = False
                nbOfConsecutiveFailures = 0
                for neighbour in neighbours:
                    while True:
                        try:
                            probeListInfo += subprocess.check_output(['../contrib/probe-list.pl', '--asn', neighbour])
                            nbOfConsecutiveFailures = 0
                            break
                        except subprocess.CalledProcessError:
                            nbOfConsecutiveFailures += 1
                            time.sleep(120)

                            # if download-attempt fails for 5 consecutive times, abord
                            if nbOfConsecutiveFailures == 5:
                                giveUp = True
                                break
                    if giveUp:
                        break

                if giveUp:
                    continue

            if probeListInfo: # we have found neighbour-probes
                probes = pa.parseProbeListOutput(probeListInfo, True, probeToASMap)
                if probes == None:
                    output.close()
                    logFile.close()
                    return None

                encounteredASes[AS] = probes
            else:
                encounteredASes[AS] = ''

        # pinging neighbours - start
        if AS != 'NA_MAP':
            probes = encounteredASes[AS]

        if not probes: # if no probes in neighbourhood, use randomly selected probes
            additionalInfoAboutMeasurements[IP] = '[RANDOM]'

            idx = random.sample(range(0, probeList.__len__()), 100)
            selectedProbes = [probeList[i][0] for i in idx]

            try:
                ASMap = open('../logs/ID_To_AS.log', 'a', 0)
            except IOError:
                if verbose:
                    print "error: Could not open/create file '../logs/ID_To_AS.log'\n"
                output.close()
                logFile.close()
                return None
            for i in idx:
                ASMap.write(probeList[i][0] + '\t' + probeList[i][1] + '\n')
            ASMap.close()

            probes = [selectedProbes[i:i + 500] for i in range(0, selectedProbes.__len__(), 500)]
        elif AS != 'NA_MAP':
            additionalInfoAboutMeasurements[IP] = '[OK]'

        nbOfConsecutiveFailures = 0
        giveUp = False

        for probeSet in probes:
            probesToUse = ','.join(probeSet)
            while True:
                try:
                    udmCreateInfo = subprocess.check_output(['../contrib/udm-create.pl', '--api', API_KEY, '--type',  'ping', '--target',
                                                         IP, '--probe-list', probesToUse, '--packets', '10'])
                    udmCreateInfo = udmCreateInfo.rstrip('\r\n')
                    nbOfConsecutiveFailures = 0

                    if udmCreateInfo:
                        if IP not in IPsToMeasurementIDs:
                            IPsToMeasurementIDs[IP] = [udmCreateInfo]
                        else:
                            IPsToMeasurementIDs[IP].append(udmCreateInfo)
                        measurementIDs.add(udmCreateInfo)
                    break
                except subprocess.CalledProcessError, e: # maybe too many measurements running?
                    nbOfConsecutiveFailures += 1
                    time.sleep(180)

                    # if 5 consecutive measurement-attempts fail, give up
                    if nbOfConsecutiveFailures == 5:
                        IPsToMeasurementIDs.pop(IP, None) # delete this entry; should not be analyzed
                        giveUp = True
                        break
            if giveUp:
                break
        if giveUp:
            break

        if IPsToMeasurementIDs[IP]:
            logFile.write('\t'.join(IPsToMeasurementIDs[IP]) + '\t' + IP + '\t'
                                    + additionalInfoAboutMeasurements[IP] + '\n')
        # pinging neighbours - end

    # launching measurements to find closest box - end
    logFile.close()

    # waiting for ping-measurements to finish
    if verbose:
        print 'Waiting for ping-measurements to finish...\n'
    status = cm.checkMeasurements(measurementIDs, True)
    if status == None:
        return None

    while not status:
        time.sleep(180)
        status = cm.checkMeasurements(measurementIDs, True)

        if status == None:
            output.close()
            return None

    if verbose:
        print 'Computing closest RIPE Atlas box...\n'

    results = getSmallestPingProbe(IPsToMeasurementIDs, output)

    output.close()
    # os.remove('../logs/current_ping_measurementIDs.log')
    # if os.path.exists('../logs/ID_To_AS.log'):
    #     os.remove('../logs/ID_To_AS.log')

    return results

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Find the closest RIPE Atlas box to a set of IPs')
    parser.add_argument('-v', action="version", version="version 1.0")
    parser.add_argument('-n', action="store", dest="filename", help="File containing the IPs for which you want to find the closest box."
                                                                    "The file has to be stored in the folder 'input'")
    parser.add_argument('-o', action="store", dest="targetIP", help="The IP for which you want to find the closest box.")
    parser.add_argument('-r', action="store", dest="recovery", type=int, choices=[0, 1], default=0,
                                                                                            help="1 if you want to enable the"
                                                                                              "recovery-mode, 0 otherwise."
                                                                                              "For more information about the "
                                                                                              "recovery-mode, please have a look"
                                                                                              "at the documentation in 'doc'")

    arguments = vars(parser.parse_args())

    if not arguments['targetIP'] and not arguments['filename']:
        parser.error("error: You must either specify an IP or a filename of a file containing IPs!")
        exit(1)

    # if an IP is specified, we always go for the IP
    if arguments['targetIP']:
        targetIP = arguments['targetIP']
        if checkIP(targetIP) == None:
            print 'error: The indicated IPs must be in the format <X.X.X.X>!\n'
            exit(3)
        targetIPs = [targetIP]
    else:   # check file
        try:
            IPfile = open('../input/' + arguments['filename'], 'r')
        except IOError:
            print "error: Could not open file '../input/" + arguments['filename'] + "'\n"
            exit(2)

        # load IPs from file
        targetIPs = list()
        for line in IPfile:
            l = line.rstrip('\r\n')
            if l and not l.isspace():
                if checkIP(l) == None:
                    print 'error: The indicated IPs must be in the format <X.X.X.X>!\n'
                    IPfile.close()
                    exit(3)
                targetIPs.append(l)
        IPfile.close()

    # launch measurements and get psboxes
    if arguments['recovery'] and arguments['recovery'] == 1:
        if not os.path.exists('../logs/current_ping_measurementIDs.log'):
            print "error: Could not launch recovery-mode!\n"
            exit(5)
        psBoxMap = find_psboxes(targetIPs, True, True)
    else:
        psBoxMap = find_psboxes(targetIPs, True, False)

    if psBoxMap != None and psBoxMap:
        for IP in targetIPs:
            if IP in psBoxMap:
                print IP + '\t' + '\t'.join(psBoxMap[IP]) + '\t' + additionalInfoAboutMeasurements[IP] + '\n'
    if psBoxMap == None:
        exit(4)
    else:
        exit(0)
