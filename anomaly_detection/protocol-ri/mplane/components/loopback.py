# mPlane Protocol Reference Implementation
# loopback test component code
#
# (c) 2013-2015 mPlane Consortium (http://www.ict-mplane.eu)
#               Author: Brian Trammell
#               (based on an example by Stefano Pentassuglia)
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

import mplane.model
import mplane.scheduler
import mplane.utils
from datetime import datetime


def services():
    # the parameter is passed to this function by component-py,
    # that reads it from the [module_exampleServiceName] section
    # in the config file
    services = [LoopbackTestService(loopback_test_capability())]
    return services

def loopback_test_capability():
    return mplane.model.parse_json(
        """
        {
          "capability": "measure",
          "version":    0,
          "registry":   "http://mplane.corvid.ch/registry/loopback",
          "label":      "test-loopback",
          "when":       "now ... future",
          "parameters": {
                          "test.input" : "*"
                        },
          "results":    ["test.output"]
        }
        """
    )

class LoopbackTestService(mplane.scheduler.Service):
    """
    This class handles the capabilities exposed by the component:
    executes them, and fills the results

    """

    def __init__(self, cap):
        super().__init__(cap)

    def run(self, spec, check_interrupt):
        """ Run a loopback test: copy the input string to the output """

        res = mplane.model.Result(specification=spec)
        res.set_when(mplane.model.When(a=datetime.utcnow()))
        res.set_result_value("test.output",
                             spec.get_parameter_value("test.input"))
        return res
