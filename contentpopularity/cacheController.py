# mPlane Protocol Reference Implementation
# Cache controller code
#
# (c) 2013-2014 mPlane Consortium (http://www.ict-mplane.eu)
#               Author: Maurizio Dusi
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.
#

import sys
import os
import configparser
import argparse
from datetime import datetime
import json
import urllib.parse
import http.client

pri = os.getenv('MPLANE_RI')
if pri is None:
    raise ValueError("environment variable MPLANE_RI has not been set")
sys.path.append(pri)

import mplane.model
import mplane.scheduler
import mplane.utils
import mplane.component

_module_path = os.path.dirname(os.path.abspath(__file__))
_capabilitypath = os.path.join(_module_path, "capabilities")

_controller_address = "127.0.0.1"
_controller_port = 8838
_controller_daemon = '%s:%d' % (_controller_address, _controller_port)

"""
Implements Cache Controller capabilities and services

"""


def services():
    services = []
    services.append(cacheControllerService(get_list_capability()))
    return services


def get_list_capability():
    cap = mplane.model.Capability(label="cache-controller-list",
                                  when="now ... future / 1s")
    cap.add_metadata("System_type", "cache-controller")
    cap.add_metadata("System_ID", "cache-controller-Proxy")
    cap.add_metadata("System_version", "0.1")

    cap.add_parameter("cache.size")
    cap.add_parameter("cache.algo")
    cap.add_parameter("cache.bins")

    cap.add_result_column("time")
    cap.add_result_column("tstat.cache.videos")
    return cap


class cacheControllerService(mplane.scheduler.Service):
    """
    This class handles the capabilities exposed by the proxy:
    executes them, and fills the results

    """

    def __init__(self, cap):
        super(cacheControllerService, self).__init__(cap)

    def run(self, spec, check_interrupt):
        """
        Execute this Service

        """

        start_time = datetime.utcnow()

        _algo = spec.get_parameter_value("cache.algo")
        _csize = spec.get_parameter_value("cache.size")
        _history = spec.get_parameter_value("cache.bins")

        _params = urllib.parse.urlencode({'size': _csize,
                                          'history-soa': _history,
                                          'history-our': _history
                                          }, True)
        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain"}

        conn = http.client.HTTPConnection(_controller_daemon)
        conn.request("POST", "", _params, headers)
        response = conn.getresponse()
        ret = json.loads(response.read().decode('utf-8'))
        conn.close()

        ret_algo = list(filter(lambda x: x['strategy'] == _algo, ret))
        if len(ret_algo) == 0:
            contents = []
        else:
            contents = ret_algo[0]['contents']

        ret = {'time': datetime.utcnow(),
               'tstat.cache.videos': str(contents)[1:-1]}

        end_time = datetime.utcnow()
        print("specification {0}: start = {1} end = {2}".format(
            spec._label, start_time, end_time))

        res = mplane.model.Result(specification=spec)
        res.set_when(mplane.model.When(a=start_time, b=end_time))

        labels = ["time", "tstat.cache.videos"]
        for label in labels:
            if res.has_result_column(label):
                res.set_result_value(label, ret[label])
        # print(mplane.model.unparse_json(res))
        return res


def main():
    """docstring for main"""
    global args
    parser = argparse.ArgumentParser(
        description='run a Cache Controller mPlane proxy')
    parser.add_argument('--config', metavar='conf-file', dest='CONF',
                        help='Configuration file for the component')
    args = parser.parse_args()
    # check if conf file parameter has been inserted in the command line
    if not args.CONF:
        print('\nERROR: missing --config\n')
        parser.print_help()
        exit(1)

    # Read the configuration file
    config = configparser.ConfigParser()
    config.optionxform = str
    config.read(mplane.utils.search_path(args.CONF))

    if config["component"]["workflow"] == "component-initiated":
        component = mplane.component.InitiatorHttpComponent(config)
    elif config["component"]["workflow"] == "client-initiated":
        component = mplane.component.ListenerHttpComponent(config)
    else:
        error = "workflow setting in " + args.CONF + \
            " can only be 'client-initiated' or 'component-initiated'"
        raise ValueError(error)


if __name__ == '__main__':
    main()
