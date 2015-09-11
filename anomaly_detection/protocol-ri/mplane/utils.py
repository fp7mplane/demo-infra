# mPlane Protocol Reference Implementation
# Various Utilities
#
# (c) 2013-2014 mPlane Consortium (http://www.ict-mplane.eu)
#               Author: Stefano Pentassuglia
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
#

import os.path
import re
import mplane.model
import json
import urllib3

def read_setting(filepath, param):
    """
    Reads a setting from the indicated conf file

    """
    with open(filepath,'r') as f:
        for line in f.readlines():
            if line[0] != "#":
                line = line.rstrip('\n')
                if line.split('= ')[0] == param:
                    if line.split('= ')[1] == 'True':
                        return True
                    elif line.split('= ')[1] == 'False':
                        return False
                    else:
                        return line.split('= ')[1]
    return None

def search_path(path):
    """
    Converts every path into absolute paths,
    and checks if file exists.
    Should replace check_file() and normalize_path()

    """
    if path[0] != '/':
        norm_path = os.path.abspath(path)
    else:
        norm_path = path

    if not os.path.exists(norm_path):
        raise ValueError("Error: File " + norm_path + " does not appear to exist.")
        exit(1)

    return norm_path

def check_file(filename):
    """
    Checks if the file exists at the given path

    """
    if not os.path.exists(filename):
        raise ValueError("Error: File " + filename + " does not appear to exist.")
        exit(1)

def normalize_path(path):
    """
    Converts every path into absolute paths

    """
    if path[0] != '/':
        return os.path.abspath(path)
    else:
        return path

def print_then_prompt(line):
    """
    Prints a message on screen, then prints the mplane prompt

    """
    print(line)
    print('|mplane| ', end="", flush = True)
    pass

def add_value_to(container, key, value):
    """
    Adds a value to a dict() of lists

    """
    if key not in container:
        container[key] = [value]
    else:
        container[key].append(value)

def split_stmt_list(msg):
    """
    Splits a JSON array of statements (capabilities or specifications) in
    JSON format into a list of single statements

    """
    json_stmts = json.loads(msg)
    stmts = []
    for json_stmt in json_stmts:
        stmts.append(mplane.model.parse_json(json.dumps(json_stmt)))
    return stmts

def parse_url(url):
    """ Returns a link in string format from an Url object """
    link = url.scheme + "://" + url.host + ":" + str(url.port)
    if url.path.startswith("/"):
        link = link + url.path
    else:
        link = link + "/" + url.path
    return link
