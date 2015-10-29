#!/usr/bin/env python3
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
##
# mPlane Protocol Reference Implementation
# Simple client command-line interface
#
# (c) 2013-2014 mPlane Consortium (http://www.ict-mplane.eu)
#               Author: Brian Trammell <brian@trammell.ch>
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

import sys
import cmd
import traceback
import urllib3
import argparse
import configparser
from time import sleep

import queue
import re
import tornado.web
from time import sleep
import threading
from threading import Thread
import logging

import mplane.model
import mplane.tls
import mplane.utils
import mplane.client
import mplane.component
import mplane.svgui_handlers

DUMMY_DN = "Identity.Unauthenticated.Default"

# DEFAULT_IDENTITY = "default"
# FORGED_DN_HEADER = "Forged-MPlane-Identity"
# DEFAULT_PORT = 8888
# DEFAULT_HOST = "127.0.0.1"
# CAPABILITY_PATH_ELEM = "capability"

REGISTRATION_PATH = "register/capability"
SPECIFICATION_PATH = "show/specification"
RESULT_PATH = "register/result"
S_CAPABILITY_PATH = "show/capability"
S_SPECIFICATION_PATH = "register/specification"
S_RESULT_PATH = "show/result"

GUI_PORT = '8899'
GUI_LOGIN_PATH = "gui/login"
GUI_USERSETTINGS_PATH = "gui/settings"
GUI_STATIC_PATH = "gui/static"

GUI_LISTCAPABILITIES_PATH = "gui/list/capabilities"
GUI_RUNCAPABILITY_PATH = "gui/run/capability"
GUI_LISTPENDINGS_PATH = "gui/list/pendings"
GUI_LISTRESULTS_PATH = "gui/list/results"
GUI_GETRESULT_PATH = "gui/get/result"

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


class ClientShell(cmd.Cmd):

    intro = 'mPlane client shell (rev 20.1.2015, sdk branch)\n'\
            'Type help or ? to list commands. ^D to exit.\n'
    prompt = '|mplane| '

    def __init__(self, config):
        # We're using our own root.

        # FIXME HACK
        # some urllib3 versions let you disable warnings about untrusted CAs,
        # which we use a lot in the project demo. Try to disable warnings if
        # we can.
        try:
            urllib3.disable_warnings()
        except:
            pass
            
        self.config = config
        self.exited = False

        self._caps = []
        self._defaults = {}
        self._when = None

        # don't print tracebacks by default
        self._print_tracebacks = False

        # preload any registries necessary
        # from_begin supervisor
        # preload any registries necessary
        if "registry_preload" in config["component"]:
            mplane.model.preload_registry(config["component"]["registry_preload"])
        # initialize core registry
        if "registry_uri" in config["component"]:
            registry_uri = config["component"]["registry_uri"]
        else:
            registry_uri = None
        # from_end supervisor
     
        if "registry_preload" in config["client"]:
            mplane.model.preload_registry(config["client"]["registry_preload"])
        if "registry_uri" in config["client"]:
            registry_uri = config["client"]["registry_uri"]
        else:
            registry_uri = None

        # load default registry
        mplane.model.initialize_registry(registry_uri)

        #? kell ez? from svgui/clientshell
        super().__init__()
        
        tls_state = mplane.tls.TlsState(config)
        # tls_state.onesided_https = True;

        # default workflow is client-initiated
        # FIXME this should be boolean instead
        # self._workflow = "client-initiated"

        # from_begin supervisor.py
        
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
        # self.run()
        # from_end supervisor.py
        
        if "client" in config and self.cli_workflow != "component-initiated":
            if "default-url" in config["client"]:
                self.do_seturl(config["client"]["default-url"])

            if "capability-url" in config["client"]:
                self.do_getcap(config["client"]["capability-url"])

        # share Http*Client's environment thru self._client
        # self._supervisor = mplane.svgui_handlers.ClientGui(config=config, cs=self,client=self._client)
        self._client._reguri = registry_uri
        self._supervisor = ClientGui(config=config, cs=self,client=self._client)
        # self.run()

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
                                                            
    """
    this is ClientShell stuff
    """
    
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

    def do_listcap(self, arg):
        """
        List available capabilities by label (if available) or token
        (for unlabeled capabilities)

        Usage: listcap

        """
        for label in sorted(self._client.capability_labels()):
            print("Capability %s (token %s)" %
                  (label, self._client.capability_for(label).get_token()))

        for token in sorted(self._client.capability_tokens()):
            cap = self._client.capability_for(token)
            if cap.get_label() is None:
                print("Capability (token %s)" % (token))

    def do_showcap(self, arg):
        """
        Show details for a capability by label or token

        Usage: showcap [label-or-token]

        """
        try:
            print(mplane.model.render_text(self._client.capability_for(arg)))
        except:
            print("Usage: showcap [label-or-token]")
            return

    def complete_showcap(self, text, line, start_index, end_index):
        """Tab-complete known capability labels and tokens in first position"""

        matches = []
        beginning = line[len("showcap "):]
        for label in self._client.capability_labels():
            if label.startswith(beginning):
                matches.append(label[len(beginning) - len(text):])

        for token in self._client.capability_tokens():
            if token.startswith(beginning):
                matches.append(token[len(beginning) - len(text):])
        return matches

    def do_when(self, arg):
        """
        Get or set a default temporal scope to use for capability
        invocation.

        Usage: when
        Usage: when [temporal-scope]

        """
        if len(arg) > 0:
            try:
                self._when = mplane.model.When(arg)
            except:
                print("Invalid temporal scope "+arg)
                return

        print("when = "+str(self._when))

    def do_set(self, arg):
        """
        Set a default parameter value for subsequent capability
        invocation.

        Usage: set [parameter-name] [value]

        """
        try:
            sarg = arg.split()
            key = sarg.pop(0)
            val = " ".join(sarg)
            self._defaults[key] = val
            print(key + " = " + val)
        except:
            print("Couldn't set default "+arg)

    def complete_set(self, text, line, start_index, end_index):
        """Tab-complete the set of names in the registry in first position"""

        matches = []
        beginning = line[len("set "):]
        for key in self._defaults:
            if key.startswith(beginning):
                matches.append(key[len(beginning) - len(text):])
        return matches

    def do_unset(self, arg):
        """
        Unset values for previously set default parameters.
        Without an argument, clears all defaults.

        Usage: unset
        Usage: unset [parameter-name] ([parameter-name] ...)

        """
        if len(arg) > 0:
            try:
                keys = arg.split()
                for key in keys:
                    del self._defaults[key]
            except:
                print("Couldn't unset default(s) "+arg)
                return
        else:
            self._defaults.clear()

        print("ok")

    def complete_unset(self, text, line, start_index, end_index):
        """Tab-complete the set of defaults in any position"""

        matches = []
        beginning = line[len("unset "):]
        for key in self._defaults:
            if key.startswith(beginning):
                matches.append(key[len(beginning) - len(text):])
        return matches

    def do_show(self, arg):
        """
        Show values for parameter defaults, or all values
        if no parameter names given

        Usage: show
        Usage: show [parameter-name] ([parameter-name] ...)

        """
        if len(arg) > 0:
            try:
                for key in arg.split():
                    val = self._defaults[key]
                    print(key + " = " + val)
            except:
                print("No such default "+key)
        else:
            print("%4u defaults" % len(self._defaults))
            for key, val in self._defaults.items():
                print(key + " = " + val)

    def complete_show(self, text, line, start_index, end_index):
        """Tab-complete the set of defaults in any position"""

        matches = []
        beginning = line[len("show "):]
        for key in self._defaults:
            if key.startswith(beginning):
                matches.append(key[len(beginning) - len(text):])
        return matches

    def do_runcap(self, arg):
        """
        Invoke a capability, identified by label or token. Uses any
        default temporal scope set by a previous when command, and any
        applicable default parameters. Parameters and temporal
        scopes required for the capability but not present are prompted for.

        The optional second argument sets a label for the specification (which
        will apply to the receipt and results as well). If no relabel is given,
        the specification will have the same label as the capability, with a
        serial number attached.

        Usage: runcap [label-or-token] ([relabel])

        """

        try:
            arglist = arg.split()

            if len(arglist) >= 1:
                capspec = arglist[0]
                if len(arglist) >= 2:
                    relabel = arglist[1]
                else:
                    relabel = None
            else:
                print("Usage: runcap [label-or-token] ([relabel])")
                return
        except:
            print("Usage: runcap [label-or-token] ([relabel])")
            return

        # Retrieve a capability
        cap = self._client.capability_for(capspec)

        # Prompt for when if missing or inappropriate
        while self._when is None or \
              not self._when.follows(cap.when()):
            sys.stdout.write("|when| = ")
            self._when = mplane.model.When(input())

        # Prompt for missing capabilities (saving these in defaults)
        params = {}
        for pname in sorted(cap.parameter_names()):
            while pname not in self._defaults or \
                  not cap.can_set_parameter_value(pname, self._defaults[pname]):
                single_val = cap.get_single_parameter_value(pname)
                if single_val is not None:
                    self._defaults[pname] = str(single_val)
                    sys.stdout.write(pname + " = " + str(single_val) + "\n")
                else:
                    sys.stdout.write(pname + " = ")
                    self._defaults[pname] = input()
            params[pname] = self._defaults[pname]

        # Now invoke it
        self._client.invoke_capability(cap.get_token(), self._when, params, relabel)
        print("ok")

    def complete_runcap(self, text, line, start_index, end_index):
        """Tab-complete known capability labels and tokens in first position"""

        matches = []
        beginning = line[len("runcap "):]
        for label in self._client.capability_labels():
            if label.startswith(beginning):
                matches.append(label[len(beginning) - len(text):])

        for token in self._client.capability_tokens():
            if token.startswith(beginning):
                matches.append(token[len(beginning) - len(text):])
        return matches

    def do_listmeas(self, arg):
        """
        List running/completed measurements by label and/or token

        Usage: listmeas

        """
        for label in self._client.receipt_labels():
            rec = self._client.result_for(label)
            if isinstance(rec, mplane.model.Receipt):
                print("Receipt %s (token %s): %s" %
                      (label, rec.get_token(), rec.when()))

        for token in self._client.receipt_tokens():
            rec = self._client.result_for(token)
            if isinstance(rec, mplane.model.Receipt):
                if rec.get_label() is None:
                    print("Receipt (token %s): %s" % (token, rec.when()))

        for label in self._client.result_labels():
            res = self._client.result_for(label)
            if not isinstance(res, mplane.model.Exception):
                print("Result  %s (token %s): %s" %
                      (label, res.get_token(), res.when()))

        for token in self._client.result_tokens():
            res = self._client.result_for(token)
            if isinstance(res, mplane.model.Exception):
                print(res.__repr__())
            elif res.get_label() is None:
                print("Result  (token %s): %s" % (token, res.when()))

    def do_stopmeas(self, arg):
        """
        Interrupts the measurement identified by label and/or token

        Usage: stopmeas [label-or-token]

        """
        try:
            meas_tol = arg.split()[0]
        except:
            print("Usage: stopmeas [label-or-token]")
            return

        self._client.interrupt_capability(meas_tol)

    def complete_stopmeas(self, text, line, start_index, end_index):
        """Tab-complete known capability labels and tokens in first position"""

        matches = []
        beginning = line[len("stopmeas "):]
        for label in self._client.receipt_labels():
            if label.startswith(beginning):
                matches.append(label[len(beginning) - len(text):])
        for token in self._client.receipt_tokens():
            if token.startswith(beginning):
                matches.append(token[len(beginning) - len(text):])
        for label in self._client.result_labels():
            if label.startswith(beginning):
                matches.append(label[len(beginning) - len(text):])
        for token in self._client.result_tokens():
            if token.startswith(beginning):
                matches.append(token[len(beginning) - len(text):])
        return matches

    def do_showmeas(self, arg):
        """
        Show details of measurements by label and/or token

        Usage: showmeas [label-or-token]

        """
        try:
            meas = arg.split()[0]
        except:
            print("Usage: showmeas [label-or-token]")
            return

        res = self._client.result_for(meas)
        mplane.model.render_text(res)

    def complete_showmeas(self, text, line, start_index, end_index):
        """Tab-complete known capability labels and tokens in first position"""

        matches = []
        beginning = line[len("showmeas "):]
        for label in self._client.receipt_labels():
            if label.startswith(beginning):
                matches.append(label[len(beginning) - len(text):])
        for token in self._client.receipt_tokens():
            if token.startswith(beginning):
                matches.append(token[len(beginning) - len(text):])
        for label in self._client.result_labels():
            if label.startswith(beginning):
                matches.append(label[len(beginning) - len(text):])
        for token in self._client.result_tokens():
            if token.startswith(beginning):
                matches.append(token[len(beginning) - len(text):])
        return matches

    def do_tbenable(self, arg):
        """Enable tracebacks on uncaught exceptions"""
        self._print_tracebacks = True

    def do_EOF(self, arg):
        """Exit the shell by typing ^D"""
        print("Ciao!")
        self.exited = True
        return True

    def handle_uncaught(self, e):
        print("An exception occurred:")
        print(e)
        if self._print_tracebacks:
            traceback.print_tb(sys.exc_info()[2])
        print("You can try to continue, but client state may be inconsistent.")


class ClientGui(mplane.client.BaseClient):
    """
    Based on: mplane.client.HttpListenerClient.
    Core implementation of an mPlane JSON-over-HTTP(S) client.
    Supports component-initiated workflows. Intended for building
    supervisors.

    """
    def __init__(self, config, tls_state=None,
                 supervisor=False, exporter=None, io_loop=None, cs=None, client=None):
        super().__init__(tls_state, supervisor=supervisor,
                        exporter=exporter)

        self._cs = cs
        self._client = client
        self._tls_state = tls_state
        
        # TODO: cleanup if not needed, as being common (self._cs)
        gui_port = GUI_PORT
        if "gui-port" in config["gui"]:
            listen_port = int(config["gui"]["gui-port"])

        registration_path = REGISTRATION_PATH
        if "registration-path" in config["client"]:
            registration_path = config["client"]["registration-path"]

        specification_path = SPECIFICATION_PATH
        if "registration-path" in config["client"]:
            specification_path = config["client"]["specification-path"]

        result_path = RESULT_PATH
        if "result-path" in config["client"]:
            result_path = config["client"]["result-path"]

        # link to which results must be sent
        self._link = config["client"]["listen-spec-link"]
        logging.debug(">>> ClientGui.__init__: self._link = " + str(self._link))

        # Outgoing messages per component identifier
        self._outgoing = {}

        # specification serial number
        # used to create labels programmatically
        self._ssn = 0

        # Capability
        self._callback_capability = {}

        # Create a request handler pointing at this client
        self._tornado_application = tornado.web.Application([
            (r"/" + registration_path, mplane.client.RegistrationHandler, {'supervisor': self._client, 'tlsState': self._tls_state}),
            (r"/" + registration_path + "/", mplane.client.RegistrationHandler, {'supervisor': self._client, 'tlsState': self._tls_state}),
            (r"/" + specification_path, mplane.client.SpecificationHandler, {'supervisor': self._client, 'tlsState': self._tls_state}),
            (r"/" + specification_path + "/", mplane.client.SpecificationHandler, {'supervisor': self._client, 'tlsState': self._tls_state}),
            (r"/" + result_path, mplane.client.ResultHandler, {'supervisor': self._client, 'tlsState': self._tls_state}),
            (r"/" + result_path + "/", mplane.client.ResultHandler, {'supervisor': self._client, 'tlsState': self._tls_state}),

            (r"/" + S_CAPABILITY_PATH, mplane.svgui_handlers.S_CapabilityHandler, {'supervisor': self._client, 'tlsState': self._tls_state}),
            (r"/" + S_CAPABILITY_PATH + "/", mplane.svgui_handlers.S_CapabilityHandler, {'supervisor': self._client, 'tlsState': self._tls_state}),
            (r"/" + S_SPECIFICATION_PATH, mplane.svgui_handlers.S_SpecificationHandler, {'supervisor': self._client, 'tlsState': self._tls_state}),
            (r"/" + S_SPECIFICATION_PATH + "/", mplane.svgui_handlers.S_SpecificationHandler, {'supervisor': self._client, 'tlsState': self._tls_state}),
            (r"/" + S_RESULT_PATH, mplane.svgui_handlers.S_ResultHandler, {'supervisor': self._client, 'tlsState': self._tls_state}),
            (r"/" + S_RESULT_PATH + "/", mplane.svgui_handlers.S_ResultHandler, {'supervisor': self._client, 'tlsState': self._tls_state}),

            (r"/" + GUI_LOGIN_PATH, mplane.svgui_handlers.LoginHandler, {'supervisor': self._client}),
            (r"/" + GUI_USERSETTINGS_PATH, mplane.svgui_handlers.UserSettingsHandler, {'supervisor': self._client}),
            (r"/" + GUI_LISTCAPABILITIES_PATH, mplane.svgui_handlers.ListCapabilitiesHandler, {'supervisor': self._client, 'tlsState': self._tls_state}),
            (r"/" + GUI_LISTPENDINGS_PATH, mplane.svgui_handlers.ListPendingsHandler, {'supervisor': self._client, 'tlsState': self._tls_state}),
            (r"/" + GUI_LISTRESULTS_PATH, mplane.svgui_handlers.ListResultsHandler, {'supervisor': self._client, 'tlsState': self._tls_state}),
            (r"/" + GUI_GETRESULT_PATH, mplane.svgui_handlers.GetResultHandler, {'supervisor': self._client, 'tlsState': self._tls_state}),
            (r"/" + GUI_RUNCAPABILITY_PATH, mplane.svgui_handlers.RunCapabilityHandler, {'supervisor': self._client, 'tlsState': self._tls_state}),
            (r"/", mplane.svgui_handlers.ForwardHandler, {'forwardUrl': '/gui/static/login.html'}),
            (r"/gui", mplane.svgui_handlers.ForwardHandler, {'forwardUrl': '/gui/static/login.html'})
        ], cookie_secret="123456789-TODO-REPLACE", static_path=r"www/", static_url_prefix=r"/" + GUI_STATIC_PATH + "/")
        # ssl_options=tls_state.get_ssl_options() removed for GUI access
        http_server = tornado.httpserver.HTTPServer(self._tornado_application)

        # run the server
        logging.debug(">>> ClientGui running on port " + str(listen_port))
        http_server.listen(listen_port)
        if io_loop is not None:
            cli_t = Thread(target=self.listen_in_background(io_loop))
        else:
            cli_t = Thread(target=self.listen_in_background)
        cli_t.daemon = True
        cli_t.start()

    def listen_in_background(self, io_loop=None):
        """
        The server listens for requests in background, while
        the supervisor console remains accessible
        """
        if io_loop is None:
            tornado.ioloop.IOLoop.instance().start()

    def _push_outgoing(self, identity, msg):
        if identity not in self._outgoing:
            self._outgoing[identity] = []
        self._outgoing[identity].append(msg)

    def invoke_capability(self, cap_tol, when, params, relabel=None, callback_when=None):
        """
        Given a capability token or label, a temporal scope, a dictionary
        of parameters, and an optional new label, derive a specification
        and queue it for retrieval by the appropriate identity (i.e., the
        one associated with the capability).

        If the identity has indicated it supports callback control,
        the optional callback_when parameter queues a callback spec to
        schedule the next callback.
        """
        # grab cap, spec, and identity
        # logging.debug(">>> ClientGui.invoke_capability")
        (cap, spec) = self._spec_for(cap_tol, when, params, relabel)
        identity = self.identity_for(cap.get_token())
        spec.set_link(self._link)

        callback_cap = None
        if identity in self._callback_capability:
            # prepare a callback spec if we need to
            callback_cap = self._callback_capability[identity]
        if callback_cap and callback_when:
            callback_spec = mplane.model.Specification(capability=callback_cap)
            callback_spec.set_when(callback_when)
            envelope = mplane.model.Envelope()
            envelope.append_message(callback_spec)
            envelope.append_message(spec)
            self._push_outgoing(identity, envelope)
        else:
            self._push_outgoing(identity, spec)
        return spec

    def interrupt_capability(self, cap_tol):
        # get the receipt
        rr = super().result_for(cap_tol)
        identity = self.identity_for(rr.get_token(), receipt=True)
        interrupt = mplane.model.Interrupt(specification=rr)
        self._push_outgoing(identity, interrupt)

    def _add_capability(self, msg, identity):
        """
        Override Client's add_capability, check for callback control
        """
        if msg.verb() == mplane.model.VERB_CALLBACK:
            # FIXME this is kind of dodgy; we should do better checks to
            # make sure this is a real callback capability
            self._callback_capability[identity] = msg
        else:
            # not a callback control cap, just add the capability
            super()._add_capability(msg, identity)


if __name__ == "__main__":

    # look for TLS configuration
    parser = argparse.ArgumentParser(description="mPlane generic testing client")
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

    # create a shell
    logging.debug(">>> creating ClientShell\n")
    cs = ClientShell(config)
    while not cs.exited:
        try:
            cs.cmdloop()
        except Exception as e:
            cs.handle_uncaught(e)
