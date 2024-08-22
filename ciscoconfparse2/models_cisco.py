from __future__ import absolute_import
from typing import Union, Any, Set, Tuple, List, Dict
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
from ciscoconfparse2.ccp_util import CiscoIOSInterface, CiscoIOSXRInterface
from ciscoconfparse2.ccp_util import IPv4Obj, IPv6Obj
from ciscoconfparse2.ccp_util import CiscoRange
from ciscoconfparse2.ccp_abc import BaseCfgLine

from ciscoconfparse2.models_base import BaseFactoryInterfaceLine
from ciscoconfparse2.models_base import BaseFactoryLine


### HUGE UGLY WARNING:
###   Anything in models_cisco.py could change at any time, until I remove this
###   warning.  I have good reason to believe that these methods are stable and
###   function correctly, but I've been wrong before.  There are no unit tests
###   for this functionality yet, so I consider all this code alpha quality.
###
###   Use models_cisco.py at your own risk.  You have been warned :-)
r""" models_cisco.py - Parse, Query, Build, and Modify IOS-style configurations

     Copyright (C) 2021-2024 David Michael Pennington
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

##
##-------------  Tracking Interface (HSRP, GLBP, VRRP)
##


@attrs.define(repr=False, slots=False)
class TrackingInterface(BaseCfgLine):
    grp: int = None
    intf: BaseCfgLine = None
    decr: int = None
    weight: int = None
    feature = "tracking_interface"
    _group: int = None
    _interface: Any = None
    _decrement: int = None
    _weighting: int = None

    # This method is on TrackingInterface()
    @logger.catch(reraise=True)
    def __init__(self,
                 grp: int,
                 intf: BaseCfgLine,
                 decr: int = 0,
                 weight: int = None):
        """Implement a TrackingInterface() object for Cisco IOS HSRP, GLBP and VRRP"""
        super(TrackingInterface, self).__init__()

        self._group = int(grp)
        self._interface = intf
        self._decrement = decr
        self._weighting = weight

    @property
    def group(self):
        return self._group

    @property
    def interface(self):
        return self._interface

    @property
    def decrement(self):
        return self._decrement

    @property
    def weighting(self):
        return self._weighting

    # This method is on TrackingInterface()
    def __str__(self):
        return f"'{self.name}' group: {self._group}, weighting: {self._weighting}, decrement: {self._decrement}"

    # This method is on TrackingInterface()
    def __repr__(self):
        return f"<TrackingInterface {self.__str__()}>"""

    # This method is on TrackingInterface()
    @logger.catch(reraise=True)
    def __hash__(self):
        """Return a hash value based on the Tracking interface group, interface name and decrement / weighting."""
        if self._name is None or self._group is None:
            error = f"Cannot hash TrackingInterface() {self}"
            logger.critical(error)
            raise ValueError(error)
        else:
            return hash(self.name) * hash(self._group) * hash(self.interface_name) * hash(self._decrement) * hash(self._weighting)

    # This method is on TrackingInterface()
    @logger.catch(reraise=True)
    def __eq__(self, other):
        """Return True or False based on whether this Tracking interface is equal to the other instance; both instances must be a TrackingInterface() instance to compare True"""
        if isinstance(other, TrackingInterface):
            if self.name == other.name and self.group == other.group and self._interface == other._linterface and self._decrement == other._decrement and self._weighting == other._weighting:
                return True
            else:
                return False
        return False

    # This method is on TrackingInterface()
    @property
    @logger.catch(reraise=True)
    def interface_name(self):
        """Return the interface name as a string, or return None"""
        # Derive the interface_name from 'interface GigabitEthernet 5/2'
        # return the name of the interface that owns this TrackingInterface()
        if isinstance(self._interface, (int, str)):
            return str(self._interface)
        else:
            return None

    # This method is on TrackingInterface()
    @property
    @logger.catch(reraise=True)
    def name(self):
        # Derive the interface_name from 'interface GigabitEthernet 5/2'
        # return the name of the interface that owns this TrackingInterface()
        return self.interface_name

    # This method is on TrackingInterface()
    @property
    @logger.catch(reraise=True)
    def interface(self):
        # Derive the interface_name from 'interface GigabitEthernet 5/2'
        # return the name of the interface that owns this TrackingInterface()
        return self.interface_name

    # This method is on TrackingInterface()
    @property
    @logger.catch(reraise=True)
    def tracking_interface_group(self):
        """Return an integer with the TrackingInterface() Group"""
        return int(self._group)

    # This method is on TrackingInterfac3()
    @property
    @logger.catch(reraise=True)
    def decrement(self):
        """Return an integer with the TrackingInterface() decrement or None if there is no decrement."""
        if isinstance(self._decrement, (str, int)) and str(self._decrement) != "":
            return int(self._decrement)
        else:
            return None

    # This method is on TrackingInterface()
    @property
    @logger.catch(reraise=True)
    def weighting(self):
        """Return the weighting (ref GLBP) integer value."""
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production
        # Default HSRP weighting value...
        return None

##
##-------------  HSRP Interface Group
##


@attrs.define(repr=False, slots=False)
class HSRPInterfaceGroup(BaseCfgLine):
    grp: int = 0
    parent_obj: BaseCfgLine = None
    parent: BaseCfgLine = None
    feature: str = "hsrp"
    _group: int = None
    intf_name: str = None

    ##-------------  HSRP

    # This method is on HSRPInterfaceGroup()
    @logger.catch(reraise=True)
    def __init__(self, grp = 0, parent_obj = None):
        """A HSRP Interface Group object"""
        super(HSRPInterfaceGroup, self).__init__()
        if isinstance(parent_obj, BaseCfgLine):
            self.parent = parent_obj
        else:
            raise NotImplementedError()
        self.feature = "hsrp"
        self._group = int(grp)
        self.intf_name = parent_obj

    # This method is on HSRPInterfaceGroup()
    def __str__(self):
        """Return a string representation of this HSRPInterfaceGroup() instance."""
        return f"'{self.interface_name}' version: {self.version}, group: {self.group}, ipv4: {self.ipv4}, has_ipv6: {self.has_ipv6}, priority: {self.priority}, preempt: {self.preempt}, preempt_delay: {self.preempt_delay}, hello_timer: {self.hello_timer}, hold_timer: {self.hold_timer}"

    # This method is on HSRPInterfaceGroup()
    def __repr__(self):
        return f"<HSRPInterfaceGroup {self.__str__()}>"""

    # This method is on HSRPInterfaceGroup()
    @logger.catch(reraise=True)
    def __hash__(self):
        """Return a hash for this HSRPInterfaceGroup() instance."""
        return hash(self.interface_name) * hash(self.group)

    # This method is on HSRPInterfaceGroup()
    @logger.catch(reraise=True)
    def __eq__(self, other):
        """Return True if this HSRPInterfaceGroup() is equal to the other instance or False if the other instance is not an HSRPInterfaceGroup()."""
        if isinstance(other, HSRPInterfaceGroup):
            if self.group == other.group and self.interface_name == other.interface_name:
                return True
            else:
                return False
        return False

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def hsrp_group(self):
        """Return the integer HSRP group number for this HSRPInterfaceGroup() instance."""
        return int(self._group)

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def ip(self):
        """Return the string IPv4 HSRP address for this HSRP group"""
        return self.ipv4

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def ipv4(self):
        """Return the string IPv4 HSRP address for this HSRP group"""
        ipv4 = ""
        for obj in self.parent.children:
            parts = obj.text.lower().strip().split()
            if parts[0] == "standby":
                if len(parts) == 4:
                    # standby 100 ip 172.16.0.1
                    if parts[1].isdigit() and int(parts[1]) == self.group and parts[2] == "ip":
                        ipv4 = parts[3]
                elif len(parts) == 3:
                    # standby ip 172.16.0.1
                    if self.group == 0 and parts[2] == "ip":
                        ipv4 = parts[2]
        return ipv4

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def has_ipv6(self):
        """Return a boolean for whether this interface is configured with an IPv6 HSRP address"""
        # NOTE: I have no intention of checking self.is_shutdown here
        #     People should be able to check the sanity of interfaces
        #     before they put them into production
        return bool(self.ipv6)

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def ipv6(self):
        """Return the string IPv6 HSRP address for this HSRP group"""
        # NOTE: I have no intention of checking self.is_shutdown here
        #     People should be able to check the sanity of interfaces
        #     before they put them into production
        ipv6 = ""
        for obj in self.parent.children:
            parts = obj.text.lower().strip().split()
            if parts[0] == "standby":
                if len(parts) == 4:
                    # standby 100 ipv6 autoconfig
                    if parts[1].isdigit() and int(parts[1]) == self.group and parts[2] == "ipv6":
                        ipv6 = parts[3]
                elif len(parts) == 3:
                    # standby ipv6 autoconfig
                    if self.group == 0 and parts[2] == "ipv6":
                        ipv6 = parts[2]
        return ipv6

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def interface_name(self):
        """Return the string interface name of the interface owning this HSRP group instance."""
        # return the name of the interface that owns this HSRPInterfaceGroup()
        if self.parent is None:
            error = "HSRPInterfaceGroup() parent interface is None"
            logger.critical(error)
            raise ValueError(error)
        return " ".join(self.parent.text.strip().split()[1:])

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def interface_tracking(self):
        """Return a list of HSRP TrackingInterface() objects for this HSRPInterfaceGroup()"""
        return self.get_hsrp_tracking_interfaces()

    # This method is on HSRPInterfaceGroup()
    @logger.catch(reraise=True)
    def get_glbp_tracking_interfaces(self):
        """Get a list of unique GLBP tracked interfaces.  This may never be supported by HSRPInterfaceGroup()"""
        raise NotImplementedError()

    # This method is on HSRPInterfaceGroup()
    @logger.catch(reraise=True)
    def get_vrrp_tracking_interfaces(self):
        """Get a list of unique VRRP tracked interfaces.  This may never be supported by HSRPInterfaceGroup()"""
        raise NotImplementedError()

    # This method is on HSRPInterfaceGroup()
    @logger.catch(reraise=True)
    def get_hsrp_tracking_interfaces(self):
        """Return a list of HSRP TrackingInterface() interfaces for this HSRPInterfaceGroup()"""
        retval = list()
        for obj in self.parent.children:
            parts = obj.text.lower().strip().split()
            if parts[0] == "standby":
                _gg = obj.re_match_iter_typed(
                    r"standby\s(?P<group>\d+)\s+track\s+(?P<intf>\S.+?)(?P<decr>\s+\d+)*\s*$",
                    groupdict={"group": int, "intf": str, "decr": str},
                )
                _hh = obj.re_match_iter_typed(
                    r"standby\s+track\s+(?P<intf>\S.+?)(?P<decr>\s+\d+)*\s*$",
                    groupdict={"intf": str, "decr": str},
                )

                if _gg["group"] == "":
                    hsrp_group = 0
                else:
                    hsrp_group = int(_gg["group"])

                # Default IOS decrement value
                decrement = 10

                if _gg is not None and hsrp_group == self._group:
                    # standby 111 track Dialer0 50
                    interface = _gg["intf"]
                    if isinstance(_gg["decr"], str) and _gg["decr"] != "None":
                        decr_str = _gg["decr"].strip()
                        if decr_str == "":
                            decr_str = "0"
                        decrement = int(decr_str)
                    if interface != "":
                        retval.append(
                            TrackingInterface(
                                grp=int(self._group),
                                intf=interface,
                                decr=decrement,
                                weight=None
                            )
                        )
                elif _hh is not None and self._group == 0:
                    # standby track Dialer0 50
                    interface = _hh["intf"]
                    if isinstance(_hh["decr"], str) and _hh["decr"] != "None":
                        decr_str = _hh["decr"].strip()
                        if decr_str == "":
                            decr_str = "0"
                        decrement = int(decr_str)
                    if interface != "":
                        retval.append(
                            TrackingInterface(
                                grp=int(self._group),
                                intf=interface,
                                decr=decrement,
                                weight=None
                            )
                        )
        return retval

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def group(self):
        """Return the integer HSRP Group for this HSRPInterfaceGroup() instance."""
        # For API simplicity, I always assume there is only one hsrp
        #     group on the interface
        return self._group

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def preempt_delay_minimum(self):
        """Return the configured integer HSRP preempt delay minimum, or 0 if there is none."""
        # NOTE: I have no intention of checking self.is_shutdown here
        #     People should be able to check the sanity of interfaces
        #     before they put them into production
        delay_min = 0
        for obj in self.parent.children:
            parts = obj.text.lower().strip().split()
            if parts[0] == "standby":
                if len(parts) == 6:
                    # standby 100 preempt delay minimum 120
                    if parts[1].isdigit() and int(parts[1]) == self.group and parts[3] == "delay" and parts[4] == "minimum":
                        delay_min = int(parts[5])
                elif len(parts) == 5:
                    # standby preempt delay minimum 120
                    if self.group == 0 and parts[2] == "delay" and parts[3] == "minimum":
                        delay_min = int(parts[4])
        return delay_min

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def preempt_delay(self):
        """Return the configured integer HSRP preempt delay, or 0 if there is none."""
        # NOTE: I have no intention of checking self.is_shutdown here
        #     People should be able to check the sanity of interfaces
        #     before they put them into production
        delay = 0
        for obj in self.parent.children:
            parts = obj.text.lower().strip().split()
            if parts[0] == "standby":
                if len(parts) == 5:
                    # standby 100 preempt delay 120
                    if parts[1].isdigit() and int(parts[1]) == self.group and parts[3] == "delay" and parts[4] != "minimum":
                        delay = int(parts[4])
                elif len(parts) == 4:
                    # standby preempt delay 120
                    if self.group == 0 and parts[2] == "delay" and parts[3] != "minimum":
                        delay = int(parts[3])

        delay_minimum = self.preempt_delay_minimum
        if delay_minimum > delay:
            return delay_minimum
        else:
            return delay

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def hello_timer(self):
        """Return the configured integer HSRP hello timer, or the HSRP default of 3 if there is no explicit hello timer."""
        # NOTE: I have no intention of checking self.is_shutdown here
        #     People should be able to check the sanity of interfaces
        #     before they put them into production
        for obj in self.parent.children:
            obj_parts = obj.text.lower().strip().split()
            if obj_parts[0:4] == ["standby", str(self._group), "timers", "msec"]:
                return float(obj_parts[4]) / 1000.0
            elif obj_parts[0:3] == ["standby", str(self._group), "timers"]:
                return int(obj_parts[-2])
        # The default hello timer is 3 seconds...
        return 3

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def hold_timer(self):
        """Return the configured integer HSRP hold timer, or the HSRP default of 10 if there is no explicit hold timer."""
        # NOTE: I have no intention of checking self.is_shutdown here
        #     People should be able to check the sanity of interfaces
        #     before they put them into production
        for obj in self.parent.children:
            obj_parts = obj.text.lower().strip().split()
            if obj_parts[0:2] == ["standby", str(self._group)] and obj_parts[-2] == "msec":
                return float(obj_parts[-1]) / 1000.0
            elif obj_parts[0:3] == ["standby", str(self._group), "timers"]:
                return int(obj_parts[-1])
        # The default hold timer is 10 seconds...
        return 10

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def priority(self):
        """Return the configured integer HSRP priority, or the HSRP default of 100 if there is no explicit HSRP priority configured."""
        for obj in self.parent.children:
            obj_parts = obj.text.lower().strip().split()
            if obj_parts[0:3] == ["standby", str(self._group), "priority"]:
                return int(obj_parts[3])
        # The default priority is 100...
        return 100

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def version(self):
        """Return the configured integer HSRP version, or the HSRP default of 1 if there is no explicit HSRP version configured."""
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production
        for obj in self.parent.children:
            obj_parts = obj.text.lower().strip().split()
            if obj_parts[0:2] == ["standby", "version"]:
                return int(obj_parts[-1])
        # default to version 1...
        return 1

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def has_hsrp_track(self):
        return any(self.interface_tracking)

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def use_bia(self):
        """Return True if the router is configured with `standby use-bia`; `standby use-bia` helps avoid instability when introducing new HSRP routers.  Return False if the router is not configured with `standby use-bia`."""
        for obj in self.parent.children:
            if "use-bia" in obj.text:
                return True
        return False

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def preempt(self):
        """Return True if the router is configured to preempt for this HSRP Group; otherwise return False."""
        ## For API simplicity, I always assume there is only one hsrp
        ##     group on the interface
        for obj in self.parent.children:
            obj_parts = obj.text.lower().strip().split()
            if obj_parts[0:3] == ["standby", str(self._group), "preempt"]:
                return True
        return False

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def authentication_md5_keychain(self):
        """Return the string text of the MD5 key-chain if this HSRP group is configured with an MD5 authentication key-chain; otherwise return an empty string."""
        ## For API simplicity, I always assume there is only one hsrp
        ##     group on the interface
        retval = self.re_match_iter_typed(
            r"^\s*standby\s+{self.group}\s+authentication\s+md5\s+key-chain\s+(\S+)",
            group=1,
            result_type=str,
            default="",
        )
        return retval

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def has_authentication_md5(self):
        """Return True if the router is configured with an MD5 key-chain; otherwise return False."""
        keychain = self.authentication_md5_keychain
        return bool(keychain)

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def hsrp_authentication_cleartext(self):
        pass

##
##-------------  IOS Configuration line object
##


@attrs.define(repr=False, slots=False)
class IOSCfgLine(BaseFactoryLine):
    """An object for a parsed IOS-style configuration line.
    :class:`~ciscoconfparse2.models_cisco.IOSCfgLine` objects contain
    references to other parent and child
    :class:`~ciscoconfparse2.models_cisco.IOSCfgLine` objects.

    Parameters
    ----------
    line : str
        A string containing a text copy of the IOS configuration line.  :class:`~ciscoconfparse2.CiscoConfParse` will automatically identify the parent and children (if any) when it parses the configuration.

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

    Returns
    -------
    An instance of :class:`~ciscoconfparse2.models_cisco.IOSCfgLine`.

    """

    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        r"""Accept an IOS line number and initialize family relationship attributes"""
        super(IOSCfgLine, self).__init__(*args, **kwargs)

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
    def from_list(cls, *list_of_args) -> BaseCfgLine:
        """Helper-method to allow strictly positional *arg calls .i.e. IOSCfgLine([], 'hostname Foo')"""
        return cls(list_of_args)

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, index=None, re=re) -> bool:
        """Return True if this object should be used for a given configuration line; otherwise return False"""
        ## Default object, for now
        if cls.is_object_for_hostname(line=line):
            return False
        elif cls.is_object_for_interface(line=line):
            return False
        elif cls.is_object_for_aaa_authentication(line=line):
            return False
        elif cls.is_object_for_aaa_authorization(line=line):
            return False
        elif cls.is_object_for_aaa_accounting(line=line):
            return False
        elif cls.is_object_for_ip_route(line=line):
            return False
        elif cls.is_object_for_ipv6_route(line=line):
            return False
        else:
            return True

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for_hostname(cls, line) -> bool:
        if isinstance(line, str):
            line_parts = line.strip().split()
            if len(line_parts) > 0 and line_parts[0] == "hostname":
                return True
        return False

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for_interface(cls, line) -> bool:
        if isinstance(line, str):
            line_parts = line.strip().split()
            if len(line_parts) > 0 and line_parts[0] == "interface":
                return True
        return False

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for_aaa_authentication(cls, line) -> bool:
        """Return True if this is an object for aaa authentication.  Be sure to reject 'aaa new-model'"""
        if isinstance(line, str):
            line_parts = line.strip().split()
            if len(line_parts) > 0 and line_parts[0:2] == ["aaa", "authentication"]:
                return True
        return False

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for_aaa_authorization(cls, line) -> bool:
        """Return True if this is an object for aaa authorization.  Be sure to reject 'aaa new-model'"""
        if isinstance(line, str):
            line_parts = line.strip().split()
            if len(line_parts) > 0 and line_parts[0:2] == ["aaa", "authorization"]:
                return True
        return False

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for_aaa_accounting(cls, line) -> bool:
        """Return True if this is an object for aaa accounting.  Be sure to reject 'aaa new-model'"""
        if isinstance(line, str):
            line_parts = line.strip().split()
            if len(line_parts) > 0 and line_parts[0:2] == ["aaa", "accounting"]:
                return True
        return False

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for_ip_route(cls, line) -> bool:
        if isinstance(line, str):
            line_parts = line.strip().split()
            if len(line_parts) > 0 and line_parts[0:2] == ["ip", "route"]:
                return True
        return False

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for_ipv6_route(cls, line) -> bool:
        if isinstance(line, str):
            line_parts = line.strip().split()
            if len(line_parts) > 0 and line_parts[0:2] == ["ipv6", "route"]:
                return True
        return False

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

        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 18,21

           >>> from ciscoconfparse2 import CiscoConfParse
           >>> config = [
           ...     '!',
           ...     'interface Serial1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     '!',
           ...     'interface ATM2/0',
           ...     ' no ip address',
           ...     '!',
           ...     'interface ATM2/0.100 point-to-point',
           ...     ' ip address 1.1.1.5 255.255.255.252',
           ...     ' pvc 0/100',
           ...     '  vbr-nrt 704 704',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config)
           >>> obj = parse.find_objects('^interface\sSerial')[0]
           >>> obj.is_intf
           True
           >>> obj = parse.find_objects('^interface\sATM')[0]
           >>> obj.is_intf
           True
           >>>
        """
        if self.text[0:10] == "interface " and self.text[10] != " ":
            return True
        return False

    @property
    @logger.catch(reraise=True)
    def is_subintf(self) -> bool:
        r"""
        :return: Returns a boolean (True or False) to answer whether this
                 :class:`ciscoconfparse2.models_base.BaseFactoryLine` is a subinterface.
        :rtype: bool

        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 18,21

           >>> from ciscoconfparse2 import CiscoConfParse
           >>> config = [
           ...     '!',
           ...     'interface Serial1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     '!',
           ...     'interface ATM2/0',
           ...     ' no ip address',
           ...     '!',
           ...     'interface ATM2/0.100 point-to-point',
           ...     ' ip address 1.1.1.5 255.255.255.252',
           ...     ' pvc 0/100',
           ...     '  vbr-nrt 704 704',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config)
           >>> obj = parse.find_objects(r'^interface\sSerial')[0]
           >>> obj.is_subintf
           False
           >>> obj = parse.find_objects(r'^interface\sATM')[0]
           >>> obj.is_subintf
           True
           >>>
        """
        intf_regex = r"^interface\s+(\S+?\.\d+)"
        if self.re_match(intf_regex):
            return True
        return False

    _VIRTUAL_INTF_REGEX_STR = (
        r"""^interface\s+(Loopback|Vlan|Tunnel|Dialer|Virtual-Template|Port-Channel)"""
    )
    _VIRTUAL_INTF_REGEX = re.compile(_VIRTUAL_INTF_REGEX_STR, re.I)

    @property
    @logger.catch(reraise=True)
    def is_virtual_intf(self) -> bool:
        if self.re_match(self._VIRTUAL_INTF_REGEX):
            return True
        return False

    @property
    @logger.catch(reraise=True)
    def is_loopback_intf(self) -> bool:
        r"""
        :return: Returns a boolean (True or False) to answer whether this
                 :class:`ciscoconfparse2.models_base.BaseFactoryLine` is a loopback interface.
        :rtype: bool

        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 13,16

           >>> from ciscoconfparse2 import CiscoConfParse
           >>> config = [
           ...     '!',
           ...     'interface FastEthernet1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     '!',
           ...     'interface Loopback0',
           ...     ' ip address 1.1.1.5 255.255.255.255',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config)
           >>> obj = parse.find_objects(r'^interface\sFast')[0]
           >>> obj.is_loopback_intf
           False
           >>> obj = parse.find_objects(r'^interface\sLoop')[0]
           >>> obj.is_loopback_intf
           True
           >>>
        """
        intf_regex = r"^interface\s+(\Soopback)"
        if self.re_match(intf_regex):
            return True
        return False

    @property
    @logger.catch(reraise=True)
    def is_ethernet_intf(self) -> bool:
        r"""
        :return: Returns a boolean (True or False) to answer whether this
                 :class:`ciscoconfparse2.models_base.BaseFactoryLine` is an ethernet interface.  Any ethernet interface
                 (10M and up) is considered an ethernet interface.
        :rtype: bool

        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 18,21

           >>> from ciscoconfparse2 import CiscoConfParse
           >>> config = [
           ...     '!',
           ...     'interface FastEthernet1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     '!',
           ...     'interface ATM2/0',
           ...     ' no ip address',
           ...     '!',
           ...     'interface ATM2/0.100 point-to-point',
           ...     ' ip address 1.1.1.5 255.255.255.252',
           ...     ' pvc 0/100',
           ...     '  vbr-nrt 704 704',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config)
           >>> obj = parse.find_objects('^interface\sFast')[0]
           >>> obj.is_ethernet_intf
           True
           >>> obj = parse.find_objects('^interface\sATM')[0]
           >>> obj.is_ethernet_intf
           False
           >>>
        """
        intf_regex = r"^interface\s+(.*?\Sthernet)"
        if self.re_match(intf_regex):
            return True
        return False

    @property
    @logger.catch(reraise=True)
    def is_in_portchannel(self) -> bool:
        r"""
        :return: Return a boolean indicating whether this port is configured in a port-channel
        :rtype: bool
        """
        retval = self.re_match_iter_typed(
            r"^\s*channel-group\s+(\d+)", result_type=bool, default=False
        )
        return retval

    @property
    @logger.catch(reraise=True)
    def portchannel_number(self) -> bool:
        r"""

        :return: Return an integer for the port-channel which it's configured in, default to -1
        :rtype: int
        """
        retval = self.re_match_iter_typed(
            r"^\s*channel-group\s+(\d+)", result_type=int, default=-1
        )
        return retval

    @property
    @logger.catch(reraise=True)
    def is_portchannel_intf(self) -> bool:
        r"""
        :return: Return a boolean indicating whether this port is a port-channel intf
        :rtype: bool
        """
        return "channel" in self.name.lower()


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
class BaseIOSIntfLine(IOSCfgLine, BaseFactoryInterfaceLine):
    ifindex: str = None
    default_ipv4_addr_object: Any = None
    default_ipv6_addr_object: Any = None

    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super(BaseIOSIntfLine, self).__init__(*args, **kwargs)
        self.ifindex = None  # Optional, for user use
        self.default_ipv4_addr_object = IPv4Obj()
        self.default_ipv6_addr_object = IPv6Obj()

    # This method is on BaseIOSIntfLine()
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

    # This method is on BaseIOSIntfLine()
    @logger.catch(reraise=True)
    def _build_abbvs(self) -> set[str]:
        r"""
        :return: a set of valid abbreviations (lowercased) for the interface
        :rtype: set[str]
        """
        retval = set([])
        port_type = self.port_type.lower()
        subinterface_number = self.subinterface_number
        for sep in ["", " "]:
            for ii in range(1, len(port_type) + 1):
                retval.add(f"{port_type[0:ii]}{sep}{subinterface_number}")
        return retval

    # This method is on BaseIOSIntfLine()
    @logger.catch(reraise=True)
    def get_hsrp_groups(self) -> List[HSRPInterfaceGroup]:
        """
        :return: the sequence of configured HSRPInterfaceGroup() instances
        :rtype: List[HSRPInterfaceGroup]
        """
        retval = set()
        for obj in self.children:
            # Get each HSRP group number...
            tmp = obj.text.split()
            if tmp[0] == "standby" and tmp[1] == "ip":
                retval.add(HSRPInterfaceGroup(grp=0, parent_obj=self))
            elif tmp[0] == "standby" and tmp[2] == "ip":
                group = int(tmp[1])
                retval.add(HSRPInterfaceGroup(grp=group, parent_obj=self))
        # Return a sorted list of HSRPInterfaceGroup() instances...
        intf_groups = sorted(retval, key=lambda x: x.group, reverse=False)
        return intf_groups

    # This method is on BaseIOSIntfLine()
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

    # This method is on BaseIOSIntfLine()
    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, index=None, re=re) -> bool:
        return False

    ##-------------  Basic interface properties

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def abbvs(self) -> set[str]:
        r"""A python set of valid abbreviations (lowercased) for the interface"""
        return self._build_abbvs()

    _INTF_NAME_RE_STR = r"^interface\s+(\S+[0-9\/\.\s]+)\s*"
    _INTF_NAME_REGEX = re.compile(_INTF_NAME_RE_STR)

    @property
    def cisco_interface_object(self) -> Union[CiscoIOSInterface, CiscoIOSXRInterface]:
        """Return a CiscoIOSInterface() instance for this interface

        :return: The interface name as a CiscoIOSInterface() / CiscoIOSXRInterface() instance, or '' if the object is not an interface.  The CiscoIOSInterface instance can be transparently cast as a string into a typical Cisco IOS name.
        :rtype: Union[CiscoIOSInterface, CiscoIOSXRInterface]
        """
        if not self.is_intf:
            error = f"`{self.text}` is not a valid Cisco interface"
            logger.error(error)
            raise InvalidCiscoInterface(error)
        return CiscoIOSInterface("".join(self.text.split()[1:]))

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def name(self) -> str:
        r"""
        :return: The interface name as a string, such as 'GigabitEthernet0/1'
        :rtype: str

        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 17,20,23

           >>> from ciscoconfparse2 import CiscoConfParse
           >>> config = [
           ...     '!',
           ...     'interface FastEthernet1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     '!',
           ...     'interface ATM2/0',
           ...     ' no ip address',
           ...     '!',
           ...     'interface ATM2/0.100 point-to-point',
           ...     ' ip address 1.1.1.5 255.255.255.252',
           ...     ' pvc 0/100',
           ...     '  vbr-nrt 704 704',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config, factory=True)
           >>> obj = parse.find_objects('^interface\sFast')[0]
           >>> obj.name
           'FastEthernet1/0'
           >>> obj = parse.find_objects('^interface\sATM')[0]
           >>> obj.name
           'ATM2/0'
           >>> obj = parse.find_objects('^interface\sATM')[1]
           >>> obj.name
           'ATM2/0.100'
           >>>
        """
        return " ".join(self.text.split()[1:])

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def port(self) -> int:
        r"""
        :return: The interface's port number
        :rtype: int

        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 17,20

           >>> from ciscoconfparse2 import CiscoConfParse
           >>> config = [
           ...     '!',
           ...     'interface FastEthernet1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     '!',
           ...     'interface ATM2/0',
           ...     ' no ip address',
           ...     '!',
           ...     'interface ATM2/0.100 point-to-point',
           ...     ' ip address 1.1.1.5 255.255.255.252',
           ...     ' pvc 0/100',
           ...     '  vbr-nrt 704 704',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config, factory=True)
           >>> obj = parse.find_objects('^interface\sFast')[0]
           >>> obj.port
           0
           >>> obj = parse.find_objects('^interface\sATM')[0]
           >>> obj.port
           0
           >>>
        """
        return self.cisco_interface_object.port

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def port_type(self) -> str:
        r"""

        :return: The port type: Loopback, ATM, GigabitEthernet, Virtual-Template, etc...
        :rtype: str

        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 17,20

           >>> from ciscoconfparse2 import CiscoConfParse
           >>> config = [
           ...     '!',
           ...     'interface FastEthernet1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     '!',
           ...     'interface ATM2/0',
           ...     ' no ip address',
           ...     '!',
           ...     'interface ATM2/0.100 point-to-point',
           ...     ' ip address 1.1.1.5 255.255.255.252',
           ...     ' pvc 0/100',
           ...     '  vbr-nrt 704 704',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config, factory=True)
           >>> obj = parse.find_objects('^interface\sFast')[0]
           >>> obj.port_type
           'FastEthernet'
           >>> obj = parse.find_objects('^interface\sATM')[0]
           >>> obj.port_type
           'ATM'
           >>>
        """
        port_type_regex = r"^interface\s+([A-Za-z\-]+)"
        return self.re_match(port_type_regex, group=1, default="")

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ordinal_list(self) -> tuple[int, ...]:
        r"""

        :return: Return a tuple of integers representing card, slot, port for this interface.  If you call ordinal_list on GigabitEthernet2/25.100, you'll get this python tuple of integers: (2, 25).  If you call ordinal_list on GigabitEthernet2/0/25.100 you'll get this python list of integers: (2, 0, 25).  This method strips all subinterface information in the returned value.
        :rtype: tuple[int, ...]

        .. warning::

           ordinal_list should silently fail (returning an empty python tuple) if the interface doesn't parse correctly

        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 17,20

           >>> from ciscoconfparse2 import CiscoConfParse
           >>> config = [
           ...     '!',
           ...     'interface FastEthernet1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     '!',
           ...     'interface ATM2/0',
           ...     ' no ip address',
           ...     '!',
           ...     'interface ATM2/0.100 point-to-point',
           ...     ' ip address 1.1.1.5 255.255.255.252',
           ...     ' pvc 0/100',
           ...     '  vbr-nrt 704 704',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config, factory=True)
           >>> obj = parse.find_objects('^interface\sFast')[0]
           >>> obj.ordinal_list
           (1, 0)
           >>> obj = parse.find_objects('^interface\sATM')[0]
           >>> obj.ordinal_list
           (2, 0)
           >>>
        """
        if not self.is_intf:
            return ()
        else:
            ifobj = self.cisco_interface_object
            retval = []
            static_list = (
                ifobj.slot, ifobj.card, ifobj.port,
                ifobj.subinterface, ifobj.channel, ifobj.interface_class
            )
            if ifobj:
                for ii in static_list:
                    if isinstance(ii, int):
                        retval.append(ii)
                    else:
                        retval.append(-1)
                return tuple(retval)
            else:
                return ()

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def interface_number(self) -> str:
        r"""

        :return: Return a string representing the card, slot, port for this interface.  If you call interface_number on GigabitEthernet2/25.100, you'll get this python string: '2/25'.  If you call interface_number on GigabitEthernet2/0/25.100 you'll get this python string '2/0/25'.  This method strips all subinterface information in the returned value.
        :rtype: str

        .. warning::

           interface_number should silently fail (returning an empty python string) if the interface doesn't parse correctly

        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 17,20

           >>> from ciscoconfparse2 import CiscoConfParse
           >>> config = [
           ...     '!',
           ...     'interface FastEthernet1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     '!',
           ...     'interface ATM2/0',
           ...     ' no ip address',
           ...     '!',
           ...     'interface ATM2/0.100 point-to-point',
           ...     ' ip address 1.1.1.5 255.255.255.252',
           ...     ' pvc 0/100',
           ...     '  vbr-nrt 704 704',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config, factory=True)
           >>> obj = parse.find_objects('^interface\sFast')[0]
           >>> obj.interface_number
           '1/0'
           >>> obj = parse.find_objects('^interface\sATM')[-1]
           >>> obj.interface_number
           '2/0'
           >>>
        """
        if not self.is_intf:
            return ""
        else:
            intf_regex = r"^interface\s+[A-Za-z\-]+\s*(\d+.*?)(\.\d+)*(\s\S+)*\s*$"
            intf_number = self.re_match(intf_regex, group=1, default="")
            return intf_number

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def subinterface_number(self) -> str:
        r"""

        :return: Return a string representing the card, slot, port for this interface or subinterface.  If you call subinterface_number on GigabitEthernet2/25.100, you'll get this python string: '2/25.100'.  If you call interface_number on GigabitEthernet2/0/25 you'll get this python string '2/0/25'.  This method strips all subinterface information in the returned value.
        :rtype: str

        .. warning::

           subinterface_number should silently fail (returning an empty python string) if the interface doesn't parse correctly

        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 17,20

           >>> from ciscoconfparse2 import CiscoConfParse
           >>> config = [
           ...     '!',
           ...     'interface FastEthernet1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     '!',
           ...     'interface ATM2/0',
           ...     ' no ip address',
           ...     '!',
           ...     'interface ATM2/0.100 point-to-point',
           ...     ' ip address 1.1.1.5 255.255.255.252',
           ...     ' pvc 0/100',
           ...     '  vbr-nrt 704 704',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config, factory=True)
           >>> obj = parse.find_objects('^interface\sFast')[0]
           >>> obj.subinterface_number
           '1/0'
           >>> obj = parse.find_objects('^interface\sATM')[-1]
           >>> obj.subinterface_number
           '2/0.100'
           >>>
        """
        if not self.is_intf:
            return ""
        else:
            subintf_regex = r"^interface\s+[A-Za-z\-]+\s*(\d+.*?\.?\d?)(\s\S+)*\s*$"
            subintf_number = self.re_match(subintf_regex, group=1, default="")
            return subintf_number

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def description(self) -> str:
        r"""
        :return: Return the current interface description string, default to ''.
        :rtype: str
        """
        retval = self.re_match_iter_typed(
            r"^\s*description\s+(\S.*)$", result_type=str, default=""
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_bandwidth(self) -> int:
        r"""
        :return: Return the integer bandwidth, default to -1
        :rtype: int
        """
        retval = self.re_match_iter_typed(
            r"^\s*bandwidth\s+(\d+)$", result_type=int, default=-1
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_delay(self) -> int:
        r"""
        :return: Return the integer delay
        :rtype: int
        """
        retval = self.re_match_iter_typed(
            r"^\s*delay\s+(\d+)$", result_type=int, default=-1
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_holdqueue_out(self) -> int:
        r"""
        :return: Return the current hold-queue out depth, default to -1
        :rtype: int
        """
        retval = self.re_match_iter_typed(
            r"^\s*hold-queue\s+(\d+)\s+out$", result_type=int, default=-1
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_holdqueue_in(self) -> int:
        r"""
        :return: Return the current hold-queue int depth, default to -1
        :rtype: int
        """
        retval = self.re_match_iter_typed(
            r"^\s*hold-queue\s+(\d+)\s+in$", result_type=int, default=-1
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_encapsulation(self) -> str:
        r"""
        :return: Return the current encapsulation (i.e. ppp, hdlc, ethernet, etc...), default to ''
        :rtype: str
        """
        retval = self.re_match_iter_typed(
            r"^\s*encapsulation\s+(\S+)", result_type=str, default=""
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_mpls(self) -> bool:
        r"""
        :return: Whether this interface is configured with MPLS
        :rtype: bool
        """
        retval = self.re_match_iter_typed(
            r"^\s*(mpls\s+ip)$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_addr_object(self) -> IPv4Obj:
        r"""
        :return: A :class:`ccp_util.IPv4Obj` object representing the address on this interface, default to IPv4Obj()
        :rtype: IPv4Obj
        """
        retval = self.re_match_iter_typed(
            r"^\s+ip\s+address\s+(?P<v4addr>\S+)\s+(?P<v4netmask>\d+\.\d+\.\d+\.\d+)",
            groupdict={"v4addr": str, "v4netmask": str},
            default="",
        )

        if retval["v4addr"] == "":
            return self.default_ipv4_addr_object
        elif retval["v4addr"] == "dhcp":
            return self.default_ipv4_addr_object
        elif retval["v4addr"] == "negotiated":
            return self.default_ipv4_addr_object
        else:
            return IPv4Obj(f"{retval['v4addr']}/{retval['v4netmask']}")

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv6_addr_objects(self) -> Dict[str,List[IPv6Obj]]:
        r"""
        :return: A Dict of :class:`ccp_util.IPv6Obj` objects representing the addresss on this interface, default to {}
        :rtype: IPv6Obj
        """
        v6_globals = self.re_list_iter_typed(
            r"^\s+ipv6\s+address\s+(?P<v6addr>\S+?)\/(?P<v6masklength>\d+)",
            groupdict={"v6addr": str, "v6masklength": str},
            result_type=IPv6Obj
        )
        return {"globals": v6_globals}

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ip_secondary_addresses(self) -> set[str]:
        r"""
        :return: Return a set of IPv4 secondary addresses (as strings), default to an empty set
        :rtype: set[str]
        """
        retval = set()
        for obj in self.parent.all_children:
            _gg = obj.re_match_iter_typed(
                r"^\s*ip\s+address\s+(?P<secondary>\S+\s+\S+)\s+secondary\s*$",
                groupdict={"secondary": IPv4Obj},
                default=False
            )
            if _gg["secondary"]:
                retval.add(str(_gg["secondary"].ip))
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ip_secondary_networks(self) -> set[str]:
        r"""
        :return: Return a set of IPv4 network / prefixlen (as strings), default to an empty set
        :rtype: set[str]
        """
        retval = set()
        for obj in self.parent.all_children:
            _gg = obj.re_match_iter_typed(
                r"^\s*ip\s+address\s+(?P<secondary>\S+\s+\S+)\s+secondary\s*$",
                groupdict={"secondary": IPv4Obj},
                default=False
            )
            if _gg["secondary"]:
                retval.add(f"{_gg['secondary'].ip}/{_gg['secondary'].prefixlen}")
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ip(self) -> IPv4Obj:
        r"""
        :return: A :class:`ccp_util.IPv4Obj` object representing the IPv4 address on this interface, default to IPv4Obj()
        :rtype: IPv4Obj
        """
        return self.ipv4_addr_object

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv4(self) -> IPv4Obj:
        r"""
        :return: A :class:`ccp_util.IPv4Obj` object representing the IPv4 address on this interface, default to IPv4Obj()
        :rtype: IPv4Obj
        """
        return self.ipv4_addr_object

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_network_object(self) -> IPv4Obj:
        r"""
        :return: A :class:`ccp_util.IPv4Obj` object representing the IPv4 subnet on this interface, default to IPv4Obj()
        :rtype: IPv4Obj
        """
        return self.ip_network_object

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ip_network_object(self) -> IPv4Obj:
        r"""
        :return: A :class:`ccp_util.IPv4Obj` object representing the IPv4 subnet on this interface, default to IPv4Obj()
        :rtype: IPv4Obj
        """
        # Simplified on 2014-12-02
        try:
            return IPv4Obj(f"{self.ipv4_addr}/{self.ipv4_mask}", strict=False)
        except DynamicAddressException as e:
            raise DynamicAddressException(e)
        except BaseException:
            return self.default_ipv4_addr_object

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_autonegotiation(self) -> bool:
        r"""
        :return: Whether autonegotiation is enabled on this interface
        :rtype: bool
        """
        if not self.is_ethernet_intf:
            return False
        elif self.is_ethernet_intf and (
            self.manual_speed != "" and self.manual_duplex != ""
        ):
            return False
        elif self.is_ethernet_intf:
            return True
        else:
            raise ValueError

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_carrierdelay(self) -> float:
        r"""
        :return: The manual carrier delay (in seconds) of the interface as a python float, default to -1.0
        :rtype: float
        """
        cd_seconds = self.re_match_iter_typed(
            r"^\s*carrier-delay\s+(\d+)$", result_type=float, default=-1.0
        )
        cd_msec = self.re_match_iter_typed(
            r"^\s*carrier-delay\s+msec\s+(\d+)$", result_type=float, default=-1.0
        )

        if cd_seconds > -1.0:
            return cd_seconds
        elif cd_msec > -1.0:
            return cd_msec / 1000.0
        else:
            return -1.0

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_clock_rate(self) -> int:
        r"""
        :return: Return the clock rate of the interface as a python integer, default to -1
        :rtype: int
        """
        retval = self.re_match_iter_typed(
            r"^\s*clock\s+rate\s+(\d+)$", result_type=int, default=-1
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_mtu(self) -> int:
        ## Due to the diverse platform defaults, this should be the
        ##    only mtu information I plan to support
        r"""
        :return: Return the manual MTU of the interface as a python integer, default to -1
        :rtype: int

        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 18,21

           >>> from ciscoconfparse2 import CiscoConfParse
           >>> config = [
           ...     '!',
           ...     'interface FastEthernet1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     '!',
           ...     'interface ATM2/0',
           ...     ' mtu 4470',
           ...     ' no ip address',
           ...     '!',
           ...     'interface ATM2/0.100 point-to-point',
           ...     ' ip address 1.1.1.5 255.255.255.252',
           ...     ' pvc 0/100',
           ...     '  vbr-nrt 704 704',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config, factory=True)
           >>> obj = parse.find_objects('^interface\sFast')[0]
           >>> obj.manual_mtu
           -1
           >>> obj = parse.find_objects('^interface\sATM')[0]
           >>> obj.manual_mtu
           4470
           >>>
        """
        retval = self.re_match_iter_typed(
            r"^\s*mtu\s+(\d+)$", result_type=int, default=-1
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_mpls_mtu(self) -> int:
        ## Due to the diverse platform defaults, this should be the
        ##    only mtu information I plan to support
        r"""
        :return: Return the manual MPLS MTU of the interface as a python integer, default to -1
        :rtype: int
        """
        retval = self.re_match_iter_typed(
            r"^\s*mpls\s+mtu\s+(\d+)$", result_type=int, default=-1
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_ip_mtu(self) -> int:
        ## Due to the diverse platform defaults, this should be the
        ##    only mtu information I plan to support
        r"""
        :return: Return the manual IP MTU of the interface as a python integer, default to -1
        :rtype: int
        """
        retval = self.re_match_iter_typed(
            r"^\s*ip\s+mtu\s+(\d+)$", result_type=int, default=-1
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_ipv6_mtu(self) -> int:
        ## Due to the diverse platform defaults, this should be the
        ##    only mtu information I plan to support
        r"""
        :return: Return the manual IPv6 MTU of the interface as a python integer, default to -1
        :rtype: int
        """
        retval = self.re_match_iter_typed(
            r"^\s*ipv6\s+mtu\s+(\d+)$", result_type=int, default=-1
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_speed(self) -> int:
        r"""
        :return: Return the manual speed of the interface as a python integer, default to -1
        :rtype: int
        """
        retval = self.re_match_iter_typed(
            r"^\s*speed\s+(\d+)$", result_type=int, default=-1
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_duplex(self) -> str:
        r"""
        :return: Return the manual duplex of the interface as a python integer, default to ''
        :rtype: str
        """
        retval = self.re_match_iter_typed(
            r"^\s*duplex\s+(\S.+)$", result_type=str, default=""
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def is_shutdown(self) -> bool:
        r"""
        :return: Whether the interface is shutdown
        :rtype: bool
        """
        retval = self.re_match_iter_typed(
            r"^\s*(shut\S*)\s*$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def vrf(self) -> str:
        r"""
        :return: The name of the VRF configured on the interface, default to ''
        :rtype: str
        """
        retval = self.re_match_iter_typed(
            r"^\s*(ip\s+)*vrf\sforwarding\s(\S+)$", result_type=str, group=2, default=""
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ip_addr(self) -> str:
        r"""
        :return: The IP address configured on the interface, default to ''
        :rtype: str
        """
        return self.ipv4_addr

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_addr(self) -> str:
        r"""
        :return: The IP address configured on the interface, default to ''
        :rtype: str
        """
        retval = self.re_match_iter_typed(
            r"^\s+ip\s+address\s+(\d+\.\d+\.\d+\.\d+)\s+\d+\.\d+\.\d+\.\d+\s*$",
            result_type=str,
            default="",
        )
        condition1 = self.re_match_iter_typed(
            r"^\s+ip\s+address\s+(dhcp)\s*$", result_type=str, default=""
        )
        condition2 = self.re_match_iter_typed(
            r"^\s+ip\s+address\s+(negotiated)\s*$", result_type=str, default=""
        )
        if condition1.lower() == "dhcp":
            return ""
        elif condition2.lower() == "negotiated":
            return ""
        else:
            return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_netmask(self) -> str:
        r"""
        :return: The IP netmask configured on the interface, default to ''
        :rtype: str
        """
        retval = self.re_match_iter_typed(
            r"^\s+ip\s+address\s+\d+\.\d+\.\d+\.\d+\s+(\d+\.\d+\.\d+\.\d+)\s*$",
            result_type=str,
            default="",
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_masklength(self) -> int:
        r"""
        :return: Return an integer with the interface's IPv4 mask length, default to -1
        :rtype: int
        """
        ipv4_addr_object = self.ipv4_addr_object
        if ipv4_addr_object != self.default_ipv4_addr_object:
            return ipv4_addr_object.prefixlen
        return -1

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv6_addr(self) -> str:
        r"""
        :return: The IPv6 address configured on the interface, default to ''
        :rtype: str
        """
        retval = self.re_match_iter_typed(
            r"^\s+ipv6\s+address\s+(?P<v6addr>[^\/]+)",
            result_type=str,
            default="",
        )
        condition1 = self.re_match_iter_typed(
            r"^\s+ipv6\s+address\s+(dhcp)\s*$", result_type=str, default=""
        )
        condition2 = self.re_match_iter_typed(
            r"^\s+ipv6\s+address\s+(autoconfig)\s*$", result_type=str, default=""
        )
        condition3 = self.re_match_iter_typed(
            r"^\s+ipv6\s+address\s+(negotiated)\s*$", result_type=str, default=""
        )
        if condition1.lower() == "dhcp":
            return ""
        elif condition2.lower() == "autoconfig":
            return ""
        elif condition3.lower() == "negotiated":
            return ""
        else:
            return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv6_masklength(self) -> int:
        r"""
        :return: The IPv6 masklength configured on the interface, default to -1
        :rtype: int
        """
        ipv6_addr_object = self.ipv6_addr_object
        if ipv6_addr_object != self.default_ipv6_addr_object:
            return ipv6_addr_object.masklength
        return -1

    # This method is on BaseIOSIntfLine()
    @logger.catch(reraise=True)
    def is_abbreviated_as(self, value: str) -> int:
        """
        :return: Whether ``value`` is a good abbreviation for the interface
        :rtype: bool
        """
        if value.lower() in self.abbvs:
            return True
        return False

    # This method is on BaseIOSIntfLine()
    @logger.catch(reraise=True)
    def in_ipv4_subnet(self, ipv4network: IPv4Obj=None, strict: bool=False) -> bool:
        r"""
        :return: Whether the interface is in a :class:`~ciscoconfparse2.ccp_util.IPv4Obj` subnet, default to False.
        :rtype: bool

        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 21,23

           >>> from ciscoconfparse2.ccp_util import IPv4Obj
           >>> from ciscoconfparse2 import CiscoConfParse
           >>> config = [
           ...     '!',
           ...     'interface Serial1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     '!',
           ...     'interface ATM2/0',
           ...     ' no ip address',
           ...     '!',
           ...     'interface ATM2/0.100 point-to-point',
           ...     ' ip address 1.1.1.5 255.255.255.252',
           ...     ' pvc 0/100',
           ...     '  vbr-nrt 704 704',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config, factory=True)
           >>> obj = parse.find_objects('^interface\sSerial')[0]
           >>> obj
           <IOSIntfLine # 1 'Serial1/0' primary_ipv4: '1.1.1.1/30'>
           >>> obj.in_ipv4_subnet(IPv4Obj('1.1.1.0/24', strict=False))
           True
           >>> obj.in_ipv4_subnet(IPv4Obj('2.1.1.0/24', strict=False))
           False
           >>>
        """
        if self.ipv4_addr_object.empty is True:
            return False
        elif ipv4network is None:
            return False
        elif isinstance(ipv4network, IPv4Obj) and ipv4network.empty is True:
            return False
        elif isinstance(ipv4network, IPv4Obj):
            intf_ipv4obj = self.ipv4_addr_object
            if isinstance(intf_ipv4obj, IPv4Obj):
                try:
                    # Return a boolean for whether the interface is in that
                    #    network and mask
                    return intf_ipv4obj in ipv4network
                except Exception as eee:
                    error = f"FATAL: {self}.in_ipv4_subnet(ipv4network={ipv4network}) is invalid: {eee}"
                    logger.error(error)
                    raise ValueError(error)
            else:
                error = f"{self}.ipv4_addr_object must be an instance of IPv4Obj, but it is {type(intf_ipv4obj)}"
                logger.error(error)
                raise ValueError(error)
        else:
            return None

    # This method is on BaseIOSIntfLine()
    @logger.catch(reraise=True)
    def in_ipv4_subnets(self, subnets: Union[Set[IPv4Obj], List[IPv4Obj], Tuple[IPv4Obj, ...]]=None) -> bool:
        r"""
        :return: Whether the interface is in a sequence or set of ccp_util.IPv4Obj objects
        :rtype: bool
        """
        if subnets is None:
            raise ValueError(
                "A python list or set of ccp_util.IPv4Obj objects must be supplied"
            )
        for subnet in subnets:
            if subnet.empty is True:
                continue
            tmp = self.in_ipv4_subnet(ipv4network=subnet)
            if self.ipv4_addr_object in subnet:
                return tmp
        return tmp

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_no_icmp_unreachables(self) -> bool:
        r"""
        :return: Whether the interface is configured without ICMP unreachables
        :rtype: bool
        """
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## Interface must have an IP addr to respond
        if self.ipv4_addr == "":
            return False

        retval = self.re_match_iter_typed(
            r"^\s*no\sip\s(unreachables)\s*$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_no_icmp_redirects(self) -> bool:
        r"""
        :return: Whether the interface is configured without ICMP redirects
        :rtype: bool
        """
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## Interface must have an IP addr to respond
        if self.ipv4_addr == "":
            return False

        retval = self.re_match_iter_typed(
            r"^\s*no\sip\s(redirects)\s*$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_no_ip_proxyarp(self) -> bool:
        r"""
        :return: Whether the interface is configured without Proxy-ARP
        :rtype: bool

        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 12

           >>> from ciscoconfparse2.ccp_util import IPv4Obj
           >>> from ciscoconfparse2 import CiscoConfParse
           >>> config = [
           ...     '!',
           ...     'interface FastEthernet1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     ' no ip proxy-arp',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config, factory=True)
           >>> obj = parse.find_objects('^interface\sFast')[0]
           >>> obj.has_no_ip_proxyarp
           True
           >>>
        """

        ## Interface must have an IP addr to respond
        if self.ipv4_addr == "":
            return False

        ## By default, Cisco IOS answers proxy-arp
        ## By default, Nexus disables proxy-arp
        ## By default, IOS-XR disables proxy-arp
        retval = self.re_match_iter_typed(
            r"^\s*no\sip\s(proxy-arp)\s*$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_ip_pim_dense_mode(self) -> bool:
        r"""
        :return: Whether the interface is configured with IP PIM Dense-Mode
        :rtype: bool
        """
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## Interface must have an IP addr to run PIM
        if self.ipv4_addr == "":
            return False

        retval = self.re_match_iter_typed(
            r"^\s*(ip\spim\sdense-mode)\s*$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_ip_pim_sparse_mode(self) -> bool:
        r"""
        :return: Whether the interface is configured with IP PIM Sparse-Mode
        :rtype: bool
        """
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## Interface must have an IP addr to run PIM
        if self.ipv4_addr == "":
            return False

        retval = self.re_match_iter_typed(
            r"^\s*(ip\spim\ssparse-mode)\s*$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_ipv6_pim_sparse_mode(self) -> bool:
        r"""
        :return: Whether the interface is configured with IP PIM Sparse-Mode
        :rtype: bool
        """
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## Interface must have an IP addr to run PIM
        if self.ipv4_addr == "":
            return False

        retval = self.re_match_iter_typed(
            r"^\s*(ipv6\spim\ssparse-mode)\s*$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_ip_pim_sparsedense_mode(self) -> bool:
        r"""
        :return: Whether the interface is configured with IP PIM Sparse-Dense-Mode
        :rtype: bool
        """
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## Interface must have an IP addr to run PIM
        if self.ipv4_addr == "":
            return False

        for _obj in self.children:
            if _obj.text.strip().split()[0:3] == ["ip", "pim", "sparse-dense-mode"]:
                return True
        return False

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_arp_timeout(self) -> int:
        r"""
        :return: An integer with the manual ARP timeout, default to -1
        :rtype: int
        """
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## Interface must have an IP addr to respond
        if self.ipv4_addr == "":
            return -1

        ## By default, Cisco IOS defaults to 4 hour arp timers
        ## By default, Nexus defaults to 15 minute arp timers
        retval = self.re_match_iter_typed(
            r"^\s*arp\s+timeout\s+(\d+)\s*$", result_type=int, default=-1
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ip_helper_addresses(self) -> List[Dict[str,str]]:
        r"""
        :return: A sequence of dicts with IP helper-addresses.  Each helper-address is in a dictionary.
        :rtype: List[Dict[str,str]]

        .. code-block:: python
           :emphasize-lines: 11

           >>> from ciscoconfparse2 import CiscoConfParse
           >>> config = [
           ...     '!',
           ...     'interface FastEthernet1/1',
           ...     ' ip address 1.1.1.1 255.255.255.0',
           ...     ' ip helper-address 172.16.20.12',
           ...     ' ip helper-address 172.19.185.91',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config)
           >>> obj = parse.find_objects('^interface\sFastEthernet1/1$')[0]
           >>> obj.ip_helper_addresses
           [{'addr': '172.16.20.12', 'vrf': '', 'scope': 'local'}, {'addr': '172.19.185.91', 'vrf': '', 'scope': 'local'}]
           >>>
        """
        retval = list()
        for child in self.children:
            if "helper-address" in child.text:
                addr = child.re_match_typed(
                    r"ip\s+helper-address\s.*?(\d+\.\d+\.\d+\.\d+)"
                )
                global_addr = child.re_match_typed(
                    r"ip\s+helper-address\s+(global)", result_type=bool, default=False
                )
                vrf = child.re_match_typed(
                    r"ip\s+helper-address\s+vrf\s+(\S+)", default=""
                )
                if global_addr:
                    retval.append({"addr": addr, "vrf": vrf, "scope": 'global'})
                else:
                    retval.append({"addr": addr, "vrf": vrf, "scope": 'local'})
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv6_dhcp_server(self) -> List[Dict[str,str]]:
        r"""
        :return: A sequence of dicts with IPv6 dhcp server.  Each address is in a dictionary.
        :rtype: List[Dict[str,str]]
        """
        raise NotImplementedError()

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def is_switchport(self) -> bool:
        r"""
        :return: Whether the interface is a switchport
        :rtype: bool
        """
        for _obj in self.children:
            if _obj.text.strip().split()[0] == "switchport":
                return True
        return False

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_switch_access(self) -> bool:
        r"""
        :return: Whether the interface is manually configured as an access switchport
        :rtype: bool
        """
        for _obj in self.children:
            if _obj.text.strip().split()[0:3] == ["switchport", "mode", "access"]:
                return True
        return False

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_switch_trunk_encap(self) -> bool:
        r"""
        :return: Whether the interface is has a manual switchport trunk encapsulation
        :rtype: bool
        """
        return bool(self.manual_switch_trunk_encap)

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_switch_trunk_encap(self) -> str:
        r"""
        :return: The type of trunk encapsulation of this switchport.
        :rtype: str
        """
        for _obj in self.children:
            _parts = _obj.text.strip().split()
            if len(_parts) == 4 and _parts[0:3] == ["switchport", "trunk", "encap"]:
                return _parts[3]
        return ""

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_switch_trunk(self) -> bool:
        r"""
        :return: Whether this interface is manually configured as a trunk switchport
        :rtype: bool
        """
        for _obj in self.children:
            if _obj.text.strip().split()[0:3] == ["switchport", "mode", "trunk"]:
                return True
        return False

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_switch_portsecurity(self) -> bool:
        r"""
        :return: Whether this interface is fully configured with port-security
        :rtype: bool
        """
        if not self.is_switchport:
            return False
        ## IMPORTANT: Cisco IOS will not enable port-security on the port
        ##    unless 'switch port-security' (with no other options)
        ##    is in the configuration
        for _obj in self.children:
            if _obj.text.strip().split()[0:2] == ["switchport", "port-security"]:
                return True
        return False

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_switch_stormcontrol(self) -> bool:
        r"""
        :return: Whether this interface is fully configured with storm-control
        :rtype: bool
        """
        if not self.is_switchport:
            return False
        for _obj in self.children:
            if _obj.text.strip().split()[0:1] == ["storm-control"]:
                return True
        return False

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_dtp(self) -> bool:
        r"""
        :return: Whether this interface is configured to use Cisco DTP
        :rtype: bool
        """
        if not self.is_switchport:
            return False

        ## Not using self.re_match_iter_typed, because I want to
        ##   be sure I build the correct API for regex_match is False, and
        ##   default value is True
        for obj in self.children:
            switch = obj.re_match(r"^\s*(switchport\snoneg\S*)\s*$")
            if (switch is not None):
                return False
        return True

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def access_vlan(self) -> int:
        r"""
        :return: An integer access vlan number, default to 1.  Return -1 if the port is not a switchport.
        :rtype: int
        """
        if self.is_switchport:
            default_val = 1
        else:
            default_val = -1

        for _obj in self.children:
            if _obj.text.strip().split()[0:3] == ["switchport", "access", "vlan"]:
                return int(_obj.text.strip().split()[3])
        return default_val

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def trunk_vlans_allowed(self) -> CiscoRange:
        r"""
        :return: A CiscoRange() with the list of allowed vlan numbers (as int).
        :rtype: CiscoRange
        """
        # The default value for retval...
        if self.is_switchport and not self.has_manual_switch_access:
            retval = CiscoRange(result_type=int)
        else:
            # Default to an empty CiscoRange()
            return CiscoRange(result_type=int)

        _all_vlans = "1-4094"
        _max_number_vlans = 4094
        # Default to allow allow all vlans...
        vdict = {
            "allowed": _all_vlans,
            "add": None,
            "except": None,
            "remove": None,
        }

        ## Iterate over switchport trunk statements
        for obj in self.children:

            if obj.text.split()[0:5] == ["switchport", "trunk", "allowed", "vlan", "add"]:
                add_str = obj.re_match_typed(
                    r"^\s+switchport\s+trunk\s+allowed\s+vlan\s+add\s+(\d[\d\-\,\s]*)$",
                    default="_nomatch_",
                    result_type=str,
                ).lower()
                if add_str != "_nomatch_":
                    if vdict["add"] is None:
                        vdict["add"] = add_str
                    else:
                        vdict["add"] += f",{add_str}"

            elif obj.text.split()[0:5] == ["switchport", "trunk", "allowed", "vlan", "except"]:
                exc_str = obj.re_match_typed(
                    r"^\s+switchport\s+trunk\s+allowed\s+vlan\s+except\s+(\d[\d\-\,\s]*)$",
                    default="_nomatch_",
                    result_type=str,
                ).lower()
                if exc_str != "_nomatch_":
                    if vdict["except"] is None:
                        vdict["except"] = exc_str
                    else:
                        vdict["except"] += f",{exc_str}"

            elif obj.text.split()[0:5] == ["switchport", "trunk", "allowed", "vlan", "remove"]:
                rem_str = obj.re_match_typed(
                    r"^\s+switchport\s+trunk\s+allowed\s+vlan\s+remove\s+(\d[\d\-\,\s]*)$",
                    default="_nomatch_",
                    result_type=str,
                ).lower()
                if rem_str != "_nomatch_":
                    if vdict["remove"] is None:
                        vdict["remove"] = rem_str
                    else:
                        vdict["remove"] += f",{rem_str}"

            elif obj.text.split()[0:4] == ["switchport", "trunk", "allowed", "vlan"]:
                ## For every child object, check whether the vlan list is modified
                allowed_str = obj.re_match_typed(
                    # switchport trunk allowed vlan
                    r"^\s+switchport\s+trunk\s+allowed\s+vlan\s+(all|none|\d[\d\-\,\s]*)$",
                    default="_nomatch_",
                    result_type=str,
                ).lower()
                if allowed_str != "_nomatch_":
                    if allowed_str == "none":
                        # Replace the default allow of 1-4094...
                        vdict["allowed"] = ""
                    elif allowed_str == "all":
                        # Specify an initial list of vlans...
                        vdict["allowed"] = _all_vlans
                    else:
                        # handle **double allowed** statements here...
                        if vdict["allowed"] == _all_vlans:
                            vdict["allowed"] = f"{allowed_str}"
                        elif vdict["allowed"] == "":
                            vdict["allowed"] = f"{allowed_str}"
                        else:
                            vdict["allowed"] += f",{allowed_str}"

        ## Analyze each vdict in sequence and apply to retval sequentially
        if isinstance(vdict["allowed"], str):
            if vdict["allowed"] == _all_vlans:
                if len(retval) != _max_number_vlans:
                    retval = CiscoRange(f"1-{MAX_VLAN}", result_type=int)
            elif vdict["allowed"] == "":
                retval = CiscoRange(result_type=int)
            elif vdict["allowed"] != "_nomatch_":
                retval = CiscoRange(vdict["allowed"], result_type=int)

        # Inspect vdict keys in a specific order to ensure best results...
        for key in ["allowed", "add", "except", "remove"]:
            _value = vdict[key]

            if isinstance(_value, str):
                _value = _value.strip()
            elif _value is None:
                # There is nothing to be done if _value is None...
                continue

            if _value == "":
                continue
            elif _value != "_nomatch_":
                ## allowed in the key overrides previous values
                if key == "allowed":
                    # When considering 'allowed', reset retval to be empty...
                    retval = CiscoRange(result_type=int)
                    if _value.lower() == "none":
                        continue
                    elif _value.lower() == "all":
                        retval = CiscoRange(text=f"1-{MAX_VLAN}", result_type=int)
                    elif isinstance(re.search(r"^\d[\d\-\,\s]*", _value), re.Match):
                        retval = retval + CiscoRange(_value, result_type=int)
                    else:
                        error = f"Could not derive a vlan range for {_value}"
                        logger.error(error)
                        raise InvalidCiscoEthernetVlan(error)

                elif key == "add":
                    retval = retval + CiscoRange(_value, result_type=int)
                elif key == "except" or key == "remove":
                    retval = retval - CiscoRange(_value, result_type=int)
                else:
                    error = f"{key} is an invalid Cisco switched dot1q ethernet trunk action."
                    logger.error(error)
                    raise InvalidCiscoEthernetTrunkAction(error)
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def native_vlan(self) -> int:
        r"""
        :return: Return an integer with the native vlan number.  Return 1, if the switchport has no explicit native vlan configured; return -1 if the port isn't a switchport
        :rtype: int
        """
        if self.is_switchport:
            default_val = 1
        else:
            default_val = -1
        for _obj in self.children:
            _parts = _obj.text.strip().split()
            if len(_parts) == 5 and _parts[0:4] == ["switchport", "trunk", "native", "vlan"]:
                # return the vlan integer from 'switchport trunk native vlan 911'
                return int(_parts[4])
        return default_val

    ##-------------  CDP

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_disable_cdp(self) -> bool:
        """
        :return: Whether CDP is manually disabled on this interface
        :rtype: bool
        """
        for _obj in self.children:
            _parts = _obj.text.strip().split()
            if len(_parts) == 3 and _parts[0:3] == ["no", "cdp", "enable",]:
                return True
        return False

    ##-------------  EoMPLS

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_xconnect(self) -> bool:
        """
        :return: Whether this interface has an MPLS or L2TP xconnect
        :rtype: bool
        """
        return bool(self.xconnect_vc)

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def xconnect_vc(self) -> int:
        """
        :return: The virtual circuit ID of the xconnect on this interface, default to -1 (even if no xconnect)
        :rtype: int
        """
        retval = self.re_match_iter_typed(
            r"^\s*xconnect\s+\S+\s+(\d+)\s+\S+", result_type=int, default=-1
        )
        return retval

    ##-------------  HSRP

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_ip_hsrp(self) -> bool:
        """
        :return: Whether this interface has HSRP configured on it
        :rtype: bool
        """
        return bool(self.hsrp_ip_addr)

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def hsrp_ip_addr(self) -> Dict[int,str]:
        """
        :return: A dict keyed by integer HSRP group number with a string ipv4 address, default to an empty dict
        :rtype: Dict[int,str]
        """
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## For API simplicity, I always assume there is only one hsrp
        ##     group on the interface
        retval = dict()
        if self.ipv4_addr == "":
            return retval

        for cmd in self.all_children:
            parts = cmd.splilt()
            if cmd[0] == "standby" and cmd[1] == "ip":
                # Standby with no explicit group number
                hsrp_group = 0
                hsrp_addr = cmd[2]
                retval[hsrp_group] = hsrp_addr
            elif cmd[0] == "standby" and cmd[2] == "ip":
                # Standby with an explicit group number
                hsrp_group = int(cmd[1])
                hsrp_addr = cmd[3]
                retval[hsrp_group] = hsrp_addr

        return retval

    # This method is on BaseFactoryInterfaceLine()
    @property
    @logger.catch(reraise=True)
    def hsrp_ip_addr_secondary(self) -> Dict[int,str]:
        """
        :return: A dict keyed by integer HSRP group number with a comma-separated string secondary ipv4 address, default to an empty dict
        :rtype: Dict[int,str]
        """
        # See self.hsrp_ip_addr, above for implementation template
        raise NotImplementedError()

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def hsrp_priority(self) -> Dict[int,int]:
        """
        :return: A dict keyed by integer HSRP group number with an integer HSRP priority per-group
        :rtype: Dict[int,int]
        """
        ## For API simplicity, I always assume there is only one hsrp
        ##     group on the interface
        retval = dict()
        if self.ipv4_addr == "":
            return retval

        for cmd in self.all_children:
            parts = cmd.split()
            if cmd[0] == "standby" and cmd[1] == "priority":
                # Standby with no explicit group number
                hsrp_group = 0
                hsrp_priority = int(cmd[2])
                retval[hsrp_group] = hsrp_priority
            elif cmd[0] == "standby" and cmd[2] == "priority":
                # Standby with an explicit group number
                hsrp_group = int(cmd[1])
                hsrp_priority = int(cmd[3])
                retval[hsrp_group] = hsrp_priority

        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def hsrp_hello_timer(self):
        # See self.hsrp_priority, above for implementation template
        raise NotImplementedError()

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def hsrp_hold_timer(self):
        # See self.priority, above for implementation template
        raise NotImplementedError()

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def hsrp_usebia(self):
        # See self.hsrp_priority, above for implementation template
        raise NotImplementedError()

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def hsrp_preempt(self):
        # See self.hsrp_priority, above for implementation template
        raise NotImplementedError()

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def hsrp_authentication_md5_keychain(self):
        ## For API simplicity, I always assume there is only one hsrp
        ##     group on the interface
        retval = dict()
        if self.ipv4_addr == "":
            return retval

        # example:
        #   standby 110 authentication md5 key-chain KEYCHAINNAME
        for cmd in self.all_children:
            parts = cmd.split()
            if cmd[0] == "standby" and cmd[1] == "authentication" and cmd[3] == "key-chain":
                # Standby with no explicit group number
                hsrp_group = 0
                hsrp_auth_name = cmd[4]
                retval[hsrp_group] = hsrp_auth_name
            elif cmd[0] == "standby" and cmd[2] == "authentication" and cmd[4] == "key-chain":
                # Standby with an explicit group number
                hsrp_group = int(cmd[1])
                hsrp_auth_name = cmd[5]
                retval[hsrp_group] = hsrp_auth_name

        return retval

    ##-------------  MAC ACLs

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def mac_accessgroup_in(self) -> bool:
        """
        :return: Whether this interface has an inbound mac access-list
        :rtype: bool
        """
        retval = self.re_match_iter_typed(
            r"^\s*mac\saccess-group\s+(?P<group_number>\S+)\s+in\s*$",
            groupdict={"group_number": str},
            default=""
        )
        return retval["group_number"]

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def mac_accessgroup_out(self) -> bool:
        """
        :return: Whether this interface has an outbound mac access-list
        :rtype: bool
        """
        retval = self.re_match_iter_typed(
            r"^\s*mac\saccess-group\s+(?P<group_number>\S+)\s+out\s*$",
            groupdict={"group_number": str},
            default=""
        )
        return retval["group_number"]

    ##-------------  IPv4 ACLs

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ip_accessgroup_in(self) -> str:
        """
        :return: The name or number of the inbound IPv4 access-group
        :rtype: str
        """
        return self.ipv4_accessgroup_in

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ip_accessgroup_out(self) -> str:
        """
        :return: The name or number of the outbound IPv4 access-group
        :rtype: str
        """
        return self.ipv4_accessgroup_out

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_accessgroup_in(self) -> str:
        """
        :return: The name or number of the inbound IPv4 access-group
        :rtype: str
        """
        retval = self.re_match_iter_typed(
            r"^\s*ip\saccess-group\s+(\S+)\s+in\s*$", result_type=str, default=""
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv6_trafficfilter_in(self) -> str:
        """
        :return: The name or number of the inbound IPv6 ACL
        :rtype: str
        """
        retval = self.re_match_iter_typed(
            r"^\s*ipv6\straffic-filter\s+(\S+)\s+in\s*$", result_type=str, default=""
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_accessgroup_out(self) -> str:
        """
        :return: The name or number of the outbound IPv4 access-group
        :rtype: str
        """
        retval = self.re_match_iter_typed(
            r"^\s*ip\saccess-group\s+(\S+)\s+out\s*$", result_type=str, default=""
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv6_trafficfilter_in(self) -> str:
        """
        :return: The name or number of the inbound IPv6 ACL
        :rtype: str
        """
        retval = self.re_match_iter_typed(
            r"^\s*ipv6\straffic-filter\s+(\S+)\s+in\s*$", result_type=str, default=""
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv6_trafficfilter_out(self) -> str:
        """
        :return: The name or number of the outbound IPv6 ACL
        :rtype: str
        """
        retval = self.re_match_iter_typed(
            r"^\s*ipv6\straffic-filter\s+(\S+)\s+out\s*$", result_type=str, default=""
        )
        return retval

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
class IOSIntfLine(BaseIOSIntfLine):

    # This method is on IOSIntfLine()
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        r"""Accept an IOS line number and initialize family relationship
        attributes

        Warnings
        --------
        All :class:`~ciscoconfparse2.models_cisco.IOSIntfLine` methods are still considered beta-quality, until this notice is removed.  The behavior of APIs on this object could change at any time.
        """
        super(IOSIntfLine, self).__init__(*args, **kwargs)
        self.feature = "interface"

    @logger.catch(reraise=True)
    def __eq__(self, other):
        return self.get_unique_identifier() == other.get_unique_identifier()

    @logger.catch(reraise=True)
    def __ne__(self, other):
        return self.get_unique_identifier() != other.get_unique_identifier()

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
class IOSIntfGlobal(IOSCfgLine):
    # This method is on IOSIntGlobal()
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super(IOSIntfGlobal, self).__init__(*args, **kwargs)
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

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, index=None, re=re):
        if re.search(
            r"^(no\s+cdp\s+run)|(logging\s+event\s+link-status\s+global)|(spanning-tree\sportfast\sdefault)|(spanning-tree\sportfast\sbpduguard\sdefault)",
            line,
        ):
            return True
        return False

    @property
    @logger.catch(reraise=True)
    def has_cdp_disabled(self):
        if self.re_search(r"^no\s+cdp\s+run\s*"):
            return True
        return False

    @property
    @logger.catch(reraise=True)
    def has_intf_logging_def(self):
        if self.re_search(r"^logging\s+event\s+link-status\s+global"):
            return True
        return False

    @property
    @logger.catch(reraise=True)
    def has_stp_portfast_def(self):
        if self.re_search(r"^spanning-tree\sportfast\sdefault"):
            return True
        return False

    @property
    @logger.catch(reraise=True)
    def has_stp_portfast_bpduguard_def(self):
        if self.re_search(r"^spanning-tree\sportfast\sbpduguard\sdefault"):
            return True
        return False

    @property
    @logger.catch(reraise=True)
    def has_stp_mode_rapidpvst(self):
        if self.re_search(r"^spanning-tree\smode\srapid-pvst"):
            return True
        return False


#
#-------------  IOS Access Line
#


@attrs.define(repr=False, slots=False)
class IOSAccessLine(IOSCfgLine):
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super(IOSAccessLine, self).__init__(*args, **kwargs)
        self.feature = "access line"

    @logger.catch(reraise=True)
    def __eq__(self, other):
        return self.get_unique_identifier() == other.get_unique_identifier()

    @logger.catch(reraise=True)
    def __ne__(self, other):
        return self.get_unique_identifier() != other.get_unique_identifier()

    @logger.catch(reraise=True)
    def __hash__(self):
        return self.get_unique_identifier()

    def __repr__(self):
        return "<%s # %s '%s' info: '%s'>" % (
            self.classname,
            self.linenum,
            self.name,
            self.range_str,
        )

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, index=None, re=re):
        if re.search(r"^line", line):
            return True
        return False

    @property
    @logger.catch(reraise=True)
    def is_accessline(self):
        retval = self.re_match_typed(r"^(line\s+\S+)", result_type=str, default="")
        return bool(retval)

    @property
    @logger.catch(reraise=True)
    def name(self):
        retval = self.re_match_typed(r"^line\s+(\S+)", result_type=str, default="")
        # special case for IOS async lines: i.e. "line 33 48"
        if re.search(r"\d+", retval):
            return ""
        return retval

    @property
    @logger.catch(reraise=True)
    def range_str(self):
        return " ".join(map(str, self.line_range))

    @property
    @logger.catch(reraise=True)
    def line_range(self):
        ## Return the access-line's numerical range as a list
        ## line con 0 => [0]
        ## line 33 48 => [33, 48]
        retval = self.re_match_typed(
            r"([a-zA-Z]+\s+)*(\d+\s*\d*)$", group=2, result_type=str, default=""
        )
        tmp = map(int, retval.strip().split())
        return tmp

    @logger.catch(reraise=True)
    def manual_exectimeout_minutes(self):
        tmp = self.parse_exectimeout
        return tmp[0]

    @logger.catch(reraise=True)
    def manual_exectimeout_seconds(self):
        tmp = self.parse_exectimeout
        if len(tmp > 0):
            return 0
        return tmp[1]

    @property
    @logger.catch(reraise=True)
    def parse_exectimeout(self):
        retval = self.re_match_iter_typed(
            r"^\s*exec-timeout\s+(\d+\s*\d*)\s*$", group=1, result_type=str, default=""
        )
        tmp = map(int, retval.strip().split())
        return tmp


##
##-------------  Base IOS Route line object
##


@attrs.define(repr=False, slots=False)
class BaseIOSRouteLine(IOSCfgLine):
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super(BaseIOSRouteLine, self).__init__(*args, **kwargs)

    def __repr__(self):
        return "<%s # %s '%s' info: '%s'>" % (
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
    def vrf(self):
        raise NotImplementedError

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
(?:\s+(?P<prefix>{0})\/(?P<masklength>\d+))    # Prefix detection
(?:
  (?:\s+(?P<nh_addr1>{1}))
  |(?:\s+(?P<nh_intf>\S+(?:\s+\d\S*?\/\S+)?)(?:\s+(?P<nh_addr2>{2}))?)
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
class IOSRouteLine(IOSCfgLine):
    _address_family: str = None
    route_info: dict = None

    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super(IOSRouteLine, self).__init__(*args, **kwargs)

        self.feature = "__NONE__"
        self._address_family = "__NONE__"

        if "ipv6" in self.text[0:4]:
            self.feature = "ipv6 route"
            self._address_family = "ipv6"

            # 2 / 2 == 0 below is to avoid trivial complaints from SonarCloud
            #     about 'if False'...
            #
            # _RE_IPV6_ROUTE was broken by the fix for
            # IPv6Obj() included in ciscoconfparse2 version 0.7.11
            # when I added a ^ at the beginning of all
            # IPv6 regex to avoid allowing invalid leading IPv6 characters.
            #
            # TODO Re-implement IPv6 route parse
            if 4 / 2 == 0:
                mm = _RE_IPV6_ROUTE.search(self.text)
                if (mm is not None):
                    self.route_info = mm.groupdict()
                else:
                    raise ValueError("Could not parse '{0}'".format(self.text))

            raise NotImplementedError("ipv6 route factory to be implemented in a future ciscoconfparse2")


        else:
            self.feature = "ip route"
            self._address_family = "ip"
            mm = _RE_IP_ROUTE.search(self.text)
            if (mm is not None):
                self.route_info = mm.groupdict()
            else:
                raise ValueError("Could not parse '{0}'".format(self.text))

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
        if (line[0:9] == "ip route ") or (line[0:11] == "ipv6 route "):
            return True
        return False

    @property
    @logger.catch(reraise=True)
    def vrf(self):
        if (self.route_info["vrf"] is not None):
            return self.route_info["vrf"]
        else:
            return ""

    @property
    @logger.catch(reraise=True)
    def address_family(self):
        ## ipv4, ipv6, etc
        return self._address_family

    @property
    @logger.catch(reraise=True)
    def network(self):
        if self._address_family == "ip":
            return self.route_info["prefix"]
        elif self._address_family == "ipv6":
            retval = self.re_match_typed(
                r"^ipv6\s+route\s+(vrf\s+)*(\S+?)\/\d+",
                group=2,
                result_type=str,
                default="",
            )
        return retval

    @property
    @logger.catch(reraise=True)
    def netmask(self):
        if self._address_family == "ip":
            return self.route_info["netmask"]
        elif self._address_family == "ipv6":
            return str(self.network_object.netmask)

    @property
    @logger.catch(reraise=True)
    def masklen(self):
        if self._address_family == "ip":
            return self.network_object.prefixlen
        elif self._address_family == "ipv6":
            masklen_str = self.route_info["masklength"] or "128"
            return int(masklen_str)

    @property
    @logger.catch(reraise=True)
    def network_object(self):
        try:
            if self._address_family == "ip":
                return IPv4Obj("%s/%s" % (self.network, self.netmask), strict=False)
            elif self._address_family == "ipv6":
                return IPv6Obj("%s/%s" % (self.network, self.masklen))
        except BaseException:
            logger.critical("Found _address_family = '{}''".format(self._address_family))
            return None

    @property
    @logger.catch(reraise=True)
    def nexthop_str(self):
        if self._address_family == "ip":
            if self.next_hop_interface:
                return self.next_hop_interface + " " + self.next_hop_addr
            else:
                return self.next_hop_addr
        elif self._address_family == "ipv6":
            retval = self.re_match_typed(
                r"^ipv6\s+route\s+(vrf\s+)*\S+\s+(\S+)",
                group=2,
                result_type=str,
                default="",
            )
        return retval

    @property
    @logger.catch(reraise=True)
    def next_hop_interface(self):
        if self._address_family == "ip":
            if self.route_info["nh_intf"]:
                return self.route_info["nh_intf"]
            else:
                return ""
        elif self._address_family == "ipv6":
            if self.route_info["nh_intf"]:
                return self.route_info["nh_intf"]
            else:
                return ""

    @property
    @logger.catch(reraise=True)
    def next_hop_addr(self):
        if self._address_family == "ip":
            return self.route_info["nh_addr"] or ""
        elif self._address_family == "ipv6":
            return self.route_info["nh_addr1"] or self.route_info["nh_addr2"] or ""

    @property
    @logger.catch(reraise=True)
    def global_next_hop(self):
        if self._address_family == "ip" and bool(self.vrf):
            return bool(self.route_info["global"])
        elif self._address_family == "ip" and not bool(self.vrf):
            return True
        elif self._address_family == "ipv6":
            ## ipv6 uses nexthop_vrf
            raise ValueError(
                "[FATAL] ipv6 doesn't support a global_next_hop for '{0}'".format(
                    self.text
                )
            )
        else:
            raise ValueError(
                "[FATAL] Could not identify global next-hop for '{0}'".format(self.text)
            )

    @property
    @logger.catch(reraise=True)
    def nexthop_vrf(self):
        if self._address_family == "ipv6":
            return self.route_info["nexthop_vrf"] or ""
        else:
            raise ValueError(
                "[FATAL] ip doesn't support a global_next_hop for '{0}'".format(
                    self.text
                )
            )

    @property
    @logger.catch(reraise=True)
    def admin_distance(self):
        if self.route_info["ad"]:
            return int(self.route_info["ad"])
        else:
            return 1

    @property
    @logger.catch(reraise=True)
    def multicast(self):
        r"""Return whether the multicast keyword was specified"""
        return bool(self.route_info["mcast"])

    @property
    @logger.catch(reraise=True)
    def unicast(self):
        ## FIXME It's unclear how to implement this...
        raise NotImplementedError

    @property
    @logger.catch(reraise=True)
    def route_name(self):
        if self.route_info["name"]:
            return self.route_info["name"]
        else:
            return ""

    @property
    @logger.catch(reraise=True)
    def permanent(self):
        if self._address_family == "ip":
            if self.route_info["permanent"]:
                return bool(self.route_info["permanent"])
            else:
                return False
        elif self._address_family == "ipv6":
            raise NotImplementedError

    @property
    @logger.catch(reraise=True)
    def tracking_object_name(self):
        if bool(self.route_info["track"]):
            return self.route_info["track"]
        else:
            return ""

    @property
    @logger.catch(reraise=True)
    def tag(self):
        return self.route_info["tag"] or ""


