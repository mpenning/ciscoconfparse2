r""" models_asa.py - Parse, Query, Build, and Modify IOS-style configurations

     Copyright (C) 2023      David Michael Pennington

     This program is free software: you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation, either version 3 of the License, or
     (at your option) any later version.

     This program is distributed in the hope that it will be useful,
     but WITHOUT ANY WARRANTY; without even the implied warranty of
     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
     GNU General Public License for more details.

     You should have received a copy of the GNU General Public License
     along with this program.  If not, see <http://www.gnu.org/licenses/>.

     If you need to contact the author, you can do so by emailing:
     mike [~at~] pennington [/dot\] net
"""

### HUGE UGLY WARNING:
###   Anything in models_asa.py could change at any time, until I remove this
###   warning.  I have good reason to believe that these methods
###   function correctly, but I've been wrong before.  There are no unit tests
###   for this functionality yet, so I consider all this code alpha quality.
###
###   Use models_asa.py at your own risk.  You have been warned :-)

from typing import Any, Union
import ipaddress
import re

from loguru import logger
import attrs

from ciscoconfparse2.protocol_values import ASA_IP_PROTOCOLS
from ciscoconfparse2.ccp_util import L4Object
from ciscoconfparse2.ccp_util import IPv4Obj, IPv6Obj

from ciscoconfparse2.ccp_abc import BaseCfgLine

from ciscoconfparse2.errors import InvalidParameters

##
##-------------  ASA Configuration line object
##


@attrs.define(repr=False, slots=False)
class ASACfgLine(BaseCfgLine):
    """An object for a parsed ASA-style configuration line.
    :class:`~models_asa.ASACfgLine` objects contain references to other
    parent and child :class:`~models_asa.ASACfgLine` objects.

    Args:
        - line (str): A string containing a text copy of the ASA configuration line.  :class:`~ciscoconfparse2.CiscoConfParse` will automatically identify the parent and children (if any) when it parses the configuration.

    Attributes:
        - text     (str): A string containing the parsed ASA configuration statement
        - linenum  (int): The line number of this configuration statement in the original config; default is -1 when first initialized.
        - parent (:class:`~models_asa.ASACfgLine()`): The parent of this object; defaults to ``self``.
        - children (list): A list of ``ASACfgLine()`` objects which are children of this object.
        - child_indent (int): An integer with the indentation of this object's children
        - indent (int): An integer with the indentation of this object's ``text``
        - oldest_ancestor (bool): A boolean indicating whether this is the oldest ancestor in a family
        - is_comment (bool): A boolean indicating whether this is a comment

    Returns:
        - an instance of :class:`~models_asa.ASACfgLine`.

    """
    _mm_results: Any = None

    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        """Accept an ASA line number and initialize family relationship
        attributes"""
        super(ASACfgLine, self).__init__(*args, **kwargs)

        #self.text = kwargs.get("line", None)
        self._mm_results = None

    @logger.catch(reraise=True)
    def __eq__(self, other):
        if other is None:
            return False
        return self.get_unique_identifier() == other.get_unique_identifier()

    @logger.catch(reraise=True)
    def __ne__(self, other):
        if other is None:
            return True
        return self.get_unique_identifier() != other.get_unique_identifier()

    @logger.catch(reraise=True)
    def __hash__(self):
        return self.get_unique_identifier()



    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, index=None, re=re):
        ## Default object, for now
        return True

    @property
    @logger.catch(reraise=True)
    def is_intf(self):
        # Includes subinterfaces
        intf_regex = r"^interface\s+(\S+.+)"
        if self.re_match(intf_regex):
            return True
        return False

    @property
    @logger.catch(reraise=True)
    def is_subintf(self):
        intf_regex = r"^interface\s+(\S+?\.\d+)"
        if self.re_match(intf_regex):
            return True
        return False

    @property
    @logger.catch(reraise=True)
    def is_virtual_intf(self):
        intf_regex = r"^interface\s+(Loopback|Tunnel|Virtual-Template|Port-Channel)"
        if self.re_match(intf_regex):
            return True
        return False

    @property
    @logger.catch(reraise=True)
    def is_loopback_intf(self):
        intf_regex = r"^interface\s+(\Soopback)"
        if self.re_match(intf_regex):
            return True
        return False

    @property
    @logger.catch(reraise=True)
    def is_ethernet_intf(self):
        intf_regex = r"^interface\s+(.*?\Sthernet)"
        if self.re_match(intf_regex):
            return True
        return False


##
##-------------  ASA Interface ABC
##

# Valid method name substitutions:
#    switchport -> switch
#    spanningtree -> stp
#    interfce -> intf
#    address -> addr
#    default -> def


class BaseASAIntfLine(ASACfgLine):
    default_ipv4_addr_object = IPv4Obj()
    default_ipv6_addr_object = IPv6Obj()

    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super(BaseASAIntfLine, self).__init__(*args, **kwargs)
        self.ifindex = None  # Optional, for user use
        self.default_ipv4_addr_object = IPv4Obj()

    @logger.catch(reraise=True)
    def __eq__(self, other):
        return self.get_unique_identifier() == other.get_unique_identifier()

    @logger.catch(reraise=True)
    def __ne__(self, other):
        return self.get_unique_identifier() != other.get_unique_identifier()

    @logger.catch(reraise=True)
    def __hash__(self):
        return self.get_unique_identifier()



    @logger.catch(reraise=True)
    def __repr__(self):
        if not self.is_switchport:
            if self.ipv4_addr_object == self.default_ipv4_addr_object:
                addr = "No IPv4"
            else:
                addr = self.ipv4_addr_object
            return f"<{self.classname} # {self.linenum} '{self.text.strip()}' info: '{addr}'>"
        else:
            return f"<{self.classname} # {self.linenum} '{self.text.strip()}' info: 'switchport'>"

    @property
    @logger.catch(reraise=True)
    def verbose(self):
        if not self.is_switchport:
            return (
                "<%s # %s '%s' info: '%s' (child_indent: %s / len(children): %s / family_endpoint: %s)>"
                % (
                    self.classname,
                    self.linenum,
                    self.text,
                    self.ipv4_addr_object or "No IPv4",
                    self.child_indent,
                    len(self.children),
                    self.family_endpoint,
                )
            )
        else:
            return (
                "<%s # %s '%s' info: 'switchport' (child_indent: %s / len(children): %s / family_endpoint: %s)>"
                % (
                    self.classname,
                    self.linenum,
                    self.text,
                    self.child_indent,
                    len(self.children),
                    self.family_endpoint,
                )
            )

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, index=None, re=re):
        return False

    ##-------------  Basic interface properties

    @property
    @logger.catch(reraise=True)
    def name(self):
        """Return a string, such as 'GigabitEthernet0/1'"""
        if not self.is_intf:
            return ""
        return " ".join(self.text.split()[1:])

    @property
    @logger.catch(reraise=True)
    def port(self):
        """Return the interface's port number"""
        return self.ordinal_list[-1]

    @property
    @logger.catch(reraise=True)
    def port_type(self):
        """Return Loopback, GigabitEthernet, etc..."""
        port_type_regex = r"^interface\s+([A-Za-z\-]+)"
        return self.re_match(port_type_regex, group=1, default="")

    @property
    @logger.catch(reraise=True)
    def ordinal_list(self):
        """Return a list of numbers representing card, slot, port for this interface.  If you call ordinal_list on GigabitEthernet2/25.100, you'll get this python list of integers: [2, 25].  If you call ordinal_list on GigabitEthernet2/0/25.100 you'll get this python list of integers: [2, 0, 25].  This method strips all subinterface information in the returned value.

        ..warning:: ordinal_list should silently fail (returning an empty python list) if the interface doesn't parse correctly"""
        if not self.is_intf:
            return []
        else:
            intf_regex = r"^interface\s+[A-Za-z\-]+\s*(\d+.*?)(\.\d+)*(\s\S+)*\s*$"
            intf_number = self.re_match(intf_regex, group=1, default="")
            if intf_number:
                return [int(ii) for ii in intf_number.split("/")]
            else:
                return []

    @property
    @logger.catch(reraise=True)
    def description(self):
        retval = self.re_match_iter_typed(
            r"^\s*description\s+(\S.+)$", result_type=str, default=""
        )
        return retval

    @property
    @logger.catch(reraise=True)
    def manual_delay(self):
        retval = self.re_match_iter_typed(
            r"^\s*delay\s+(\d+)$", result_type=int, default=0
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_ipv4(self):
        r"""Return an ccp_util.IPv4Obj object representing the subnet on this interface; if there is no address, return ccp_util.IPv4Obj()"""
        return self.ipv4_addr_object != IPv4Obj()

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ip(self):
        r"""Return an ccp_util.IPv4Obj object representing the IPv4 address on this interface; if there is no address, return ccp_util.IPv4Obj()"""
        return self.ipv4_addr_object

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv4(self):
        r"""Return an ccp_util.IPv4Obj object representing the IPv4 address on this interface; if there is no address, return ccp_util.IPv4Obj()"""
        return self.ipv4_addr_object

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_addr_object(self):
        """Return a ccp_util.IPv4Obj object representing the address on this interface; if there is no address, return IPv4Obj()"""
        try:
            return IPv4Obj("{}/{}".format(self.ipv4_addr, self.ipv4_netmask))
        except BaseException:
            return self.default_ipv4_addr_object

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv6_addr_object(self):
        r"""Return a ccp_util.IPv6Obj object representing the address on this interface; if there is no address, return IPv6Obj()"""

        retval = self.re_match_iter_typed(
            r"^\s+ipv6\s+address\s+(?P<v6addr>\S+?)\/(?P<v6masklength>\d+)",
            groupdict={"v6addr": str, "v6masklength": str},
            default="",
        )

        if retval["v6addr"] == "":
            return self.default_ipv6_addr_object
        elif retval["v6addr"] == "dhcp":
            return self.default_ipv6_addr_object
        elif retval["v6addr"] == "negotiated":
            return self.default_ipv6_addr_object
        else:
            return IPv6Obj(f"{retval['v6addr']}/{retval['v6masklength']}")

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_standby_addr_object(self):
        """Return a ccp_util.IPv4Obj object representing the standby address on this interface; if there is no address, return IPv4Obj()"""
        try:
            return IPv4Obj("{}/{}".format(self.ipv4_standby_addr, self.ipv4_netmask))
        except Exception:
            return self.default_ipv4_addr_object

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_network_object(self):
        """Return an ccp_util.IPv4Obj object representing the subnet on this interface; if there is no address, return ccp_util.IPv4Obj()"""
        return self.ip_network_object

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ip_network_object(self):
        try:
            return IPv4Obj(
                "{}/{}".format(self.ipv4_addr, self.ipv4_netmask), strict=False
            ).network
        except AttributeError:
            err_text = f"{self.ipv4_addr}/{self.ipv4_netmask} does not have a .network attribute."
            raise AttributeError(err_text)
        except BaseException:
            err_text = f"{self.ipv4_addr}/{self.ipv4_netmask} does not seem to have a valid network address."
            raise ValueError(err_text)

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv6_addr(self):
        if self.ipv6_addr_object.empty is False:
            return str(self.ipv6_addr_object.ip)
        return ""

    @property
    @logger.catch(reraise=True)
    def ipv6_standby_addr(self):
        for cobj in self.children:
            cmd_parts = cobj.text.split()
            if len(cmd_parts) == 5:
                if cmd_parts[0:2] == ["ipv6", "address"] and cmd_parts[3] == "standby":
                    return cmd_parts[4]
        return ""

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv6_masklength(self):
        if self.ipv6_addr_object.empty is False:
            return int(self.ipv6_addr_object.masklength)
        return 0

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_autonegotiation(self):
        if not self.is_ethernet_intf:
            return False
        elif self.is_ethernet_intf and (
            self.has_manual_speed or self.has_manual_duplex
        ):
            return False
        elif self.is_ethernet_intf:
            return True
        else:
            raise ValueError

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_speed(self):
        retval = self.re_match_iter_typed(
            r"^\s*speed\s+(\d+)$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_duplex(self):
        retval = self.re_match_iter_typed(
            r"^\s*duplex\s+(\S.+)$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def is_shutdown(self):
        retval = self.re_match_iter_typed(
            r"^\s*(shut\S*)\s*$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ip_addr(self):
        return self.ipv4_addr

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_addr(self):
        """Return a string with the interface's IPv4 address, or '' if there is none"""
        retval = self.re_match_iter_typed(
            r"^\s+ip\s+address\s+(\d+\.\d+\.\d+\.\d+)",
            result_type=str,
            default="",
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_standby_addr(self):
        """Return a string with the interface's IPv4 address, or '' if there is none"""
        retval = self.re_match_iter_typed(
            r"^\s+ip\s+address\s+\d+\.\d+\.\d+\.\d+\s+\d+\.\d+\.\d+\.\d+\sstandby\s+(\S+)\s*$",
            result_type=str,
            default="",
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_netmask(self):
        """Return a string with the interface's IPv4 netmask, or '' if there is none"""
        retval = self.re_match_iter_typed(
            r"^\s+ip\s+address\s+\d+\.\d+\.\d+\.\d+\s+(\d+\.\d+\.\d+\.\d+)",
            result_type=str,
            default="",
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_masklength(self):
        """Return an integer with the interface's IPv4 mask length, or 0 if there is no IP address on the interace"""
        ipv4_addr_object = self.ipv4_addr_object
        if ipv4_addr_object != self.default_ipv4_addr_object:
            return ipv4_addr_object.prefixlen
        return 0

    # This method is on BaseIOSIntfLine()
    @logger.catch(reraise=True)
    def in_ipv4_subnet(self, ipv4network=IPv4Obj("0.0.0.0/32", strict=False)):
        """Accept two string arguments for network and netmask, and return a boolean for whether this interface is within the requested subnet.  Return None if there is no address on the interface"""
        if self.ipv4_addr_object.empty is False:
            try:
                # Return a boolean for whether the interface is in that network and mask
                return self.ipv4_addr_object in ipv4network
            except BaseException:
                raise ValueError(
                    "FATAL: %s.in_ipv4_subnet(ipv4network={}) is an invalid arg".format(
                        ipv4network
                    )
                )
        else:
            return None

    # This method is on BaseIOSIntfLine()
    @logger.catch(reraise=True)
    def in_ipv4_subnets(self, subnets=None):
        """Accept a set or list of ccp_util.IPv4Obj objects, and return a boolean for whether this interface is within the requested subnets."""
        if subnets is None:
            raise ValueError(
                "A python list or set of ccp_util.IPv4Obj objects must be supplied"
            )
        for subnet in subnets:
            tmp = self.in_ipv4_subnet(ipv4network=subnet)
            if self.ipv4_addr_object in subnet:
                return tmp
        return tmp

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_ip_pim_sparse_mode(self):
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## Interface must have an IP addr to run PIM
        if self.ipv4_addr == "":
            return False

        retval = self.re_match_iter_typed(
            r"^\s*ip\spim\ssparse-mode\s*$)\s*$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def is_switchport(self):
        retval = self.re_match_iter_typed(
            r"^\s*(switchport)\s*", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_switch_access(self):
        retval = self.re_match_iter_typed(
            r"^\s*(switchport\smode\s+access)\s*$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_switch_trunk_encap(self):
        return bool(self.manual_switch_trunk_encap)

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_switch_trunk(self):
        retval = self.re_match_iter_typed(
            r"^\s*(switchport\s+mode\s+trunk)\s*$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def access_vlan(self):
        """Return an integer with the access vlan number.  Return 0, if the port has no explicit vlan configured."""
        retval = self.re_match_iter_typed(
            r"^\s*switchport\s+access\s+vlan\s+(\d+)$", result_type=int, default=0
        )
        return retval


##
##-------------  ASA name
##

_RE_NAMEOBJECT_STR = r"^name\s+(?P<addr>\d+\.\d+\.\d+\.\d+)\s(?P<name>\S+)"
_RE_NAMEOBJECT = re.compile(_RE_NAMEOBJECT_STR, re.VERBOSE)


@attrs.define(repr=False, slots=False)
class ASAName(ASACfgLine):
    name: str = None
    addr: str = None

    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        """Accept an ASA line number and initialize family relationship
        attributes"""
        super(ASAName, self).__init__(*args, **kwargs)
        mm = _RE_NAMEOBJECT.search(self.text)
        if (mm is not None):
            self._mm_results = mm.groupdict()  # All regex match results
        else:
            raise ValueError

        self.name = self._mm_results["name"]
        self.addr = self._mm_results["addr"]


    @logger.catch(reraise=True)
    def __eq__(self, other):
        return self.get_unique_identifier() == other.get_unique_identifier()

    @logger.catch(reraise=True)
    def __ne__(self, other):
        return self.get_unique_identifier() != other.get_unique_identifier()

    @logger.catch(reraise=True)
    def __hash__(self):
        return self.get_unique_identifier()


    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, index=None, re=re):
        if "name " in line[0:5].lower():
            return True
        return False

    @property
    @logger.catch(reraise=True)
    def result_dict(self):
        retval = dict()

        retval["name"] = self._mm_results["name"]
        retval["addr"] = self._mm_results["addr"]

        return retval


##
##-------------  ASA object network
##


@attrs.define(repr=False, slots=False)
class ASAObjNetwork(ASACfgLine):
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        """Accept an ASA line number and initialize family relationship
        attributes"""
        super(ASAObjNetwork, self).__init__(*args, **kwargs)


    @logger.catch(reraise=True)
    def __eq__(self, other):
        return self.get_unique_identifier() == other.get_unique_identifier()

    @logger.catch(reraise=True)
    def __ne__(self, other):
        return self.get_unique_identifier() != other.get_unique_identifier()

    @logger.catch(reraise=True)
    def __hash__(self):
        return self.get_unique_identifier()


    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, index=None, re=re):
        if "object network " in line[0:15].lower():
            return True
        return False


##
##-------------  ASA object service
##


@attrs.define(repr=False, slots=False)
class ASAObjService(ASACfgLine):
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        """Accept an ASA line number and initialize family relationship
        attributes"""
        super(ASAObjService, self).__init__(*args, **kwargs)


    @logger.catch(reraise=True)
    def __eq__(self, other):
        return self.get_unique_identifier() == other.get_unique_identifier()

    @logger.catch(reraise=True)
    def __ne__(self, other):
        return self.get_unique_identifier() != other.get_unique_identifier()

    @logger.catch(reraise=True)
    def __hash__(self):
        return self.get_unique_identifier()


    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, index=None, re=re):
        if "object service " in line[0:15].lower():
            return True
        return False


##
##-------------  ASA object-group network
##
_RE_NETOBJECT_STR = r"""(?:                         # Non-capturing parenthesis
 (^\s*network-object\s+host\s+(?P<host>\S+))
|(^\s*network-object\s+(?P<network>\S+)\s+(?P<netmask>\d+\.\d+\.\d+\.\d+))
|(^\s*group-object\s+(?P<groupobject>\S+))
)                                                   # Close non-capture parens
"""
_RE_NETOBJECT = re.compile(_RE_NETOBJECT_STR, re.VERBOSE)


@attrs.define(repr=False, slots=False)
class ASAObjGroupNetwork(ASACfgLine):
    name: str = None

    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        """Accept an ASA line number and initialize family relationship
        attributes"""
        super(ASAObjGroupNetwork, self).__init__(*args, **kwargs)

        self.name = self.re_match_typed(
            r"^object-group\s+network\s+(\S+)", group=1, result_type=str
        )


    @logger.catch(reraise=True)
    def __eq__(self, other):
        return self.get_unique_identifier() == other.get_unique_identifier()

    @logger.catch(reraise=True)
    def __ne__(self, other):
        return self.get_unique_identifier() != other.get_unique_identifier()

    @logger.catch(reraise=True)
    def __hash__(self):
        return self.get_unique_identifier()


    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, index=None, re=re):
        if "object-group network " in line[0:21].lower():
            return True
        return False

    @property
    @logger.catch(reraise=True)
    def hash_children(self):
        ## Manually override the BaseCfgLine method since this recurses through
        ##    children
        ## FIXME: Implement hash_children for ASAObjGroupService
        return hash(tuple(self.network_strings))  # network_strings recurses...

    @property
    @logger.catch(reraise=True)
    def network_count(self):
        ## Return the number of discrete network objects covered by this group
        ## FIXME: Implement port_count for ASAObjGroupService
        return len(self.network_strings)

    @property
    @logger.catch(reraise=True)
    def network_strings(self):
        """Return a list of strings which represent the address space allowed by
        this object-group"""
        retval = list()
        names = self.confobj.asa_object_group_names
        for obj in self.children:

            ## Parse out 'object-group ...' and 'group-object' lines...
            mm = _RE_NETOBJECT.search(obj.text)
            if (mm is not None):
                net_obj = mm.groupdict()
                if net_obj["netmask"] == "255.255.255.255":
                    net_obj["host"] = net_obj["network"]
            else:
                net_obj = dict()

            if net_obj.get("host", None):
                retval.append(names.get(net_obj["host"], net_obj["host"]))
            elif net_obj.get("network", None):
                ## This is a non-host network object
                retval.append(
                    "{}/{}".format(
                        names.get(net_obj["network"], net_obj["network"]),
                        net_obj["netmask"],
                    )
                )
            elif net_obj.get("groupobject", None):
                groupobject = net_obj["groupobject"]
                if groupobject == self.name:
                    ## Throw an error when importing self
                    raise ValueError(
                        "FATAL: Cannot recurse through group-object {} in object-group network {}".format(
                            groupobject, self.name
                        )
                    )

                group_nets = self.confobj.asa_object_group_network.get(groupobject, None)
                if group_nets is None:
                    raise ValueError(
                        "FATAL: Cannot find group-object named {}".format(self.name)
                    )
                else:
                    retval.extend(group_nets.network_strings)
            elif "description " in obj.text:
                pass
            else:
                raise NotImplementedError("Cannot parse '{}'".format(obj.text))
        return retval

    @property
    @logger.catch(reraise=True)
    def networks(self):
        """Return a list of IPv4Obj objects which represent the address space allowed by
        This object-group"""
        ## FIXME: Implement object caching for other ConfigList objects
        ## Return a cached result if the networks lookup has already been done

        retval = list()
        for net_str in self.network_strings:
            ## Check the ASACfgList cache of network objects
            if not self.confobj._network_cache.get(net_str, False):
                net = IPv4Obj(net_str)
                self.confobj._network_cache[net_str] = net
                retval.append(net)
            else:
                retval.append(self.confobj._network_cache[net_str])

        return retval


##
##-------------  ASA object-group service
##
_RE_PORTOBJ_STR = r"""(?:                            # Non-capturing parentesis
 # service-object udp destination eq dns
 (^\s*service-object\s+(?P<protocol>{})\s+(?P<src_dst>\S+)\s+(?P<s_port>\S+))
|(^\s*port-object\s+(?P<operator>eq|range)\s+(?P<p_port>\S.+))
|(^\s*group-object\s+(?P<groupobject>\S+))
)                                                   # Close non-capture parens
""".format(
    "tcp|udp|tcp-udp"
)
_RE_PORTOBJECT = re.compile(_RE_PORTOBJ_STR, re.VERBOSE)


@attrs.define(repr=False, slots=False)
class ASAObjGroupService(ASACfgLine):
    name: str = None
    protocol_type: Any = None
    L4Objects_are_directional: bool = None

    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        """Accept an ASA line number and initialize family relationship
            attributes"""
        super(ASAObjGroupService, self).__init__(*args, **kwargs)

        self.protocol_type = self.re_match_typed(
            r"^object-group\s+service\s+\S+(\s+.+)*$",
            group=1,
            default="",
            result_type=str,
        ).strip()
        self.name = self.re_match_typed(
            r"^object-group\s+service\s+(\S+)", group=1, default="", result_type=str
        )
        ## If *no protocol* is specified in the object-group statement, the
        ##   object-group can be used for both source or destination ports
        ##   at the same time.  Thus L4Objects_are_directional is True if we
        ##   do not specify a protocol in the 'object-group service' line
        if self.protocol_type == "":
            self.L4Objects_are_directional = True
        else:
            self.L4Objects_are_directional = False


    @logger.catch(reraise=True)
    def __eq__(self, other):
        return self.get_unique_identifier() == other.get_unique_identifier()

    @logger.catch(reraise=True)
    def __ne__(self, other):
        return self.get_unique_identifier() != other.get_unique_identifier()

    @logger.catch(reraise=True)
    def __hash__(self):
        return self.get_unique_identifier()


    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, index=None, re=re):
        if "object-group service " in line[0:21].lower():
            return True
        return False

    @logger.catch(reraise=True)
    def __repr__(self):
        return "<ASAObjGroupService {} protocol: {}>".format(
            self.name, self.protocol_type
        )

    @property
    @logger.catch(reraise=True)
    def ports(self):
        """Return a list of objects which represent the protocol and ports allowed by this object-group"""
        retval = list()
        ## TODO: implement processing for group-objects (which obviously
        ##    involves iteration
        # GROUP_OBJ_REGEX = r'^\s*group-object\s+(\S+)'
        for obj in self.children:

            ## Parse out 'service-object ...' and 'port-object' lines...
            mm = _RE_PORTOBJECT.search(obj.text)
            if (mm is not None):
                svc_obj = mm.groupdict()
            else:
                svc_obj = dict()

            if svc_obj.get("protocol", None):
                protocol = svc_obj.get("protocol")
                port = svc_obj.get("s_port", "")

                if protocol == "tcp-udp":
                    retval.append(
                        L4Object(protocol="tcp", port_spec=port, syntax="asa")
                    )
                    retval.append(
                        L4Object(protocol="udp", port_spec=port, syntax="asa")
                    )
                else:
                    retval.append(
                        L4Object(protocol=protocol, port_spec=port, syntax="asa")
                    )

            elif svc_obj.get("operator", None):
                op = svc_obj.get("operator", "")
                port = svc_obj.get("p_port", "")
                port_spec = "{} {}".format(op, port)

                if self.protocol_type == "tcp-udp":
                    retval.append(
                        L4Object(protocol="tcp", port_spec=port_spec, syntax="asa")
                    )
                    retval.append(
                        L4Object(protocol="udp", port_spec=port_spec, syntax="asa")
                    )
                else:
                    retval.append(
                        L4Object(
                            protocol=self.protocol_type,
                            port_spec=port_spec,
                            syntax="asa",
                        )
                    )

            elif svc_obj.get("groupobject", None):
                name = svc_obj.get("groupobject")
                group_ports = self.confobj.object_group_service.get(name, None)
                if name == self.name:
                    ## Throw an error when importing self
                    raise ValueError(
                        "FATAL: Cannot recurse through group-object {} in object-group service {}".format(
                            name, self.name
                        )
                    )
                if group_ports is None:
                    raise ValueError(
                        "FATAL: Cannot find group-object named {}".format(name)
                    )
                else:
                    retval.extend(group_ports.ports)
            elif "description " in obj.text:
                pass
            else:
                raise NotImplementedError("Cannot parse '{}'".format(obj.text))
        return retval


##
##-------------  ASA Interface Object
##


@attrs.define(repr=False, slots=False)
class ASAIntfLine(BaseASAIntfLine):
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        """Accept an ASA line number and initialize family relationship
        attributes"""
        super(ASAIntfLine, self).__init__(*args, **kwargs)


    @logger.catch(reraise=True)
    def __eq__(self, other):
        return self.get_unique_identifier() == other.get_unique_identifier()

    @logger.catch(reraise=True)
    def __ne__(self, other):
        return self.get_unique_identifier() != other.get_unique_identifier()

    @logger.catch(reraise=True)
    def __hash__(self):
        return self.get_unique_identifier()


    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, index=None, re=re):
        intf_regex = r"^interface\s+(\S+.+)"
        if re.search(intf_regex, line):
            return True
        return False


##
##-------------  ASA Interface Globals
##


@attrs.define(repr=False, slots=False)
class ASAIntfGlobal(BaseCfgLine):
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super(ASAIntfGlobal, self).__init__(*args, **kwargs)
        self.feature = "interface global"


    @logger.catch(reraise=True)
    def __eq__(self, other):
        return self.get_unique_identifier() == other.get_unique_identifier()

    @logger.catch(reraise=True)
    def __ne__(self, other):
        return self.get_unique_identifier() != other.get_unique_identifier()

    @logger.catch(reraise=True)
    def __hash__(self):
        return self.get_unique_identifier()


    @logger.catch(reraise=True)
    def __repr__(self):
        return "<{} # {} '{}'>".format(self.classname, self.linenum, self.text)

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, index=None, re=re):
        if re.search("^mtu", line):
            return True
        return False


##
##-------------  ASA Hostname Line
##


@attrs.define(repr=False, slots=False)
class ASAHostnameLine(BaseCfgLine):
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super(ASAHostnameLine, self).__init__(*args, **kwargs)
        self.feature = "hostname"


    @logger.catch(reraise=True)
    def __eq__(self, other):
        return self.get_unique_identifier() == other.get_unique_identifier()

    @logger.catch(reraise=True)
    def __ne__(self, other):
        return self.get_unique_identifier() != other.get_unique_identifier()

    @logger.catch(reraise=True)
    def __hash__(self):
        return self.get_unique_identifier()


    @logger.catch(reraise=True)
    def __repr__(self):
        return "<{} # {} '{}'>".format(self.classname, self.linenum, self.hostname)

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, index=None, re=re):
        if re.search("^hostname", line):
            return True
        return False

    @property
    @logger.catch(reraise=True)
    def hostname(self):
        retval = self.re_match_typed(r"^hostname\s+(\S+)", result_type=str, default="")
        return retval


##
##-------------  Base ASA Route line object
##


class BaseASARouteLine(BaseCfgLine):
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super(BaseASARouteLine, self).__init__(*args, **kwargs)


    @logger.catch(reraise=True)
    def __eq__(self, other):
        return self.get_unique_identifier() == other.get_unique_identifier()

    @logger.catch(reraise=True)
    def __ne__(self, other):
        return self.get_unique_identifier() != other.get_unique_identifier()

    @logger.catch(reraise=True)
    def __hash__(self):
        return self.get_unique_identifier()


    @logger.catch(reraise=True)
    def __repr__(self):
        return "<{} # {} '{}' info: '{}'>".format(
            self.classname,
            self.linenum,
            self.network_object,
            self.routeinfo,
        )

    @property
    @logger.catch(reraise=True)
    def routeinfo(self):
        ### Route information for the repr string
        if self.tracking_object_name:
            return (
                self.nexthop_str
                + " AD: "
                + str(self.admin_distance)
                + " Track: "
                + self.tracking_object_name
            )
        else:
            return self.nexthop_str + " AD: " + str(self.admin_distance)

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, index=None, re=re):
        return False

    @property
    @logger.catch(reraise=True)
    def address_family(self):
        ## ipv4, ipv6, etc
        raise NotImplementedError

    @property
    @logger.catch(reraise=True)
    def network(self):
        raise NotImplementedError

    @property
    @logger.catch(reraise=True)
    def netmask(self):
        raise NotImplementedError

    @property
    @logger.catch(reraise=True)
    def admin_distance(self):
        raise NotImplementedError

    @property
    @logger.catch(reraise=True)
    def nexthop_str(self):
        raise NotImplementedError

    @property
    @logger.catch(reraise=True)
    def tracking_object_name(self):
        raise NotImplementedError


##
##-------------  ASA Configuration line object
##


@attrs.define(repr=False, slots=False)
class ASARouteLine(BaseASARouteLine):
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super(ASARouteLine, self).__init__(*args, **kwargs)
        if "ipv6" in self.text:
            self.feature = "ipv6 route"
        else:
            self.feature = "ip route"


    @logger.catch(reraise=True)
    def __eq__(self, other):
        return self.get_unique_identifier() == other.get_unique_identifier()

    @logger.catch(reraise=True)
    def __ne__(self, other):
        return self.get_unique_identifier() != other.get_unique_identifier()

    @logger.catch(reraise=True)
    def __hash__(self):
        return self.get_unique_identifier()


    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, index=None, re=re):
        if re.search(r"^(ip|ipv6)\s+route\s+\S", line):
            return True
        return False

    @property
    @logger.catch(reraise=True)
    def address_family(self):
        ## ipv4, ipv6, etc
        retval = self.re_match_typed(
            r"^(ip|ipv6)\s+route\s+*(\S+)", group=1, result_type=str, default=""
        )
        return retval

    @property
    @logger.catch(reraise=True)
    def network(self):
        if self.address_family == "ip":
            retval = self.re_match_typed(
                r"^ip\s+route\s+*(\S+)", group=2, result_type=str, default=""
            )
        elif self.address_family == "ipv6":
            retval = self.re_match_typed(
                r"^ipv6\s+route\s+*(\S+?)\/\d+", group=2, result_type=str, default=""
            )
        return retval

    @property
    @logger.catch(reraise=True)
    def netmask(self):
        if self.address_family == "ip":
            retval = self.re_match_typed(
                r"^ip\s+route\s+*\S+\s+(\S+)", group=2, result_type=str, default=""
            )
        elif self.address_family == "ipv6":
            retval = self.re_match_typed(
                r"^ipv6\s+route\s+*\S+?\/(\d+)", group=2, result_type=str, default=""
            )
        return retval

    @property
    @logger.catch(reraise=True)
    def network_object(self):
        try:
            if self.address_family == "ip":
                return IPv4Obj(f"{self.network}/{self.netmask}", strict=False)
            elif self.address_family == "ipv6":
                return ipaddress.IPv6Network(f"{self.network}/{self.netmask}")
        except BaseException:
            return None

    @property
    @logger.catch(reraise=True)
    def nexthop_str(self):
        if self.address_family == "ip":
            retval = self.re_match_typed(
                r"^ip\s+route\s+*\S+\s+\S+\s+(\S+)",
                group=2,
                result_type=str,
                default="",
            )
        elif self.address_family == "ipv6":
            retval = self.re_match_typed(
                r"^ipv6\s+route\s+*\S+\s+(\S+)", group=2, result_type=str, default=""
            )
        return retval

    @property
    @logger.catch(reraise=True)
    def admin_distance(self):
        retval = self.re_match_typed(r"(\d+)$", group=1, result_type=int, default=1)
        return retval

    @property
    @logger.catch(reraise=True)
    def tracking_object_name(self):
        retval = self.re_match_typed(
            r"^ip(v6)*\s+route\s+.+?track\s+(\S+)", group=2, result_type=str, default=""
        )
        return retval


_ACL_PROTOCOLS = (
    r"ip|tcp|udp|ah|eigrp|esp|gre|igmp|igrp|ipinip|ipsec|ospf|pcp|pim|pptp|snp|\d+"
)
_ACL_ICMP_PROTOCOLS = "alternate-address|conversion-error|echo-reply|echo|information-reply|information-request|mask-reply|mask-request|mobile-redirect|parameter-problem|redirect|router-advertisement|router-solicitation|source-quench|time-exceeded|timestamp-reply|timestamp-request|traceroute|unreachable"
_ACL_LOGLEVELS = r"alerts|critical|debugging|emergencies|errors|informational|notifications|warnings|[0-7]"
_RE_ACLOBJECT_STR = r"""(?:                         # Non-capturing parenthesis
# remark
 (^access-list\s+(?P<acl_name0>\S+)\s+(?P<action0>remark)\s+(?P<remark>\S.+?)$)

# extended service object with source network object, destination network object
|(?:^access-list\s+(?P<acl_name1>\S+)
  \s+extended\s+(?P<action1>permit|deny)
  \s+(?:
     (?:object-group\s+(?P<service_object1>\S+))
    |(?P<protocol1>{0})
  )
  \s+(?:                       # 10.0.0.0 255.255.255.0
     (?:object-group\s+(?P<src_networkobject1>\S+))
    |(?:object\s+(?P<src_object1>\S+))
    |(?:(?P<src_network1a>\S+)\s+(?P<src_netmask1a>\d+\.\d+\.\d+\.\d+))
  )
  \s+(?:                       # 10.0.0.0 255.255.255.0
     (?:object-group\s+(?P<dst_networkobject1>\S+))
    |(?:object\s+(?P<dst_object1>\S+))
    |(?:(?P<dst_network1a>\S+)\s+(?P<dst_netmask1a>\d+\.\d+\.\d+\.\d+))
  )
  (?:\s+
    (?P<log1>log)
    (?:\s+(?P<loglevel1>{1}))?
    (?:\s+interval\s+(?P<log_interval1>\d+))?
  )?
  (?:\s+(?P<disable1>disable))?
  (?:
    (?:\s+(?P<inactive1>inactive))
   |(?:\s+time-range\s+(?P<time_range1>\S+))
  )?
 \s*$)    # END access-list 1 parse

# extended service object with source network, destination network
# access-list TESTME1 extended permit ip any any log
|(?:^access-list\s+(?P<acl_name2>\S+)
  \s+extended
  \s+(?P<action2>permit|deny)
  \s+(?:                       # service-object or protocol
     (?:object-group\s+(?P<service_object2>\S+))
    |(?P<protocol2>{0})
  )
  (?:\s+       # any, any4, host foo, object-group FOO or 10.0.0.0 255.255.255.0
     (?:
       (?P<src_network2a>any|any4)
      |(?:host\s+(?P<src_network2b>\S+))
      |(?:object\s+(?P<src_object2>\S+))
      |(?:object-group\s+(?P<src_networkobject2>\S+))
      |(?:(?P<src_network2c>\S+)\s+(?P<src_netmask2c>\d+\.\d+\.\d+\.\d+))
    )
  )
  (?:\s+
    (?:
       (?:(?P<src_port_operator>eq|neq|lt|gt)\s+(?P<src_port>\S+))
      |(?:range\s+(?P<src_port_low>\S+)\s+(?P<src_port_high>\S+))
      |(?:object-group\s+(?P<src_service_object>\S+))
    )
  )?
  (?:\s+       # any, any4, host foo, object-group FOO or 10.0.0.0 255.255.255.0
     (?:
       (?P<dst_network2a>any|any4)
      |(?:host\s+(?P<dst_network2b>\S+))
      |(?:object\s+(?P<dst_object2>\S+))
      |(?:object-group\s+(?P<dst_networkobject2>\S+))
      |(?:(?P<dst_network2c>\S+)\s+(?P<dst_netmask2c>\d+\.\d+\.\d+\.\d+))
    )
  )
  (?:\s+
    (?:
       (?:(?P<dst_port_operator>eq|neq|lt|gt)\s+(?P<dst_port>\S+))
      |(?:range\s+(?P<dst_port_low>\S+)\s+(?P<dst_port_high>\S+))
      |(?:object-group\s+(?P<dst_service_object>\S+))
    )
  )?
  (?:\s+
    (?P<log2>log)
    (?:\s+(?P<loglevel2>{1}))?
    (?:\s+interval\s+(?P<log_interval2>\d+))?
  )?
  (?:\s+(?P<disable2>disable))?
  (?:
    (?:\s+(?P<inactive2>inactive))
   |(?:\s+time-range\s+(?P<time_range2>\S+))
  )?
 \s*$)    # END access-list 2 parse

# access-list SPLIT_TUNNEL_NETS standard permit 192.0.2.0 255.255.255.0
|(?:^access-list\s+(?P<acl_name3>\S+)
  \s+standard
  \s+(?P<action3>permit|deny)
  \s+(?:
    (?P<dst_network3a>any|any4)
   |(?:host\s+(?P<dst_network3b>\S+))
   |(?:(?P<dst_network3c>\S+)\s+(?P<dst_netmask3c>\d+\.\d+\.\d+\.\d+))
  )

  )
#access-list TESTME extended permit icmp any4 0.0.0.0 0.0.0.0 unreachable log interval 1
|(?:^access-list\s+(?P<acl_name4>\S+)
  \s+extended
  \s+(?P<action4>permit|deny)
  \s+(?P<protocol4>icmp)
  (?:\s+       # any, any4, host foo, object-group FOO or 10.0.0.0 255.255.255.0
     (?:
       (?P<src_network4a>any|any4)
      |(?:host\s+(?P<src_network4b>\S+))
      |(?:object\s+(?P<src_object4>\S+))
      |(?:object-group\s+(?P<src_networkobject4>\S+))
      |(?:(?P<src_network4c>\S+)\s+(?P<src_netmask4c>\d+\.\d+\.\d+\.\d+))
    )
  )
  (?:\s+       # any, any4, host foo, object-group FOO or 10.0.0.0 255.255.255.0
     (?:
       (?P<dst_network4a>any|any4)
      |(?:host\s+(?P<dst_network4b>\S+))
      |(?:object\s+(?P<dst_object4>\S+))
      |(?:object-group\s+(?P<dst_networkobject4>\S+))
      |(?:(?P<dst_network4c>\S+)\s+(?P<dst_netmask4c>\d+\.\d+\.\d+\.\d+))
    )
  )
  (?:\s+(?P<icmp_proto4>{2}|\d+))?
  (?:\s+
    (?P<log4>log)
    (?:\s+(?P<loglevel4>{1}))?
    (?:\s+interval\s+(?P<log_interval4>\d+))?
  )?
  (?:\s+(?P<disable4>disable))?
  (?:
    (?:\s+(?P<inactive4>inactive))
   |(?:\s+time-range\s+(?P<time_range4>\S+))
  )?
  )
)                                                   # Close non-capture parens
""".format(
    _ACL_PROTOCOLS, _ACL_LOGLEVELS, _ACL_ICMP_PROTOCOLS
)
_RE_ACLOBJECT = re.compile(_RE_ACLOBJECT_STR, re.VERBOSE)


@attrs.define(repr=False, slots=False)
class ASAAclLine(ASACfgLine):
    _mm_results: dict = None

    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        """Provide attributes on Cisco ASA Access-Lists"""
        super(ASAAclLine, self).__init__(*args, **kwargs)

        # Parse out the most common parameter names...
        text = kwargs.get("text", None) or kwargs.get("line", None)

        if text is None:
            error = "line=None is an invalid input"
            logger.critical(error)
            raise InvalidParameters(error)

        self.text = text
        self._mm_results = None

        mm = _RE_ACLOBJECT.search(text)
        if (mm is not None):
            self._mm_results = mm.groupdict()  # All regex match results
        else:
            raise ValueError("[FATAL] ASAAclLine() cannot parse text:'{}'".format(text))


    @logger.catch(reraise=True)
    def __eq__(self, other):
        return self.get_unique_identifier() == other.get_unique_identifier()

    @logger.catch(reraise=True)
    def __ne__(self, other):
        return self.get_unique_identifier() != other.get_unique_identifier()

    @logger.catch(reraise=True)
    def __hash__(self):
        return self.get_unique_identifier()


    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, index=None, re=re):
        # if _RE_ACLOBJECT.search(line):
        if "access-list " in line[0:12].lower():
            return True
        return False

    @property
    @logger.catch(reraise=True)
    def src_addr_method(self):
        mm_r = self._mm_results
        if mm_r["action0"] and (mm_r["action0"] == "remark"):
            # remarks return an empty string
            return ""
        elif (
            mm_r["src_networkobject1"]
            or mm_r["src_networkobject2"]
            or mm_r["src_networkobject4"]
        ):
            return "object-group"
        elif mm_r["src_object1"] or mm_r["src_object2"] or mm_r["src_object4"]:
            return "object"
        elif (
            mm_r["src_network1a"]
            or mm_r["src_network2a"]
            or mm_r["src_network2b"]
            or mm_r["src_network2c"]
            or mm_r["src_network4a"]
            or mm_r["src_network4b"]
            or mm_r["src_network4c"]
        ):
            return "network"
        ## NOTE: I intended to match dst addrs here...
        elif mm_r["acl_name3"]:
            ## Special case: standard ACLs match any src implicitly
            self._mm_results["src_network3"] = "any4"
            return "network"
        else:
            raise ValueError(
                "Cannot parse ACL source address method for '{}'".format(self.text)
            )

    @property
    @logger.catch(reraise=True)
    def dst_addr_method(self):
        mm_r = self._mm_results
        if mm_r["action0"] and (mm_r["action0"] == "remark"):
            # remarks return an empty string
            return ""
        elif (
            mm_r["dst_networkobject1"]
            or mm_r["dst_networkobject2"]
            or mm_r["dst_networkobject4"]
        ):
            return "object-group"
        elif mm_r["dst_object1"] or mm_r["dst_object2"] or mm_r["dst_object4"]:
            return "object"
        elif (
            mm_r["dst_network1a"]
            or mm_r["dst_network2a"]
            or mm_r["dst_network2b"]
            or mm_r["dst_network2c"]
            or mm_r["dst_network4a"]
            or mm_r["dst_network4b"]
            or mm_r["dst_network4c"]
        ):
            return "network"
        elif mm_r["dst_network3a"] or mm_r["dst_network3b"] or mm_r["dst_network3c"]:
            return "network"
        else:
            raise ValueError(
                "Cannot parse ACL destination address method for '{}'".format(
                    self.text
                )
            )

    @property
    @logger.catch(reraise=True)
    def acl_protocol_dict(self):
        mm_r = self._mm_results
        retval = dict()

        if mm_r["remark"]:
            # remarks get IP protocol -1
            retval["protocol"] = -1
            retval["protocol_object"] = ""
            return retval
        elif mm_r["protocol1"] or mm_r["protocol2"] or mm_r["protocol4"]:
            _proto = mm_r["protocol1"] or mm_r["protocol2"] or mm_r["protocol4"] or -1
            retval["protocol"] = int(ASA_IP_PROTOCOLS.get(_proto, _proto))
            retval["protocol_object"] = ""
            return retval
        elif mm_r["acl_name3"]:
            # Special case for standard ASA ACLs
            _proto = "ip"
            retval["protocol"] = int(ASA_IP_PROTOCOLS.get(_proto, _proto))
            retval["protocol_object"] = ""
            return retval
        elif mm_r["service_object1"] or mm_r["service_object2"]:
            # protocol service objects get a special protocol number
            retval["protocol"] = 65535
            retval["protocol_object"] = (
                mm_r["service_object1"] or mm_r["service_object2"]
            )
            return retval
        else:
            raise ValueError(
                "Cannot parse ACL protocol value for '{}'".format(self.text)
            )

    @property
    @logger.catch(reraise=True)
    def result_dict(self):
        mm_r = self._mm_results
        retval = dict()

        proto_dict = self.acl_protocol_dict
        retval["ip_protocol"] = proto_dict["protocol"]
        retval["ip_protocol_object"] = proto_dict["protocol_object"]
        retval["acl_name"] = (
            mm_r["acl_name0"]
            or mm_r["acl_name1"]
            or mm_r["acl_name2"]
            or mm_r["acl_name3"]
            or mm_r["acl_name4"]
        )
        retval["action"] = (
            mm_r["action0"]
            or mm_r["action1"]
            or mm_r["action2"]
            or mm_r["action3"]
            or mm_r["action4"]
        )
        retval["remark"] = mm_r["remark"]
        retval["src_addr_method"] = self.src_addr_method
        retval["dst_addr_method"] = self.dst_addr_method
        retval["disable"] = bool(
            mm_r["disable1"] or mm_r["disable2"] or mm_r["disable4"]
        )
        retval["time_range"] = (
            mm_r["time_range1"] or mm_r["time_range2"] or mm_r["time_range4"]
        )
        retval["log"] = bool(mm_r["log1"] or mm_r["log2"] or mm_r["log4"])
        if not retval["log"]:
            retval["log_interval"] = -1
            retval["log_level"] = ""
        else:
            retval["log_level"] = (
                mm_r["loglevel1"]
                or mm_r["loglevel2"]
                or mm_r["loglevel4"]
                or "informational"
            )
            retval["log_interval"] = int(
                mm_r["log_interval1"]
                or mm_r["log_interval2"]
                or mm_r["log_interval4"]
                or 300
            )

        return retval


################################
################################ Groups ###############################
################################
