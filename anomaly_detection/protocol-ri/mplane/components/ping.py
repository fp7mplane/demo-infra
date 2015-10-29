#
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#
# mPlane Protocol Reference Implementation
# ICMP Ping probe component code
#
# (c) 2013-2014 mPlane Consortium (http://www.ict-mplane.eu)
#               Author: Brian Trammell <brian@trammell.ch>
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

"""
Implements ICMP ping (delay.twoway.icmp) for integration into 
the mPlane reference implementation.

"""

import re
import subprocess
import collections
from datetime import datetime
import mplane.model
import mplane.scheduler

_pingline_re = re.compile("icmp_seq=(\d+)\s+\S+=(\d+)\s+time=([\d\.]+)\s+ms")

_ping4cmd = "ping"
_ping6cmd = "ping6"
_pingopts = ["-n"]
_pingopt_period = "-i"
_pingopt_count = "-c"
_pingopt_source = "-S"

LOOP4 = "127.0.0.1"
LOOP6 = "::1"

PingValue = collections.namedtuple("PingValue", ["time", "seq", "ttl", "usec"])

def services(ip4addr = None, ip6addr = None):
    services = []
    if ip4addr is not None:
        services.append(PingService(ping4_aggregate_capability(ip4addr)))
        services.append(PingService(ping4_singleton_capability(ip4addr)))
    if ip6addr is not None:
        services.append(PingService(ping6_aggregate_capability(ip6addr)))
        services.append(PingService(ping6_singleton_capability(ip6addr)))
    return services
    
def _parse_ping_line(line):
    m = _pingline_re.search(line)
    if m is None:
        print(line)
        return None
    mg = m.groups()
    return PingValue(datetime.utcnow(), int(mg[0]), int(mg[1]), int(float(mg[2]) * 1000))

def _ping_process(progname, sipaddr, dipaddr, period=None, count=None):
    ping_argv = [progname]
    if period is not None:
        ping_argv += [_pingopt_period, str(period)]
    if count is not None:
        ping_argv += [_pingopt_count, str(count)]
    ping_argv += [_pingopt_source, str(sipaddr)]
    ping_argv += [str(dipaddr)]

    print("running " + " ".join(ping_argv))

    return subprocess.Popen(ping_argv, stdout=subprocess.PIPE)

def _ping4_process(sipaddr, dipaddr, period=None, count=None):
    return _ping_process(_ping4cmd, sipaddr, dipaddr, period, count)

def _ping6_process(sipaddr, dipaddr, period=None, count=None):
    return _ping_process(_ping6cmd, sipaddr, dipaddr, period, count)

def pings_min_delay(pings):
    return min(map(lambda x: x.usec, pings))

def pings_mean_delay(pings):
    return int(sum(map(lambda x: x.usec, pings)) / len(pings))

def pings_median_delay(pings):
    return sorted(map(lambda x: x.usec, pings))[int(len(pings) / 2)]

def pings_max_delay(pings):
    return max(map(lambda x: x.usec, pings))

def pings_start_time(pings):
    return pings[0].time

def pings_end_time(pings):
    return pings[-1].time

def ping4_aggregate_capability(ipaddr):
    cap = mplane.model.Capability(label="ping-average-ip4", when = "now ... future / 1s")
    cap.add_parameter("source.ip4",ipaddr)
    cap.add_parameter("destination.ip4")
    cap.add_result_column("delay.twoway.icmp.us.min")
    cap.add_result_column("delay.twoway.icmp.us.mean")
    cap.add_result_column("delay.twoway.icmp.us.max")
    cap.add_result_column("delay.twoway.icmp.count")
    return cap

def ping4_singleton_capability(ipaddr):
    cap = mplane.model.Capability(label="ping-detail-ip4", when = "now ... future / 1s")
    cap.add_parameter("source.ip4",ipaddr)
    cap.add_parameter("destination.ip4")
    cap.add_result_column("time")
    cap.add_result_column("delay.twoway.icmp.us")
    return cap

def ping6_aggregate_capability(ipaddr):
    cap = mplane.model.Capability(label="ping-average-ip6", when = "now ... future / 1s")
    cap.add_parameter("source.ip6",ipaddr)
    cap.add_parameter("destination.ip6")
    cap.add_result_column("delay.twoway.icmp.us.min")
    cap.add_result_column("delay.twoway.icmp.us.mean")
    cap.add_result_column("delay.twoway.icmp.us.max")
    cap.add_result_column("delay.twoway.icmp.count")
    return cap

def ping6_singleton_capability(ipaddr):
    cap = mplane.model.Capability(label="ping-detail-ip6", when = "now ... future / 1s")
    cap.add_parameter("source.ip6",ipaddr)
    cap.add_parameter("destination.ip6")
    cap.add_result_column("time")
    cap.add_result_column("delay.twoway.icmp.us")
    return cap

class PingService(mplane.scheduler.Service):
    def __init__(self, cap):
        # verify the capability is acceptable
        if not ((cap.has_parameter("source.ip4") or 
                 cap.has_parameter("source.ip6")) and
                (cap.has_parameter("destination.ip4") or 
                 cap.has_parameter("destination.ip6")) and
                (cap.has_result_column("delay.twoway.icmp.us") or
                 cap.has_result_column("delay.twoway.icmp.us.min") or
                 cap.has_result_column("delay.twoway.icmp.us.mean") or                
                 cap.has_result_column("delay.twoway.icmp.us.max") or
                 cap.has_result_column("delay.twoway.icmp.count"))):
            raise ValueError("capability not acceptable")
        super(PingService, self).__init__(cap)

    def run(self, spec, check_interrupt):
         # unpack parameters
        period = int(spec.when().period().total_seconds())
        duration = spec.when().duration().total_seconds()
        if duration is not None and duration > 0:
            count = int(duration / period)
        else:
            count = None

        if spec.has_parameter("destination.ip4"):
            sipaddr = spec.get_parameter_value("source.ip4")
            dipaddr = spec.get_parameter_value("destination.ip4")
            ping_process = _ping4_process(sipaddr, dipaddr, period, count)
        elif spec.has_parameter("destination.ip6"):
            sipaddr = spec.get_parameter_value("source.ip6")
            dipaddr = spec.get_parameter_value("destination.ip6")
            ping_process = _ping6_process(sipaddr, dipaddr, period, count)
        else:
            raise ValueError("Missing destination")

        # read output from ping
        pings = []
        for line in ping_process.stdout:
            if check_interrupt():
                break
            oneping = _parse_ping_line(line.decode("utf-8"))
            if oneping is not None:
                print("ping "+repr(oneping))
                pings.append(oneping)
 
        # shut down and reap
        try:
            ping_process.kill()
        except OSError:
            pass
        ping_process.wait()

        # derive a result from the specification
        res = mplane.model.Result(specification=spec)

        # put actual start and end time into result
        res.set_when(mplane.model.When(a = pings_start_time(pings), b = pings_end_time(pings)))

        # are we returning aggregates or raw numbers?
        if res.has_result_column("delay.twoway.icmp.us"):
            # raw numbers
            for i, oneping in enumerate(pings):
                res.set_result_value("delay.twoway.icmp.us", oneping.usec, i)
            if res.has_result_column("time"):
                for i, oneping in enumerate(pings):
                    res.set_result_value("time", oneping.time, i)
        else:
            # aggregates. single row.
            if res.has_result_column("delay.twoway.icmp.us.min"):
                res.set_result_value("delay.twoway.icmp.us.min", pings_min_delay(pings))
            if res.has_result_column("delay.twoway.icmp.us.mean"):
                res.set_result_value("delay.twoway.icmp.us.mean", pings_mean_delay(pings))
            if res.has_result_column("delay.twoway.icmp.us.median"):
                res.set_result_value("delay.twoway.icmp.us.median", pings_median_delay(pings))
            if res.has_result_column("delay.twoway.icmp.us.max"):
                res.set_result_value("delay.twoway.icmp.us.max", pings_max_delay(pings))
            if res.has_result_column("delay.twoway.icmp.count"):
                res.set_result_value("delay.twoway.icmp.count", len(pings))


        return res