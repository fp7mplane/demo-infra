#
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
##
# mPlane Protocol Reference Implementation
# Simple mPlane Supervisor (JSON over HTTP)
#
# (c) 2013-2015 mPlane Consortium (http://www.ict-mplane.eu)
#               Author: Stefano Pentassuglia <stefano.pentassuglia@ssbprogetti.it>
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
import mplane.client
import mplane.component
import mplane.utils
import mplane.tls

import queue
import re
import tornado.web
from time import sleep
import threading
from threading import Thread

class RelayService(mplane.scheduler.Service):

    def __init__(self, cap, identity, client, lock, messages):
        self.relay = True
        self._identity = identity
        self._client = client
        self._lock = lock
        self._messages = messages
        super(RelayService, self).__init__(cap)

    def run(self, spec, check_interrupt):
        pattern = re.compile("-\d+$")
        trunc_pos = pattern.search(spec.get_label())
        trunc_label = spec.get_label()[:trunc_pos.start()]
        fwd_spec = self._client.invoke_capability(trunc_label, spec.when(), spec.parameter_values())
        result = None
        pending = False
        while result is None:
            if check_interrupt() and not pending:
                self._client.interrupt_capability(fwd_spec.get_token())
                pending = True
            sleep(1)
            with self._lock:
                if self._identity in self._messages:
                    for msg in self._messages[self._identity]:
                        if msg.get_token() == fwd_spec.get_token():
                            if (isinstance(msg, mplane.model.Result) or
                                isinstance(msg, mplane.model.Envelope)):
                                print("Received result for " + trunc_label + " from " + self._identity)
                            elif isinstance(msg, mplane.model.Exception):
                                print("Received exception for " + trunc_label + " from " + self._identity)
                            result = msg
                            self._messages[self._identity].remove(msg)
                            break

        if (not isinstance(result, mplane.model.Exception)
           and not isinstance(result, mplane.model.Envelope)):
            result.set_label(spec.get_label())
        result.set_token(spec.get_token())
        return result

class BaseSupervisor(object):
    
    def __init__(self, config):
        self._caps = []
        self.config = config

        # preload any registries necessary
        if "registry_preload" in config["component"]:
            mplane.model.preload_registry(
                config["component"]["registry_preload"])

        # initialize core registry
        if "registry_uri" in config["component"]:
            registry_uri = config["component"]["registry_uri"]
        else:
            registry_uri = None
        mplane.model.initialize_registry(registry_uri)

        tls_state = mplane.tls.TlsState(config)

        self.from_cli = queue.Queue()
        self._lock = threading.RLock()
        self._spec_messages = dict()
        self._io_loop = tornado.ioloop.IOLoop.instance()
        if self.config["client"]["workflow"] == "component-initiated":
            self.cli_workflow = "component-initiated"
            self._client = mplane.client.HttpListenerClient(config=config,
                                                            tls_state=tls_state, supervisor=True,
                                                            exporter=self.from_cli,
                                                            io_loop=self._io_loop)
        elif self.config["client"]["workflow"] == "client-initiated":
            self.cli_workflow = "client-initiated"
            self._client = mplane.client.HttpInitiatorClient(tls_state=tls_state, supervisor=True,
                                                             exporter=self.from_cli)
            self._urls = self.config["client"]["component-urls"].split(",")
        else:
            raise ValueError("workflow setting in " + args.CONF + " can only be 'client-initiated' or 'component-initiated'")

        if self.config["component"]["workflow"] == "component-initiated":
            self.comp_workflow = "component-initiated"
            self._component = mplane.component.InitiatorHttpComponent(config, supervisor=True)
        elif self.config["component"]["workflow"] == "client-initiated":
            self.comp_workflow = "client-initiated"
            self._component = mplane.component.ListenerHttpComponent(config, io_loop=self._io_loop)
        else:
            raise ValueError("workflow setting in " + args.CONF + " can only be 'client-initiated' or 'component-initiated'")
        self.run()

    def run(self):
        if (self.cli_workflow == "component-initiated" or
            self.comp_workflow == "client-initiated"):
            t_listen = Thread(target=self.listen_in_background)
            t_listen.daemon = True
            t_listen.start()
        if self.cli_workflow == "client-initiated":
            t_poll = Thread(target=self.poll_in_background)
            t_poll.daemon = True
            t_poll.start()
        while True:
            if not self.from_cli.empty():
                [msg, identity] = self.from_cli.get()
                self.handle_message(msg, identity)
            sleep(0.1)

    def handle_message(self, msg, identity):
        if isinstance(msg, mplane.model.Capability):
            if [msg.get_label(), identity] not in self._caps:
                self._caps.append([msg.get_label(), identity])
                serv = RelayService(msg, identity, self._client,
                                    self._lock, self._spec_messages)
                if self.comp_workflow == "client-initiated":
                    serv.set_capability_link(self.config["component"]["listen-cap-link"])
                self._component.scheduler.add_service(serv)
                if self.comp_workflow == "component-initiated":
                    self._component.register_to_client([serv.capability()])

        elif isinstance(msg, mplane.model.Receipt):
            pass
            
        elif (isinstance(msg, mplane.model.Result) or
            isinstance(msg, mplane.model.Exception)):
            with self._lock:
                mplane.utils.add_value_to(self._spec_messages, identity, msg)
            
        elif isinstance(msg, mplane.model.Withdrawal):
            # not yet implemented
            pass

        elif isinstance(msg, mplane.model.Envelope):
            for imsg in msg.messages():
                if isinstance(imsg, mplane.model.Result):
                    mplane.utils.add_value_to(self._spec_messages, identity, msg)
                    break
                else:
                    self.handle_message(imsg, identity)
        else:
            raise ValueError("Internal error: unknown message "+repr(msg))

    def listen_in_background(self):
        """ Start the listening server """
        self._io_loop.start()

    def poll_in_background(self):
        """ Periodically poll components """
        while True:
            for url in self._urls:
                try:
                    self._client.retrieve_capabilities(url)
                except:
                    print(str(url) + " unreachable. Retrying in 5 seconds")

            # poll for results
            for label in self._client.receipt_labels():
                self._client.result_for(label)

            for token in self._client.receipt_tokens():
                self._client.result_for(token)

            for label in self._client.result_labels():
                self._client.result_for(label)

            for token in self._client.result_tokens():
                self._client.result_for(token)

            sleep(5)