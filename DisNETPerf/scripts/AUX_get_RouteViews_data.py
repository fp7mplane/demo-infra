#!/usr/bin/env python

# Author: Sarah Wassermann <sarah.wassermann@student.ulg.ac.be>

import os

def getASPath(start, end):
    """
    Tries to find an ASPath between the ASes <start> and <end> through RouteViews data
    :param start:   the start-AS of the path
    :param end:     the end-AS of the path
    :return:        a list containing all the AS-hop between <start> and <end> (including <start> and <end>) if a path
                    was found; en empty list otherwise
    """
    if os.path.exists('../lib/routeviews_paths/' + start + '.txt'):
        file = open('../lib/routeviews_paths/' + start + '.txt', 'r')
    else:
        return list()

    for line in file:
        pathList = line.rstrip('\r\n').split()
        if pathList[pathList.__len__() - 1] == end:
            file.close()
            return pathList
    file.close()
    return  list()
