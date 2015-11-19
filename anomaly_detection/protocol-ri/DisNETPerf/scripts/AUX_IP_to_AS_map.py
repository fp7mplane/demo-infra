# Author: Sarah Wassermann <sarah.wassermann@student.ulg.ac.be>

import csv

def IPToInt(ip):
    """
    :param ip: a string representing an IP
    :return: ip converted into an integer
    """
    parts = list(map(int, ip.split('.')))
    return (16777216 * parts[0]) + (65536 * parts[1]) + (256 * parts[2]) + parts[3]

def mapIPtoAS(IPListArg, IPtoASFilename, verbose):
    """
    :param IPListArg: list containing the IPs to be analysed
    :param IPtoASFilename: CSV-file containing IP-to-AS mappings (IPs given in range).
                            Line-format: <IP lower bound> <IP upper bound> <AS>
    :return: a dictionary with an IP as key and the corresponding AS as value
    """
    IPtoASMap = dict()

    try:
        with open(IPtoASFilename, encoding = "ISO-8859-1") as csvfile:
            reader = csv.reader(csvfile)
            IPRangeData = list(reader)
    except IOError:
        if verbose:
            print("error: Could not open '" + IPtoASFilename + "'\n")
        return None
    IPList = list(IPListArg)
    IPList.sort(key=IPToInt)

    currentIndex = 0
    nbOfMappings = IPRangeData.__len__()

    for ip in IPList:
        IP = IPToInt(ip)

        while currentIndex < nbOfMappings:
            mapping = IPRangeData[currentIndex]
            lowerbound, upperbound = int(mapping[0]), int(mapping[1])
            if IP >= lowerbound and IP <= upperbound:
                ASdata = mapping[2].split()
                IPtoASMap[ip] = ASdata[0][2:]
                break
            elif lowerbound > IP: # no match found!
                IPtoASMap[ip] = 'NA_MAP'
                break
            else:
                currentIndex += 1

    csvfile.close()
    return IPtoASMap
