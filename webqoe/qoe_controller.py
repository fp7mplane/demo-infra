# mPlane Protocol Reference Implementation
# web qoe controller
#
# (c) 2013-2014 mPlane Consortium (http://www.ict-mplane.eu)
#               Author: Marco Milanesio
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
# import json
# import http.client
from .webqoe.reasoner import Reasoner

pri = os.getenv('MPLANE_RI')
if pri is None:
    raise ValueError("environment variable MPLANE_RI has not been set")
sys.path.append(pri)

import mplane.model
import mplane.scheduler
import mplane.utils
import mplane.component

"""
Implements Web QoE Global Diagnosis capabilities and services

"""


def services():
    services = []
    services.append(globalDiagnoseService(global_diagnose_capability()))
    return services


def global_diagnose_capability():
    cap = mplane.model.Capability(label="webqoe-diagnose", when="now + 5m")
    cap.add_metadata("System_type", "QoEReasoner")
    cap.add_metadata("System_ID", "QoEReasoner")
    cap.add_metadata("System_version", "0.1")
    cap.add_parameter("destination.url")
    cap.add_result_column("webqoe.diagnose")
    return cap


class globalDiagnoseService(mplane.scheduler.Service):
    """
    This class handles the capabilities exposed by the proxy:
    executes them, and fills the results

    """

    def __init__(self, cap):
        super(globalDiagnoseService, self).__init__(cap)

    def run(self, spec, check_interrupt):
        """
        Execute this Service

        """

        start_time = datetime.utcnow()
        if not spec.has_parameter("destination.url"):
            raise ValueError("Missing destination.url")

        try:
            r = Reasoner()
            result = r.diagnose(None, spec.get_parameter_value("destination.url"), globaldiag=True)
        except Exception as e:
            result = {"Error": "Something bad happened"}
            print(e)

        # FIXME add parsing json

        end_time = datetime.utcnow()
        print("specification {0}: start = {1} end = {2}".format(spec._label, start_time, end_time))

        res = mplane.model.Result(specification=spec)
        res.set_when(mplane.model.When(a=start_time, b=end_time))

        labels = ["trace", "ws", "problems", "all"]
        for label in labels:
            if res.has_result_column(label):
                res.set_result_value(label, result[label])
        return res


def main():
    """docstring for main"""
    global args
    parser = argparse.ArgumentParser(
        description='run a WebQoE mPlane proxy')
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
