#
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#
# mPlane Protocol Reference Implementation
# Information Model and Element Registry
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
Information model and element registry for the mPlane protocol.

This module implements Statements and Notifications, the core
messages used by the mPlane protocol to describe measurement
and query schemas, and various other classes to support them.

There are three kinds of Statements:

    - Capability represents something a component can do
    - Specification tells a component to do something it
      advertised a Capability for
    - Result returns the results for a Specification in-band

Notifications are used to transfer other information between
components and clients. There are four kinds of Notifications:

    - Receipt notifies that a Result is not yet ready or
      that the results of an operation will be indirectly exported.
    - Redemption is a subsequent attempt to redeem a Receipt.
    - Withdrawal notifies that a Capability is no longer available.
    - Interrupt notifies that a running Specification should be stopped.

To see how all this fits together, let's simulate the message exchange
in a simple ping measurement. Initially, we have to load the default element
registry and programatically create a new empty Capability, as it would
be advertised by the component.

>>> import mplane
>>> import json
>>> mplane.model.initialize_registry()
>>> cap = mplane.model.Capability()

First, we set a temporal scope for the capability. Probe components
generally advertise a temporal scope from the present stretching
into the indeterminate future. In this case, we advertise that the
measurement performed is periodic, by setting the minimum period
supported by the capability: one ping per second.

>>> cap.set_when("now ... future / 1s")

We can only ping from one IPv4 address, to any IPv4 address.
Adding a parameter without a constraint makes it unconstrained:

>>> cap.add_parameter("source.ip4", "10.0.27.2")
>>> cap.add_parameter("destination.ip4")

Then we define the result columns this measurement can produce. Here,
we want quick reporting of min, max, and mean delays, as well as a
total count of singleton measurements taken and packets lost:

>>> cap.add_result_column("delay.twoway.icmp.us.min")
>>> cap.add_result_column("delay.twoway.icmp.us.max")
>>> cap.add_result_column("delay.twoway.icmp.us.mean")
>>> cap.add_result_column("delay.twoway.icmp.count")
>>> cap.add_result_column("packets.lost")

Now we have a capability we could transform into JSON and make it
available to clients via the mPlane protocol, or via static
download or configuration:

>>> capjson = mplane.model.unparse_json(cap)
>>> capjson # doctest: +SKIP
'{"capability": "measure",
  "version": 1,
  "registry": "http://ict-mplane.eu/registry/core",
  "when": "now ... future / 1s",
  "parameters": {"source.ip4": "10.0.27.2",
                 "destination.ip4": "*"},
  "results": ["delay.twoway.icmp.us.min",
              "delay.twoway.icmp.us.max",
              "delay.twoway.icmp.us.mean",
              "delay.twoway.icmp.count",
              "packets.lost"]}'

On the client side, we'd receive this capability as a JSON object and turn it
into a capability, from which we generate a specification:

>>> clicap = mplane.model.parse_json(capjson)
>>> spec = mplane.model.Specification(capability=clicap)
>>> spec
<specification: measure when now ... future / 1s token e00d7fe8 schema 5ce99352 p(v)/m/r 2(1)/0/5>

Here we have a specification with a given token, schema, and 2 parameters,
no metadata, and five result columns.

.. note:: The schema of the statement is identified by a
          schema hash, the first eight hex digits of which are shown for
          diagnostic purposes. Statements with identical sets of parameters
          and columns (schemas) will have identical schema hashes. Likewise,
          the token is defined by the schema as well as the parameter values.

First, let's fill in a specific temporal scope for the measurement:

>>> spec.set_when("2017-12-24 22:18:42 + 1m / 1s")

And then let's fill in some parameters. All od the parameters whose
single values are already given by their constraints (in this case, source.ip4)
have already been filled in. So let's start with the destination.
Note that strings are accepted and automatically parsed using each
parameter's primitive type:

>>> spec.set_parameter_value("destination.ip4", "10.0.37.2")

And now we can transform this specification and send it back to
the component from which we got the capability:

>>> specjson = mplane.model.unparse_json(spec)
>>> specjson # doctest: +SKIP
'{"specification": "measure",
  "version": 1,
  "registry": "http://ict-mplane.eu/registry/core",
  "token": "ea839b56bc3f6004e95d780d7a64d899",
  "when": "2017-12-24 22:18:42.000000 + 1m / 1s",
  "parameters": {"source.ip4": "10.0.27.2",
                 "destination.ip4": "10.0.37.2"},
  "results": ["delay.twoway.icmp.us.min",
              "delay.twoway.icmp.us.max",
              "delay.twoway.icmp.us.mean",
              "delay.twoway.icmp.count",
              "packets.lost"]}'

On the component side, likewise, we'd receive this specification as a JSON
object and turn it back into a specification:

>>> comspec = mplane.model.parse_json(specjson)

The component would determine the measurement, query, or other operation to
run given by the specification, then extract the necessary parameter values, e.g.:

>>> comspec.get_parameter_value("destination.ip4")
IPv4Address('10.0.37.2')
>>> comspec.when().period()
datetime.timedelta(0, 1)

After running the measurement, the component would return the results
by assigning values to parameters which changed and result columns
measured:

>>> res = mplane.model.Result(specification=comspec)
>>> res.set_when("2017-12-24 22:18:42.993000 ... 2017-12-24 22:19:42.991000")
>>> res.set_result_value("delay.twoway.icmp.us.min", 33155)
>>> res.set_result_value("delay.twoway.icmp.us.mean", 55166)
>>> res.set_result_value("delay.twoway.icmp.us.max", 192307)
>>> res.set_result_value("delay.twoway.icmp.count", 58220)
>>> res.set_result_value("packets.lost", 2)

The result can then be serialized and sent back to the client:

>>> resjson = mplane.model.unparse_json(res)
>>> resjson # doctest: +SKIP
'{"result": "measure",
  "version": 1,
  "registry": "http://ict-mplane.eu/registry/core",
  "token": "ea839b56bc3f6004e95d780d7a64d899",
  "when": "2017-12-24 22:18:42.993000 ... 2017-12-24 22:19:42.991000",
  "parameters": {"source.ip4": "10.0.27.2",
                 "destination.ip4": "10.0.37.2"},
  "results": ["delay.twoway.icmp.us.min",
              "delay.twoway.icmp.us.max",
              "delay.twoway.icmp.us.mean",
              "delay.twoway.icmp.count",
              "packets.lost"],
  "resultvalues": [["33155", "192307", "55166", "58220", "2"]]}'

which can transform them back to a result and extract the values:

>>> clires = mplane.model.parse_json(resjson)
>>> clires
<result: measure when 2017-12-24 22:18:42.993000 ... 2017-12-24 22:19:42.991000 token e00d7fe8 schema 5ce99352 p/m/r(r) 2/0/5(1)>

If the component cannot return results immediately (for example, because
the measurement will take some time), it can return a receipt instead:

>>> rcpt = mplane.model.Receipt(specification=comspec)

This receipt contains all the information in the specification, as well as a token
which can be used to quickly identify it in the future.

>>> rcpt.get_token()
'e00d7fe813cf17eeeea37b313dcfa4e7'

.. note:: The mPlane protocol specification allows components to assign tokens
          however they like. In the reference implementation, the default token
          is based on a hash like the schema hash: statements with the same verb,
          schema, parameter values, and metadata will have identical default tokens.
          A component could, however, assign serial-number based tokens, or tokens
          mapping to structures in its own filesystem, etc.

>>> jsonrcpt = mplane.model.unparse_json(rcpt)
>>> jsonrcpt # doctest: +SKIP
'{"receipt": "measure",
  "version": 1,
  "registry": "http://ict-mplane.eu/registry/core",
  "token": "e00d7fe813cf17eeeea37b313dcfa4e7",
  "when": "2017-12-24 22:18:42.000000 + 1m / 1s",
  "parameters": {"destination.ip4": "10.0.37.2",
                 "source.ip4": "10.0.27.2"},
  "results": ["delay.twoway.icmp.us.min",
              "delay.twoway.icmp.us.max",
              "delay.twoway.icmp.us.mean",
              "delay.twoway.icmp.count",
              "packets.lost"],}'

The component keeps the receipt, keyed by token, and returns it to the
client in a message. The client then which generates a future redemption
referring to this receipt to retrieve the results:

>>> clircpt = mplane.model.parse_json(jsonrcpt)
>>> clircpt
<receipt: e00d7fe813cf17eeeea37b313dcfa4e7>
>>> rdpt = mplane.model.Redemption(receipt=clircpt)
>>> rdpt
<redemption: e00d7fe813cf17eeeea37b313dcfa4e7>

Note here that the redemption has the same token as the receipt;
just the token may be sent back to the component to retrieve the
results:

>>> mplane.model.unparse_json(rdpt, token_only=True) # doctest: +SKIP
'{"redemption": "measure",
  "version": 1,
  "registry": "http://ict-mplane.eu/registry/core",
  "token": "e00d7fe813cf17eeeea37b313dcfa4e7"
}'

As long as the measurement is running, the client can stop the measurement by sending an
interrupt:

>>> irpt = mplane.model.Interrupt(specification=spec)
>>> jsonrcpt = mplane.model.unparse_json(irpt)

The component receives the interrupt, stops the measurement and returns the results of
performed measurement.

Otherwise, in case the component cannot perform the speficied operation, it sends a
withdrawal to cancel the previously advertised capability:

>>> wtdr = mplane.model.Withdrawal(capability=cap)
>>> mplane.model.unparse_json(wtdr) # doctest: +SKIP
'{"withdrawal": "measure",
"version": 1,
"registry": "http://ict-mplane.eu/registry/core",
"token": "d7e9df75145e209e144bf9c06e7a9d2f",
"when": "now ... future / 1s",
"parameters": {"destination.ip4": "*",
"source.ip4": "10.0.27.2"},
"results": ["delay.twoway.icmp.us.min",
"delay.twoway.icmp.us.max",
"delay.twoway.icmp.us.mean",
"delay.twoway.icmp.count",
"packets.lost"]
}'

Further several messages can be send at once by using an Envelope,
e.g. a component could announce serval capabilites at once.

In case of our simple ping component we create a second capability
that only provides the mean of the measurement values:

>>> cap2 = mplane.model.Capability()
>>> cap2.set_when("now ... future / 1s")
>>> cap2.add_parameter("source.ip4", "10.0.27.2")
>>> cap2.add_parameter("destination.ip4")
>>> cap2.add_result_column("delay.twoway.icmp.us.mean")

Now we create an Envelope and append the two capabilities.

>>> env = mplane.model.Envelope()
>>> env.append_message(cap)
>>> env.append_message(cap2)
>>> env  # doctest: +SKIP
<Envelope message (2):
 <capability: measure when now ... future / 1s token d7e9df75 schema 5ce99352 p/m/r 2/0/5>
 <capability: measure when now ... future / 1s token a9ec7fce schema ea37cea5 p/m/r 2/0/1>
>

Similar as with every other message this Envelope is serialized and send to the client:

>>> envjson = mplane.model.unparse_json(env)

The client receives the Envelope and decomposes the encapsulated messages:

>>> clienv = mplane.model.parse_json(envjson)
>>> messages = [message for message in clienv.messages()]
"""

try:
    from ipaddress import ip_address
except ImportError:
    from ipaddr import IPAddress as ip_address

from datetime import datetime, timedelta, timezone
from copy import copy, deepcopy
import urllib.request
import urllib.parse
import collections
import functools
import operator
import hashlib
import json
import yaml
import re
import os

from mplane.utils import normalize_path

#######################################################################
# String constants for protocol framing
#######################################################################

ELEMENT_SEP = "."

RANGE_SEP = " ... "
DURATION_SEP = " + "
PERIOD_SEP = " / "
SET_SEP = ","
ANCHOR_SEP = "#"
INNER_WHEN_SEP_START = " { "
INNER_WHEN_SEP_END = " } "

CONSTRAINT_ALL = "*"
VALUE_NONE = "*"

TIME_PAST = "past"
TIME_NOW = "now"
TIME_FUTURE = "future"
#FIX ME
MAX_TIME = 100000

WHEN_REPEAT = "repeat "
WHEN_CRON = " cron "

VERB_MEASURE = "measure"
VERB_QUERY = "query"
VERB_COLLECT = "collect"
VERB_STORE = "store"
VERB_CALLBACK = "callback"

KEY_PARAMETERS = "parameters"
KEY_METADATA = "metadata"
KEY_RESULTS = "results"
KEY_RESULTVALUES = "resultvalues"
KEY_TOKEN = "token"
KEY_MESSAGE = "message"
KEY_LINK = "link"
KEY_EXPORT = "export"
KEY_VERSION = "version"
KEY_WHEN = "when"
KEY_REGISTRY = "registry"
KEY_LABEL = "label"
KEY_CONTENTS = "contents"

KEY_MONTHS = "months"
KEY_DAYS = "days"
KEY_WEEKDAYS = "weekdays"
KEY_HOURS = "hours"
KEY_MINUTES = "minutes"
KEY_SECONDS = "seconds"

KIND_CAPABILITY = "capability"
KIND_SPECIFICATION = "specification"
KIND_RESULT = "result"
KIND_RECEIPT = "receipt"
KIND_REDEMPTION = "redemption"
KIND_INDIRECTION = "indirection"
KIND_WITHDRAWAL = "withdrawal"
KIND_INTERRUPT = "interrupt"
KIND_EXCEPTION = "exception"
KIND_ENVELOPE = "envelope"

ENVELOPE_MESSAGE = "message"
ENVELOPE_STATEMENT = "statement"
ENVELOPE_NOTIFICATION = "notification"

KEY_REGFMT = "registry-format"
KEY_REGREV = "registry-revision"
KEY_REGURI = "registry-uri"
KEY_REGINCLUDE = "includes"
KEY_ELEMENTS = "elements"
KEY_ELEMNAME = "name"
KEY_ELEMPRIM = "prim"
KEY_ELEMDESC = "desc"
REGURI_DEFAULT = "http://ict-mplane.eu/registry/core"
REGFMT_FLAT = "mplane-0"

#######################################################################
# Protocol constants
#######################################################################

MPLANE_VERSION = 1 # version 1 -- D1.4 protocol, interop guarantee

#######################################################################
# Reference implementation constants
#######################################################################

# Hash length in __repr__ strings
REPHL = 8

#######################################################################
# Universal parse and unparse functions for times and durations
#######################################################################

_iso8601_pat = '(\d+-\d+-\d+)(\s+\d+:\d+(:\d+)?)?(\.\d+)?'
_iso8601_re = re.compile(_iso8601_pat)
_iso8601_fmt = { 'us': '%Y-%m-%d %H:%M:%S.%f',
                  's': '%Y-%m-%d %H:%M:%S',
                  'm': '%Y-%m-%d %H:%M',
                  'd': '%Y-%m-%d'}

_dur_pat = '((\d+)d)?((\d+)h)?((\d+)m)?((\d+)s)?'
_dur_re = re.compile(_dur_pat)
_dur_seclabel = ( (86400, 'd'),
                  ( 3600, 'h'),
                  (   60, 'm'),
                  (    1, 's') )

_innerwhen_pat = '\{ (.*?) \}'
_innerwhen_re = re.compile(_innerwhen_pat)


def parse_time(valstr):
    if valstr is None:
        return None
    elif valstr == TIME_PAST:
        return time_past
    elif valstr == TIME_FUTURE:
        return time_future
    elif valstr == TIME_NOW:
        return time_now
    else:
        m = _iso8601_re.match(valstr)
        if m:
            mstr = m.group(0)
            mg = m.groups()
            if mg[3]:
                # FIXME this only handles millseconds; we should handle
                # general precision fractional seconds correctly
                dt = datetime.strptime(mstr, "%Y-%m-%d %H:%M:%S.%f")
            elif mg[2]:
                dt = datetime.strptime(mstr, "%Y-%m-%d %H:%M:%S")
            elif mg[1]:
                dt = datetime.strptime(mstr, "%Y-%m-%d %H:%M")
            else:
                dt = datetime.strptime(mstr, "%Y-%m-%d")
            return dt
        else:
            raise ValueError(repr(valstr)+" does not appear to be an mPlane timestamp")

def unparse_time(valts, precision="us"):
    if isinstance(valts, datetime):
        return valts.strftime(_iso8601_fmt[precision])
    else:
        return str(valts)

def parse_dur(valstr):
    if valstr is None:
        return None
    else:
        m = _dur_re.match(valstr)
        if "inf" == valstr:
            return timedelta(seconds=MAX_TIME*_dur_seclabel[0][0])
        elif m:
            mg = m.groups()
            valsec = 0
            for i in range(4):
                if mg[2*i + 1]:
                    valsec += _dur_seclabel[i][0] * int(mg[2*i + 1])
            return timedelta(seconds=valsec)
        else:
            raise ValueError(repr(valstr)+" does not appear to be an mPlane duration")

def unparse_dur(valtd):
    valsec = int(valtd.total_seconds())
    valstr = ""
    for i in range(4):
        if valsec >= _dur_seclabel[i][0]:
            valunit = int(valsec / _dur_seclabel[i][0])
            valstr += str(valunit) + _dur_seclabel[i][1]
            valsec -= valunit * _dur_seclabel[i][0]
    if len(valstr) == 0:
        valstr = "0s"
    return valstr

#######################################################################
# Temporal Scoping and Scheduling
#######################################################################

class _PastTime:
    """
    Class representing the indeterminate past.
    Do not instantiate; use the time_past instance of this class.

    """
    def __str__(self):
        return TIME_PAST

    def __repr__(self):
        return "mplane.model.time_past"

    def strftime(self, ign):
        return str(self)

time_past = _PastTime()

class _NowTime:
    """
    Class representing the present.
    Do not instantiate; use the time_now instance of this class.

    """
    def __str__(self):
        return TIME_NOW

    def __repr__(self):
        return "mplane.model.time_now"

    def strftime(self, ign):
        return str(self)

time_now = _NowTime()

class _FutureTime:
    """
    Class representing the indeterminate future.
    Do not instantiate; use the time_future instance of this class.

    """
    def __str__(self):
        return TIME_FUTURE

    def __repr__(self):
        return "mplane.model.time_future"

    def strftime(self, ign):
        return str(self)

time_future = _FutureTime()

def _parse_numset(valstr):
    return set(map(int, valstr.split(SET_SEP)))

def _unparse_numset(valset):
    return SET_SEP.join(map(str, sorted(list(valset))))

_dow_label = ('mo', 'tu', 'we', 'th', 'fr', 'sa', 'so')
_dow_number = { k: v for (v, k) in enumerate(_dow_label) }

def _parse_wdayset(valstr):
    return set(map(lambda x:_dow_number[x], valstr.split(SET_SEP)))

def _unparse_wdayset(valset):
    return SET_SEP.join(map(lambda x: _dow_label[x], sorted(list(valset))))


class _Crontab(object):
    def __init__(self):
        super().__init__()
        self._months = set()
        self._days = set()
        self._weekdays = set()
        self._hours = set()
        self._minutes = set()
        self._seconds = set()

    def _parse_value(self, val):
        # Check if this is a range
        rangesplit = val.split('-')
        if len(rangesplit) > 1:
            return set(range(int(rangesplit[0]),int(rangesplit[1])+1))

        # Parse numset
        return _parse_numset(val)

    def _parse(self, valstr):
        valsplit = valstr.split()

        if len(valsplit) != 6:
            raise ValueError(repr(valstr)+" does not appear to be a mPlane crontab")

        self._seconds = set(range(0,60)) if (valsplit[0] == '*') else self._parse_value(valsplit[0])
        self._minutes = set(range(0,60)) if (valsplit[1] == '*') else self._parse_value(valsplit[1])
        self._hours = set(range(0,60)) if (valsplit[2] == '*') else self._parse_value(valsplit[2])
        self._days = set(range(1,32)) if (valsplit[3] == '*') else self._parse_value(valsplit[3])
        self._weekdays = set(range(0,7)) if (valsplit[4] == '*') else self._parse_value(valsplit[4])
        self._months = set(range(1,13)) if (valsplit[5] == '*') else self._parse_value(valsplit[5])

    def __str__(self):
        return" ".join([_unparse_numset(self._seconds),
                        _unparse_numset(self._minutes),
                        _unparse_numset(self._hours),
                        _unparse_numset(self._days),
                        _unparse_numset(self._weekdays),
                        _unparse_numset(self._months)])

    def __repr__(self):
        return "cron "+str(self)

class When(object):
    """
    Defines the temporal scopes for capabilities, results, or
    single measurement specifications.

    """
    def __init__(self, valstr=None, a=None, b=None, duration=None, period=None,
                 repeated=False, inner_duration=None, inner_period=None, crontab=None):
        super().__init__()
        self._a = a
        self._b = b
        self._duration = duration
        self._period = period
        self._repeated = repeated
        self._inner_duration = inner_duration
        self._inner_period = inner_period
        self._crontab = crontab

        if valstr is not None:
            self._parse(valstr)

    def _parse(self, valstr):
        # First check if this is a repeated measurement
        valsplit = valstr.split(WHEN_REPEAT)
        if len(valsplit) > 1:
            self._repeated = True

            # Remove 'repeat '
            valstr = valsplit[1]

            # Check for inner when
            innervalstr = _innerwhen_re.search(valstr)
            if innervalstr:
                innervalstr = innervalstr.group(1)
                # check if inner-when begins with 'now'
                if not innervalstr.startswith(TIME_NOW):
                    raise ValueError(repr(valstr)+" does not appear to be an mPlane repeated-when (inner when has to be relative to now)")

                # Separate the period from the value and parse it
                valsplit = innervalstr.split(PERIOD_SEP)
                if len(valsplit) > 1:
                    (innervalstr, perstr) = valsplit
                    self._inner_period = parse_dur(perstr)
                else:
                    self._period = None

                # then try to split duration
                valsplit = innervalstr.split(DURATION_SEP)
                if len(valsplit) > 1:
                    (innervalstr, durstr) = valsplit
                    self._inner_duration = parse_dur(durstr)
                    valsplit = [innervalstr]
                else:
                    self._inner_duration = None

            # Remove inner when
            valsplit = valstr.split(INNER_WHEN_SEP_START)[0]

            # Finally check for a crontab
            valsplit = valsplit.split(WHEN_CRON)
            if len(valsplit) > 1:
                # remove inner when and parse the crontab
                self._crontab = _Crontab()
                self._crontab._parse(valsplit[1])
            else:
                self._crontab = None

            # Remove crontab
            valstr = valsplit[0]
        else:
            self._inner_duration = None
            self._inner_period = None
            self._crontab = None

        # Outer-when or simple-when
        # separate the period from the value and parse it
        valsplit = valstr.split(PERIOD_SEP)
        if len(valsplit) > 1:
            (valstr, perstr) = valsplit
            self._period = parse_dur(perstr)
        else:
            self._period = None

        # then try to split duration or range
        valsplit = valstr.split(DURATION_SEP)
        if len(valsplit) > 1:
            (valstr, durstr) = valsplit
            self._duration = parse_dur(durstr)
            valsplit = [valstr]
        else:
            self._duration = None
            valsplit = valstr.split(RANGE_SEP)

        # if this is a repeated-when without a cron, period has to be set
        if self._repeated and self._crontab is None and self._period is None:
            raise ValueError(repr(valstr)+" does not appear to be an mPlane repeated-when (no duration or cron set)")

        # if this is a repeated-when with cron, period must not be set
        if self._repeated and self._crontab and self._period:
            raise ValueError(repr(valstr)+" does not appear to be an mPlane repeated-when (duration and cron set at the same time)")

        self._a = parse_time(valsplit[0])
        if len(valsplit) > 1:
            self._b = parse_time(valsplit[1])
        else:
            self._b = None

    def __str__(self):
        if self._repeated:
            valstr = "".join((WHEN_REPEAT, unparse_time(self._a)))
        else:
            valstr = "".join((unparse_time(self._a)))

        if self._b is not None:
            valstr = "".join((valstr, RANGE_SEP, unparse_time(self._b)))
        elif self._duration is not None:
            valstr = "".join((valstr, DURATION_SEP, unparse_dur(self._duration)))

        if self._period is not None:
            valstr = "".join((valstr, PERIOD_SEP, unparse_dur(self._period)))

        if self._crontab is not None:
            valstr = "".join((valstr, WHEN_CRON, str(self._crontab)))

        if self._inner_duration is not None:
            valstr = "".join((valstr, INNER_WHEN_SEP_START, TIME_NOW, DURATION_SEP, unparse_dur(self._inner_duration)))

            if self._inner_period is not None:
                valstr = "".join((valstr, PERIOD_SEP, unparse_dur(self._inner_period)))

            valstr = "".join((valstr, INNER_WHEN_SEP_END))

        return valstr

    def __repr__(self):
        return "<When: "+str(self)+">"

    def is_immediate(self):
        """Returns True if this is an immediate scope (i.e., starts now)."""
        return self._a is time_now

    def is_forever(self):
        """Returns True if this scope ends in the indeterminate future."""
        return self._b is time_future

    def is_past(self):
        """Returns True if this is an indefinite past scope."""
        return self._a is time_past and self._b is time_now

    def is_future(self):
        """Returns True if this is an indefinite future scope."""
        return self._a is time_now and self._b is time_future

    def is_infinite(self):
        """
        Returns True if this scope is completely infinite
        (from the infinite past to the infinite future).

        """
        return self._a is time_past and self._b is time_future

    def is_definite(self):
        """
        Returns True if this scope defines a definite time
        or a definite time interval.

        """
        if self._b is None:
            return isinstance(self._a, datetime)
        else:
            return isinstance(self._a, datetime) and isinstance(self._b, datetime)

    def is_singleton(self):
        """
        Returns True if this temporal scope refers to a
        singleton measurement. Used in scheduling an enclosing
        Specification; has no meaning for Capabilities
        or Results.

        """
        return self._a is not None and self._b is None and self.duration() is None

    def is_repeated(self):
        """
        Return True if this temporal scope referes to a
        repeated when.
        """
        return self._repeated

    def datetimes(self, tzero=None):
        """
        Return start and end times as absolute timestamps
        for this temporal scope, relative to a given tzero.
        """

        if tzero is None:
            tzero = datetime.utcnow()

        if self._a is time_now:
            start = tzero
        elif self._a is time_past:
            start = None
        else:
            start = self._a

        if self._b is time_now:
            end = tzero
        elif self._b is time_future:
            end = None
        elif self._b is None:
            if self.duration() is not None:
                end = start + self.duration()
            else:
                end = start
        else:
            end = self._b

        return (start, end)

    def duration(self, tzero=None):
        """
        Return the duration of this temporal scope as a timedelta.

        If the temporal scope is indefinite in the future, returns None.
        """
        if self._duration is not None:
            return self._duration
        elif self._b is None:
            return timedelta()
        elif self._b is time_future:
            return None
        else:
            (start, end) = self.datetimes(tzero)
            return end - start

    def period(self):
        """Returns the period of this temporal scope."""
        return self._period

    def timer_delays(self, tzero=None):
        """
        Returns a tuple with delays for timers to signal the start and end of
        a temporal scope, given a specified time zero, which defaults to the
        current system time.

        The start delay is defined to be zero if the scheduled start time has
        already passed or the temporal scope is immediate (i.e., starts now).
        The start delay is None if the temporal scope has expired (that is,
        the current time is after the calculated end time).

        The end delay is defined to be None if the temporal scope has already
        expired, or if the temporal scope has no scheduled end (is infinite or
        a singleton). End delays are calculated to give priority to duration
        when a temporal scope is expressed in terms of duration, and to
        prioritize end time otherwise.

        Used in scheduling an enclosing Specification for execution.
        Has no meaning for Capabilities or Results.

        """
        # default to current time
        if tzero is None:
            tzero = datetime.utcnow()

        # get datetimes
        (start, end) = self.datetimes(tzero=tzero)

        # determine start delay, account for late start
        sd = (start - tzero).total_seconds()
        if sd < 0:
            sd = 0

        # determine end delay
        if self._b is not None and self._b is not time_future:
            ed = (end - tzero).total_seconds()
        elif self.duration() is not None:
            ed = sd + self.duration().total_seconds()
        else:
            ed = None

        # detect expired temporal scope
        if ed is not None and ed < 0:
            sd = None
            ed = None

        return (sd, ed)

    def sort_scope(self, t, tzero=None):
        """
        Returns < 0 if time t falls before this scope,
        0 if time t falls within the scope,
        or > 0 if time t falls after this scope.

        """

        # Special handling for "now"
        if t is time_now:
            if self._a is time_now or self._b is time_now:
                return 0
            else:
                if tzero is None:
                    tzero = datetime.utcnow()
                t = tzero

        # Get concrete time range
        (start, end) = self.datetimes(tzero=tzero)

        if start and t < start:
            return (t - start).total_seconds()
        elif end and t > end:
            return (t - end).total_seconds()
        else:
            return 0

    def in_scope(self, t, tzero=None):
        """
        Returns True if time t falls within this scope.

        """
        return self.sort_scope(t, tzero) == 0

    def follows(self, s, tzero=None):
        """
        Returns True if this scope follows (is contained by) another.

        """
        if not self._repeated and s.period() is not None and (self.period() is None or self.period() < s.period()):
            return False
        if self._repeated and s.period() is not None and (self._inner_period is None or self._inner_period < s.period()):
            return False
        if s.in_scope(self._a, tzero):
            return True
        if isinstance(self._b, datetime) and s.in_scope(self._b, tzero):
            return True
        else:
            return False

    def iterator(self, tzero=None):
        """
        Returns an iterator over When statements generated by a repeated when.

        """
        if not self._repeated:
            raise Exception("Can't get iterator for non-repeated when")

        # default to now, zero microseconds, initialize minus one second
        if tzero is None:
            t = datetime.utcnow().replace(microsecond=0)
        else:
            t = tzero

        # get base period (default 1s) and
        period = self.period()
        if period is None:
            period = timedelta(seconds=1)

        # fast forward if necessary
        lag = self.sort_scope(t, tzero)
        if lag < 0:
            t += timedelta(seconds=-lag)

        tzero = t

        # loop through time by period and check for match
        t -= period
        # repeat with cron
        if self._crontab:
            while True:
                t += period
                if self.sort_scope(t, tzero) > 0:
                    break
                if len(self._crontab._seconds) and (t.second not in self._crontab._seconds):
                    continue
                if len(self._crontab._minutes) and (t.minute not in self._crontab._minutes):
                    continue
                if len(self._crontab._hours) and (t.hour not in self._crontab._hours):
                    continue
                if len(self._crontab._days) and (t.day not in self._crontab._days):
                    continue
                if len(self._crontab._weekdays) and ((t.weekday() + 1) % 7 not in self._crontab._weekdays):
                    continue
                if len(self._crontab._months) and (t.month not in self._crontab._months):
                    continue
                yield When(a=t, period=self._inner_period, duration=self._inner_duration)
        # repeat without cron
        else:
            while True:
                t += period
                if self.sort_scope(t, tzero) > 0:
                    break

                yield When(a=t, period=self._inner_period, duration=self._inner_duration)

when_infinite = When(a=time_past, b=time_future)

# class Schedule(object):
#     """
#     Defines a schedule for repeated operations based on crontab-like
#     sets of months, days, days of weeks, hours, minutes, and seconds.
#     Used to specify repetitions of single measurements in a Specification.
#     Designed to be broadly compatible with LMAP calendar-based scheduling.

#     This class is not yet fully implemented or integrated into the
#     information model.

#     """
#     def __init__(self, dictval=None, when=None):
#         super().__init__()
#         self._when = when
#         self._months = set()
#         self._days = set()
#         self._weekdays = set()
#         self._hours = set()
#         self._minutes = set()
#         self._seconds = set()

#         if dictval is not None:
#             self._from_dict(dictval)

#     def __repr__(self):
#         rs = "<Schedule "
#         if self._when is not None:
#             rs += repr(self._when) + " "
#         rs += "cron "
#         rs += "/".join(map(str, [len(self._months),
#                                  len(self._days),
#                                  len(self._weekdays),
#                                  len(self._hours),
#                                  len(self._minutes),
#                                  len(self._seconds)]))
#         rs += ">"
#         return rs

#     def to_dict(self):
#         """
#         Represents this schedule as a dictionary (for serialization).

#         """
#         d = {}
#         if self._when:
#             d[KEY_WHEN] = str(self._when)
#         if len(self._months):
#             d[KEY_MONTHS] = _unparse_numset(self._months)
#         if len(self._days):
#             d[KEY_DAYS] = _unparse_numset(self._days)
#         if len(self._weekdays):
#             d[KEY_WEEKDAYS] = _unparse_wdayset(self._weekdays)
#         if len(self._hours):
#             d[KEY_HOURS] = _unparse_numset(self._hours)
#         if len(self._minutes):
#             d[KEY_MINUTES] = _unparse_numset(self._minutes)
#         if len(self._seconds):
#             d[KEY_SECONDS] = _unparse_numset(self._seconds)
#         return d

#     def _from_dict(self, d):
#         if KEY_WHEN in d:
#             self._when = When(valstr=d[KEY_WHEN])
#         if KEY_MONTHS in d:
#             self._months = _parse_numset(d[KEY_MONTHS])
#         if KEY_DAYS in d:
#             self._days = _parse_numset(d[KEY_DAYS])
#         if KEY_WEEKDAYS in d:
#             self._weekdays = _parse_wdayset(d[KEY_WEEKDAYS])
#         if KEY_HOURS in d:
#             self._hours = _parse_numset(d[KEY_HOURS])
#         if KEY_MINUTES in d:
#             self._minutes = _parse_numset(d[KEY_MINUTES])
#         if KEY_SECONDS in d:
#             self._seconds = _parse_numset(d[KEY_SECONDS])

#     def datetime_iterator(self, t=None):
#         """
#         Returns an iterator over datetimes generated by the schedule
#         and period.

#         """
#         # default to now, zero microseconds, initialize minus one second
#         if t is None:
#             t = datetime.utcnow().replace(microsecond=0)

#         # get base period (default 1s) and
#         period = None
#         if self._when is not None:
#             period = self._when.period()
#         if period is None:
#             period = timedelta(seconds=1)

#         # fast forward if necessary
#         lag = self._when.sort_scope(t)
#         if lag < 0:
#             t += timedelta(seconds=-lag)

#         # loop through time by period and check for match
#         t -= period
#         while True:
#             t += period
#             if self._when is not None and not self._when.in_scope(t):
#                 break
#             if len(self._seconds) and (t.second not in self._seconds):
#                 continue
#             if len(self._minutes) and (t.minute not in self._minutes):
#                 continue
#             if len(self._hours) and (t.hour not in self._hours):
#                 continue
#             if len(self._days) and (t.day not in self._days):
#                 continue
#             if len(self._weekdays) and (t.weekday() not in self._weekdays):
#                 continue
#             if len(self._months) and (t.month not in self._months):
#                 continue
#             yield t

def test_tscope():
    # Definite scope
    wdef = When("2009-02-20 13:00:00 ... 2009-02-20 15:00:00")
    assert wdef.duration() == timedelta(0,7200)
    assert wdef.period() is None
    assert wdef.is_definite()
    assert not wdef.is_infinite()
    assert not wdef.is_repeated()
    assert wdef.in_scope(parse_time("2009-02-20 14:15:16"))
    assert not wdef.in_scope(parse_time("2009-02-21 14:15:16"))
    assert wdef.sort_scope(parse_time("2009-01-20 22:30:15")) < 0
    assert wdef.sort_scope(parse_time("2010-07-27 22:30:15")) > 0
    assert wdef.datetimes() == (parse_time("2009-02-20 13:00:00"),
                                 parse_time("2009-02-20 15:00:00"))
    assert wdef.timer_delays(tzero=parse_time("2009-02-20 12:00:00")) == (3600, 10800)

    # Immediate scope with period
    wrel = When("now + 30m / 15s")
    assert wrel.duration() == timedelta(0,1800)
    assert wrel.period() == timedelta(0,15)
    assert not wrel.is_definite()
    assert not wrel.is_repeated()
    assert wrel.is_immediate()
    assert wrel.in_scope(parse_time("2009-02-20 13:44:45"), tzero=parse_time("2009-02-20 13:30:00"))
    assert wrel.datetimes(tzero=parse_time("2009-02-20 13:30:00")) == \
           (parse_time("2009-02-20 13:30:00"), parse_time("2009-02-20 14:00:00"))
    assert wrel.follows(wdef, tzero=parse_time("2009-02-20 13:30:00"))
    assert wrel.timer_delays(tzero=parse_time("2009-02-20 12:00:00")) == (0, 1800)

    # Infinite scope
    assert when_infinite.duration() is None
    assert when_infinite.period() is None
    assert not when_infinite.is_repeated()
    assert wdef.follows(when_infinite)
    assert wrel.follows(when_infinite)
    assert (when_infinite.datetimes()) == (None, None)

    # repeated when without inner-when (should be the same as immediate scrope with period)
    wrep = When("repeat now + 30m / 15s")
    assert wrep.is_repeated()
    assert wrep.duration() == timedelta(0,1800)
    assert wrep.period() == timedelta(0,15)
    assert not wrep.is_definite()
    assert wrep.is_immediate()
    assert wrep.in_scope(parse_time("2009-02-20 13:44:45"), tzero=parse_time("2009-02-20 13:30:00"))
    assert wrep.datetimes(tzero=parse_time("2009-02-20 13:30:00")) == \
           (parse_time("2009-02-20 13:30:00"), parse_time("2009-02-20 14:00:00"))
    assert wrep.follows(wdef, tzero=parse_time("2009-02-20 13:30:00"))
    assert wrep.timer_delays(tzero=parse_time("2009-02-20 12:00:00")) == (0, 1800)

    # repeated when with period and inner-when
    wrep = When("repeat now + 30m / 1m { now + 5s / 1s }")
    assert wrep.is_repeated()
    assert wrep.duration() == timedelta(0,1800)
    assert wrep.period() == timedelta(0,60)
    assert not wrep.is_definite()
    assert wrep.is_immediate()
    assert wrep.in_scope(parse_time("2009-02-20 13:44:45"), tzero=parse_time("2009-02-20 13:30:00"))
    assert wrep.datetimes(tzero=parse_time("2009-02-20 13:30:00")) == \
           (parse_time("2009-02-20 13:30:00"), parse_time("2009-02-20 14:00:00"))
    assert wrep.follows(wdef, tzero=parse_time("2009-02-20 13:30:00"))
    assert wrep.timer_delays(tzero=parse_time("2009-02-20 12:00:00")) == (0, 1800)

    # check when from subspec (first iteration)
    iter = wrep.iterator(parse_time("2009-02-20 13:30:00"))
    wrep_subspec = next(iter)
    assert wrep_subspec.duration() == timedelta(0,5)
    assert wrep_subspec.period() == timedelta(0,1)
    assert wrep_subspec.is_definite()
    assert not wrep_subspec.is_immediate()
    assert wrep_subspec.in_scope(parse_time("2009-02-20 13:30:04"), tzero=parse_time("2009-02-20 13:30:00"))
    assert not wrep_subspec.in_scope(parse_time("2009-02-20 13:30:06"), tzero=parse_time("2009-02-20 13:30:00"))
    assert wrep_subspec.datetimes(tzero=parse_time("2009-02-20 13:30:00")) == \
           (parse_time("2009-02-20 13:30:00"), parse_time("2009-02-20 13:30:05"))
    assert wrep_subspec.follows(wdef, tzero=parse_time("2009-02-20 13:30:00"))
    assert wrep_subspec.timer_delays(tzero=parse_time("2009-02-20 12:00:00")) == (5400, 5405)

    # check when from subspec (second iteration)
    wrep_subspec = next(iter)
    assert wrep_subspec.duration() == timedelta(0,5)
    assert wrep_subspec.period() == timedelta(0,1)
    assert wrep_subspec.is_definite()
    assert not wrep_subspec.is_immediate()
    assert wrep_subspec.in_scope(parse_time("2009-02-20 13:31:04"), tzero=parse_time("2009-02-20 13:30:00"))
    assert not wrep_subspec.in_scope(parse_time("2009-02-20 13:31:06"), tzero=parse_time("2009-02-20 13:30:00"))
    assert wrep_subspec.datetimes(tzero=parse_time("2009-02-20 13:30:00")) == \
           (parse_time("2009-02-20 13:31:00"), parse_time("2009-02-20 13:31:05"))
    assert wrep_subspec.follows(wdef, tzero=parse_time("2009-02-20 13:30:00"))
    assert wrep_subspec.timer_delays(tzero=parse_time("2009-02-20 12:00:00")) == (5460, 5465)

    # cron when (first monday each month)
    wcron = When("repeat now ... future cron 0 0 * 1,2,3,4,5,6,7 1 * { now + 5s / 1s }")
    assert wcron.is_repeated()
    assert not wcron.is_definite()
    assert wcron.is_immediate()
    assert wcron.in_scope(parse_time("2009-02-20 13:44:45"), tzero=parse_time("2009-02-20 13:30:00"))

    # check when from subspec (first iteration)
    iter = wcron.iterator(parse_time("2009-02-20 13:30:00"))
    wrep_subspec = next(iter)
    assert wrep_subspec.duration() == timedelta(0,5)
    assert wrep_subspec.period() == timedelta(0,1)
    assert wrep_subspec.is_definite()
    assert not wrep_subspec.is_immediate()
    assert wrep_subspec.in_scope(parse_time("2009-03-02 00:00:04"), tzero=parse_time("2009-02-20 13:30:00"))
    assert not wrep_subspec.in_scope(parse_time("2009-02-20 00:06:06"), tzero=parse_time("2009-02-20 13:30:00"))
    assert wrep_subspec.datetimes(tzero=parse_time("2009-02-20 13:30:00")) == \
           (parse_time("2009-03-02 00:00:00"), parse_time("2009-03-02 00:00:05"))
    assert wrep_subspec.follows(When("2009-03-02 00:00:00 ... 2009-03-02 15:00:00"), tzero=parse_time("2009-03-02 00:00:03"))
    assert wrep_subspec.timer_delays(tzero=parse_time("2009-03-01 23:00:00")) == (3600, 3605)

#######################################################################
# Primitive Types
#######################################################################

class _Primitive(object):
    """
    Represents a primitive mPlane data type. Primitive types define
    textual and native representations for data elements, and convert
    between the two.

    In general, client code will not need to interact with Primitives;
    conversion between strings and values is handled automatically by
    the Statement and Notification classes.

    """
    def __init__(self, name):
        super().__init__()
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<special mplane primitive "+self.name+">"

    def parse(self, sval):
        """
        Converts a string to a value; default implementation
        returns the string directly, returning None for the
        special string "*", which represents "all values" in
        mPlane.

        """
        if sval is None or sval == VALUE_NONE:
            return None
        else:
            return sval

    def unparse(self, val):
        """
        Converts a value to a string; default implementation
        uses native __str__ representation, replaces None with a
        the special string "*", representing all values.

        """
        if val is None:
            return VALUE_NONE
        else:
            return str(val)

class _StringPrimitive(_Primitive):
    """
    Represents a string. Uses the default implementation.
    If necessary, use the prim_string instance of this class;
    in general, however, this is used internally by Element.

    """
    def __init__(self):
        super().__init__("string")

    def __repr__(self):
        return "mplane.model.prim_string"

class _NaturalPrimitive(_Primitive):
    """
    Represents a natural number (unsigned integer).

    Uses a Python int as the native representation.
    If necessary, use the prim_natural instance of this class;
    in general, however, this is used internally by Element.

    """
    def __init__(self):
        super().__init__("natural")

    def __repr__(self):
        return "mplane.model.prim_natural"

    def parse(self, sval):
        """Convert a string to a natural value."""
        if sval is None or sval == VALUE_NONE:
            return None
        else:
            # also converts values like 100.0 or 10E2
            return int(float(sval))

class _RealPrimitive(_Primitive):
    """
    Represents a real number (floating point).

    Uses a Python float as the native representation.
    If necessary, use the prim_real instance of this class;
    in general, however, this is used internally by Element.

    """
    def __init__(self):
        super().__init__("real")

    def __repr__(self):
        return "mplane.model.prim_real"

    def parse(self, sval):
        """Convert a string to a floating point value."""
        if sval is None or sval == VALUE_NONE:
            return None
        else:
            return float(sval)

class _BooleanPrimitive(_Primitive):
    """
    Represents a real number (floating point).

    Uses a Python bool as the native representation.
    If necessary, use the prim_boolean instance of this class;
    in general, however, this is used internally by Element.

    """
    def __init__(self):
        super().__init__("boolean")

    def __repr__(self):
        return "mplane.model.prim_boolean"

    def parse(self, sval):
        """Convert a string to a boolean value."""
        if sval is None or sval == VALUE_NONE:
            return None
        elif sval == 'True':
            return True
        elif sval == 'False':
            return False

        # also converts 1 and 0
        elif sval == '1':
            return True
        elif sval == '0':
            return False

        else:
            raise ValueError("Invalid boolean value "+sval)

class _AddressPrimitive(_Primitive):
    """
    Represents a IPv4 or IPv6 host or network address.

    Uses the Python standard library ipaddress module
    for the native representation.

    """
    def __init__(self):
        super().__init__("address")

    def __repr__(self):
        return "mplane.model.prim_address"

    def parse(self, sval):
        """Convert a string to an address value."""
        if sval is None or sval == VALUE_NONE:
            return None
        else:
            return ip_address(sval)

class _URLPrimitive(_Primitive):
    """
    Represents a URL. For now, URLs are implemented only as strings,
    without any parsing or validation.

    """
    def __init__(self):
        super().__init__("url")

    def __repr__(self):
        return "mplane.model.prim_url"

class _TimePrimitive(_Primitive):
    """
    Represents a UTC timestamp with arbitrary precision.
    Also handles special-purpose mPlane timestamps.

    """
    def __init__(self):
        super().__init__("time")

    def __repr__(self):
        return "mplane.model.prim_time"

    def parse(self, valstr):
        return parse_time(valstr)

    def unparse(self, val):
        return unparse_time(val)

prim_string = _StringPrimitive()
prim_natural = _NaturalPrimitive()
prim_real = _RealPrimitive()
prim_boolean = _BooleanPrimitive()
prim_time = _TimePrimitive()
prim_address = _AddressPrimitive()
prim_url = _URLPrimitive()

_prim = {x.name: x for x in [prim_string,
                             prim_natural,
                             prim_real,
                             prim_boolean,
                             prim_time,
                             prim_address,
                             prim_url]}

def test_primitives():
    import math
    assert prim_string.parse("foo") == 'foo'
    assert prim_string.unparse("foo") == 'foo'
    assert prim_string.parse("*") is None
    assert prim_string.unparse(None) == '*'
    assert prim_natural.parse("42") == 42
    assert prim_natural.unparse(27) == '27'
    assert prim_real.unparse(math.pi) == '3.141592653589793'
    assert prim_real.parse("4.2e6") == 4200000.0
    assert prim_boolean.unparse(False) == 'False'
    assert prim_boolean.parse("True") == True
    assert prim_address.parse("10.0.27.101") == ip_address('10.0.27.101')
    assert prim_address.unparse(ip_address("10.0.27.101")) == '10.0.27.101'
    assert prim_address.parse("2001:db8:1:33::c0:ffee") == \
           ip_address('2001:db8:1:33::c0:ffee')
    assert prim_address.unparse(ip_address("2001:db8:1:33::c0:ffee")) == \
           '2001:db8:1:33::c0:ffee'
    assert prim_time.parse("2013-07-30 23:19:42") == \
           datetime(2013, 7, 30, 23, 19, 42)
    assert prim_time.unparse(datetime(2013, 7, 30, 23, 19, 42)) == \
           '2013-07-30 23:19:42.000000'
    assert prim_time.parse("now") is time_now
    assert prim_time.parse("past") is time_past
    assert prim_time.parse("future") is time_future
    assert prim_time.unparse(time_now) == "now"
    assert prim_time.unparse(time_past) == "past"
    assert prim_time.unparse(time_future) == "future"

#######################################################################
# Elements and registries
#######################################################################

class Element(object):
    """
    An Element represents a name for a particular type of data with
    a specific semantic meaning; it is analogous to an IPFIX Information
    Element, or a named column in a relational database.

    An Element has a Name by which it can be compared to other Elements,
    and a primitive type, which it uses to convert values to and from
    strings.

    The mPlane reference implementation includes a default registry of
    elements; use initialize_registry() to use these.

    """
    def __init__(self, name, prim, desc=None, namespace=REGURI_DEFAULT):
        super().__init__()
        self._name = name
        self._prim = prim
        self._desc = desc
        self._qualname = namespace + ANCHOR_SEP + name

    def __str__(self):
        return self._name

    def __repr__(self):
        return "<Element "+self._qualname+" "+repr(self._prim)+" >"

    def name(self):
        """Returns the name of this Element"""
        return self._name

    def desc(self):
        """Returns the description of this Element"""
        return self._desc

    def qualified_name(self):
        """Returns the name of this Element along with its namespace"""
        return self._qualname

    def primitive_name(self):
        """Returns the name of this Element's primitive"""
        return self._prim.name

    def parse(self, sval):
        """
        Converts a string to a value for this Element; delegates to primitive.
        """
        return self._prim.parse(sval)

    def unparse(self, val):
        """
        Converts a value to a string for this Element; delegates to primitive.
        """
        return self._prim.unparse(val)

    def compatible_with(self, rval):
        """
        Determines based on naming rules if this element is compatible with
        element rval; that is, if transformation_to will return a function
        for turning a value of this element to the other. Compatibility based
        on name structure is a future feature; this method currently checks for
        name equality only.

        """
        return self._name == rval._name

    def transformation_to(self, rval):
        """
        Returns a function which will transform values of this element
        into values of element rval; used to support unit conversions.
        This is a future feature, and is currently a no-op.
        Only valid if compatible_with returns True.

        """
        return lambda x: x

class Registry(object):
    """
    A Registry is a collection of named Elements associated with a
    namespace URI, from which it is retrieved.

    """

    def __init__(self, uri=None, filename=None, noparse=False):
        super().__init__()
        self._revision = None
        self._elements = collections.OrderedDict()
        self._namespaces = set()

        # stash URI and parse the registry
        if uri:
            if noparse:
                self._uri = uri
            else:
                self._parse_from_uri(uri)
        elif filename:
            self._parse_from_file(filename)
        else:
            self._parse_from_file()

    def __len__(self):
        return len(self._elements)

    def __getitem__(self, name):
        return self._elements.get(name, None)

    def _add_element(self, elem):
        self._elements[elem.name()] = elem

    def _include_registry(self, other_registry):
        for elem in other_registry._elements.values():
            self._add_element(elem)

    def _parse_json_bytestream(self, stream):
        # Turn the stream into a dict
        s = stream.read()
        if isinstance(s, bytes):
            s = s.decode("utf-8")
        d = json.loads(s)

        # check format
        if d[KEY_REGFMT] != REGFMT_FLAT:
            raise ValueError("Unsupported registry format "+str(d[KEY_REGFMT]))

        # stash revision
        self._revision = int(d[KEY_REGREV])

        # get namespace, store it and check for loops
        self._uri = d[KEY_REGURI]

        if self._uri in self._namespaces:
            raise ValueError("Registry include loop at "+self._uri)
        self._namespaces.add(self._uri)

        # now parse includes depth-first
        if KEY_REGINCLUDE in d:
            for incuri in d[KEY_REGINCLUDE]:
                self._include_registry(registry_for_uri(incuri))

        # finally, iterate over elements and add them to the table
        for elem in d[KEY_ELEMENTS]:
            name = elem[KEY_ELEMNAME]
            prim = _prim[elem[KEY_ELEMPRIM]]
            if KEY_ELEMDESC in elem:
                desc = elem[KEY_ELEMDESC]
            else:
                desc = None
            # Add the element in the subordinate in the parent namespace --
            # FIXME probably want to check to make sure this is the right
            # thing to do
            self._add_element(Element(name, prim, desc, self._uri))

    def _parse_from_file(self, filename=None):
        if filename is None:
            filename = os.path.join(os.path.dirname(__file__), "registry.json")
        with open(filename, "r") as stream:
            self._parse_json_bytestream(stream)

    def _parse_from_uri(self, uri):
        if uri == REGURI_DEFAULT:
            with open(os.path.join(os.path.dirname(__file__), "registry.json"), "r") as stream:
                self._parse_json_bytestream(stream)
        else:
            # normalize path if is a file or if no scheme is given
            # (we assume that is is a file)
            scheme = urllib.parse.urlparse(uri).scheme
            if scheme == "file" or scheme == "":
                uri = "file://" + normalize_path(uri)

            try:
                with urllib.request.urlopen(uri) as stream:
                    self._parse_json_bytestream(stream)
            except:
                raise ValueError("Invalid Registry uri: " + uri)

    def _dump_json(self):
        d = collections.OrderedDict()
        d[KEY_REGFMT] = REGFMT_FLAT
        d[KEY_REGREV] = int(self._revision)
        d[KEY_REGURI] = self._uri
        d[KEY_ELEMENTS] = []
        for elem in self._elements.values():
            ed = collections.OrderedDict()
            ed[KEY_ELEMNAME] = elem.name()
            ed[KEY_ELEMPRIM] = elem.primitive_name()
            desc = elem.desc()
            if desc is not None:
                ed[KEY_ELEMDESC] = desc
            d[KEY_ELEMENTS].append(ed)

        return json.dumps(d, indent=4)

    def uri(self):
        """
        Returns the URI by which this registry is known.

         """
        return self._uri

_base_registry = None
_registries = collections.OrderedDict()

def preload_registry(filename=None):
    global _registries
    preloaded = Registry(filename=filename)
    _registries[preloaded.uri()] = preloaded

def registry_for_uri(uri):
    """
    Get a registry for a given URI, maintaining a local cache.
    Called when parsing statements; generally not useful in client code.

    """
    global _registries

    if uri not in _registries:
        _registries[uri] = Registry(uri=uri)

    return _registries[uri]

def initialize_registry(uri=REGURI_DEFAULT):
    """
    Initializes the mPlane registry from a URI; if no URI is given,
    initializes the registry from the internal core registry.

    Call this after preloading registries, but before doing anything else.

    """
    global _base_registry
    _base_registry = registry_for_uri(uri)

def element(name, reguri=None):
    """
    Returns the Element with the given name.
    If reguri is given, searches the speficied Registry,
    otherwise searches the base Registry.
    """
    global _base_registry
    global _registries

    for reg in _registries:
        if _registries[reg][name] != None:
            return _registries[reg][name]
    if _base_registry[name] != None:
        return _base_registry[name]

    # fall-through: no results
    raise KeyError("Key error: " + name + " not present in registries")

def test_registry():
    # default registry trough the Registry-Object
    base_registry = Registry()
    assert repr(base_registry["start"]) == "<Element " + REGURI_DEFAULT + "#start mplane.model.prim_time >"
    assert base_registry["start"].name() == "start"
    assert base_registry["start"].primitive_name() == "time"
    assert base_registry["start"].desc() == "Start time of an event/flow that may have a non-zero duration"

    # registry with a parent

    test_registry = Registry(os.path.join(os.path.dirname(__file__), os.pardir, "testdata", "registry_with_parent.json"))
    assert repr(test_registry["testName"]) == "<Element testdata/registry_with_parent.json#testName mplane.model.prim_time >"
    assert test_registry["testName"].name() == "testName"
    assert test_registry["testName"].primitive_name() == "time"
    assert test_registry["testName"].desc() == "testDesc"
    # element from the parent registry
    assert repr(test_registry["start"]) == "<Element http://ict-mplane.eu/registry/core#start mplane.model.prim_time >"
    assert test_registry["start"].name() == "start"
    assert test_registry["start"].primitive_name() == "time"
    assert test_registry["start"].desc() == "Start time of an event/flow that may have a non-zero duration"
    # overwritten element
    assert repr(test_registry["end"]) == "<Element testdata/registry_with_parent.json#end mplane.model.prim_time >"
    assert test_registry["end"].name() == "end"
    assert test_registry["end"].primitive_name() == "time"
    assert test_registry["end"].desc() == "overwritten end"

    # default registry through the element-method
    initialize_registry()
    assert repr(element("start")) == "<Element http://ict-mplane.eu/registry/core#start mplane.model.prim_time >"
    assert element("start").name() == "start"
    assert element("start").primitive_name() == "time"
    assert element("start").desc() == "Start time of an event/flow that may have a non-zero duration"

#######################################################################
# Constraints
#######################################################################

class _Constraint(object):
    """
    Represents a set of acceptable values for an element.
    The default constraint accepts everything; use
    the special instance constraint_all for this.

    Clients and components will generally interact with the
    Constraint classes through Parameters.

    """
    def __init__(self, prim):
        super().__init__()
        self._prim = prim

    def __str__(self):
        """Represents this Constraint as a string"""
        return CONSTRAINT_ALL

    def __repr__(self):
        return "mplane.model.constraint_all"

    def met_by(self, val):
        """Determines if this constraint is met by a given value."""
        return True

    def single_value(self):
        """
        If this constraint only allows a single value, return it.
        Otherwise, return None. The default constraint allows all values,
        so this always returns None.

        """
        return None

constraint_all = _Constraint(None)

class _RangeConstraint(_Constraint):
    """Represents acceptable values for an element as an inclusive range"""

    def __init__(self, prim, sval=None, a=None, b=None):
        super().__init__(prim)
        if sval is not None:
            (astr, bstr) = sval.split(RANGE_SEP)
            self.a = prim.parse(astr)
            self.b = prim.parse(bstr)
        elif a is not None and b is not None:
            self.a = a
            self.b = b
        else:
            raise "RangeConstraint needs either a string "+\
                  "or an explicit range"

        if (self.a > self.b):
            (self.a, self.b) = (self.b, self.a)

    def __str__(self):
        return self._prim.unparse(self.a) + \
               RANGE_SEP + \
               self._prim.unparse(self.b)

    def __repr__(self):
        return "mplane.model.RangeConstraint("+repr(self._prim)+\
                                             ", "+repr(str(self))+")"

    def met_by(self, val):
        """Determines if the value is within the range"""
        return (val >= self.a) and (val <= self.b)

    def single_value(self):
        """If this constraint only allows a single value, return it. Otherwise, return None."""
        if self.a == self.b:
            return self.a
        else:
            return None

class _SetConstraint(_Constraint):
    """Represents acceptable values as a discrete set."""
    def __init__(self, prim, sval=None, vs=None):
        super().__init__(prim)
        if sval is not None:
            self.vs = set(map(self._prim.parse, sval.split(SET_SEP)))
        elif vs is not None:
            self.vs = vs
        else:
            self.vs = set()

    def __str__(self):
        return SET_SEP.join(map(self._prim.unparse, self.vs))

    def __repr__(self):
        return "mplane.model.SetConstraint("+repr(self._prim)+\
                                             ", "+repr(str(self))+")"

    def met_by(self, val):
        """Determines if the value is a mamber of the set"""
        return val in self.vs

    def single_value(self):
        """If this constraint only allows a single value, return it. Otherwise, return None."""
        if len(self.vs) == 1:
            return list(self.vs)[0]
        else:
            return None

def parse_constraint(prim, sval):
    """
    Given a primitive and a string value, parses a constraint
    string (returned via str(constraint)) into an instance of an
    appropriate constraint class.

    """
    if sval == CONSTRAINT_ALL:
        return constraint_all
    elif sval.find(RANGE_SEP) > 0:
        return _RangeConstraint(prim=prim, sval=sval)
    else:
        return _SetConstraint(prim=prim, sval=sval)

def test_constraints():
    assert constraint_all.met_by("whatever")
    assert constraint_all.met_by(None)

    rc = parse_constraint(prim_natural,"0 ... 99")
    assert not rc.met_by(-1)
    assert rc.met_by(0)
    assert rc.met_by(33)
    assert rc.met_by(99)
    assert not rc.met_by(100)
    assert str(rc) == "0 ... 99"

    sc = parse_constraint(prim_address,"10.0.27.100,10.0.28.103")
    assert sc.met_by(ip_address('10.0.28.103'))
    assert not sc.met_by(ip_address('10.0.27.103'))

#######################################################################
# Statements
#######################################################################

class Parameter(Element):
    """
    A Parameter is an element which can take a constraint and a value.
    In Capabilities, Parameters have constraints and no value; in
    Specifications and Results, Parameters have both constraints and
    values.

    """
    def __init__(self, parent_element, constraint=constraint_all, val=None):
        super().__init__(parent_element._name, parent_element._prim)
        self._val = None

        if isinstance(constraint, str):
            self._constraint = parse_constraint(self._prim, constraint)
        elif isinstance(constraint, _Constraint):
            self._constraint = constraint
        else:
            self._constraint = _SetConstraint(vs=set([constraint]), prim=self._prim)

        self.set_value(val)

    def __repr__(self):
        return "<Parameter "+str(self)+" "+repr(self._prim)+" "+\
               str(self._constraint)+" value "+repr(self._val)+">"

    def has_value(self):
        """Returns True if this component has a value."""
        return self._val is not None

    def is_single_value(self):
        """
        Returns True if this parameter's Constraint only allows a single value

        """
        return self._constraint.single_value() is not None

    def get_single_value(self):
        """
        If this parameter's Constraint only allows a single value, returns it

        """
        single_val = self._constraint.single_value()
        if single_val is not None:
            return single_val
        else:
            return None

    def set_single_value(self):
        """
        If this Parameter's Constraint allows only a single value, and this
        Paramater does not yet have a value, set the value to the only one
        allowed by the Constraint.

        """
        if not self.has_value():
            self._val = self._constraint.single_value()

    def can_set_value(self, val):
        """
        Returns True if the parameter can take the specified value,
        False otherwise.
        Either takes a value of the correct type for the associated
        Primitive, or a string, which will be parsed to a value of
        the correct type.

        """
        if isinstance(val, str):
            val = self._prim.parse(val)

        return self._constraint.met_by(val)

    def set_value(self, val):
        """
        Sets the value of the Parameter.
        Either takes a value of the correct type for the associated Primitive, or
        a string, which will be parsed to a value of the correct type.

        Raises ValueError if the value is not allowable for the Constraint.

        """
        if isinstance(val, str):
            val = self._prim.parse(val)

        if (val is None) or self._constraint.met_by(val):
            self._val = val
        else:
            raise ValueError(repr(self) + " cannot take value " + repr(val))

    def get_value(self):
        """Returns this Parameter's value"""
        return self._val

    def _as_tuple(self):
        if self._val is not None:
            return (self._name, self._prim.unparse(self._val))
        else:
            return (self._name, str(self._constraint))

    def _clear_constraint(self):
        self._constraint = constraint_all

class Metavalue(Element):
    """
    A Metavalue is an element which can take an unconstrained value.
    Metavalues are used in statement metadata sections.

    """
    def __init__(self, parent_element, val):
        super().__init__(parent_element._name, parent_element._prim)
        self.set_value(val)

    def __repr__(self):
        return "<Metavalue "+str(self)+" "+repr(self._prim)+\
               " value "+repr(self._val)+" >"

    def set_value(self, val):
        """
        Sets the value.
        If the value is a string it parses it.
        """
        if isinstance(val, str):
            val = self._prim.parse(val)
        self._val = val

    def get_value(self):
        """ Returns the value """
        return self._val

    def _as_tuple(self):
        return (self._name, self._prim.unparse(self._val))

class ResultColumn(Element):
    """
    A ResultColumn is an element which can take an array of values.
    In Capabilities and Specifications, this array is empty, while in
    Results it has one or more values, such that all the ResultColumns
    in the Result have the same number of values.

    """
    def __init__(self, parent_element):
        super().__init__(parent_element._name, parent_element._prim)
        self._vals = []

    def __repr__(self):
        return "<ResultColumn "+str(self)+" "+repr(self._prim)+\
               " with "+str(len(self))+" values>"

    def __len__(self):
        return len(self._vals)

    def __getitem__(self, key):
        return self._vals[key]

    def __setitem__(self, key, val):
        # Automatically parse strings
        if isinstance(val, str):
            val = self._prim.parse(val)

        # Automatically extend column to fit
        while len(self) < key:
            self._vals.append(None)

        # Append or replace value
        if len(self) == key:
            self._vals.append(val)
        else:
            self._vals[key] = val

    def __delitem__(self, key):
        del(self._vals[key])

    def __iter__(self):
        return iter(self._vals)

    def clear(self):
        """ Clears values. """
        self._vals.clear()

class Statement(object):
    """
    A Statement is an assertion about the properties of a measurement
    or other action performed by an mPlane component. This class
    contains common implementation for the three kinds of mPlane
    statement. Clients and components should use the
    :class:`mplane.model.Capability`, :class:`mplane.model.Specification`,
    and :class:`mplane.model.Result` classes instead.

    """

    def __init__(self, dictval=None, verb=VERB_MEASURE, label=None, token=None, when=None, reguri=None):
        super().__init__()
        # Make a blank statement
        self._version = MPLANE_VERSION
        self._params = collections.OrderedDict()
        self._metadata = collections.OrderedDict()
        self._resultcolumns = collections.OrderedDict()
        self._verb = None
        self._label = None
        self._token = None
        self._link = None
        self._export = None

        if dictval is not None:
            # Fill in from dictionary
            self._from_dict(dictval)
        else:
            # Fill in from defaults
            self._verb = verb
            self._label = label
            self._token = token
            if when is None:
                when = when_infinite
            elif isinstance(when, str):
                when = When(when)
            self._when = when
            if reguri is not None:
                self._reguri = reguri
            else:
                self._reguri = _base_registry.uri()

    def __repr__(self):
        return "<"+self.kind_str()+": "+self._verb+self._label_repr()+\
               " when "+str(self._when)+\
               " token "+self.get_token(REPHL)+" schema "+self._schema_hash(REPHL)+\
               self._more_repr()+">"

    def _more_repr(self):
        return ""

    def _label_repr(self):
        if self._label is None:
            return ""
        else:
            return " ("+self._label+")"

    def kind_str(self):
        raise NotImplementedError("Cannot instantiate a raw Statement")

    def validate(self):
        raise NotImplementedError("Cannot instantiate a raw Statement")

    def verb(self):
        """Returns this statement's verb"""
        return self._verb

    def add_parameter(self, elem_name, constraint=constraint_all, val=None):
        """Programatically adds a parameter to this Statement."""
        self._params[elem_name] = Parameter(element(elem_name, reguri=self._reguri),
                                            constraint=constraint,
                                            val = val)

    def has_parameter(self, elem_name):
        """Returns True if the statement has a parameter with the given name."""
        return elem_name in self._params

    def parameter_names(self):
        """Iterates over the names of parameters in this Statement."""
        yield from self._params.keys()

    def parameter_values(self):
        """
        Returns a dict mapping parameter names to values
        for each parameter with a value.
        """
        d = {}
        for k in self.parameter_names():
            v = self.get_parameter_value(k)
            if v:
                d[k] = v
        return d

    def count_parameters(self):
        """Returns the number of parameters in this Statement."""
        return len(self._params)

    def count_parameter_values(self):
        """Returns the number of parameters with values in this Statement."""
        return sum(map(lambda p: p.has_value(), self._params.values()))

    def get_parameter_value(self, elem_name):
        """Returns the value for a named parameter on this Statement."""
        return self._params[elem_name].get_value()

    def set_parameter_value(self, elem_name, value):
        """Programatically sets a value for a parameter on this Statement."""
        elem = self._params[elem_name]
        elem.set_value(value)

    def can_set_parameter_value(self, elem_name, value):
        """Determines whether a given Parameter can take a value."""
        elem = self._params[elem_name]
        return elem.can_set_value(value)

    def get_single_parameter_value(self, elem_name):
        """
        If a given parameter is single-valued returns
        that value, otherwise returns None
        """
        return self._params[elem_name].get_single_value()

    def add_metadata(self, elem_name, val):
        """Programatically adds a metadata element to this Statement."""
        self._metadata[elem_name] = Metavalue(element(elem_name, reguri=self._reguri), val)

    def has_metadata(self, elem_name):
        """Returns True if the statement has a metadata element with the given name."""
        return elem_name in self._metadata

    def metadata_names(self):
        """Iterates over the names of metadata elements in this Statement."""
        yield from self._metadata.keys()

    def count_metadata(self):
        """Returns the number of metavalues in this Statement."""
        return len(self._metadata)

    def add_result_column(self, elem_name):
        """Programatically adds a result column to this Statement."""
        self._resultcolumns[elem_name] = ResultColumn(element(elem_name, reguri=self._reguri))

    def has_result_column(self, elem_name):
        """Returns True if the statement has results column with the given name."""
        return elem_name in self._resultcolumns

    def result_column_names(self):
        """Iterates over the names of result columns in this Statement."""
        yield from self._resultcolumns.keys()

    def count_result_columns(self):
        """Returns the number of result columns in this Statement."""
        return len(self._resultcolumns)

    def count_result_rows(self):
        """Returns the number of result rows in this Statement."""
        return functools.reduce(max,
                   [len(col) for col in self._resultcolumns.values()], 0)

    def get_link(self):
        """
        Returns the statement's link URL, which specifies where the next message
        in the workflow should be sent to or retrieved from.
        """
        return self._link

    def set_link(self, link):
        """Sets the Statement's link URL"""
        self._link = link

    def get_export(self):
        """
        Returns the Statement's export URL, which specifies where
        results will be indirectly exported.
        """
        return self._export

    def set_export(self, export):
        """Sets the Statement's export URL."""
        self._export = export

    def get_label(self):
        """Returns the Statement's label."""
        return self._label

    def set_label(self, label):
        """Sets the statement's label"""
        self._label = label

    def when(self):
        """Returns the statement's temporal scope."""
        return self._when

    def set_when(self, when, force=False):
        """
        Sets the statement's temporal scope. Ensures that the temporal scope is
        within the previous temporal scope unless force is True.
        Takes either an instance of
        mplane.model.When, or a string describing the scope.
        """
        if isinstance(when, str):
            when = When(when)
        if not force and \
           (self._when is not None) and \
           not when.follows(self._when):
            raise ValueError("Cannot set temporal scope "+str(when)+
                             " within "+str(self._when))
        self._when = when

    def _schema_hash(self, lim=None):
        """
        Returns a hex string uniquely identifying the set of parameters
        and result columns (the schema) of this statement.

        """
        sstr = self._reguri + \
               " p " + " ".join(sorted(self._params.keys())) + \
               " r " + " ".join(sorted(self._resultcolumns.keys()))
        hstr = hashlib.md5(sstr.encode('utf-8')).hexdigest()
        if lim is not None:
            return hstr[:lim]
        else:
            return hstr

    def _pv_hash(self, lim=None, astr=None):
        """
        Returns a hex string uniquely identifying the set of parameters,
        temporal scope, parameter values, and result columns
        of this statement. Used as a specification key.

        """
        spk = sorted(self._params.keys())
        spv = [self._params[k].unparse(self._params[k].get_value()) for k in spk]
        tstr = self._reguri + self._verb + " w " + str(self._when) +\
               " pk " + " ".join(spk) + \
               " pv " + " ".join(spv) + \
               " r " + " ".join(sorted(self._resultcolumns.keys()))
        if astr:
            tstr += astr
        hstr = hashlib.md5(tstr.encode('utf-8')).hexdigest()
        if lim is not None:
            return hstr[:lim]
        else:
            return hstr

    def _mpcv_hash(self, lim=None, astr=None):
        """
        Returns a hex string uniquely identifying the set of parameters,
        temporal scope, parameter constraints, parameter values, metadata, metadata values,
        and result columns (the extended specification) of this statement.
        Used as a complete token for statements.

        """
        spk = sorted(self._params.keys())
        spc = [str(self._params[k]._constraint) for k in spk]
        spv = [self._params[k].unparse(self._params[k].get_value()) for k in spk]
        smk = sorted(self._metadata.keys())
        smv = [self._metadata[k].unparse(self._metadata[k].get_value()) for k in smk]
        tstr = self._reguri + self._verb + \
               " w " + str(self._when) + \
               " pk " + " ".join(spk) + \
               " pc " + " ".join(spc) + " pv " + " ".join(spv) + \
               " mk " + " ".join(smk) + " mv " + " ".join(smv) + \
               " r " + " ".join(sorted(self._resultcolumns.keys())) + \
               " ex " + str(self._export)
        if astr:
            tstr += astr
        hstr = hashlib.md5(tstr.encode('utf-8')).hexdigest()
        if lim is not None:
            return hstr[:lim]
        else:
            return hstr

    def get_token(self, lim=None):
        """
        Returns the token of a Statement.
        If a token has not been explicitely set,
        it returns the default token for the Statement type.
        """
        if self._token is None:
          self._token = self._default_token()
        if lim is not None and len(self._token) > lim:
          return self._token[:lim]
        else:
          return self._token

    def set_token(self, token):
        self._token = token

    def _default_token(self):
      return self._mpcv_hash()

    def _result_rows(self):
        rows = []
        for row_index in range(self.count_result_rows()):
            row = []
            rows.append(row)
            for col in self._resultcolumns.values():
                try:
                    valstr = col._prim.unparse(col[row_index])
                except IndexError:
                    valstr = VALUE_NONE
                row.append(valstr)
        return rows

    def to_dict(self, token_only=False):
        """
        Converts a Statement to a dictionary (for further conversion
        to JSON or YAML), which can be passed as the dictval
        argument of the appropriate statement constructor.

        """
        self.validate()
        d = collections.OrderedDict()
        d[self.kind_str()] = self._verb

        d[KEY_VERSION] = self._version

        d[KEY_REGISTRY] = self._reguri

        if self._label is not None:
            d[KEY_LABEL] = self._label

        if self._link is not None:
            d[KEY_LINK] = self._link

        if self._export is not None:
            d[KEY_EXPORT] = self._export

        if self._token is not None:
            d[KEY_TOKEN] = self._token

        d[KEY_WHEN] = str(self._when)

        if self.count_parameters() > 0:
            d[KEY_PARAMETERS] = {t[0] : t[1] for t in [v._as_tuple()
                                        for v in self._params.values()]}

        if self.count_metadata() > 0:
            d[KEY_METADATA] = {t[0] : t[1] for t in [v._as_tuple()
                                        for v in self._metadata.values()]}

        if self.count_result_columns() > 0:
            d[KEY_RESULTS] = [k for k in self._resultcolumns.keys()]
            if self.count_result_rows() > 0:
                d[KEY_RESULTVALUES] = self._result_rows()

        return d

    def _params_from_dict(self, d):
        """
        Fills in parameters from a dictionary; used internally.
        The default implementation interprets dictionary values
        as parameter values.

        """
        for (k, v) in d.items():
            self.add_parameter(k, val=v)

    def _from_dict(self, d):
        """
        Fills in this Statement with values from a dictionary
        produced with to_dict (i.e., as taken from JSON or YAML).
        Ignores result values, as these are handled by :func:`Result._from_dict()`;
        ignores the schedule section, as this is handled in :func:`Specification._from_dict()`.

        """
        self._verb = d[self.kind_str()]

        if KEY_VERSION in d:
            if int(d[KEY_VERSION]) > MPLANE_VERSION:
                raise ValueError("Version mismatch")

        if KEY_REGISTRY in d:
            self._reguri = d[KEY_REGISTRY]
            registry_for_uri(self._reguri) # make sure the registry is loaded

        if KEY_LABEL in d:
            self._label = d[KEY_LABEL]

        if KEY_LINK in d:
          self._link = d[KEY_LINK]

        if KEY_EXPORT in d:
          self._link = d[KEY_EXPORT]

        if KEY_TOKEN in d:
          self._token = d[KEY_TOKEN]

        if KEY_WHEN in d:
            self._when = When(d[KEY_WHEN])

        if KEY_PARAMETERS in d:
            self._params_from_dict(d[KEY_PARAMETERS])

        if KEY_METADATA in d:
            for (k, v) in d[KEY_METADATA].items():
                self.add_metadata(k, v)

        if KEY_RESULTS in d:
            for v in d[KEY_RESULTS]:
                self.add_result_column(v)

    def _clear_constraints(self):
        for param in self._params.values():
            param._clear_constraint()

class Capability(Statement):
    """
    A Capability represents something an mPlane component can do.
    Capabilities contain verbs (strings identifying the thing the
    component can do), parameters (which must be given by a client
    in a Specification in order for the component to do that thing),
    metadata (additional information about the process used to do
    that thing), and result columns (the data that thing will return).

    Capabilities can either be created programatically, using the
    add_parameter(), add_metadata(), and add_result_column()
    methods, or by reading from a JSON object using parse_json().

    """

    def __init__(self, dictval=None, verb=VERB_MEASURE, label=None, token=None, when=None, registry_uri=None):
        super().__init__(dictval=dictval, verb=verb, label=label, token=token, when=when, reguri=registry_uri)

    def _more_repr(self):
        return " p/m/r "+str(self.count_parameters())+"/"+\
               str(self.count_metadata())+"/"+\
               str(self.count_result_columns())

    def kind_str(self):
        return KIND_CAPABILITY

    def set_when(self, when, force=True):
        """By default, changes to capability temporal scopes are always forced."""
        super().set_when(when, force)

    def validate(self):
        """
        Checks that this is a valid Capability; i.e., capabilites can not parameter nor results values.
        """
        pval = functools.reduce(operator.__or__,
                                (p.has_value() for p in self._params.values()),
                                False)

        if pval or (self.count_result_rows() > 0):
            raise ValueError("Capabilities must have neither parameter nor "+
                             "result values.")

    def _params_from_dict(self, d):
        """
        Fills in parameters from a dictionary; used internally.
        The Capability implementation interprets dictionary values
        as constraints.

        """
        for (k, v) in d.items():
            self.add_parameter(k, constraint=v)

class Specification(Statement):
    """
    A Specification represents a request for an mPlane component to do
    something it has advertised in a Capability.
    Capabilities contain verbs (strings identifying the thing the
    component can do), parameters (which must be given by a client
    in a Specification in order for the component to do that thing),
    metadata (additional information about the process used to do
    that thing), and result columns (the data that thing will return).

    Specifications are created either by passing a Capability the
    Specification is intended to use as the capability= argument of
    the constructor, or by reading from a JSON object (see model.parse_json()).

    """

    def __init__(self, dictval=None, capability=None, verb=VERB_MEASURE, label=None, token=None, when=None, schedule=None):
        super().__init__(dictval=dictval, verb=verb, label=label, token=token, when=when)

        if dictval is None and capability is not None:
            # Build a statement from a capabilitiy
            self._verb = capability._verb
            self._label = capability._label
            self._metadata = capability._metadata
            self._params = deepcopy(capability._params)
            self._resultcolumns = deepcopy(capability._resultcolumns)
            self._reguri = capability._reguri

            # inherit from capability only when necessary
            if when is None:
                self._when = capability._when

            # now set values we know we can
            for param in self._params.values():
                param.set_single_value()

    def _more_repr(self):
        return " p(v)/m/r "+str(self.count_parameters())+"("+\
               str(self.count_parameter_values())+")/"+\
               str(self.count_metadata())+"/"+\
               str(self.count_result_columns())

    def kind_str(self):
        return KIND_SPECIFICATION

    def fulfills(self, capability):
        """ Returns True if this Speficication fulfills the Capability"""
        # verify that the schema hash is equal
        if self._schema_hash() != capability._schema_hash():
            return False

        # Verify that the specification is within the capability's temporal scope
        if not self._when.follows(capability.when()):
            return False

        # Works for me.
        return True

    def validate(self):
        """
        Checks that this is a valid Specification; i.e., that all parameters have values.

        """
        pval = functools.reduce(operator.__and__,
                        (p.has_value() for p in self._params.values()),
                        True)

        if (not pval) or (self.count_result_rows() > 0):
            raise ValueError("Specifications must have parameter values.")

    def is_schedulable(self):
        """
        Determine if a specification can be scheduled -- i.e., that its
        temporal scope refers to some time in the future at which a
        measurement or other operation should take place, or some range of
        time for which existing data should be searched and/or retrieved.

        Currently, this just checks to see whether the verb is 'query'.
        """
        return self._verb != VERB_QUERY

    def _default_token(self):
        return self._pv_hash()

    def retoken(self, force=False):
        """
        Generates a new token, if necessary, taking into account the current time
        if a specification has a relative temporal scope.

        """
        if force:
            self._token = self._default_token()
        elif not self._when.is_definite():
            self._token = self._pv_hash(astr = repr(self._when.datetimes()))

    def subspec_iterator(self):
        """
        Iterates over subordinate specifications if this specification is repeated
        (i.e., has a repeated Temporal Scope); otherwise yields self once. Each subordinate
        specification has an absolute temporal scope derived from this specification's
        relative temporal scope and schedule.
        """
        if self._when.is_repeated():
            subspec = deepcopy(self)  # Brian does not like that but he said it is okay

            iter = self._when.iterator()
            while 1:
                subspec._when = next(iter)
                subspec.retoken(True)
                yield subspec
        else:
            yield self


class Result(Statement):
    """
    A result is a statement that a component measured
    a given set of values at a given point in time, according to a specification.

    Results are generally created by passing the specification the new result responds to as the specification= argument to the constructor. A result inherits its token from the specification it responds to.

    """
    def __init__(self, dictval=None, specification=None, verb=VERB_MEASURE, label=None, token=None, when=None):
        super().__init__(dictval=dictval, verb=verb, label=label, token=token, when=when)
        if dictval is None and specification is not None:
            self._verb = specification._verb
            self._label = specification._label
            self._metadata = specification._metadata
            self._params = deepcopy(specification._params)
            self._resultcolumns = deepcopy(specification._resultcolumns)
            self._reguri = specification._reguri
            # assign token from specification
            self._token = specification.get_token()
            # allow parameters to take values other than constrained
            self._clear_constraints()
            # inherit from specification only when necessary
            if when is not None:
                self._when = specification._when


    def _more_repr(self):
        return " p/m/r(r) "+str(self.count_parameters())+"/"+\
               str(self.count_metadata())+"/"+\
               str(self.count_result_columns())+"("+\
               str(self.count_result_rows())+")"

    def kind_str(self):
        return KIND_RESULT

    def validate(self):
        """
        Checks that this is a valid Result; i.e., that all parameters have values.

        """
        pval = functools.reduce(operator.__and__,
                        (p.has_value() for p in self._params.values()),
                        True)

        if (not pval):
            raise ValueError("Results must have parameter values.")

        if (not self._when.is_definite()):
            raise ValueError("Results must have definite temporal scope.")

    def _from_dict(self, d):
        """
        Fill in this Result with values from a dictionary
        produced with to_dict().

        """
        super()._from_dict(d)

        column_key = list(self._resultcolumns.keys())

        if KEY_RESULTVALUES in d:
            for i, row in enumerate(d[KEY_RESULTVALUES]):
                for j, val in enumerate(row):
                    self._resultcolumns[column_key[j]][i] = val

    def set_result_value(self, elem_name, val, row_index=0):
        """
        Sets a single result value.
        """
        self._resultcolumns[elem_name][row_index] = val

    def schema_dict_iterator(self):
        """
        Iterates over each row in this result, yielding a dictionary
        mapping all parameter and result column names to their values.

        """
        for i in range(self.count_result_rows()):
            d = self.parameter_values()
            for k in self.result_column_names():
                d[k] = self._resultcolumns[k][i]
            yield d


#######################################################################
# Notifications
#######################################################################

class BareNotification(object):
    """
    Notifications are used to send additional information between
    mPlane clients and components other than measurement statements.
    Notifications can either be part of a normal measurement workflow
    (as Receipts and Redemptions) or signal exceptional conditions
    (as Withdrawals and Interrupts).

    This class contains implementation common to all Notifications
    which do not contain any information from a related Capability
    or Specification.

    """
    def __init__(self, dictval=None, token=None):
        super().__init__()
        if dictval is not None:
            self._from_dict(dictval)
        else:
            self._token = token

class Exception(BareNotification):
    """
    A Component sends an Exception to a Client, or a Client to a
    Component, to present a human-readable message about a failure
    or non-nominal condition.

    The status field is used to store an HTTP
    status code corresponding to the exception to the
    client and component frameworks.

    """
    def __init__(self, token=None, dictval=None, errmsg=None, status=None):
        super().__init__(dictval=dictval, token=token)
        if dictval is None:
            if errmsg is None:
                errmsg = "Unspecified exception"
            self._errmsg = errmsg

        self.status = status

    def __repr__(self):
        return "<Exception: "+self.get_token()+" "+self._errmsg+">"

    def kind_str(self):
        return KIND_EXCEPTION

    def get_token(self):
        """
        Returns a token that originates from a message that has caused
        the Expection or None if the token was explictly not set
        """
        return self._token

    def set_token(self, token):
        self._token = token

    def to_dict(self, token_only=False):
        d = collections.OrderedDict()
        d[KIND_EXCEPTION] = self._token
        d[KEY_MESSAGE] = self._errmsg
        return d

    def _from_dict(self, d):
        self._token = d[KIND_EXCEPTION]
        self._errmsg = d[KEY_MESSAGE]

class _StatementNotification(Statement):
    """
    Common implementation superclass for notifications that
    may contain all or part of a related Capability or Specification.

    Clients and components should use :class:`mplane.model.Receipt`,
    :class:`mplane.model.Redemption`, and :class:`mplane.model.Withdrawal`
    directly

    """
    def __init__(self, dictval=None, statement=None, verb=VERB_MEASURE, token=None):
        super().__init__(dictval=dictval, verb=verb, token=token)
        if dictval is None and statement is not None:
            self._label = statement._label
            self._verb = statement._verb
            self._when = statement._when
            self._reguri = statement._reguri
            self._metadata = statement._metadata
            self._params = deepcopy(statement._params)
            self._resultcolumns = deepcopy(statement._resultcolumns)
            self._token = statement.get_token()
            self._reguri = statement._reguri

    def __repr__(self):
        return "<"+self.kind_str()+": "+self._label_repr()+self.get_token()+">"

    def to_dict(self, token_only=False):
        d = super().to_dict(token_only)

        if token_only and self._token is not None:
            for sk in (KEY_PARAMETERS, KEY_METADATA, KEY_RESULTS, KEY_LINK, KEY_WHEN):
                try:
                    del(d[sk])
                except KeyError:
                    pass

        return d

    def kind_str(self):
        raise NotImplementedError("Cannot instantiate a raw StatementNotification")

class Receipt(_StatementNotification):
    """
    A component presents a receipt to a Client in lieu of a result, when the
    result will not be available in a reasonable amount of time; or to confirm
    a Specification """
    def __init__(self, dictval=None, specification=None, token=None):
        super().__init__(dictval=dictval, statement=specification, token=token)

    def kind_str(self):
        return KIND_RECEIPT

    def validate(self):
        """
        Checks that this is a valid Receipt; performes the same checks as for a Specification.

        """
        Specification.validate(self)

class Redemption(_StatementNotification):
    """
    A client presents a Redemption to a component from which it has received
    a Receipt in order to get the associated Result.

    """
    def __init__(self, dictval=None, receipt=None, token=None):
        super().__init__(dictval=dictval, statement=receipt, token=token)
        if receipt is not None and token is None:
            self._token = receipt.get_token()

    def kind_str(self):
        return KIND_REDEMPTION

    def validate(self):
        """
        Checks that this is a valid Redemption; performes the same checks as for a Specification.
        """
        Specification.validate(self)

class Withdrawal(_StatementNotification):
    """A Withdrawal cancels a Capability"""
    def __init__(self, dictval=None, capability=None, token=None):
        super().__init__(dictval=dictval, statement=capability, token=token)

    def kind_str(self):
        return KIND_WITHDRAWAL

    def validate(self):
        """
        Checks that this is a valid Withdrawal; performes the same checks as for a Capability.
        """
        Capability.validate(self)

class Interrupt(_StatementNotification):
    """An Interrupt cancels a Specification"""
    def __init__(self, dictval=None, specification=None, token=None):
        super().__init__(dictval=dictval, statement=specification, token=token)

    def kind_str(self):
        return KIND_INTERRUPT

    def validate(self):
        """
        Checks that this is a valid Interrupt; performes the same checks as for a Specification.
        """
        Specification.validate(self)

#######################################################################
# Envelope
#######################################################################

class Envelope(object):
    """
    Envelopes are used to contain other Messages.

    """

    def __init__(self, dictval=None, content_type=ENVELOPE_MESSAGE, token=None, label=None, when=None):
        super().__init__()

        self._version = MPLANE_VERSION
        self._messages = []
        self._content_type = content_type
        self._token = token
        self._label = label
        self._when = None
        if when:
            (start, end) = when.datetimes()
            self._when = When(a=start,
                              b=end,
                              period=when.period())

        if dictval is not None:
            self._from_dict(dictval)

    def __repr__(self):
        if self._token:
            token_part = " token "+self.get_token()
        else:
            token_part = ""

        return "<envelope: "+self._content_type+\
                " ("+str(len(self._messages))+")"+token_part+": "+\
                " ".join(map(repr, self._messages))+">"

    def __len__(self):
        return len(self._messages)

    def trim(self, n):
        """ Removes everything except the last n elements """
        del self._messages[:-n]

    def append_message(self, msg):
        """ Appends a message to an Envelope """
        self._messages.append(msg)

    def messages(self):
        """ Returns an iterator to iterate over all messages in an Envelope """
        return iter(self._messages)

    def kind_str(self):
        return KIND_ENVELOPE

    def to_dict(self, token_only=False):
        d = {}
        d[self.kind_str()] = self._content_type
        d[KEY_VERSION] = self._version

        d[KEY_CONTENTS] = [m.to_dict(token_only=token_only) for m in self.messages()]

        if self._token is not None:
            d[KEY_TOKEN] = self._token

        if self._when is not None:
            d[KEY_WHEN] = str(self._when)

        if self._label is not None:
            d[KEY_LABEL] = self._label

        return d

    def _from_dict(self, d):
        self._content_type = d[self.kind_str()]

        if KEY_VERSION in d:
            if int(d[KEY_VERSION]) > MPLANE_VERSION:
                raise ValueError("Version mismatch")

        if KEY_TOKEN in d:
          self._token = d[KEY_TOKEN]

        if KEY_WHEN in d:
          self._when = When(d[KEY_WHEN])

        if KEY_LABEL in d:
          self._label = d[KEY_LABEL]

        for md in d[KEY_CONTENTS]:
            self.append_message(message_from_dict(md))

    def get_label(self):
        """ Returns the label or None if no label has been set """
        return self._label

    def get_token(self, lim=None):
        """ Returns the token or None if no token has been set """
        if self._token is not None and lim is not None and len(self._token) > lim:
          return self._token[:lim]
        else:
          return self._token

    def set_token(self, token):
        self._token = token

    def when(self):
        """ Returns the envelope's temporal scope. (If it's a bunch of multijob results) """
        return self._when

#######################################################################
# Utility methods
#######################################################################

def message_from_dict(d):
    """
    Given a dictionary returned from to_dict(), return a decoded
    mPlane message (statement or notification).

    """
    classmap = { KIND_CAPABILITY : Capability,
                 KIND_SPECIFICATION : Specification,
                 KIND_RESULT : Result,
                 KIND_RECEIPT : Receipt,
                 KIND_REDEMPTION : Redemption,
                 KIND_WITHDRAWAL : Withdrawal,
                 KIND_INTERRUPT : Interrupt,
                 KIND_EXCEPTION : Exception,
                 KIND_ENVELOPE : Envelope}

    for k in classmap.keys():
        if k in d:
            return classmap[k](dictval = d)
    raise ValueError("Cannot determine message type from "+repr(d))

def parse_json(jstr):
    """
    Parse a JSON object in a string and return the associated mPlane message.

    """
    return message_from_dict(json.loads(jstr))

def unparse_json(msg, token_only=False):
    """
    Transform an mPlane message into a JSON object representing it. If
    token_only is True, uses tokens only for message types for which that is
    appropriate (i.e. Reciepts, Redemptions, Withdrawals, and Interrupts).

    """
    return json.dumps(msg.to_dict(token_only=token_only),
                      sort_keys=True, indent=2, separators=(',',': '))

def parse_yaml(ystr):
    return mplane.model.message_from_dict(yaml.load(ystr))

def unparse_yaml(msg):
    return yaml.dump(dict(msg.to_dict()), default_flow_style=False, indent=4)

def render_text(message):
    if isinstance(message, Envelope):
        for msg in message.messages():
            print(render(msg))
    else:
        print(render(message))

def render(msg):
    d = msg.to_dict()

    if msg.kind_str() == KIND_EXCEPTION:
        out = KIND_EXCEPTION + ": " + d[KIND_EXCEPTION] + "\n"
    else:
        out = "%s: %s\n" % (msg.kind_str(), msg.verb())

    for section in (KEY_MESSAGE, KEY_LABEL, KEY_LINK,
                    KEY_EXPORT, KEY_TOKEN, KEY_WHEN, KEY_REGISTRY):
        if section in d:
            out += "    %-12s: %s\n" % (section, d[section])

    for section in (KEY_PARAMETERS, KEY_METADATA):
        if section in d:
            out += "    %-12s(%2u): \n" % (section, len(d[section]))
            for element in d[section]:
                out += "        %32s: %s\n" % (element, d[section][element])

    if KEY_RESULTVALUES in d:
        out += "    %-12s(%2u):\n" % (KEY_RESULTVALUES, len(d[KEY_RESULTVALUES]))
        for i, row in enumerate(d[KEY_RESULTVALUES]):
            out += "          result %u:\n" % (i)
            for j, val in enumerate(row):
                out += "            %32s: %s\n" % (d[KEY_RESULTS][j], val)
    elif KEY_RESULTS in d:
        out += "    %-12s(%2u):\n" % (KEY_RESULTS, len(d[KEY_RESULTS]))
        for element in d[KEY_RESULTS]:
            out += "        %s\n" % (element)

    return out
