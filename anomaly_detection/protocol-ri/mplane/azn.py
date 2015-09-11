#
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
##
# mPlane Protocol Reference Implementation
# Authorization context for mPlane components
#
# (c) 2014-2015 mPlane Consortium (http://www.ict-mplane.eu)
#     Author: Stefano Pentassuglia <stefano.pentassuglia@ssbprogetti.it>
#
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

# Factory function to create Authorization ON or OFF object
def Authorization(config=None):
    if config is None:
        return AuthorizationOff()
    else:
        if "TLS" not in config.sections():
            return AuthorizationOff()
        else:
            return AuthorizationOn(config)
        
class AuthorizationOff(object):
        
    def check(self, cap, identity):
        return True

always_authorized = AuthorizationOff()

class AuthorizationOn(object):
    
    def __init__(self, config):
        self.id_role = self._load_roles(config["Roles"])
        self.cap_role = self._load_roles(config["Authorizations"])

    def _load_roles(self, config_obj):
        """ Loads user-role-capability associations and keeps them in cache """
        r = {}
        for elem in config_obj:
            roles = set(config_obj[elem].split(','))
            r[elem] = roles
        return r
            
    def check(self, cap, identity): 
        """
        Return true if the given identiy is authorized to use the given
        capability by this set of authorization rules, false otherwise.

        """
        # Remove the suffix serial number from the specification label
        # in order to make controls on the original label
        cap_label = None
        for label in self.cap_role:
            if label in cap._label:
                cap_label = label

        if ((cap_label in self.cap_role) and (identity in self.id_role)): # Deny unless explicitly allowed in .conf files
            intersection = self.cap_role[cap_label] & self.id_role[identity]
            if len(intersection) > 0:
                return True
        return False
