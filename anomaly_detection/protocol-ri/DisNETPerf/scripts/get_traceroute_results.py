#!/usr/bin/env python

# Author: Sarah Wassermann <sarah.wassermann@student.ulg.ac.be>

import argparse
import subprocess

def retrieve_traceroute_results(filename, timestamp):
    """
    Download and parse traceroute-results for the measurement-IDs indicated in file '../logs/<filename>'
    and write results to file '../output/<timestamp>_scheduled_traceroutes.log'
    :param filename:    the name of the file containing measurement-IDs
    :param timestamp:   the timestamp to be added in the name of the file containing results
    """
    try:
        udmFile = open('..logs/' + filename, 'r')
    except IOError:
        print "error: Could not open '..logs/current_scheduled_traceroutes.log'!\n"
        return

    try:
        resultFile = open('..output/' + timestamp + '_scheduled_traceroutes.log', 'w', 1)
    except IOError:
        print "error: Could not open '..output/scheduled_traceroutes.log'!\n"
        udmFile.close()
        return

    for line in udmFile:
        l = line.rstrip('\r\n')
        data = l.split('\t')
        udms = data[:data.__len__() - 1]

        for udm in udms:
            try:
                result = subprocess.check_output(['../contrib/udm-result.pl', '--udm', udm])
            except subprocess.CalledProcessError:
                continue
            resultFile.write(result)

    udmFile.close()
    resultFile.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Retrieve and store the results of the launched scheduled traceroutes')

    parser.add_argument('-v', action="version", version="version 1.0")
    parser.add_argument('-n', action="store", help="name of the file the measurement-IDs are stored in")

    arguments = vars(parser.parse_args())

    if not any(arguments.values()):
        parser.error('error: You must specify the filename containing measurement.IDs!')
        exit(1)