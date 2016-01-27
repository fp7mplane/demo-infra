#!/usr/bin/env python

# Author: Sarah Wassermann <sarah.wassermann@student.ulg.ac.be>

import argparse
import subprocess
import datetime
import time
import AUX_IP_to_AS_map as parseIP
import AUX_get_RouteViews_data as rv

# global vars - begin

# keys: (start, end) tuple where start is the beginning of a path and end the end of the path
# values: the inferred AS-path (in form of a list) between start and end via RouteViews data; empty list of no info available
hiddenTraceroutePathParts = dict()

IPToPoPMapping = dict()
# global vars - end

class TracerouteMeasurement:
    """
    This class represents a traceroute-measurement
    """
    def __init__(self):
        """
        Initializes the object's attributes
        """
        self.probeID = ''   # the source-probe's ID
        self.nbHops = -1    # the number of IP-hops performed until the destination was reached

        # list of tuples where each tuple has the form (<IP>, <INFO>)
        # if the IP-address is known, <IP> = given address; 'NA_TR' otherwise
        # <INFO> = 'init' if the tuple describes the source-IP address; the RTT if the analysed IP corresponds to the
        # one of a hop; the empty-string if RTT is unknown for a hop-IP
        self.IPInfos = list()

        self.timestamp = -1 # the UNIX-timestamp corresponding to the time at which the measurement was launched

    def addProbeID(self, probe):
        """
        Sets the probeID-attribute to <probe>
        """
        self.probeID = probe

    def addNbHops(self, nb):
        """
        Sets the nbHops-attribute to <nb>
        """
        self.nbHops = nb

    def addTimestamp(self, ts):
        """
        Sets the timestamp-attribute to <ts>
        """
        self.timestamp = ts

    def addIPInfo(self, IP, info):
        """
        Adds the tuple (<IP>, <info>) to the IPinfos-attribute
        """
        self.IPInfos.append((IP, info))

    def completeASPath(self, ASPathArg):
        """
        Tries to fill the missing parts in the ASPath <ASPathArg> as much as possible. This is done with the help of
        RouteViews data. Returns the completed ASPath.
        (Example: if <ASPathArg> = [A, NA_TR/NA_MAP, C]; this method tries to find out which ASes are traversed between
        A and C)
        :param ASPathArg:   a list representing the ASPath to be analysed
        :return:            the processed ASPath
        """
        idx = 0
        ASPath = list(ASPathArg)

        beginHiddenPathIdx = -1
        beginHiddenPathAS = ''
        endHiddenPathIdx = -1
        endHiddenPathAS = ''

        while idx < ASPath.__len__():
            if ASPath[idx] != 'NA_TR' and ASPath[idx] != 'NA_MAP': # Is this AS-hop unknown?
                if beginHiddenPathAS != '':
                    endHiddenPathAS = ASPath[idx]
                    endHiddenPathIdx = idx
                    hiddenPart = list()

                    # the start-AS and the end-AS of this part with missing info are different. We try to complete it
                    if beginHiddenPathAS != endHiddenPathAS:
                        if (beginHiddenPathAS, endHiddenPathAS) not in hiddenTraceroutePathParts:
                            hiddenPart = rv.getASPath(beginHiddenPathAS, endHiddenPathAS)
                            hiddenTraceroutePathParts[(beginHiddenPathAS, endHiddenPathAS)] = hiddenPart
                        else:
                            hiddenPart = hiddenTraceroutePathParts[(beginHiddenPathAS, endHiddenPathAS)]
                    beginHiddenPathAS = ''
                    endHiddenPathAS = ''
                    if hiddenPart.__len__() > 0: # Did we find something useful?
                        ASPath = ASPath[:beginHiddenPathIdx] + hiddenPart + ASPath[endHiddenPathIdx + 1:]
                        idx = beginHiddenPathIdx
                    else:
                        idx += 1
                else:
                    idx += 1
            else:
                if idx - 1 >= 0 and ASPath[idx - 1] != 'NA_TR' and ASPath[idx - 1] != 'NA_MAP':
                    beginHiddenPathAS = ASPath[idx - 1]
                    beginHiddenPathIdx = idx - 1
                    idx += 1
                else:
                    idx += 1

        finalASPath = list()
        for path in ASPath:
            length = finalASPath.__len__()
            if length == 0 or finalASPath[length - 1] != path:
                finalASPath.append(path)
        return finalASPath

    def saveToFile(self, ASMapping, currentTime):
        """
        Writes the information about this measurement to the file '<timestamp>_scheduled_traceroutes.txt' in the output-folder.
        For the exact format of the output-file, please check the documentation.
        :param ASMapping:   a dictionary. A key is an IP and the corresponding value is the AS which it is located in.
                            The IP2AS-mapping is done through a database provided by MaxMind
        :param currentTime: the timestamp to use in the name of the output-file
        """
        try:
            pointerToFile = open('../output/' + currentTime + '_scheduled_traceroutes.txt', 'a', 0)
        except IOError:
            print "error: Could not open/create file '../output/" + currentTime + "'_scheduled_traceroutes.txt'\n"
            return None

        pointerToFile.write("PROBEID:\t" + self.probeID + '\n')
        pointerToFile.write("TIMESTAMP:\t" + self.timestamp + '\n')
        pointerToFile.write("NBHOPS:\t" + str(self.nbHops) + '\n')

        ASes = list()
        PoPs = list()
        IPs = list()

        for ip in self.IPInfos:
            IPs.append(ip[0])
            if ip[1] != '' and ip[1] != 'init':
                pointerToFile.write("HOP:" + '\t' + ip[0] + '\t' + ip[1] + '\n')
            elif ip[1] != 'init':
                pointerToFile.write("HOP:" + '\t' + ip[0] + '\n')

            if ip[0] == 'NA_TR':
                res = 'NA_TR'
            else:
                res = ASMapping[ip[0]]
            if ASes.__len__() == 0 or res != ASes[ASes.__len__() - 1]:
                ASes.append(res)

            if ip[0] in IPToPoPMapping:
                pop = IPToPoPMapping[ip[0]]
            else:
                pop = 'NA'
            if PoPs.__len__() == 0 or pop != PoPs[PoPs.__len__() - 1]:
                PoPs.append(pop)

        pointerToFile.write("ASPATH:\t" + '\t'.join(self.completeASPath(ASes)) + '\n')
        pointerToFile.write("POPPATH:\t" + '\t'.join(PoPs) + '\n')
        pointerToFile.write("IPPATH:\t" + '\t'.join(IPs) + '\n')

        pointerToFile.close()

def loadIPToPoPMapping(filename):
    """
    Fills the dictionary <IPToPoPMapping>. A key corresponds to an IP and the value to the PoP in which it is located.
    The IP-to-PoP-mapping is performed through a database provided by the iPlane-project
    :param filename:    name of the file containing the mappings
    :return:            None if a problem occurred; True otherwise
    """
    try:
        PoPFile = open(filename, 'r')
    except IOError:
        print "error: Could not open file '" + filename + "'!\n"
        return None

    for line in PoPFile:
        l = line.rstrip('\r\n')
        if l:
            pair = l.split()
            IPToPoPMapping[pair[0]] = pair[1]
    PoPFile.close()
    return True

def retrieve_traceroute_results(filename, verbose):
    """
    Downloads and parses traceroute-results for the measurement-IDs indicated in file '../logs/<filename>' and write
    results to file '../output/<timestamp>_scheduled_traceroutes.log'
    The input-file has to be located in the input-folder.
    For the exact format to be followed by the input-file, please have a look at the documentation
    The download of user-defined-measurement-results is done via the Atlas-toolbox
    :param filename:    the name of the file containing measurement-IDs
    :param verbose:     if true, the progress will be written to the standard-output
    """
    try:
        udmFile = open(filename, 'r')
    except IOError:
        print "error: Could not open '" + filename + "'!\n"
        return None

    measurementsToAnalyse = list()
    IPsToAnalyse = set()

    for udmLine in udmFile:
        udmL = udmLine.rstrip('\r\n')
        data = udmL.split('\t')
        udms = data[:data.__len__() - 1]
        dstIP = data[data.__len__() - 1]

        for udm in udms:
            resultInfo = subprocess.check_output(['../contrib/udm-result.pl', '--udm', data[0]])
            if not resultInfo.rstrip('\r\n'):
                continue
            resultInfo = resultInfo.split('\n')

            for line in resultInfo:
                if line:
                    if not line.startswith('\t'):     # first line of a result
                        l = line.lstrip().split('\t')
                        nbHop = int(l[5])
                        probeID = l[1]
                        srcIP = l[2]
                        timestamp = l[0]

                        if verbose:
                            print 'Analysing traceroute from ' + srcIP + ' to ' + dstIP + '...\n'

                        currentMeasurement = TracerouteMeasurement()
                        currentMeasurement.addProbeID(probeID)
                        currentMeasurement.addNbHops(nbHop)
                        currentMeasurement.addTimestamp(timestamp)

                        IPsToAnalyse.add(srcIP)
                        currentMeasurement.addIPInfo(srcIP, 'init')
                    else:
                        l = line.lstrip().split('\t')
                        ip = l[1]
                        rtt = l[3]
                        hopIndex = l[0]
                        if rtt != '*':
                            if ip != '*':
                                currentMeasurement.addIPInfo(ip, rtt)
                                IPsToAnalyse.add(ip)
                            else:
                                currentMeasurement.addIPInfo('NA_TR', rtt)
                        else:
                            if ip == '*':
                                currentMeasurement.addIPInfo('NA_TR', '')
                            else:
                                currentMeasurement.addIPInfo(ip, '')
                                IPsToAnalyse.add(ip)

                        #finished analysing - store results for probe
                        if int(hopIndex) >= nbHop:
                            measurementsToAnalyse.append(currentMeasurement)

    # We will do the IP2AS-mapping and store the results to a file
    IPToASMapping = parseIP.mapIPtoAS(IPsToAnalyse, '../lib/GeoIPASNum2.csv', verbose)
    if IPToASMapping == None:
        return None

    if verbose:
        print 'Saving results to file...\n'

    currentTime = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
    for measurement in measurementsToAnalyse:
        measurement.saveToFile(IPToASMapping, currentTime)
    udmFile.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Retrieve and store the results of the launched scheduled traceroutes')

    parser.add_argument('-v', action="version", version="version 1.0")
    parser.add_argument('-n', action="store", dest="filename", help="name of the file the measurement-IDs are stored in")

    arguments = vars(parser.parse_args())

    if not any(arguments.values()):
        parser.error('error: You must specify the filename containing measurement-IDs!')
        exit(1)

    if loadIPToPoPMapping('../lib/ip_to_pop_mapping.txt') == None:
        exit(2)

    retrieve_traceroute_results('../input/' + arguments["filename"], True)

