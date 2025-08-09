from typing import Union, Any, Set, List, Tuple, Dict
import re

import attrs
from loguru import logger

from ciscoconfparse2.errors import DynamicAddressException

from ciscoconfparse2.ccp_util import (
    _IPV6_REGEX_STR_COMPRESSED1,
    _IPV6_REGEX_STR_COMPRESSED2,
)
from ciscoconfparse2.errors import InvalidCiscoEthernetTrunkAction
from ciscoconfparse2.errors import InvalidCiscoEthernetVlan
from ciscoconfparse2.errors import InvalidCiscoInterface

from ciscoconfparse2.ccp_util import _IPV6_REGEX_STR_COMPRESSED3
from ciscoconfparse2.ccp_util import CiscoIOSXRInterface
from ciscoconfparse2.ccp_util import CiscoIOSInterface
from ciscoconfparse2.ccp_util import CiscoRange
from ciscoconfparse2.ccp_util import IPv4Obj, IPv6Obj
from ciscoconfparse2.ccp_abc import BaseCfgLine


### HUGE UGLY WARNING:
###   Anything in models_cisco.py could change at any time, until I remove this
###   warning.  I have good reason to believe that these methods are stable and
###   function correctly, but I've been wrong before.  There are no unit tests
###   for this functionality yet, so I consider all this code alpha quality.
###
###   Use models_cisco.py at your own risk.  You have been warned :-)
r""" models_base.py - Parse, Query, Build, and Modify IOS-style configurations

     Copyright (C) 2021-2025 David Michael Pennington
     Copyright (C) 2020-2021 David Michael Pennington at Cisco Systems
     Copyright (C) 2019      David Michael Pennington at ThousandEyes
     Copyright (C) 2014-2019 David Michael Pennington at Samsung Data Services

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

MAX_VLAN = 4094
_VIRTUAL_INTF_REGEX_STR = (
    r"""^interface\s+(Loopback|Vlan|Tunnel|Dialer|Virtual-Template|Port-Channel)"""
)
_VIRTUAL_INTF_REGEX = re.compile(_VIRTUAL_INTF_REGEX_STR, re.I)

##
##-------------  IOS Configuration line object
##


@attrs.define(repr=False, slots=False)
class BaseFactoryLine(BaseCfgLine):
    """A base class for all factory class implementations.

    :param line: A string containing a text copy of the IOS configuration line.
    :type line: str
    :param comment_delimiter: A string which is considered a comment for the configuration format.
    :type line: str

    Attributes
    ----------
    text : str
        A string containing the parsed IOS configuration statement
    linenum : int
        The line number of this configuration statement in the original config; default is -1 when first initialized.
    parent : (:class:`~ciscoconfparse2.models_cisco.IOSCfgLine()`)
        The parent of this object; defaults to ``self``.
    children : list
        A list of ``IOSCfgLine()`` objects which are children of this object.
    child_indent : int
        An integer with the indentation of this object's children
    indent : int
        An integer with the indentation of this object's ``text`` oldest_ancestor (bool): A boolean indicating whether this is the oldest ancestor in a family
    is_comment : bool
        A boolean indicating whether this is a comment
    """

    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        r"""Accept an IOS line number and initialize family relationship attributes"""
        super().__init__(*args, **kwargs)

    @logger.catch(reraise=True)
    def __eq__(self, other) -> bool:
        if other is None:
            return False
        return self.get_unique_identifier() == other.get_unique_identifier()

    @logger.catch(reraise=True)
    def __ne__(self, other) -> bool:
        if other is None:
            return True
        return self.get_unique_identifier() != other.get_unique_identifier()

    @logger.catch(reraise=True)
    def __hash__(self) -> int:
        return self.get_unique_identifier()

    @classmethod
    def from_list(cls, all_lines: list[str], line: str) -> BaseCfgLine:
        """Helper-method to allow strictly positional *arg calls .i.e. IOSCfgLine([], 'hostname Foo')"""
        raise NotImplementedError()

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(
        cls, all_lines: list[str], line: str, index: int = None, re: re.Pattern = re
    ) -> bool:
        """Return True if this object should be used for a given configuration line; otherwise return False"""
        raise NotImplementedError()

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for_hostname(cls, line: str) -> bool:
        raise NotImplementedError()

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for_interface(cls, line: str) -> bool:
        """Use this method to determine whether this class should be used for a physical or logical configuration interface class"""
        raise NotImplementedError()

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for_aaa_authentication(cls, line: str) -> bool:
        """Return True if this is an object for aaa authentication.  Be sure to reject 'aaa new-model'"""
        raise NotImplementedError()

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for_aaa_authorization(cls, line: str) -> bool:
        """Return True if this is an object for aaa authorization.  Be sure to reject 'aaa new-model'"""
        raise NotImplementedError()

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for_aaa_accounting(cls, line: str) -> bool:
        """Return True if this is an object for aaa accounting.  Be sure to reject 'aaa new-model'"""
        raise NotImplementedError()

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for_ip_route(cls, line: str) -> bool:
        raise NotImplementedError()

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for_ipv6_route(cls, line: str) -> bool:
        raise NotImplementedError()

    @property
    @logger.catch(reraise=True)
    def is_intf(self) -> bool:
        # Includes subinterfaces
        r"""Returns a boolean (True or False) to answer whether this
        :class:`~ciscoconfparse2.models_cisco.IOSCfgLine` is an interface; subinterfaces
        also return True.

        :return: Returns a boolean (True or False) to answer whether this
                 :class:`ciscoconfparse2.models_base.BaseFactoryLine` is an interface; subinterfaces
                 also return True.
        :rtype: bool
        """
        raise NotImplementedError()

    @property
    @logger.catch(reraise=True)
    def is_subintf(self) -> bool:
        r"""
        :return: Returns a boolean (True or False) to answer whether this
                 :class:`ciscoconfparse2.models_base.BaseFactoryLine` is a subinterface.
        :rtype: bool
        """
        raise NotImplementedError()

    @property
    @logger.catch(reraise=True)
    def is_virtual_intf(self) -> bool:
        raise NotImplementedError()

    @property
    @logger.catch(reraise=True)
    def is_loopback_intf(self) -> bool:
        r"""
        :return: Returns a boolean (True or False) to answer whether this
                 :class:`ciscoconfparse2.models_base.BaseFactoryLine` is a loopback interface.
        :rtype: bool
        """
        raise NotImplementedError()

    @property
    @logger.catch(reraise=True)
    def is_ethernet_intf(self) -> bool:
        r"""
        :return: Returns a boolean (True or False) to answer whether this
                 :class:`ciscoconfparse2.models_base.BaseFactoryLine` is an ethernet interface.  Any ethernet interface
                 (10M and up) is considered an ethernet interface.
        :rtype: bool
        """
        raise NotImplementedError()

    @property
    @logger.catch(reraise=True)
    def is_in_portchannel(self) -> bool:
        r"""
        :return: Return a boolean indicating whether this port is configured in a port-channel
        :rtype: bool
        """
        raise NotImplementedError()

    @property
    @logger.catch(reraise=True)
    def portchannel_number(self) -> int:
        r"""

        :return: Return an integer for the port-channel which it's configured in, default to -1
        :rtype: int
        """
        raise NotImplementedError()


##
##-------------  IOS Interface ABC
##

# Valid method name substitutions:
#    switchport -> switch
#    spanningtree -> stp
#    interfce -> intf
#    address -> addr
#    default -> def


@attrs.define(repr=False, slots=False)
class BaseFactoryInterfaceLine(BaseFactoryLine):
    ifindex: str = None
    default_ipv4_addr_object: Any = None
    default_ipv6_addr_object: Any = None

    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ifindex = None  # Optional, for user use
        self.default_ipv4_addr_object = IPv4Obj()
        self.default_ipv6_addr_object = IPv6Obj()

    # This method is on BaseFactoryInterfaceLine()
    @logger.catch(reraise=True)
    def __repr__(self) -> str:
        if not self.is_switchport:
            try:
                ipv4_addr_object = self.ipv4_addr_object
            except DynamicAddressException:
                ipv4_addr_object = None

            if ipv4_addr_object is None:
                addr_str = "IPv4 dhcp"
            elif ipv4_addr_object == self.default_ipv4_addr_object:
                addr_str = "No IPv4"
            else:
                addr_str = f"{self.ipv4_addr}/{self.ipv4_masklength}"
            return f"<{self.classname} # {self.linenum} '{self.text.strip()}' primary_ipv4: '{addr_str}'>"
        else:
            return f"<{self.classname} # {self.linenum} '{self.text.strip()}' switchport: 'switchport'>"

    # This method is on BaseFactoryInterfaceLine()
    @logger.catch(reraise=True)
    def _build_abbvs(self) -> set[str]:
        r"""
        :return: a set of valid abbreviations (lowercased) for the interface
        :rtype: set[str]
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @logger.catch(reraise=True)
    def get_hsrp_groups(self) -> list[Any]:
        """
        :return: the sequence of configured HSRPInterfaceGroup() instances
        :rtype: List[Any]
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def verbose(self) -> str:
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

    # This method is on BaseFactoryInterfaceLine()
    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(
        cls, all_lines: list[str], line: str, index: int = None, re: re.Pattern = re
    ) -> bool:
        """Return a boolean for whether this object should be used based on the inputs"""
        raise NotImplementedError()

    ##-------------  Basic interface properties

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def abbvs(self) -> set[str]:
        r"""A python set of valid abbreviations (lowercased) for the interface"""
        raise NotImplementedError()

    @property
    def cisco_interface_object(self) -> Union[CiscoIOSInterface, CiscoIOSXRInterface]:
        """Return a CiscoIOSInterface() instance for this interface

        :return: The interface name as a CiscoIOSInterface() / CiscoIOSXRInterface() instance, or '' if the object is not an interface.  The CiscoIOSInterface instance can be transparently cast as a string into a typical Cisco IOS name.
        :rtype: Union[CiscoIOSInterface, CiscoIOSXRInterface]
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def name(self) -> str:
        r"""
        :return: The interface name as a string, such as 'GigabitEthernet0/1'
        :rtype: str
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def port(self) -> int:
        r"""
        :return: The interface's port number
        :rtype: int
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def port_type(self) -> str:
        r"""

        :return: The port type: Loopback, ATM, GigabitEthernet, Virtual-Template, etc...
        :rtype: str
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def ordinal_list(self) -> tuple[int, ...]:
        r"""

        :return: Return a tuple of integers representing card, slot, port for this interface.  If you call ordinal_list on GigabitEthernet2/25.100, you'll get this python tuple of integers: (2, 25).  If you call ordinal_list on GigabitEthernet2/0/25.100 you'll get this python list of integers: (2, 0, 25).  This method strips all subinterface information in the returned value.
        :rtype: tuple[int, ...]

        .. warning::

           ordinal_list should silently fail (returning an empty python tuple) if the interface doesn't parse correctly
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def interface_number(self) -> str:
        r"""

        :return: Return a string representing the card, slot, port for this interface.  If you call interface_number on GigabitEthernet2/25.100, you'll get this python string: '2/25'.  If you call interface_number on GigabitEthernet2/0/25.100 you'll get this python string '2/0/25'.  This method strips all subinterface information in the returned value.
        :rtype: str

        .. warning::

           interface_number should silently fail (returning an empty python string) if the interface doesn't parse correctly
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def subinterface_number(self) -> str:
        r"""

        :return: Return a string representing the card, slot, port for this interface or subinterface.  If you call subinterface_number on GigabitEthernet2/25.100, you'll get this python string: '2/25.100'.  If you call interface_number on GigabitEthernet2/0/25 you'll get this python string '2/0/25'.  This method strips all subinterface information in the returned value.
        :rtype: str

        .. warning::

           subinterface_number should silently fail (returning an empty python string) if the interface doesn't parse correctly
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def description(self) -> str:
        r"""
        :return: Return the current interface description string, default to ''.
        :rtype: str
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def manual_bandwidth(self) -> int:
        r"""
        :return: Return the integer bandwidth, default to -1
        :rtype: int
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def manual_delay(self) -> int:
        r"""
        :return: Return the integer delay
        :rtype: int
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def manual_holdqueue_out(self) -> int:
        r"""
        :return: Return the current hold-queue out depth, default to -1
        :rtype: int
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def manual_holdqueue_in(self) -> int:
        r"""
        :return: Return the current hold-queue int depth, default to -1
        :rtype: int
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def manual_encapsulation(self) -> str:
        r"""
        :return: Return the current encapsulation (i.e. ppp, hdlc, ethernet, etc...), default to ''
        :rtype: str
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def has_mpls(self) -> bool:
        r"""
        :return: Whether this interface is configured with MPLS
        :rtype: bool
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_addr_object(self) -> IPv4Obj:
        r"""
        :return: A :class:`ccp_util.IPv4Obj` object representing the address on this interface, default to IPv4Obj()
        :rtype: IPv4Obj
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def ipv6_addr_objects(self) -> dict[str, list[IPv6Obj]]:
        r"""
        :return: A Dict of :class:`ccp_util.IPv6Obj` objects representing all IPv6 addresses on this interface, default to {}
        :rtype: IPv6Obj
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def ip_secondary_addresses(self) -> set[str]:
        r"""
        :return: Return a set of IPv4 secondary addresses (as strings), default to an empty set
        :rtype: set[str]
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def ip_secondary_networks(self) -> set[str]:
        r"""
        :return: Return a set of IPv4 network / prefixlen (as strings), default to an empty set
        :rtype: set[str]
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def ip(self) -> IPv4Obj:
        r"""
        :return: A :class:`ccp_util.IPv4Obj` object representing the IPv4 address on this interface, default to IPv4Obj()
        :rtype: IPv4Obj
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def ipv4(self) -> IPv4Obj:
        r"""
        :return: A :class:`ccp_util.IPv4Obj` object representing the IPv4 address on this interface, default to IPv4Obj()
        :rtype: IPv4Obj
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_network_object(self) -> IPv4Obj:
        r"""
        :return: A :class:`ccp_util.IPv4Obj` object representing the IPv4 subnet on this interface, default to IPv4Obj()
        :rtype: IPv4Obj
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def ip_network_object(self) -> IPv4Obj:
        r"""
        :return: A :class:`ccp_util.IPv4Obj` object representing the IPv4 subnet on this interface, default to IPv4Obj()
        :rtype: IPv4Obj
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def has_autonegotiation(self) -> bool:
        r"""
        :return: Whether autonegotiation is enabled on this interface
        :rtype: bool
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def manual_carrierdelay(self) -> float:
        r"""
        :return: The manual carrier delay (in seconds) of the interface as a python float, default to -1.0
        :rtype: float
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def manual_clock_rate(self) -> int:
        r"""
        :return: Return the clock rate of the interface as a python integer, default to -1
        :rtype: int
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def manual_mtu(self) -> int:
        ## Due to the diverse platform defaults, this should be the
        ##    only mtu information I plan to support
        r"""
        :return: Return the manual MTU of the interface as a python integer, default to -1
        :rtype: int
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def manual_mpls_mtu(self) -> int:
        ## Due to the diverse platform defaults, this should be the
        ##    only mtu information I plan to support
        r"""
        :return: Return the manual MPLS MTU of the interface as a python integer, default to -1
        :rtype: int
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def manual_ip_mtu(self) -> int:
        ## Due to the diverse platform defaults, this should be the
        ##    only mtu information I plan to support
        r"""
        :return: Return the manual IP MTU of the interface as a python integer, default to -1
        :rtype: int
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def manual_ipv6_mtu(self) -> int:
        ## Due to the diverse platform defaults, this should be the
        ##    only mtu information I plan to support
        r"""
        :return: Return the manual IPv6 MTU of the interface as a python integer, default to -1
        :rtype: int
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def manual_speed(self) -> int:
        r"""
        :return: Return the manual speed of the interface as a python integer, default to -1
        :rtype: int
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def manual_duplex(self) -> str:
        r"""
        :return: Return the manual duplex of the interface as a python integer, default to ''
        :rtype: str
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def is_shutdown(self) -> bool:
        r"""
        :return: Whether the interface is shutdown
        :rtype: bool
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def vrf(self) -> str:
        r"""
        :return: The name of the VRF configured on the interface, default to ''
        :rtype: str
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def ip_addr(self) -> str:
        r"""
        :return: The IP address configured on the interface, default to ''
        :rtype: str
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_addr(self) -> str:
        r"""
        :return: The IP address configured on the interface, default to ''
        :rtype: str
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_netmask(self) -> str:
        r"""
        :return: The IP netmask configured on the interface, default to ''
        :rtype: str
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_masklength(self) -> int:
        r"""
        :return: Return an integer with the interface's IPv4 mask length, default to -1
        :rtype: int
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def ipv6_addr(self) -> str:
        r"""
        :return: The IPv6 address configured on the interface, default to ''
        :rtype: str
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def ipv6_masklength(self) -> int:
        r"""
        :return: The IPv6 masklength configured on the interface, default to -1
        :rtype: int
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @logger.catch(reraise=True)
    def is_abbreviated_as(self, value: str) -> int:
        """
        :return: Whether ``value`` is a good abbreviation for the interface
        :rtype: bool
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @logger.catch(reraise=True)
    def in_ipv4_subnet(self, ipv4network: IPv4Obj = None, strict: bool = False) -> bool:
        r"""
        :return: Whether the interface is in a :class:`~ciscoconfparse2.ccp_util.IPv4Obj` subnet, default to False.
        :rtype: bool
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @logger.catch(reraise=True)
    def in_ipv4_subnets(
        self, subnets: Union[set[IPv4Obj], list[IPv4Obj], tuple[IPv4Obj, ...]] = None
    ) -> bool:
        r"""
        :return: Whether the interface is in a sequence or set of ccp_util.IPv4Obj objects
        :rtype: bool
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def has_no_icmp_unreachables(self) -> bool:
        r"""
        :return: Whether the interface is configured without ICMP unreachables
        :rtype: bool
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def has_no_icmp_redirects(self) -> bool:
        r"""
        :return: Whether the interface is configured without ICMP redirects
        :rtype: bool
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def has_no_ip_proxyarp(self) -> bool:
        r"""
        :return: Whether the interface is configured without Proxy-ARP
        :rtype: bool
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def has_ip_pim_dense_mode(self) -> bool:
        r"""
        :return: Whether the interface is configured with IP PIM Dense-Mode
        :rtype: bool
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def has_ip_pim_sparse_mode(self) -> bool:
        r"""
        :return: Whether the interface is configured with IP PIM Sparse-Mode
        :rtype: bool
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def has_ipv6_pim_sparse_mode(self) -> bool:
        r"""
        :return: Whether the interface is configured with IPv6 PIM Sparse-Mode
        :rtype: bool
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def has_ip_pim_sparsedense_mode(self) -> bool:
        r"""
        :return: Whether the interface is configured with IP PIM Sparse-Dense-Mode
        :rtype: bool
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def manual_arp_timeout(self) -> int:
        r"""
        :return: An integer with the manual ARP timeout, default to -1
        :rtype: int
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def ip_helper_addresses(self) -> list[dict[str, str]]:
        r"""
        :return: A sequence of dicts with IP helper-addresses.  Each helper-address is in a dictionary.
        :rtype: List[Dict[str,str]]
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def ipv6_dhcp_server(self) -> list[dict[str, str]]:
        r"""
        :return: A sequence of dicts with IPv6 dhcp server.  Each address is in a dictionary.
        :rtype: List[Dict[str,str]]
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def is_switchport(self) -> bool:
        r"""
        :return: Whether the interface is a switchport
        :rtype: bool
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_switch_access(self) -> bool:
        r"""
        :return: Whether the interface is manually configured as an access switchport
        :rtype: bool
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_switch_trunk_encap(self) -> bool:
        r"""
        :return: Whether the interface is has a manual switchport trunk encapsulation
        :rtype: bool
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def manual_switch_trunk_encap(self) -> str:
        r"""
        :return: The type of trunk encapsulation of this switchport.
        :rtype: str
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_switch_trunk(self) -> bool:
        r"""
        :return: Whether this interface is manually configured as a trunk switchport
        :rtype: bool
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def has_switch_portsecurity(self) -> bool:
        r"""
        :return: Whether this interface is fully configured with port-security
        :rtype: bool
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def has_switch_stormcontrol(self) -> bool:
        r"""
        :return: Whether this interface is fully configured with storm-control
        :rtype: bool
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def has_dtp(self) -> bool:
        r"""
        :return: Whether this interface is configured to use Cisco DTP
        :rtype: bool
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def access_vlan(self) -> int:
        r"""
        :return: An integer access vlan number, default to 1.  Return -1 if the port is not a switchport.
        :rtype: int
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def trunk_vlans_allowed(self) -> CiscoRange:
        r"""
        :return: A CiscoRange() with the list of allowed vlan numbers (as int).
        :rtype: CiscoRange
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def native_vlan(self) -> int:
        r"""
        :return: Return an integer with the native vlan number.  Return 1, if the switchport has no explicit native vlan configured; return -1 if the port isn't a switchport
        :rtype: int
        """
        raise NotImplementedError()

    ##-------------  CDP

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_disable_cdp(self) -> bool:
        """
        :return: Whether CDP is manually disabled on this interface
        :rtype: bool
        """
        raise NotImplementedError()

    ##-------------  EoMPLS

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def has_xconnect(self) -> bool:
        """
        :return: Whether this interface has an MPLS or L2TP xconnect
        :rtype: bool
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def xconnect_vc(self) -> int:
        """
        :return: The virtual circuit ID of the xconnect on this interface, default to -1 (even if no xconnect)
        :rtype: int
        """
        raise NotImplementedError()

    ##-------------  HSRP

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def has_ip_hsrp(self) -> bool:
        """
        :return: Whether this interface has HSRP configured on it
        :rtype: bool
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def hsrp_ip_addr(self) -> dict[int, str]:
        """
        :return: A dict keyed by integer HSRP group number with a string ipv4 address, default to an empty dict
        :rtype: Dict[int,str]
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def hsrp_ip_addr_secondary(self) -> dict[int, str]:
        """
        :return: A dict keyed by integer HSRP group number with a comma-separated string secondary ipv4 address, default to an empty dict
        :rtype: Dict[int,str]
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def hsrp_priority(self) -> dict[int, int]:
        """
        :return: A dict keyed by integer HSRP group number with an integer HSRP priority per-group
        :rtype: Dict[int,int]
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def hsrp_hello_timer(self) -> dict[int, float]:
        """
        :return: A dict keyed by integer HSRP group number with an integer HSRP hello timer
        :rtype: Dict[int,float]
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def hsrp_hold_timer(self) -> dict[int, float]:
        """
        :return: A dict keyed by integer HSRP group number with an integer HSRP hold timer
        :rtype: Dict[int,float]
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def hsrp_usebia(self) -> dict[int, bool]:
        """
        :return: A dict keyed by integer HSRP group number with a bool value for whether the group is configured with use-bia
        :rtype: Dict[int,bool]
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def hsrp_preempt(self) -> dict[int, bool]:
        """
        :return: A dict keyed by integer HSRP group number with a bool value for whether the group is configured with preempt
        :rtype: Dict[int,bool]
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def hsrp_authentication_md5_keychain(self) -> dict[int, bool]:
        """
        :return: A dict keyed by integer HSRP group number with a string value of the HSRP authentication key-chain name
        :rtype: Dict[int,str]
        """
        raise NotImplementedError()

    ##-------------  MAC ACLs

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def mac_accessgroup_in(self) -> bool:
        """
        :return: Whether this interface has an inbound mac access-list
        :rtype: bool
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def mac_accessgroup_out(self) -> bool:
        """
        :return: Whether this interface has an outbound mac access-list
        :rtype: bool
        """
        raise NotImplementedError()

    ##-------------  IPv4 ACLs

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def ip_accessgroup_in(self) -> str:
        """
        :return: The name or number of the inbound IPv4 access-group
        :rtype: str
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def ip_accessgroup_out(self) -> str:
        """
        :return: The name or number of the outbound IPv4 access-group
        :rtype: str
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_accessgroup_in(self) -> str:
        """
        :return: The name or number of the inbound IPv4 access-group
        :rtype: str
        """
        raise NotImplementedError()

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_accessgroup_out(self) -> str:
        """
        :return: The name or number of the outbound IPv4 access-group
        :rtype: str
        """
        raise NotImplementedError()

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv6_trafficfilter_in(self) -> str:
        """
        :return: The name or number of the inbound IPv6 ACL
        :rtype: str
        """
        raise NotImplementedError()

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv6_trafficfilter_out(self) -> str:
        """
        :return: The name or number of the outbound IPv6 ACL
        :rtype: str
        """
        raise NotImplementedError()

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv6_accessgroup_in(self) -> str:
        """
        Alias for ipv6_trafficfilter_in

        :return: The name or number of the inbound IPv6 ACL
        :rtype: str
        """
        return self.ipv6_trafficfilter_in

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv6_accessgroup_out(self) -> str:
        """
        Alias for ipv6_trafficfilter_out

        :return: The name or number of the outbound IPv6 ACL
        :rtype: str
        """
        return self.ipv6_trafficfilter_out


##
##-------------  IOS Interface Object
##


@attrs.define(repr=False, slots=False)
class IOSIntfLine(BaseFactoryInterfaceLine):

    # This method is on IOSIntfLine()
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        r"""Accept an IOS line number and initialize family relationship
        attributes

        Warnings
        --------
        All :class:`~ciscoconfparse2.models_cisco.IOSIntfLine` methods are still considered beta-quality, until this notice is removed.  The behavior of APIs on this object could change at any time.
        """
        super().__init__(*args, **kwargs)
        self.feature = "interface"

    # This method is on IOSIntfLine()
    @logger.catch(reraise=True)
    def __eq__(self, other):
        return self.get_unique_identifier() == other.get_unique_identifier()

    # This method is on IOSIntfLine()
    @logger.catch(reraise=True)
    def __ne__(self, other):
        return self.get_unique_identifier() != other.get_unique_identifier()

    # This method is on IOSIntfLine()
    @logger.catch(reraise=True)
    def __hash__(self):
        return self.get_unique_identifier()

    # This method is on IOSIntfLine()
    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, index=None, re=re):
        return cls.is_object_for_interface(line)


##
##-------------  IOS Interface Globals
##


@attrs.define(repr=False, slots=False)
class IOSIntfGlobal(BaseFactoryLine):
    # This method is on IOSIntGlobal()
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super(IOSIntfGlobal).__init__(*args, **kwargs)
        self.feature = "interface global"

    # This method is on IOSIntGlobal()
    @logger.catch(reraise=True)
    def __eq__(self, other):
        return self.get_unique_identifier() == other.get_unique_identifier()

    # This method is on IOSIntGlobal()
    @logger.catch(reraise=True)
    def __ne__(self, other):
        return self.get_unique_identifier() != other.get_unique_identifier()

    # This method is on IOSIntGlobal()
    @logger.catch(reraise=True)
    def __hash__(self):
        return self.get_unique_identifier()

    # This method is on IOSIntGlobal()
    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, index=None, re=re):
        raise NotImplementedError()

    # This method is on IOSIntGlobal()
    @property
    @logger.catch(reraise=True)
    def has_cdp_disabled(self):
        raise NotImplementedError()

    # This method is on IOSIntGlobal()
    @property
    @logger.catch(reraise=True)
    def has_intf_logging_def(self):
        raise NotImplementedError()

    # This method is on IOSIntGlobal()
    @property
    @logger.catch(reraise=True)
    def has_stp_portfast_def(self):
        raise NotImplementedError()

    # This method is on IOSIntGlobal()
    @property
    @logger.catch(reraise=True)
    def has_stp_portfast_bpduguard_def(self):
        raise NotImplementedError()

    # This method is on IOSIntGlobal()
    @property
    @logger.catch(reraise=True)
    def has_stp_mode_rapidpvst(self):
        raise NotImplementedError()


#
# -------------  IOS Access Line
#


@attrs.define(repr=False, slots=False)
class IOSAccessLine(BaseFactoryLine):

    # This method is on IOSAccessLine()
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feature = "access line"

    # This method is on IOSAccessLine()
    @logger.catch(reraise=True)
    def __eq__(self, other):
        return self.get_unique_identifier() == other.get_unique_identifier()

    # This method is on IOSAccessLine()
    @logger.catch(reraise=True)
    def __ne__(self, other):
        return self.get_unique_identifier() != other.get_unique_identifier()

    # This method is on IOSAccessLine()
    @logger.catch(reraise=True)
    def __hash__(self):
        return self.get_unique_identifier()

    # This method is on IOSAccessLine()
    @logger.catch(reraise=True)
    def __repr__(self):
        return "<{} # {} '{}' info: '{}'>".format(
            self.classname,
            self.linenum,
            self.name,
            self.range_str,
        )

    # This method is on IOSAccessLine()
    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, index=None, re=re):
        raise NotImplementedError()

    # This method is on IOSAccessLine()
    @property
    @logger.catch(reraise=True)
    def is_accessline(self):
        raise NotImplementedError()

    # This method is on IOSAccessLine()
    @property
    @logger.catch(reraise=True)
    def name(self):
        raise NotImplementedError()

    # This method is on IOSAccessLine()
    @property
    @logger.catch(reraise=True)
    def range_str(self):
        raise NotImplementedError()

    # This method is on IOSAccessLine()
    @property
    @logger.catch(reraise=True)
    def line_range(self):
        raise NotImplementedError()

    # This method is on IOSAccessLine()
    @logger.catch(reraise=True)
    def manual_exectimeout_minutes(self):
        raise NotImplementedError()

    # This method is on IOSAccessLine()
    @logger.catch(reraise=True)
    def manual_exectimeout_seconds(self):
        raise NotImplementedError()

    # This method is on IOSAccessLine()
    @property
    @logger.catch(reraise=True)
    def parse_exectimeout(self):
        raise NotImplementedError()


##
##-------------  Base IOS Route line object
##


@attrs.define(repr=False, slots=False)
class BaseIOSRouteLine(BaseFactoryLine):
    # This method is on BaseIOSRouteLine()
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # This method is on BaseIOSRouteLine()
    @property
    @logger.catch(reraise=True)
    def network_object(self):
        raise NotImplementedError()

    # This method is on BaseIOSRouteLine()
    @logger.catch(reraise=True)
    def __repr__(self):
        return "<{} # {} '{}' info: '{}'>".format(
            self.classname,
            self.linenum,
            self.network_object,
            self.routeinfo,
        )

    # This method is on BaseIOSRouteLine()
    @property
    @logger.catch(reraise=True)
    def routeinfo(self):
        raise NotImplementedError()

    # This method is on BaseIOSRouteLine()
    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, index=None, re=re):
        return False

    # This method is on BaseIOSRouteLine()
    @property
    @logger.catch(reraise=True)
    def vrf(self):
        raise NotImplementedError

    # This method is on BaseIOSRouteLine()
    @property
    @logger.catch(reraise=True)
    def address_family(self):
        ## ipv4, ipv6, etc
        raise NotImplementedError

    # This method is on BaseIOSRouteLine()
    @property
    @logger.catch(reraise=True)
    def network(self):
        raise NotImplementedError

    # This method is on BaseIOSRouteLine()
    @property
    @logger.catch(reraise=True)
    def netmask(self):
        raise NotImplementedError

    # This method is on BaseIOSRouteLine()
    @property
    @logger.catch(reraise=True)
    def admin_distance(self):
        raise NotImplementedError

    # This method is on BaseIOSRouteLine()
    @property
    @logger.catch(reraise=True)
    def nexthop_str(self):
        raise NotImplementedError

    # This method is on BaseIOSRouteLine()
    @property
    @logger.catch(reraise=True)
    def tracking_object_name(self):
        raise NotImplementedError


##
##-------------  IOS Route line object
##

_RE_IP_ROUTE = re.compile(
    r"""^ip\s+route
(?:\s+(?:vrf\s+(?P<vrf>\S+)))?          # VRF detection
\s+
(?P<prefix>\d+\.\d+\.\d+\.\d+)          # Prefix detection
\s+
(?P<netmask>\d+\.\d+\.\d+\.\d+)         # Netmask detection
(?:\s+(?P<nh_intf>[^\d]\S+))?           # NH intf
(?:\s+(?P<nh_addr>\d+\.\d+\.\d+\.\d+))? # NH addr
(?:\s+(?P<dhcp>dhcp))?           # DHCP keyword       (FIXME: add unit test)
(?:\s+(?P<global>global))?       # Global keyword
(?:\s+(?P<ad>\d+))?              # Administrative distance
(?:\s+(?P<mcast>multicast))?     # Multicast Keyword  (FIXME: add unit test)
(?:\s+name\s+(?P<name>\S+))?     # Route name
(?:\s+(?P<permanent>permanent))? # Permanent Keyword  (exclusive of track)
(?:\s+track\s+(?P<track>\d+))?   # Track object (exclusive of permanent)
(?:\s+tag\s+(?P<tag>\d+))?       # Route tag
""",
    re.VERBOSE,
)

_RE_IPV6_ROUTE = re.compile(
    r"""^ipv6\s+route
(?:\s+vrf\s+(?P<vrf>\S+))?
(?:\s+(?P<prefix>{})\/(?P<masklength>\d+))    # Prefix detection
(?:
(?:\s+(?P<nh_addr1>{}))
|(?:\s+(?P<nh_intf>\S+(?:\s+\d\S*?\/\S+)?)(?:\s+(?P<nh_addr2>{}))?)
)
(?:\s+nexthop-vrf\s+(?P<nexthop_vrf>\S+))?
(?:\s+(?P<ad>\d+))?              # Administrative distance
(?:\s+(?:(?P<ucast>unicast)|(?P<mcast>multicast)))?
(?:\s+tag\s+(?P<tag>\d+))?       # Route tag
(?:\s+track\s+(?P<track>\d+))?   # Track object
(?:\s+name\s+(?P<name>\S+))?     # Route name
""".format(
        _IPV6_REGEX_STR_COMPRESSED1,
        _IPV6_REGEX_STR_COMPRESSED2,
        _IPV6_REGEX_STR_COMPRESSED3,
    ),
    re.VERBOSE,
)


@attrs.define(repr=False, slots=False)
class IOSRouteLine(BaseFactoryLine):
    _address_family: str = None
    route_info: dict = None

    # This method is on IOSRouteLine()
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pass

    # This method is on IOSRouteLine()
    @logger.catch(reraise=True)
    def __eq__(self, other):
        return self.get_unique_identifier() == other.get_unique_identifier()

    # This method is on IOSRouteLine()
    @logger.catch(reraise=True)
    def __ne__(self, other):
        return self.get_unique_identifier() != other.get_unique_identifier()

    # This method is on IOSRouteLine()
    @logger.catch(reraise=True)
    def __hash__(self):
        return self.get_unique_identifier()

    # This method is on IOSRouteLine()
    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, index=None, re=re):
        if (line[0:9] == "ip route ") or (line[0:11] == "ipv6 route "):
            return True
        return False

    # This method is on IOSRouteLine()
    @property
    @logger.catch(reraise=True)
    def vrf(self):
        raise NotImplementedError()

    # This method is on IOSRouteLine()
    @property
    @logger.catch(reraise=True)
    def address_family(self):
        raise NotImplementedError()

    # This method is on IOSRouteLine()
    @property
    @logger.catch(reraise=True)
    def network(self):
        raise NotImplementedError()

    # This method is on IOSRouteLine()
    @property
    @logger.catch(reraise=True)
    def netmask(self):
        raise NotImplementedError()

    # This method is on IOSRouteLine()
    @property
    @logger.catch(reraise=True)
    def masklen(self):
        raise NotImplementedError()

    # This method is on IOSRouteLine()
    @property
    @logger.catch(reraise=True)
    def network_object(self):
        raise NotImplementedError()

    # This method is on IOSRouteLine()
    @property
    @logger.catch(reraise=True)
    def nexthop_str(self):
        raise NotImplementedError()

    # This method is on IOSRouteLine()
    @property
    @logger.catch(reraise=True)
    def next_hop_interface(self):
        raise NotImplementedError()

    # This method is on IOSRouteLine()
    @property
    @logger.catch(reraise=True)
    def next_hop_addr(self):
        raise NotImplementedError()

    # This method is on IOSRouteLine()
    @property
    @logger.catch(reraise=True)
    def global_next_hop(self):
        raise NotImplementedError()

    # This method is on IOSRouteLine()
    @property
    @logger.catch(reraise=True)
    def nexthop_vrf(self):
        raise NotImplementedError()

    # This method is on IOSRouteLine()
    @property
    @logger.catch(reraise=True)
    def admin_distance(self):
        raise NotImplementedError()

    # This method is on IOSRouteLine()
    @property
    @logger.catch(reraise=True)
    def multicast(self):
        r"""Return whether the multicast keyword was specified"""
        raise NotImplementedError()

    # This method is on IOSRouteLine()
    @property
    @logger.catch(reraise=True)
    def unicast(self):
        ## FIXME It's unclear how to implement this...
        raise NotImplementedError

    # This method is on IOSRouteLine()
    @property
    @logger.catch(reraise=True)
    def route_name(self):
        raise NotImplementedError()

    # This method is on IOSRouteLine()
    @property
    @logger.catch(reraise=True)
    def permanent(self):
        raise NotImplementedError()

    # This method is on IOSRouteLine()
    @property
    @logger.catch(reraise=True)
    def tracking_object_name(self):
        raise NotImplementedError()

    # This method is on IOSRouteLine()
    @property
    @logger.catch(reraise=True)
    def tag(self):
        raise NotImplementedError()
