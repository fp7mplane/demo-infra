#!/usr/bin/env python3
#
# mPlane Protocol Reference Implementation
# Reasoner for the Web QoE Use Case
#
# (c) 2013-2014 mPlane Consortium (http://www.ict-mplane.eu)
#               Author: Marco Milanesio
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version. This program is distributed in the hope that it
# will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser
# General Public License for more details. You should have received a copy
# of the GNU General Public License along with this program.  If not, see
# <http://www.gnu.org/licenses/>.

import urllib3
import argparse
import configparser
# import signal
import sys
import os
# import time
# import random

pri = os.getenv('MPLANE_RI')
if pri is None:
    raise ValueError("environment variable MPLANE_RI has not been set")
sys.path.append(pri)

import mplane.model
import mplane.client
import mplane.utils
import mplane.tls


class WebQoEReasoner(object):

    def __init__(self, config):

        try:
            urllib3.disable_warnings()
        except:
            pass

        # preload any registries necessary
        if "client" in config:

            if "registry_preload" in config["client"]:
                mplane.model.preload_registry(
                    config["client"]["registry_preload"])

            if "registry_uri" in config["client"]:
                registry_uri = config["client"]["registry_uri"]
            else:
                registry_uri = None
        else:
            registry_uri = None

        # load default registry
        mplane.model.initialize_registry(registry_uri)

        super().__init__()
        tls_state = mplane.tls.TlsState(config)
        self._defaults = {}
        self._when = None

        # don't print tracebacks by default
        self._print_tracebacks = False

        # default workflow is client-initiated
        # FIXME this should be boolean instead
        self._workflow = "client-initiated"

        if "client" in config:
            if "workflow" in config["client"]:
                self._workflow = config["client"]["workflow"]

        if self._workflow == "component-initiated":
            self._client = mplane.client.HttpListenerClient(config=config,
                                                            tls_state=tls_state)
        elif self._workflow == "client-initiated":
            self._client = mplane.client.HttpInitiatorClient(config=config,
                                                             tls_state=tls_state)

        else:
            raise ValueError("workflow setting in " + args.CONF +
                             " can only be 'client-initiated' or \
                             'component-initiated'")

        if "client" in config and self._workflow != "component-initiated":
            if "default-url" in config["client"]:
                self.do_seturl(config["client"]["default-url"])

            if "capability-url" in config["client"]:
                self.do_getcap(config["client"]["capability-url"])

    def do_seturl(self, arg):
        """
        Set the default URL for this client.
        The default URL is the URL that will be used to invoke
        capabilities which do not have an explicit link.

        Usage: seturl [url]

        """
        try:
            url = arg.split()[0]
        except:
            print("Usage: seturl [url]")
            return

        if self._workflow == "client-initiated":
            self._client.set_default_url(url)
        else:
            print("This command can only be used in client-initiated workflows")
            return

    def do_getcap(self, arg):
        """
        Retrieve capabilities from a given URL.

        Usage: getcap [url]

        """
        if self._workflow == "client-initiated":
            try:
                url = arg.split()[0]
                url = urllib3.util.parse_url(url)
                if url.host is None or url.port is None:
                    print("Bad format for url")
                    return
            except:
                print("Usage: getcap [url]")
                return

            self._client.retrieve_capabilities(url)

            print("ok")
        else:
            print("This command can only be used in client-initiated workflows")
            return

    def do_runcap(self, capspec='webqoe-diagnose', when='now + 1s / 1s', params={}):
        """
        Invoke a capability, identified by label or token. Uses any
        default temporal scope set by a previous when command, and any
        applicable default parameters. Parameters and temporal
        scopes required for the capability but not present are prompted for.

        The optional second argument sets a label for the specification (which
        will apply to the receipt and results as well). If no relabel is given,
        the specification will have the same label as the capability, with a
        serial number attached.

        """

        # Retrieve a capability
        cap = self._client.capability_for(capspec)

        self._when = mplane.model.When(when)
        params = params

        # Now invoke it
        self._client.invoke_capability(cap.get_token(), self._when, params, None)

        for label in self._client.receipt_labels():
            res = self._client.result_for(label)
            # mplane.model.render_text(res)
            try:
                results = res.to_dict()['resultvalues']
            except:
                continue
        print("ok")


def signal_handler(signal, frame):
    print("You pressed CTRL+C, now exiting")
    sys.exit(0)


if __name__ == "__main__":

    # look for TLS configuration
    parser = argparse.ArgumentParser(description="mPlane Reasoner for the \
                                     WebQoE Use Case")
    parser.add_argument('--config', metavar="config-file",
                        help="Configuration file")
    args = parser.parse_args()

    # Read the configuration file, if given
    if args.config:
        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(mplane.utils.search_path(args.config))
    else:
        # hack a default configuration together
        config = {}
        config["is_default"] = True
        config["client"] = {}
        config["client"]["workflow"] = "client-initiated"

    # run the reasoner
    # signal.signal(signal.SIGINT, signal_handler)
    cpr = WebQoEReasoner(config)
    params = {}
    cpr.do_runcap(capspec='webqoe-diagnose', when='now + 1s / 1s', params=params)
