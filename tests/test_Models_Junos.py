import os
import sys

sys.path.insert(0, "..")

import pytest
from ciscoconfparse2.ccp_util import IPv4Obj
from ciscoconfparse2.ciscoconfparse2 import CiscoConfParse

r""" test_Models_Junos.py - Parse, Query, Build, and Modify IOS-style configs

     Copyright (C) 2023-2025      David Michael Pennington

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


# @pytest.mark.xfail(True, reason="Junos factory parsing is not supported yet")
def testVal_JunosIntfLine_dna(parse_j01):
    uut = parse_j01.objs
    assert len(uut) == 76
    # assert obj.dna == "JunosIntfLine"


def testVal_JunosCfgLine_dna_parent_01(parse_j01):
    parse = parse_j01
    obj = parse.find_parent_objects("interfaces", "ge-0/0/1")[0]
    assert obj.dna == "JunosCfgLine"
    assert obj.is_intf is False
    assert obj.is_subintf is False
    assert obj.indent == 0
    assert obj.child_indent == 4
    assert obj.confobj is not None


@pytest.mark.xfail(
    True, reason="parse_j01 ge-0/0/1 is not correctly identified by `is_intf`"
)
def testVal_JunosCfgLine_child_01(parse_j01):
    parse = parse_j01
    obj = parse.find_child_objects("interfaces", "ge-0/0/1")[0]
    assert obj.dna == "JunosCfgLine"
    assert obj.text.strip() == "ge-0/0/1"
    assert obj.is_intf is True
    assert obj.is_subintf is False
    assert obj.name == "ge-0/0/1"


def testVal_JunosCfgLine_child_02():
    """Identify a JunOS physical interface"""
    parse = CiscoConfParse(
        "fixtures/configs/sample_01.junos", syntax="junos", factory=False
    )
    obj = parse.find_child_objects("interfaces", "ge-0/0/1")[0]
    assert obj.dna == "JunosCfgLine"
    assert obj.text.strip() == "ge-0/0/1"
    assert obj.is_intf is True
    assert obj.is_subintf is False
    assert obj.is_switchport is True
    assert obj.name == "ge-0/0/1"


def testVal_JunosCfgLine_child_03():
    """Identify a JunOS logical interface unit"""
    parse = CiscoConfParse(
        "fixtures/configs/sample_01.junos", syntax="junos", factory=False
    )
    obj = parse.find_child_objects("ge-0/0/1", "unit 0")[0]
    assert obj.dna == "JunosCfgLine"
    assert obj.text.strip() == "unit 0"
    assert obj.is_intf is True
    assert obj.is_subintf is True
    assert obj.is_switchport is True
    assert obj.name == "ge-0/0/1 unit 0"


def testVal_JunosCfgLine_child_04():
    """Identify a JunOS logical interface unit"""
    parse = CiscoConfParse(
        "fixtures/configs/sample_01.junos", syntax="junos", factory=False
    )
    obj = parse.find_child_objects("vlan", "unit 0")[0]
    assert obj.dna == "JunosCfgLine"
    assert obj.text.strip() == "unit 0"
    assert obj.is_intf is True
    assert obj.is_subintf is True
    assert obj.is_switchport is False
    assert obj.name == "vlan unit 0"


def testVal_find_child_objects_01(parse_j01):
    """Identify the number of grandchildren of parse_j01 ge-0/0/1"""
    parse = parse_j01
    obj = parse.find_child_objects(["interfaces", "ge-0/0/1"])[0]
    assert not ("{" in set(obj.text))  # Ensure there are no braces on this line
    assert len(obj.all_children) == 6


def testVal_junos_factory_JunOSIntfLine_01(parse_j01):
    parse = CiscoConfParse(
        "fixtures/configs/sample_01.junos",
        syntax="junos",
        factory=True,
        ignore_blank_lines=False,
    )
    assert parse.config_objs[0].classname == "JunosCfgLine"

    assert parse.config_objs[58].text.strip() == "ge-0/0/0"
    assert parse.config_objs[58].text.strip() == "ge-0/0/0"
    assert parse.config_objs[58].classname == "JunosIntfLine"
    assert parse.config_objs[58].linenum == 58
    assert parse.config_objs[58].indent == 4

    assert parse.config_objs[59].text.strip() == "unit 0"
    assert parse.config_objs[59].classname == "JunosIntfLine"
    assert parse.config_objs[59].linenum == 59
    assert parse.config_objs[59].indent == 8

    assert parse.config_objs[60].text.strip() == "family ethernet-switching"
    assert parse.config_objs[60].classname == "JunosCfgLine"
    assert parse.config_objs[60].linenum == 60
    assert parse.config_objs[60].indent == 12


# test for Github issue #49
def testVal_parse_f5():
    """Test for Github issue #49 two different ways"""
    config = [
        "ltm virtual virtual1 {",
        "    profiles {",
        "        test1 { }",
        "    }",
        "}",
        "ltm virtual virtual2 {",
        "    profiles2 {",
        "        test2 { }",
        "    }",
        "}",
    ]
    parse = CiscoConfParse(config, syntax="junos")

    uut_01 = parse.find_objects("profiles2")[0].children
    assert len(uut_01) == 1
    assert uut_01[0].text.strip() == "test2"

    uut_02 = parse.find_child_objects("ltm virtual", "test2", recurse=True)[0]
    assert uut_02.text.strip() == "test2"
