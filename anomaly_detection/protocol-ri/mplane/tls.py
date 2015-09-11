#
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
##
# mPlane Protocol Reference Implementation
# TLS context for mPlane clients and components
#
# (c) 2014-2015 mPlane Consortium (http://www.ict-mplane.eu)
#     Author: Stefano Pentassuglia <stefano.pentassuglia@ssbprogetti.it>
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


# ## Common TLS Configuration

# Clients and components should be able to load a configuration file
# (`tls.conf`) which refers to CA, private key, and certificate files,
# for setting up a TLS context. This TLS context should be common to
# all other code (`mplane/tls.py`). When the TLS configuration file
# is not present, `https://` URLs will not be supported; when present,
# the use of TLS will be selected based on the URL used.

# - SSB will pull this out of existing utils.py and stepenta/RI code.

import urllib3
import ssl
import functools
import tornado.httpserver
from socket import socket
import mplane.utils

DUMMY_DN = "Identity.Unauthenticated.Default"

class TlsState:

    def __init__(self, config, forged_identity=None):
        if "TLS" not in config:
            self._cafile = None
            self._certfile = None
            self._keyfile = None
        else:
            # get paths to CA, cert, and key
            self._cafile = mplane.utils.search_path(config["TLS"]["ca-chain"])
            self._certfile = mplane.utils.search_path(config["TLS"]["cert"])
            self._keyfile = mplane.utils.search_path(config["TLS"]["key"])

        # load cert and get DN
        self._identity = self.extract_local_identity(forged_identity)

    @functools.lru_cache()
    def pool_for(self, scheme, host, port):
        """
        Given a URL (from which a scheme and host can be extracted),
        return a connection pool (potentially with TLS state)
        which can be used to connect to the URL.
        """

        if scheme is None:
            if self._keyfile:
                return urllib3.HTTPSConnectionPool(host, port,
                                                    key_file=self._keyfile,
                                                    cert_file=self._certfile,
                                                    ca_certs=self._cafile)
            else:
                return urllib3.HTTPConnectionPool(host, port)
        elif scheme == "http":
            return urllib3.HTTPConnectionPool(host, port)
        elif scheme == "https":
            if self._keyfile:
                return urllib3.HTTPSConnectionPool(host, port,
                                                    key_file=self._keyfile,
                                                    cert_file=self._certfile,
                                                    ca_certs=self._cafile)
            else:
                raise ValueError("SSL requested without providing certificate")
                exit(1)
        elif scheme == "file":
            # FIXME what to do here?
            raise ValueError("Unsupported scheme "+scheme)
        else:
            raise ValueError("Unsupported scheme "+scheme)

    def forged_identity(self):
        if not self._keyfile:
            return self._identity
        else:
            return None

    def get_ssl_options(self):
        """
        Get an ssl_options dictionary for this TLS context suitable
        for passing to tornado.httpserver.HTTPServer().
        """
        if self._keyfile:
            return dict(certfile=self._certfile,
                         keyfile=self._keyfile,
                        ca_certs=self._cafile,
                       cert_reqs=ssl.CERT_REQUIRED)
        else:
            return None



    def extract_local_identity(self, forged_identity = None):
        """
        Extract an identity from the designated name in an X.509 certificate
        file with an ASCII preamble (as used in mPlane)
        """
        if self._keyfile:
            identity = ""
            with open(self._certfile) as f:
                for line in f.readlines():
                    line = line.rstrip().replace(" ", "")
                    if line.startswith("Subject:"):
                        fields = line[len("Subject:"):].split(",")
                        for field in fields:
                            if identity == "":
                                identity = identity + field.split('=')[1]
                            else:
                               identity = identity + "." + field.split('=')[1]
        else:
            if forged_identity is None:
                identity = DUMMY_DN
            else:
                identity = forged_identity
        return identity

    def extract_peer_identity(self, url_or_req):
        """
        Extract an identity from a Tornado's
        HTTPRequest, or from a Urllib3's Url
        """
        
        print("In extract peer identity")
        if self._keyfile:
            print("have keyfile")
            if isinstance(url_or_req,  urllib3.util.Url):
                # extract DN from the certificate retrieved from the url.
                # Unfortunately, there seems to be no way to do this using urllib3,
                # thus ssl library is being used
                print("Is Url create socket")
                s = socket()
                c = ssl.wrap_socket(s,cert_reqs=ssl.CERT_REQUIRED,
                                    keyfile=self._keyfile,
                                    certfile=self._certfile,
                                    ca_certs=self._cafile)
                c.connect((url_or_req.host, url_or_req.port))
                cert = c.getpeercert()
                c.close()
            elif isinstance(url_or_req, tornado.httpserver.HTTPRequest):
                print("Tornado request")
                cert = url_or_req.get_ssl_certificate()
            else:
                print("Error not url")
                #raise ValueError("Passed argument is not a urllib3.util.url.Url or tornado.httpserver.HTTPRequest")

            identity = ""
            for elem in cert.get('subject'):
                if identity == "":
                    identity = identity + str(elem[0][1])
                else:
                    identity = identity + "." + str(elem[0][1])
        else:
            identity = DUMMY_DN
        
        print("Identity: "+ str(identity))
        #identity="127.0.0.1"
        return identity
