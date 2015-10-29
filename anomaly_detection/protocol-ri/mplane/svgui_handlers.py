#
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
##
# mplane supervisor GUI
# (c) 2014-2015 mPlane Consortium (http://www.ict-mplane.eu)
#               Author: Janos Bartok-Nagy <jnos.bartok-nagy@netvisor.hu>,
#                       Attila Bokor ;attila.bokor@netvisor.hu>
#
# based on mPlane Protocol Reference Implementation:
#
# (c) 2013-2015 mPlane Consortium (http://www.ict-mplane.eu)
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

import mplane.model
import mplane.utils
import mplane.client
import mplane.svgui

from datetime import datetime
import html.parser
import urllib3
import json
import collections
import sys
import os

# FIXME HACK
# some urllib3 versions let you disable warnings about untrusted CAs,
# which we use a lot in the project demo. Try to disable warnings if we can.
from threading import Thread
import queue

import tornado.web
import tornado.httpserver
import tornado.ioloop
import logging



logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

try:
    urllib3.disable_warnings()
except:
    pass

CONFIGFILE = "conf/guiconf.json"
DIRECTORY_USERSETTINGS = "conf/usersettings"


def get_dn(supervisor, request):
    """
    Extracts the DN from the request object. 
    If SSL is disabled, returns a dummy DN
    
    """
    # if supervisor._sec == True:
    if supervisor._tls_state._keyfile:
        dn = supervisor._tls_state._identity
        # dn = ""
        # for elem in request.get_ssl_certificate().get('subject'):
            # if dn == "":
                # dn = dn + str(elem[0][1])
            # else: 
                # dn = dn + "." + str(elem[0][1])
    else:
        if "Forged-Mplane-Identity" in request.headers.keys():
            dn = request.headers["Forged-Mplane-Identity"]
        else:
            dn = DUMMY_DN
    # self._tls_state = mplane.tls.TlsState(supervisor.config)
    # dn = self._tls.extract_peer_identity(supervisor, request)
    # logging.debug(">>> sv_handlers.py:get_dn(): dn = " + dn)
    return dn
               

###########################################################
# sv_gui_handlers
###########################################################

class S_CapabilityHandler(mplane.client.MPlaneHandler):
    """
    Exposes to a client the capabilities registered to this supervisor. 
    
    """

    def initialize(self, supervisor, tlsState):
        self._supervisor = supervisor
        self._tls = tlsState
        self.dn = get_dn(self._supervisor, self.request)
        # logging.debug("\n>>> S_CapabilityHandler(): self = " + str(self) + " self.dn = " + str(self.dn) + " self._supervisor =" + str(self._supervisor))
    
    def get(self):
        """
        Returns a list of all the available capabilities 
        (filtered according to the privileges of the client)
        in the form of a JSON array of Capabilities
        
        """
        # # check the class of the certificate (Client, Component, Supervisor).
        # # this function can only be used by clients
        if (self.dn.find("Clients") == -1 and self.dn != DUMMY_DN):
            self._respond_plain_text(401, "Not Authorized. Only Clients can use this function")
            return
        
        try:
            msg = ""
        
            # list capabilities
            # logging.debug("\n>>> S_CapabilityHandler: _supervisor._capabilities = \n" + str(self._supervisor._capabilities))
            for key in self._supervisor._capabilities:
                found = False
                # logging.debug(">>> key= " + key)
                cap = self._supervisor._capabilities[key]
                # logging.debug("      cap = " + str(cap))
                cap_id = cap.get_label() + ", " + key
                # 2FIX: would be better to do without raise error so that continue even in case of problems
                if self._supervisor.identity_for(cap.get_token()):
                # if self._supervisor._capabilities.check_azn(cap_id, self.dn):
                    if found == False:
                        msg = msg + "\"" + key + "\":["
                        found = True
                    msg = msg + mplane.model.unparse_json(cap) + ","
                if found == True:
                    msg = msg[:-1].replace("\n","") + "],"
            msg = "{" + msg[:-1].replace("\n","") + "}"
            # logging.debug("\n>>> S_CapabilityHandler.get: msg = \n" + msg)
            self._respond_json_text(200, msg)
        
        except Exception as e:
            self.write( "{ERROR:\"" + str(e) + "\"}" )

        
class S_SpecificationHandler(mplane.client.MPlaneHandler):
    """
    Receives specifications from a (GUI)client. If the client is
    authorized to run the spec, this supervisor forwards it 
    to the probe.

    """

    def initialize(self, supervisor, tlsState):
        self._supervisor = supervisor
        self._tls = tlsState
        self.dn = get_dn(self._supervisor, self.request)
        logging.debug("\n>>> S_SpecificationHandler:init(): self.dn = " + self.dn)
    
    def post(self):
        
        # check the class of the certificate (Client, Component, Supervisor).
        # this function can only be used by clients
        if (self.dn.find("Clients") == -1 and self.dn != DUMMY_DN):
            self._respond_plain_text(401, "Not Authorized. Only Clients can use this function")
            return
            
        # unwrap json message from body
        if (self.request.headers["Content-Type"] == "application/x-mplane+json"):
            j_spec = json.loads(self.request.body.decode("utf-8"))
            
            # get DN and specification (only one, then this for cycle breaks)
            for key in j_spec:
                probe_dn = key
                spec = mplane.model.parse_json(json.dumps(j_spec[probe_dn]))
                
                if isinstance(spec, mplane.model.Specification):
                    receipt = mplane.model.Receipt(specification=spec)
                    
                    if spec.get_label() not in self._supervisor._label_to_dn:
                        self._respond_plain_text(403, "This measure doesn't exist")
                        return
                    if probe_dn not in self._supervisor._dn_to_ip:
                        self._respond_plain_text(503, "Specification is unavailable. The component for the requested measure was not found")
                        return
                        
                    # enqueue the specification
                    if not self._supervisor.add_spec(spec, probe_dn):
                        self._respond_plain_text(503, "Specification is temporarily unavailable. Try again later")
                        return
                                                
                    # return the receipt to the client        
                    self._respond_message(receipt)
                    return
                else:
                    self._respond_plain_text(400, "Invalid format")
                    return

                    
class S_ResultHandler(mplane.client.MPlaneHandler):
    """
    Receives receipts from a client. If the corresponding result
    is ready, this supervisor sends it to the probe.
    bnj: ???? 
    """

    def initialize(self, supervisor, tlsState):
        self._supervisor = supervisor
        self._tls = tlsState
        self.dn = get_dn(self._supervisor, self.request)
        logging.debug("\n>>> S_ResultHandler:init(): self.dn = " + self.dn)
    
    def get(self):
    # def post(self):
        
        # check the class of the certificate (Client, Component, Supervisor).
        # this function can only be used by clients
        if (self.dn.find("Clients") == -1 and self.dn != DUMMY_DN):
            self._respond_plain_text(401, "Not Authorized. Only Clients can use this function")
            return
            
        # unwrap json message from body
        if (self.request.headers["Content-Type"] == "application/x-mplane+json"):
            rec = mplane.model.parse_json(self.request.body.decode("utf-8"))
            if isinstance(rec, mplane.model.Redemption):    
                # check if result is ready. if so, return it to client
                for dn in self._supervisor._results:
                    for r in self._supervisor._results[dn]:
                        if str(r.get_token()) == str(rec.get_token()):
                            self._respond_message(r)
                            self._supervisor._results[dn].remove(r)
                            return
                meas = self._supervisor.measurements()
                
                # if result is not ready, return the receipt
                for dn in meas:
                    for r in meas[dn]:
                        if str(r.get_token()) == str(rec.get_token()):
                            self._respond_message(r)
                            return
                # if there is no measurement and no result corresponding to the redemption, it is unexpected
                self._respond_plain_text(403, "Unexpected Redemption")
                return
        else:
            if (self.request.headers["Content-Type"]):
                self._respond_plain_text(400, "Not in  'application/x-mplane+json' format")
            else:
                self._respond_plain_text(400, "No Content-Type defined")
        return

        
###########################################################
# sv_gui_handlers
###########################################################

class ForwardHandler(tornado.web.RequestHandler):
    """
    This handler implements a simple static HTTP redirect.
    """
    def initialize(self, forwardUrl):
        self._forwardUrl = forwardUrl

    def get(self):
        self.redirect( self._forwardUrl )

    def post(self):
        self.redirect( self._forwardUrl )

        
class LoginHandler(tornado.web.RequestHandler):
    """
    Implements authentication.
    
    GET: redirect to the login page.
    
    POST: checks the posted user credentials, and set a secure cookie named "user", if credentials are valid. Required content type is application/x-www-form-urlencoded,
    username and password parameters are required. Response code is always 200. Body is {} for successful login, or {ERROR: "some complaints"} in all other cases.     
    """
    def initialize(self, supervisor):
        self._supervisor = supervisor

    def get(self):
        self.redirect("/gui/static/login.html")

    def post(self):
        configfile = open(CONFIGFILE, "r")
        guiconfig = json.load( configfile )
        configfile.close()
        userTry = self.get_body_argument("username", strip=True)
        pwdTry = self.get_body_argument("password", strip=True)

        if userTry in guiconfig['users'].keys() and guiconfig['users'][userTry]['password'] == pwdTry:            
            self.set_secure_cookie("user", userTry, 1)
            self.set_status(200);
            self.set_header("Content-Type", "text/json")
            self.write("{}")
        else:
            self.clear_cookie("user")
            self.set_status(200);
            self.set_header("Content-Type", "text/json")
            self.write("{ERROR:\"Authentication failed for user " + userTry + "\"}")

        self.finish()

        
class UserSettingsHandler(tornado.web.RequestHandler):
    """
    Stores and gives back user-specific settings. Signed-in user defined by secure cookie named "user".
    Content-type is always text/json.
    
    GET: answers the settings JSON of the current user (initially it's "{}").

    POST: stores the posted settings JSON for the current user (it must be a valid JSON).
    """
    def initialize(self, supervisor):
        self._supervisor = supervisor

    def get(self):
        user = self.get_secure_cookie("user")
        if user is None:
            self.redirect("/gui/static/login.html")
        else:
            try:
                self.set_status(200)
                self.set_header("Content-Type", "text/json")
                f = open(DIRECTORY_USERSETTINGS + os.sep + user.decode('utf-8'), "r")
                self.write( f.read() )
                f.close()
            except Exception as e:
                self.write( "{ERROR:\"" + str(e) + "\"}" )
            self.finish()

    def post(self):
        user = self.get_secure_cookie("user")
        if user is None:
            self.redirect("/gui/static/login.html")
        else:
            try:
                f = open(DIRECTORY_USERSETTINGS + os.sep + user.decode('utf-8'), "w")
                f.write( self.request.body.decode("utf-8") )
                self.set_status(200)
                self.set_header("Content-Type", "text/json")
                self.write("{}\n")
                f.close()
            except Exception as e:
                self.write( "{ERROR:\"" + str(e) + "\"}" )
            self.finish()
            

def filterlist(self, reguri=None):
    """
    Returns dict of {filtername, filtervalue}.
    TODO: Name collision with 'Start' - as  a workaround, we miss it out from generated filterlist
    
    """

    _filterlist = {}
    _qlist = self.request.arguments
    
    _uri = reguri
    _r = mplane.model.Registry(_uri)
    _regjson = _r._dump_json()
    for _qname in self.request.arguments:
        # print( _qname + ": " + self.get_query_argument( _qname, None, True ) )
        found = False
        for _name in _r._elements:
            # print( "compare against " + str( _name ), end="")
            if found == False:
                if ( _name == _qname ):
                    _filterlist.update( { _qname: self.get_argument( _qname, default=None ) } )
                    found = True
                    # print( _qname + " FOUND, filterlist = " + str(_filterlist))
            else:
                break
    # print("filterlist: " + str( _filterlist) )
    # !!!!! HACK IS HERE !!!!!
    del _filterlist["start"]
    # print("final filterlist: " + str( _filterlist) )
    return _filterlist


def match_filters(self, msg, filterlist):
    """
    check msg against label and parameters
    if checking against not applicable filters, always return false (eg filtering for IP address with ott-download)
    
    """
    _matched = True
    _msg = msg
    _filtlist = filterlist
    _filtname = ""
    _value = ""
    # logging.debug("msg (in json) = " + mplane.model.unparse_json(_msg))

    if isinstance(_msg,mplane.model.Exception):
        logging.debug("SKIPPED because of Exception")
        return False

    # filter by label
    _label = _msg.get_label()
    _filtvalue = self.get_argument("label", default=None)
    if _filtvalue is not None:
        logging.debug( _label + " = " + _filtvalue )
        if ( _label.find(_filtvalue) < 0 ):
            logging.debug("SKIPPED because of label " + _label + " != " + _filtvalue )
            return False
        else:
            logging.debug("label filter = " + _filtvalue + ", label = " + _label + ". Processing further...")
    # else:
        logging.debug("label filter = '', label = " + _label + ". Processing further...")
        
    # return True if no parameter filter defined
    if ( len(_filtlist) == 0 ):
        logging.debug("MATCHED, _filtlist = {}")
        return _matched
    # else:
        logging.debug("_filtlist = ", _filtlist)
        
    # logging.debug("statement type: " + str( type ( _msg ) ))
            
    if isinstance( _msg, mplane.model.Capability ):
        for _filtname in _filtlist:
            # logging.debug("_filtname = " + _filtname)
            if ( _filtname not in _msg.parameter_names() ):
                # logging.debug("SKIPPED because of msg has no filtered attribute " + _filtname )
                return False
            else:
                _value = _msg._params[_filtname]._constraint                        
                _filtvalue = _filtlist[ _filtname ]
                if ( (isinstance( _value, mplane.model._SetConstraint ) and str( _value ).find( _filtvalue ) < 0)
                        or (not isinstance( _value, mplane.model._SetConstraint ) and not _value.met_by( _filtvalue )) ):
                    # logging.debug("SKIPPED because of constraint " + str( _value ) + "is not equal to filter " + _filtvalue )
                    return False
            
    elif ( isinstance( _msg, mplane.model.Result ) or isinstance( _msg, mplane.model.Receipt ) ):
        for _filtname in _filtlist:
            # logging.debug("_filtname = " + _filtname)
            if ( _filtname not in _msg.parameter_names() ):
                # logging.debug("SKIPPED because of msg has no filtered attribute " + _filtname )
                return False
            else:
                _value = _msg.get_parameter_value( _filtname )
                _filtvalue = _filtlist[ _filtname ]
                # logging.debug("_value = " + str(_value) + ", _filtvalue = " + _filtvalue)
                if ( str( _value ).find( _filtvalue ) <0 ) :
                    # logging.debug("SKIPPED because of msg value " + str(_value) + " is not equal to filter value " + _filtvalue )
                    return False
                    
    else:
        raise ValueError("Only Capability, Receipt and Result can be filtered.")
            
    if _matched == False :
        raise NotImplementedError("should not be there - unhandled branch.")
    # print("MATCHED " + _filtname + " paramvalue = " + str( _value ) + ", filtervalue = " + _filtvalue )
    return _matched


class ListCapabilitiesHandler(mplane.client.MPlaneHandler):
# class ListCapabilitiesHandler(tornado.web.RequestHandler):
    """
    Lists the capabilites, registered in the Supervisor. Response is in mplane JSON format.

    GET: capabilites can be filtered by GET parameters named label, and names of parameters of the capability. Response is in mplane JSON format.

    POST is not supported.
    """
    def initialize(self, supervisor, tlsState):
        self._supervisor = supervisor
        self._tls = tlsState
        _flist = {}
        # self.dn = get_dn(self._supervisor, self.request)
        # logging.debug("\n>>> sv_gui_handlers.py:ListCapabilitiesHandler.initialize(): \n self._supervisor._capabilities = \n" + str(self._supervisor._capabilities))

    def get(self):
        if self.get_secure_cookie("user") is None:
            self.redirect("/gui/static/login.html")
            return
        
        # _flist = filterlist(self, reguri="mplane/components/ott-probe/ott-registry.json")
        _flist = filterlist(self, reguri=self._supervisor._reguri)
        # logging.debug("_flist = " + str( _flist ))
        try:
            msg = ""
            for token in sorted(self._supervisor.capability_tokens()):
                cap = self._supervisor.capability_for(token)
                # label = cap.get_label()
                # logging.debug("\n>>> cap = " + str(cap))
                
                found = False
                keep = True
                keep = match_filters( self, cap, _flist )

                # paramfilter = self.get_argument("label", default=None)
                    
                if keep:
                    id = mplane.client.BaseClient.identity_for(self._supervisor, token_or_label=token, receipt=False)
                    id = id + "," + token
                    if found == False:
                        msg = msg + "\"" + id + "\":["
                        found = True
                    msg = msg + mplane.model.unparse_json(cap) + ","
                else:
                    logging.debug("        SKIPPED")
                    
                if found == True:
                    msg = msg[:-1].replace("\n","") + "],"
            
            msg = "{" + msg[:-1].replace("\n","") + "}"
            logging.debug("\n>>> (filtered) capabilities: msg = \n" + msg)
            self._respond_json_text(200, msg)
            
        except Exception as e:
            self.write( "{ERROR:\"" + str(e) + "\"}" )

    def post(self):
        self.set_status(405, GUI_LISTCAPABILITIES_PATH + " is a read-only GET function")

 
class ListResultsHandler(mplane.client.MPlaneHandler):
# class ListResultsHandler(tornado.web.RequestHandler):
    """
    Lists the results from Supervisor.
    
    GET: lists results from the supervisor in a JSON array, format is as follows:
      [ { result:'measure', label:'CAPABILITY_LABEL',  when:'WHEN_OF_RESULT', token:'TOKEN_OF_RESULT',
          parameters: { specificationParam1:"value1", specificationParam2:"value2", ... }, ... ]
      Filtering can be done by GET parameters called label, and names of parameters of the capability.

    POST: not supported
    """
    def initialize(self, supervisor, tlsState):
        # logging.debug(">>> sv_gui_handlers.py:ListResultsHandler.initialize():")
        self._supervisor = supervisor
        self._tls = tlsState
        self.dn = get_dn(self._supervisor, self.request)
        _flist = {}
        # logging.debug(">>> ListResultsHandler.initialize:\n" + str(self._supervisor._results))

    def get(self):
        if self.get_secure_cookie("user") is None:
            self.redirect("/gui/static/login.html")
            return

        _flist = filterlist(self, reguri=self._supervisor._reguri)
        # logging.debug("_flist = " + str( _flist ))
        try:
            msg = ""
            for token in self._supervisor._results:
                res = self._supervisor._results[token]
                # logging.debug("res (in json) = " + mplane.model.unparse_json(res))
                dnMsg = ""
                found = False
                keep = True
                keep = match_filters( self, res, _flist )

                if keep:
                    id = self.dn + "," + token
                    if found == False:
                        dnMsg = dnMsg + "\"" + id + "\":["
                        found = True
                        
                    paramStr = ""
                    for paramname in res.parameter_names():
                        paramStr = paramStr + "'" + paramname + "': '" + str(res.get_parameter_value(paramname)) + "',"
                    dnMsg = dnMsg + "{ result:'measure', label:'" + res.get_label() + "',  when:'" + str(res.when()) + "', token:'" + res.get_token() + "', parameters: {" + paramStr[:-1] + "} },"
                else:
                    logging.debug("        SKIPPED")

                if found == True:
                    msg = msg + dnMsg[:-1] + "],"
            
            msg = "{" + msg[:-1].replace("\n","") + "}"
            
            logging.debug("\n-------------------------------\nresults msg = \n" + msg)
            self._respond_json_text(200,msg)
            
        except Exception as e:
            self.write( "{ERROR:\"" + str(e) + "\"}" )

    def post(self):
        logging.debug(">>> sv_gui_handlers.py:ListResultsHandler.get():")
        self.set_status(405, GUI_LISTCAPABILITIES_PATH + " is a read-only GET function")


class ListPendingsHandler(mplane.client.MPlaneHandler):
    """
    Lists all the pending measurement (specifications and receipts) from supervisor.
    
    GET compose mplane json representations of pending specifications and receipts, in the following format:
        { DN1: [ receipt1, receipt2 ], DN2: [ specification1, receipt3, ... ], ... }
    
    POST is not supported.
    """
    def initialize(self, supervisor, tlsState):
        logging.debug("\n>>> sv_gui_handlers.py:ListPendingsHandler.initialize():")
        self._supervisor = supervisor
        self._tls = tlsState
        _flist = {}
        # self.dn = get_dn(self._supervisor, self.request)
        # logging.debug(">>> ListPendingsHandler.initialize:\n" + str(self._supervisor._specifications))

    def get(self):
        if self.get_secure_cookie("user") is None:
            self.redirect("/gui/static/login.html")
            return

        _flist = filterlist(self, reguri=self._supervisor._reguri)
        # logging.debug("_flist = " + str( _flist ))
        try:
            msg = ""
            for token in self._supervisor.receipt_tokens():
                rec = self._supervisor._receipts[token]
                # # logging.debug("rec (in json) = " + mplane.model.unparse_json(rec))
                dnMsg = ""
                found = False
                keep = True
                keep = match_filters( self, rec, _flist )

                if keep:
                    id = mplane.client.BaseClient.identity_for(self._supervisor, token_or_label=token, receipt=True)
                    id = id + "," + token
                    if found == False:
                        dnMsg = dnMsg + "\"" + id + "\":["
                        found = True
                        
                    paramStr = ""
                    for paramname in rec.parameter_names():
                        paramStr = paramStr + "'" + paramname + "': '" + str(rec.get_parameter_value(paramname)) + "',"
                    dnMsg = dnMsg + "{ receipt:'measure', label:'" + rec.get_label() + "',  when:'" + str(rec.when()) + "', token:'" + rec.get_token() + "', parameters: {" + paramStr[:-1] + "} },"
                else:
                    logging.debug("        SKIPPED")

                if found == True:
                    msg = msg + dnMsg[:-1] + "],"
            
            msg = "{" + msg[:-1].replace("\n","") + "}"
            self._respond_json_text(200,msg)
            
        except Exception as e:
            self.write( "{ERROR:\"" + str(e) + "\"}" )

    def post(self):
        self.set_status(405, GUI_LISTCAPABILITIES_PATH + " is a read-only GET function")


class GetResultHandler(mplane.client.MPlaneHandler):
    """
    GET: Get result for specified token.
    
    POST: Get results for a filter like a specification.
        Posted JSON is like
            { capability:ping-detail-ip4, parameters:{"source.ip4":"192.168.96.1", "destination.ip4":"217.20.130.99" },
            "resultName":"delay.twoway.icmp.us", from: 1421539200000, to: 1421625600000 }

            - timestamps are in ms
            - capability is the label of the capability
            - no component DN is defined, results of different components can be merged
            - resultName: only one result column is required -> one line will be drawn from the response.
          
        The response is like as follows:

        { "result":"measure", "version":0, "registry": "http://ict-mplane.eu/registry/core", "label": ping-detail-ip4, "when": "2015-01-18 17:25:50.785761 ... 2015-01-18 17:28:00.785367",
            "parameters":{"source.ip4":"192.168.96.1", "destination.ip4":"217.20.130.99" }, "results": ["time", "delay.twoway.icmp.us"],
            "resultvalues": [["2015-01-18 17:25:50.785761", 20], ["2015-01-18 17:25:51.785761", 37], ["2015-01-18 17:28:00.785761", 31], ...] }

            - when: shows times between results are found
            - resultvalues: it has always 2 columns, first is time, second is requested by client in  "resultName"
    """
    def initialize(self, supervisor, tlsState):
        logging.debug("\n>>> sv_gui_handlers.py:GetResultHandler.initialize():")  
        self._supervisor = supervisor
        self._tls = tlsState
        self.dn = get_dn(self._supervisor, self.request)
        # logging.debug(">>> GetResultsHandler.initialize:\n" + str(self._supervisor._results))

    def get(self):
        if self.get_secure_cookie("user") is None:
            self.redirect("/gui/static/login.html")
            return
            
        try:
            token = self.get_argument("token")
            logging.debug(">>> GetResultsHandler token = " + token)
            for dn in self._supervisor._results.keys():
                # for res in self._supervisor._results[dn]:
                res = self._supervisor._results[dn]
                if res.get_token() == token:
                    self._respond_json_text(200, mplane.model.unparse_json(res) )
                    return
            
            self.write("{ERROR: \"result for token " + token + " is not found\"}")
        
        except Exception as e:
            self.write( "{ERROR:\"" + str(e) + "\"}" )

    def post(self):
        queryJson = json.loads( self.request.body.decode("utf-8") )
        fromTS = datetime.datetime.fromtimestamp( queryJson["from"] / 1000 )
        toTS = datetime.datetime.fromtimestamp( queryJson["to"] / 1000 )        
        logging.debug( 'query time: ' + str(fromTS) + " - " + str(toTS))
        
        selectedResults = []
        for dn in self._supervisor._results.keys():
            for res in self._supervisor._results[dn]:
                skip = res.get_label() != queryJson["capability"]
                for paramname in res.parameter_names():
                    if str(res.get_parameter_value(paramname)) != queryJson["parameters"][paramname]:
                        skip = True
                (resstart,resend) = res.when().datetimes()
                logging.debug( '   result time: ' + str(resstart) + " - " + str(resend) + ": " + str(resend < fromTS or resstart > toTS))

                skip = skip or resend < fromTS or resstart > toTS
                if not skip:
                    selectedResults.append(res)
        
        if len(selectedResults) == 0:
            self.write("{ERROR:\"No result was found\"}");
            self.finish()
            return;
        
        resultvalues = []
        response = { "result":"measure", "version":0, "registry": "http://ict-mplane.eu/registry/core", 
            "label": queryJson["capability"], "when": str(mplane.model.When(a=fromTS, b=toTS)), "parameters": queryJson["parameters"],
            "results": ["time", queryJson["result"]], "resultvalues": resultvalues }
                
        for res in selectedResults:
            resultvalues.extend( res._result_rows() )

        sorted( resultvalues, key=lambda resultrow: resultrow[0] )

        self.write( json.dumps(response) )
        self.finish()

        
class RunCapabilityHandler(mplane.client.MPlaneHandler):
    """
      It runs a capability.    
      
      POST: URI should be gui/run/capability?DN=Probe.Distinguished.Name 
      Posted data is a fulfilled capability, not a specification. Fulfilled means field when has a concrete value, and every parameter has a value as well.
    """

    def initialize(self, supervisor, tlsState):
        # logging.debug("\n>>> sv_gui_handlers.py:RunCapabilityHandler.initialize():")
        self._supervisor = supervisor
        self._tls = tlsState

    def get(self):
        self.set_status(405, GUI_LISTCAPABILITIES_PATH + " supports POST only")
        self.finish();

    def post(self):
        try:
            dn = self.get_query_argument("DN", strip=True)
            # token = self.get_query_argument("token")
            posted = self.request.body.decode("utf-8")
            
            filledCapability = mplane.model.parse_json( posted )           
            spec = mplane.model.Specification( capability=filledCapability )
            # logging.debug(">>> spec (1) = " + str(spec))
            cap_label = spec.get_label()
            if cap_label:
                cap = mplane.client.BaseClient.capability_for(self._supervisor,cap_label)
            else:
                raise KeyError("no such token or label "+cap_label)
            # logging.debug(">>> RunCapabilityHandler DN = " + dn + ", cap_label = " + cap_label)
            # Capability posted by GUI contains parameter values as constraints allowing single value only
            for paramname in spec.parameter_names():
                spec._params[paramname].set_single_value()
            spec.validate()
            specjson = mplane.model.unparse_json(spec)
            logging.debug(">>> spec (2) = " + str(spec))
            logging.debug(">>> specjson = " + specjson)
            logging.debug(">>> spec._when =" + str(spec._when))
            mplane.svgui.ClientGui.invoke_capability(self._supervisor, cap_label, spec._when, spec.parameter_values())
            self.write("{}")
            self.finish()

        except Exception as e:
            self.write( "{ERROR:\"" + str(e) + "\"}" )

