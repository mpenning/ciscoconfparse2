r"""test_Cli_Script.py - Parse, Query, Build, and Modify IOS-style configs

Copyright (C) 2024-2025      David Michael Pennington

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
mike [~at~] pennington [.dot.] net
"""

from argparse import Namespace

import pytest
from ciscoconfparse2.ccp_util import EUI64Obj, MACObj
from ciscoconfparse2.cli_script import CliApplication, MACEUISearch, ccp_script_entry


def testValues_ccp_script_entry_cliapplication_searchmaceui_01():
    """Ensure that CliApplication() MACEUISearch() class can find one EUI64 address correctly with one match any regex"""
    search = MACEUISearch("dead.beef.0001.0001")
    assert search.mac_retval == EUI64Obj("dead.beef.0001.0001")
    assert search.search_all_formats(mac_regex_strs={"."}) is True


def testValues_ccp_script_entry_cliapplication_searchmaceui_02():
    """Ensure that CliApplication() MACEUISearch() class can find one EUI64 address correctly with a two-byte case-insensitive regex"""
    search = MACEUISearch("dead.beef.0001.0001")
    assert search.mac_retval == EUI64Obj("dead.beef.0001.0001")
    assert search.search_all_formats(mac_regex_strs={"de-ad"}) is True
    assert search.search_all_formats(mac_regex_strs={"DE-AD"}) is True
    assert search.search_all_formats(mac_regex_strs={"dE-Ad"}) is True


def testValues_ccp_script_entry_cliapplication_searchmaceui_03():
    """Ensure that CliApplication() MACEUISearch() class can find one EUI64 dash-formatted address correctly"""
    search = MACEUISearch("dead.beef.0001.0001")
    assert search.mac_retval == EUI64Obj("dead.beef.0001.0001")
    assert search.search_all_formats(mac_regex_strs={"de-ad-be-ef-00-01"}) is True
    assert search.search_all_formats(mac_regex_strs={"ff-ff-ff-ff-ff-ff"}) is False


def testValues_ccp_script_entry_cliapplication_searchmaceui_04():
    """Ensure that CliApplication() MACEUISearch() class can find one EUI64 colon-formatted address correctly"""
    search = MACEUISearch("dead.beef.0001.0001")
    assert search.mac_retval == EUI64Obj("dead.beef.0001.0001")
    assert search.search_all_formats(mac_regex_strs={"de:ad:be:ef:00:01"}) is True
    assert search.search_all_formats(mac_regex_strs={"ff:ff:ff:ff:ff:ff"}) is False


def testValues_ccp_script_entry_cliapplication_searchmaceui_05():
    """Ensure that CliApplication() MACEUISearch() class can find one EUI64 cisco-dot-formatted address correctly"""
    search = MACEUISearch("dead.beef.0001.0001")
    assert search.mac_retval == EUI64Obj("dead.beef.0001.0001")
    assert search.search_all_formats(mac_regex_strs={"dead.beef.0001"}) is True
    assert search.search_all_formats(mac_regex_strs={"ffff.ffff.fff"}) is False


def testValues_ccp_script_entry_cliapplication_searchmaceui_06():
    """Ensure that CliApplication() MACEUISearch() class can find one EUI64 address correctly with two regex"""
    search = MACEUISearch("dead.beef.0001.0001")
    assert search.mac_retval == EUI64Obj("dead.beef.0001.0001")
    assert search.search_all_formats(mac_regex_strs={"foo", "."}) is True


def testValues_ccp_script_entry_cliapplication_searchmaceui_07():
    """Ensure that CliApplication() MACEUISearch() class can reject one EUI64 address correctly with one regex"""
    search = MACEUISearch("dead.beef.0001.0001")
    assert search.mac_retval == EUI64Obj("dead.beef.0001.0001")
    assert search.search_all_formats(mac_regex_strs={"reject_any_mac_regex"}) is False


def testValues_ccp_script_entry_cliapplication_searchmaceui_07():
    """Ensure that CliApplication() MACEUISearch() class can reject one EUI48 / MAC address correctly with one regex"""
    search = MACEUISearch("dead.beef.0001")
    assert search.mac_retval == MACObj("dead.beef.0001")
    assert search.search_all_formats(mac_regex_strs={"."}) is True


# find_ip46_addr_matches()
def testValues_ccp_script_entry_cliapplication_01():
    """Ensure that ccp_script_entry return value is an instance of CliApplication() from sample_01.ios"""
    cliapp = ccp_script_entry(
        "ccp_faked ipgrep -s 172.16.1.5/32 fixtures/configs/sample_01.ios"
    )
    assert isinstance(cliapp, CliApplication)


def testValues_ccp_script_entry_cliapplication_args_01():
    """Ensure that CliApplication().args is a single-element list from sample_01.ios"""
    cliapp = ccp_script_entry(
        "ccp_faked ipgrep -s 172.16.1.5/32 fixtures/configs/sample_01.ios"
    )
    assert cliapp.args == [""]


def testValues_ccp_script_entry_cliapplication_ipgrep_01():
    """Ensure that CliApplication() ipgrep with the unique flag clear is a list of six IP addresses from sample_01.ios"""
    cliapp = ccp_script_entry(
        "ccp_faked ipgrep -s 172.16.1.5/32 fixtures/configs/sample_01.ios"
    )
    assert len(cliapp.stdout) == 6
    assert cliapp.unique is False
    assert cliapp.subnets == "172.16.1.5/32"
    assert cliapp.stdout == [
        "172.16.1.5",
        "172.16.1.5",
        "172.16.1.5",
        "172.16.1.5",
        "172.16.1.5",
        "172.16.1.5",
    ]


def testValues_ccp_script_entry_cliapplication_ipgrep_02():
    """Ensure that CliApplication() ipgrep with the unique flag clear is a list of seven IP addresses from sample_01.ios"""
    cliapp = ccp_script_entry(
        "ccp_faked ipgrep -s 172.16.1.5,172.16.1.50 fixtures/configs/sample_01.ios"
    )
    assert len(cliapp.stdout) == 7
    assert cliapp.unique is False
    assert cliapp.subnets == "172.16.1.5,172.16.1.50"
    assert cliapp.stdout == [
        "172.16.1.50",
        "172.16.1.5",
        "172.16.1.5",
        "172.16.1.5",
        "172.16.1.5",
        "172.16.1.5",
        "172.16.1.5",
    ]


def testValues_ccp_script_entry_cliapplication_ipgrep_03():
    """Ensure that CliApplication() ipgrep with the unique flag clear is a list of eight IPv6 addresses from sample_08.ios"""
    cliapp = ccp_script_entry(
        "ccp_faked ipgrep -s fd01::/16 fixtures/configs/sample_08.ios"
    )
    assert len(cliapp.stdout) == 8
    assert cliapp.unique is False
    assert cliapp.subnets == "fd01::/16"
    assert cliapp.stdout == [
        "fd01:ab00::",
        "fd01:abff::1:1",
        "fd01:dead:beef::1",
        "fd01:ab00::",
        "fd01:ab01::",
        "fd01:ab01::",
        "fd01:ab10::",
        "fd01:ab10::",
    ]


def testValues_ccp_script_entry_cliapplication_ipgrep_04():
    """Ensure that CliApplication() ipgrep with the unique flag set is a list of one IP address from sample_01.ios"""
    cliapp = ccp_script_entry(
        "ccp_faked ipgrep -u -s 172.16.1.5/32 fixtures/configs/sample_01.ios"
    )
    assert len(cliapp.stdout) == 1
    assert cliapp.unique is True
    assert cliapp.subnets == "172.16.1.5/32"
    assert cliapp.stdout == [
        "172.16.1.5",
    ]


def testValues_ccp_script_entry_cliapplication_ipgrep_05():
    """Ensure that CliApplication() ipgrep with the unique flag set is a list of two IP addresses from sample_08.ios"""
    cliapp = ccp_script_entry(
        "ccp_faked ipgrep -u -s 172.16.1.5,172.16.1.50 fixtures/configs/sample_01.ios"
    )
    assert len(cliapp.stdout) == 2
    assert cliapp.unique is True
    assert cliapp.subnets == "172.16.1.5,172.16.1.50"
    assert cliapp.stdout == ["172.16.1.50", "172.16.1.5"]


def testValues_ccp_script_entry_cliapplication_ipgrep_06():
    """Ensure that CliApplication() ipgrep with the unique flag set is a list of six IPv6 addresses from sample_08.ios"""
    cliapp = ccp_script_entry(
        "ccp_faked ipgrep -u -s fd01::/16 fixtures/configs/sample_08.ios"
    )
    assert len(cliapp.stdout) == 5
    assert cliapp.unique is True
    assert cliapp.subnets == "fd01::/16"
    assert cliapp.stdout == [
        "fd01:ab00::",
        "fd01:abff::1:1",
        "fd01:dead:beef::1",
        "fd01:ab01::",
        "fd01:ab10::",
    ]


def testValues_ccp_script_entry_cliapplication_ipgrep_07():
    """Ensure that CliApplication() ipgrep with --show-networks is seven IPv4 / IPv6 addrs from sample_01.txt"""
    cliapp = ccp_script_entry(
        "ccp_faked ipgrep -4 -6 fixtures/plain_text/sample_01.txt"
    )
    assert len(cliapp.stdout) == 7
    assert cliapp.unique is False
    assert cliapp.subnets == "0.0.0.0/0,::/0"
    assert cliapp.stdout == [
        "2001:db8::1",
        "2001:db8::1",
        "2001:db8::1",
        "192.0.2.3",
        "192.0.2.3",
        "2001:db8::",
        "2001:db8::",
    ]


def testValues_ccp_script_entry_cliapplication_ipgrep_08():
    """Ensure that CliApplication() ipgrep with --show-networks and --show-cidr is seven IPv4 / IPv6 addrs from sample_01.txt"""
    cliapp = ccp_script_entry(
        "ccp_faked ipgrep -4 -6 --show-cidr fixtures/plain_text/sample_01.txt"
    )
    assert len(cliapp.stdout) == 7
    assert cliapp.unique is False
    assert cliapp.subnets == "0.0.0.0/0,::/0"
    assert cliapp.stdout == [
        "2001:db8::1/127",
        "2001:db8::1/128",
        "2001:db8::1/128",
        "192.0.2.3/24",
        "192.0.2.3/32",
        "2001:db8::/64",
        "2001:db8::/64",
    ]


def testValues_ccp_script_entry_cliapplication_ipgrep_09():
    """Ensure that CliApplication() ipgrep with --show-networks and --show-cidr is five IPv4 / IPv6 addrs from sample_01.txt"""
    cliapp = ccp_script_entry(
        "ccp_faked ipgrep -u -4 -6 --show-cidr fixtures/plain_text/sample_01.txt"
    )
    assert len(cliapp.stdout) == 5
    assert cliapp.unique is True
    assert cliapp.subnets == "0.0.0.0/0,::/0"
    assert cliapp.stdout == [
        "2001:db8::1/127",
        "2001:db8::1/128",
        "192.0.2.3/24",
        "192.0.2.3/32",
        "2001:db8::/64",
    ]


def testValues_ccp_script_entry_cliapplication_ipgrep_10():
    """Ensure that CliApplication() ipgrep with --exclude-hosts and --show-cidr is two IPv6 networks from sample_01.txt"""
    cliapp = ccp_script_entry(
        "ccp_faked ipgrep --exclude-hosts -4 -6 --show-cidr fixtures/plain_text/sample_01.txt"
    )
    assert len(cliapp.stdout) == 2
    assert cliapp.unique is False
    assert cliapp.subnets == "0.0.0.0/0,::/0"
    assert cliapp.stdout == ["2001:db8::/64", "2001:db8::/64"]


def testValues_ccp_script_entry_cliapplication_ipgrep_11():
    """Ensure that CliApplication() ipgrep with --show-networks and --show-cidr is seven IPv4 / IPv6 networks (including host networks) from sample_01.txt"""
    cliapp = ccp_script_entry(
        "ccp_faked ipgrep --show-networks -4 -6 fixtures/plain_text/sample_01.txt"
    )
    assert len(cliapp.stdout) == 7
    assert cliapp.unique is False
    assert cliapp.subnets == "0.0.0.0/0,::/0"
    assert cliapp.stdout == [
        "2001:db8::/127",
        "2001:db8::1/128",
        "2001:db8::1/128",
        "192.0.2.0/24",
        "192.0.2.3/32",
        "2001:db8::/64",
        "2001:db8::/64",
    ]


def testValues_ccp_script_entry_cliapplication_ipgrep_12():
    """Ensure that CliApplication() ipgrep with --show-networks and --exclude-hosts is four IPv4 / IPv6 networks (including host networks) from sample_01.txt"""
    cliapp = ccp_script_entry(
        "ccp_faked ipgrep --exclude-hosts --show-networks -4 -6 fixtures/plain_text/sample_01.txt"
    )
    assert len(cliapp.stdout) == 4
    assert cliapp.unique is False
    assert cliapp.subnets == "0.0.0.0/0,::/0"
    assert cliapp.stdout == [
        "2001:db8::/127",
        "192.0.2.0/24",
        "2001:db8::/64",
        "2001:db8::/64",
    ]


def testValues_ccp_script_entry_cliapplication_ipgrep_13():
    """Ensure that CliApplication() ipgrep with --show-networks --exclude-hosts and --show-cidr is four IPv4 / IPv6 networks (including host networks) from sample_01.txt"""
    cliapp = ccp_script_entry(
        "ccp_faked ipgrep --show-networks --exclude-hosts -4 -6 fixtures/plain_text/sample_01.txt"
    )
    assert len(cliapp.stdout) == 4
    assert cliapp.unique is False
    assert cliapp.subnets == "0.0.0.0/0,::/0"
    assert cliapp.stdout == [
        "2001:db8::/127",
        "192.0.2.0/24",
        "2001:db8::/64",
        "2001:db8::/64",
    ]


def testValues_ccp_script_entry_cliapplication_ipgrep_14():
    """Ensure that CliApplication() ipgrep with --show-networks --exclude-hosts and --show-cidr is one IPv4 network from sample_01.txt"""
    cliapp = ccp_script_entry(
        "ccp_faked ipgrep --show-networks --exclude-hosts -4 fixtures/plain_text/sample_01.txt"
    )
    assert len(cliapp.stdout) == 1
    assert cliapp.unique is False
    assert cliapp.subnets == "0.0.0.0/0"
    assert cliapp.stdout == [
        "192.0.2.0/24",
    ]


def testValues_ccp_script_entry_cliapplication_ipgrep_15():
    """Ensure that CliApplication() ipgrep with --show-networks --exclude-hosts and --show-cidr is three IPv6 networks from sample_01.txt"""
    cliapp = ccp_script_entry(
        "ccp_faked ipgrep --show-networks --exclude-hosts -6 fixtures/plain_text/sample_01.txt"
    )
    assert len(cliapp.stdout) == 3
    assert cliapp.unique is False
    assert cliapp.subnets == "::/0"
    assert cliapp.stdout == [
        "2001:db8::/127",
        "2001:db8::/64",
        "2001:db8::/64",
    ]


def testValues_ccp_script_entry_cliapplication_ipgrep_16():
    """Ensure that CliApplication() ipgrep with --show-networks --exclude-hosts is no IPv6 networks from sample_01.txt"""
    cliapp = ccp_script_entry(
        "ccp_faked ipgrep --exclude-hosts --show-networks -6 fixtures/plain_text/sample_01.txt"
    )
    assert len(cliapp.stdout) == 0
    assert cliapp.unique is False
    assert cliapp.subnets == "::/0"
    assert cliapp.stdout == []


def testValues_ccp_script_entry_cliapplication_ipgrep_16():
    """Ensure that CliApplication() ipgrep with --unique --show-networks -ipv4 -ipv6 is no IPv6 networks from sample_01.txt"""
    cliapp = ccp_script_entry(
        "ccp_faked ipgrep --unique --show-networks -4 -6 fixtures/plain_text/sample_01.txt"
    )
    assert len(cliapp.stdout) == 5
    assert cliapp.unique is True
    assert cliapp.subnets == "0.0.0.0/0,::/0"
    assert cliapp.stdout == [
        "2001:db8::/127",
        "2001:db8::1/128",
        "192.0.2.0/24",
        "192.0.2.3/32",
        "2001:db8::/64",
    ]


def testValues_ccp_script_entry_cliapplication_branch_01():
    """Ensure that CliApplication() branch as original output flag set is a list of one IP address"""
    cliapp = ccp_script_entry(
        "ccp_faked branch -o original -a 'interface Null0' fixtures/configs/sample_01.ios"
    )
    assert len(cliapp.stdout) == 2
    assert cliapp.output_format == "original"
    assert cliapp.args == ["interface Null0"]
    assert cliapp.stdout == [
        "interface Null0",
        " no ip unreachables",
    ]


def testValues_ccp_script_entry_cliapplication_branch_02():
    """Ensure that CliApplication() branch as original output flag set is a list of one IP address"""
    cliapp = ccp_script_entry(
        "ccp_faked branch -a 'interface Null0,unreachables' fixtures/configs/sample_01.ios"
    )
    assert len(cliapp.stdout) == 2
    assert cliapp.output_format == "raw_text"
    assert cliapp.args == ["interface Null0", "unreachables"]
    assert cliapp.stdout == [
        "interface Null0",
        " no ip unreachables",
    ]


def testValues_ccp_script_entry_cliapplication_parent_01():
    """Ensure that CliApplication() parent as original output flag set is a list of one IP address"""
    cliapp = ccp_script_entry(
        "ccp_faked parent -a 'interface Null0' fixtures/configs/sample_01.ios"
    )
    assert len(cliapp.stdout) == 1
    assert cliapp.output_format == "raw_text"
    assert cliapp.args == ["interface Null0"]
    assert cliapp.stdout == ["interface Null0"]


def testValues_ccp_script_entry_cliapplication_child_01():
    """Ensure that CliApplication() parent as original output flag set is a list of one IP address"""
    cliapp = ccp_script_entry(
        "ccp_faked child -a 'interface Null0,unreachables' fixtures/configs/sample_01.ios"
    )
    assert len(cliapp.stdout) == 1
    assert cliapp.output_format == "raw_text"
    assert cliapp.args == ["interface Null0", "unreachables"]
    assert cliapp.stdout == [" no ip unreachables"]
