import sys

import pytest
from ciscoconfparse2.ccp_abc import BaseCfgLine, get_brace_termination
from ciscoconfparse2.ccp_util import CiscoIOSInterface, CiscoRange, IPv4Obj, IPv6Obj
from ciscoconfparse2.ciscoconfparse2 import CiscoConfParse
from ciscoconfparse2.errors import ConfigListItemDoesNotExist, DynamicAddressException
from ciscoconfparse2.models_cisco import IOSCfgLine
from loguru import logger

sys.path.insert(0, "..")

r""" test_Ccp_Abc.py - Parse, Query, Build, and Modify IOS-style configs

     Copyright (C) 2023-2025     David Michael Pennington

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


def testVal_get_brace_termination_01():
    """Test correct parsing of opening braces"""
    line = "ltm virtual ACME {"
    uut = get_brace_termination(line)
    assert uut == "{"


def testVal_get_brace_termination_02():
    """Test correct parsing of opening braces with a trailing space"""
    line = "ltm virtual ACME { "
    uut = get_brace_termination(line)
    assert uut == "{"


def testVal_get_brace_termination_03():
    """Test correct parsing of closing braces"""
    line = "    }"
    uut = get_brace_termination(line)
    assert uut == "}"


def testVal_get_brace_termination_04():
    """Test correct parsing of closing braces with a trailing space"""
    line = "    } "
    uut = get_brace_termination(line)
    assert uut == "}"


def testVal_get_brace_termination_05():
    """Test correct parsing of opening and closing braces with a space in the middle"""
    line = "tcp { }"
    uut = get_brace_termination(line)
    assert uut == "{ }"


def testVal_get_brace_termination_06():
    """Test correct parsing of opening and closing braces with a space in the middle and a leading / trailing space"""
    line = " tcp { } "
    uut = get_brace_termination(line)
    assert uut == "{ }"


def testVal_get_brace_termination_07():
    """Test correct parsing of opening and closing braces with two spaces in the middle"""
    line = "tcp {  }"
    uut = get_brace_termination(line)
    assert uut == "{  }"


def testVal_get_brace_termination_08():
    """Test correct parsing of opening and closing braces with a parameter in the middle"""
    line = "    servers { 10.6.252.1 }"
    uut = get_brace_termination(line)
    assert uut == "{  }"


def testVal_BaseCfgLine_obj_01():
    """Test the text and other attributes of ccp_abc.BaseCfgLine()"""
    obj01 = BaseCfgLine(all_lines=None, line="hostname Foo")
    assert obj01.text == "hostname Foo"
    assert obj01.linenum == -1
    assert obj01.child_indent == 0

    # is_comment does not work until the line is part of a config
    # we should get None if the comment isn't attached to a real
    # configuration
    assert obj01.is_comment is None


def testVal_BaseCfgLine_eq_01():
    """Test the equality of BaseCfgLine() objects"""
    obj01 = BaseCfgLine(all_lines=None, line="hostname Foo")
    obj02 = BaseCfgLine(all_lines=None, line="hostname Foo")
    assert obj01 == obj02


def testVal_BaseCfgLine_neq_01():
    """Test the inequality of BaseCfgLine() objects if their linenumbers are different"""
    obj01 = BaseCfgLine(all_lines=None, line="hostname Foo")
    obj01.linenum = 1
    obj02 = BaseCfgLine(all_lines=None, line="hostname Foo")
    obj02.linenum = 2
    assert obj01 != obj02


def testVal_BaseCfgLine_gt_01():
    """Test the __gt__ of BaseCfgLine() objects if their linenumbers are different"""
    obj01 = BaseCfgLine(all_lines=None, line="hostname Foo")
    obj01.linenum = 1
    obj02 = BaseCfgLine(all_lines=None, line="hostname Foo")
    obj02.linenum = 2
    assert obj02 > obj01


def testVal_BaseCfgLine_lt_01():
    """Test the __lt__ of BaseCfgLine() objects if their linenumbers are different"""
    obj01 = BaseCfgLine(all_lines=None, line="hostname Foo")
    obj01.linenum = 1
    obj02 = BaseCfgLine(all_lines=None, line="hostname Foo")
    obj02.linenum = 2
    assert obj01 < obj02


def testVal_BaseCfgLine_split_01():
    """Test the split() method of BaseCfgLine() objects"""
    obj01 = BaseCfgLine(all_lines=None, line="hostname Foo")
    obj01.linenum = 1
    assert obj01.split() == ["hostname", "Foo"]


def testVal_BaseCfgLine_contains_01():
    """Test the __contains__() method of BaseCfgLine() objects"""
    obj01 = BaseCfgLine(all_lines=None, line="hostname Foo")
    obj01.linenum = 1
    assert "Foo" in obj01
    assert "Bar" not in obj01


def testVal_BaseCfgLine_getitem_01():
    """Test the __getitem__() method of BaseCfgLine() objects"""
    obj01 = BaseCfgLine(all_lines=None, line="hostname Foo")
    obj01.linenum = 1
    assert obj01[0:4] == "host"
    assert obj01[-1] == "o"


def testVal_BaseCfgLine_iter_01():
    """Test the __iter__() method of BaseCfgLine() objects"""
    obj01 = BaseCfgLine(all_lines=None, line="interface Vlan12")
    obj01.linenum = 1
    assert list(obj01) == [
        "i",
        "n",
        "t",
        "e",
        "r",
        "f",
        "a",
        "c",
        "e",
        " ",
        "V",
        "l",
        "a",
        "n",
        "1",
        "2",
    ]


def testVal_BaseCfgLine_index_01():
    """Test BaseCfgLine().index"""
    obj01 = BaseCfgLine(all_lines=None, line="hostname Foo")
    obj01.linenum = 1
    assert obj01.linenum == 1
    assert obj01.index == obj01.linenum


def testVal_BaseCfgLine_safe_escape_curly_braces_01():
    """Test BaseCfgLine().safe_escape_curly_braces()"""
    obj01 = BaseCfgLine(all_lines=None, line="hostname Foo")
    obj01.linenum = 1
    assert obj01.safe_escape_curly_braces("hello{") == "hello{{"


def testVal_BaseCfgLine_safe_escape_curly_braces_02():
    """Test BaseCfgLine().safe_escape_curly_braces()"""
    obj01 = BaseCfgLine(all_lines=None, line="hostname Foo")
    obj01.linenum = 1
    assert obj01.safe_escape_curly_braces("hello}") == "hello}}"


def testVal_BaseCfgLine_safe_escape_curly_braces_03():
    """Test BaseCfgLine().safe_escape_curly_braces()"""
    obj01 = BaseCfgLine(all_lines=None, line="hostname Foo")
    obj01.linenum = 1
    assert obj01.safe_escape_curly_braces("{hello} {") == "{{hello}} {{"


def testVal_BaseCfgLine_parent_01():
    """Test BaseCfgLine().parent"""
    parse = CiscoConfParse(
        ["interface GigabitEthernet1/1", " ip address 192.0.2.1 255.255.255.0"],
        syntax="ios",
    )
    obj01 = parse.find_objects("interface")[0]
    obj01.linenum = 1
    assert len(obj01.children) == 1
    assert obj01.children[0].parent is obj01


def testVal_BaseCfgLine_hash_children_01():
    """Test BaseCfgLine().hash_children"""
    parse = CiscoConfParse(
        ["interface GigabitEthernet1/1", " ip address 192.0.2.1 255.255.255.0"],
        syntax="ios",
    )
    obj01 = parse.find_objects("interface")[0]
    obj01.linenum = 1
    assert len(obj01.children) == 1
    assert isinstance(obj01.children, list)
    assert isinstance(obj01.hash_children, int)


def testVal_BaseCfgLine_family_endpoint_01():
    """Test BaseCfgLine().family_endpoint"""
    obj01 = BaseCfgLine(all_lines=None, line="interface Ethernet0/0")
    obj01.linenum = 1
    obj02 = BaseCfgLine(all_lines=None, line=" ip address 192.0.2.1 255.255.255.0")
    obj02.linenum = 2
    obj03 = BaseCfgLine(all_lines=None, line=" no ip proxy-arp")
    obj03.linenum = 3
    obj01.children = [obj02, obj03]
    assert len(obj01.children) == 2
    assert obj01.family_endpoint == 3


def testVal_BaseCfgLine_has_child_with_01():
    """Test BaseCfgLine().has_child_with()"""
    parse = CiscoConfParse(
        [
            "interface Ethernet0/0",
            " ip address 192.0.2.1 255.255.255.0",
            " no ip proxy-arp",
        ]
    )
    obj = parse.find_objects("interface")[0]
    uut = obj.has_child_with("proxy-arp", all_children=False)
    assert uut is True


def testVal_BaseCfgLine_has_child_with_02():
    """Test BaseCfgLine().has_child_with()"""
    parse = CiscoConfParse(
        [
            "interface Ethernet0/0",
            " ip address 192.0.2.1 255.255.255.0",
            # Use a fake double-indent on 'no ip proxy-arp'
            "  no ip proxy-arp",
        ]
    )
    obj = parse.find_objects("interface")[0]
    uut = obj.has_child_with("proxy-arp", all_children=False)
    assert uut is False


def testVal_BaseCfgLine_has_child_with_03():
    """Test BaseCfgLine().has_child_with()"""
    parse = CiscoConfParse(
        # A fake double-indent on 'no ip proxy-arp'
        [
            "interface Ethernet0/0",
            " ip address 192.0.2.1 255.255.255.0",
            "  no ip proxy-arp",
        ]
    )
    obj = parse.find_objects("interface")[0]
    uut = obj.has_child_with("proxy-arp", all_children=True)
    assert uut is True


def testVal_BaseCfgLine_CiscoIOS_delete_w_auto_commit_wo_reverse_01():
    """Ensure that we get an error when deleting multiple Cisco IOS configuration objects without reversing"""
    config = [
        "!",
        "hostname Example",
        "!",
        "interface GigabitEthernet1/0",
        " ip address 192.0.2.1 255.255.255.252",
        "!",
        "interface GigabitEthernet1/1",
        " ip address 192.0.2.5 255.255.255.252",
        "!",
        "interface GigabitEthernet1/2",
        " ip address 192.0.2.9 255.255.255.252",
        "!",
        "interface GigabitEthernet1/3",
        " ip address 192.0.2.11 255.255.255.252",
        "!",
        "end",
    ]

    parse = CiscoConfParse(config, auto_commit=True)
    # Ensure that the object exists...
    assert len(parse.find_objects(r"GigabitEthernet1/1")) == 1
    # Ensure that the object exists...
    assert len(parse.find_objects(r"GigabitEthernet1/2")) == 1
    with pytest.raises(ConfigListItemDoesNotExist):
        for obj in parse.find_objects(
            r"GigabitEthernet1/1|GigabitEthernet1/2", reverse=False
        ):
            obj.delete()


def testVal_BaseCfgLine_CiscoIOS_delete_w_auto_commit_w_reverse_01():
    """Ensure that we can delete multiple Cisco IOS configuration objects"""
    config = [
        "!",
        "hostname Example",
        "!",
        "interface GigabitEthernet1/0",
        " ip address 192.0.2.1 255.255.255.252",
        "!",
        "interface GigabitEthernet1/1",
        " ip address 192.0.2.5 255.255.255.252",
        "!",
        "interface GigabitEthernet1/2",
        " ip address 192.0.2.9 255.255.255.252",
        "!",
        "interface GigabitEthernet1/3",
        " ip address 192.0.2.11 255.255.255.252",
        "!",
        "end",
    ]

    parse = CiscoConfParse(config, auto_commit=True)
    # Ensure that the object exists...
    assert len(parse.find_objects(r"GigabitEthernet1/1")) == 1
    # Ensure that the object exists...
    assert len(parse.find_objects(r"GigabitEthernet1/2")) == 1

    # Execute the delete operation...
    for obj in parse.find_objects(
        r"GigabitEthernet1/1|GigabitEthernet1/2", reverse=True
    ):
        obj.delete()

    # Ensure that the object was deleted...
    assert len(parse.find_objects(r"GigabitEthernet1/1")) == 0
    # Ensure that the object was deleted...
    assert len(parse.find_objects(r"GigabitEthernet1/2")) == 0


def testVal_BaseCfgLine_insert_before_01():
    """Test BaseCfgLine().insert_before()"""
    parse = CiscoConfParse(
        # A fake double-indent on 'no ip proxy-arp'
        [
            "interface Ethernet0/0",
            " ip address 192.0.2.1 255.255.255.0",
            "  no ip proxy-arp",
        ]
    )
    obj = parse.find_objects("interface")[0]
    obj.insert_before("hostname Foo")
    parse.commit()
    uut = parse.find_objects("hostname")[0]
    assert isinstance(uut, IOSCfgLine) is True


def testVal_BaseCfgLine_insert_before_02():
    """Test BaseCfgLine().insert_before()"""
    parse = CiscoConfParse(
        # A fake double-indent on 'no ip proxy-arp'
        [
            "interface Ethernet0/0",
            " ip address 192.0.2.1 255.255.255.0",
            "  no ip proxy-arp",
        ]
    )
    obj = parse.find_objects("interface")[0]
    obj.insert_before(BaseCfgLine(line="hostname Foo"))
    parse.commit()
    uut = parse.find_objects("hostname")[0]
    assert isinstance(uut, IOSCfgLine) is True


def testVal_BaseCfgLine_insert_before_03():
    """Test BaseCfgLine().insert_before() raises TypeError"""
    parse = CiscoConfParse(
        # A fake double-indent on 'no ip proxy-arp'
        [
            "interface Ethernet0/0",
            " ip address 192.0.2.1 255.255.255.0",
            "  no ip proxy-arp",
        ]
    )
    obj = parse.find_objects("interface")[0]
    with pytest.raises(NotImplementedError):
        obj.insert_before(None)


def testVal_BaseCfgLine_insert_after_01():
    """Test BaseCfgLine().insert_after()"""
    parse = CiscoConfParse(
        # A fake double-indent on 'no ip proxy-arp'
        [
            "interface Ethernet0/0",
            " ip address 192.0.2.1 255.255.255.0",
            "  no ip proxy-arp",
        ]
    )
    obj = parse.find_objects("interface")[0]
    obj.insert_after(" description This or that")
    parse.commit()
    uut = parse.find_objects("description")[0]
    assert isinstance(uut, IOSCfgLine) is True


def testVal_BaseCfgLine_insert_after_02():
    """Test BaseCfgLine().insert_after()"""
    parse = CiscoConfParse(
        # A fake double-indent on 'no ip proxy-arp'
        [
            "interface Ethernet0/0",
            " ip address 192.0.2.1 255.255.255.0",
            "  no ip proxy-arp",
        ]
    )
    obj = parse.find_objects("interface")[0]
    obj.insert_after(BaseCfgLine(line=" description This or that"))
    parse.commit()
    uut = parse.find_objects("description")[0]
    assert isinstance(uut, IOSCfgLine) is True


def testVal_BaseCfgLine_insert_after_03():
    """Test BaseCfgLine().insert_after() raises TypeError"""
    parse = CiscoConfParse(
        # A fake double-indent on 'no ip proxy-arp'
        [
            "interface Ethernet0/0",
            " ip address 192.0.2.1 255.255.255.0",
            "  no ip proxy-arp",
        ]
    )
    obj = parse.find_objects("interface")[0]
    with pytest.raises(NotImplementedError):
        obj.insert_after(None)


def testVal_BaseCfgLine_append_to_family_01():
    """Test BaseCfgLine().append_to_family()"""
    parse = CiscoConfParse(
        # A fake double-indent on 'no ip proxy-arp'
        [
            "interface Ethernet0/0",
            " ip address 192.0.2.1 255.255.255.0",
            "  no ip proxy-arp",
        ]
    )
    obj = parse.find_objects("interface")[0]
    obj.append_to_family(" description This or that")
    assert parse.get_text() == [
        "interface Ethernet0/0",
        " ip address 192.0.2.1 255.255.255.0",
        "  no ip proxy-arp",
        " description This or that",
    ]


def testVal_BaseCfgLine_append_to_family_02():
    """Test BaseCfgLine().append_to_family() with a BaseCfgLine()"""
    parse = CiscoConfParse(
        # A fake double-indent on 'no ip proxy-arp'
        [
            "interface Ethernet0/0",
            " ip address 192.0.2.1 255.255.255.0",
            "  no ip proxy-arp",
        ]
    )
    obj = parse.find_objects("interface")[0]
    obj.append_to_family(BaseCfgLine(line=" description This or that"))
    # commit is required if appending a BaseCfgLine()
    uut = parse.objs[-1]
    assert uut.text == " description This or that"
    assert parse.objs[0].children[-1].text == " description This or that"


def testVal_BaseCfgLine_append_to_family_03():
    """Test BaseCfgLine().append_to_family(auto_indent=False)"""
    parse = CiscoConfParse(
        # A fake double-indent on 'no ip proxy-arp'
        [
            "interface Ethernet0/0",
            " ip address 192.0.2.1 255.255.255.0",
            "  no ip proxy-arp",
        ]
    )
    obj = parse.find_objects("interface")[0]
    obj.append_to_family("description This or that", auto_indent=False)
    parse.commit()
    uut = parse.objs[1]
    assert uut.text == "description This or that"
    # Now the children should be empty; this is a new parent line
    assert len(uut.children) == 1
    assert uut.children[0].text == " ip address 192.0.2.1 255.255.255.0"
    assert len(uut.all_children) == 2
    assert uut.all_children[1].text == "  no ip proxy-arp"


def testVal_BaseCfgLine_append_to_family_04():
    """Test BaseCfgLine().append_to_family(auto_indent=True) and last line is a grandchild"""
    parse = CiscoConfParse(
        # A fake double-indent on 'no ip proxy-arp'
        [
            "interface Ethernet0/0",
            " ip address 192.0.2.1 255.255.255.0",
            "  no ip proxy-arp",
        ]
    )
    obj = parse.find_objects("interface")[0]
    obj.append_to_family("description This or that", auto_indent=True)
    parse.commit()
    uut = parse.objs[-1]
    # Test that auto_indent worked
    assert uut.text == " description This or that"
    assert uut.children == []
    # Ensure this is the first line in the family
    assert parse.objs[0].children[-1].text == " description This or that"


def testVal_BaseCfgLine_append_to_family_05():
    """Test BaseCfgLine().append_to_family(auto_indent=True) and last line is a grandchild."""
    parse = CiscoConfParse(
        # A fake double-indent on 'no ip proxy-arp'
        [
            "interface Ethernet0/0",
            " ip address 192.0.2.1 255.255.255.0",
            "  no ip proxy-arp",
        ]
    )
    obj = parse.find_objects("interface")[0]
    obj.append_to_family("description This or that", auto_indent=True)

    assert obj.children[-1].text == " description This or that"

    uut = parse.objs[1]
    assert len(uut.children) == 1
    # Ensure the line is single indented after insert
    # below a grandchild
    # Ensure this is the last line in the family
    assert parse.objs[0].all_children[1].text == "  no ip proxy-arp"


def testVal_BaseCfgLine_append_to_family_06():
    """Test BaseCfgLine().append_to_family(auto_indent=True) appending a great-grandchild of Ethernet0/0 (below '  no ip proxy-arp')."""
    parse = CiscoConfParse(
        # A fake double-indent on 'no ip proxy-arp'
        [
            "interface Ethernet0/0",
            " ip address 192.0.2.1 255.255.255.0",
            "  no ip proxy-arp",
        ]
    )
    obj = parse.find_objects("proxy-arp")[0]
    obj.append_to_family(
        "a fake great-grandchild of interface Ethernet0/0", auto_indent=True
    )
    uut = parse.objs[-1]
    assert uut.children == []
    # Ensure the line is correctly indented after insert
    # below a grandchild
    assert uut.text == "   a fake great-grandchild of interface Ethernet0/0"
    # Ensure that the number of direct children is still correct
    assert len(parse.objs[0].children) == 1
    # Ensure this is the last line in the family
    assert parse.objs[0].all_children[-2].text == "  no ip proxy-arp"
    assert (
        parse.objs[0].all_children[-1].text
        == "   a fake great-grandchild of interface Ethernet0/0"
    )


def testVal_BaseCfgLine_verbose_01():
    """Test BaseCfgLine().verbose"""
    obj01 = BaseCfgLine(all_lines=None, line="interface Ethernet0/0")
    obj01.linenum = 1
    obj02 = BaseCfgLine(all_lines=None, line=" ip address 192.0.2.1 255.255.255.0")
    obj02.linenum = 2
    obj03 = BaseCfgLine(all_lines=None, line=" no ip proxy-arp")
    obj03.linenum = 3
    obj01.children = [obj02, obj03]
    assert (
        obj01.verbose
        == "<BaseCfgLine # 1 'interface Ethernet0/0' (child_indent: 0 / len(children): 2 / family_endpoint: 3)>"
    )
    assert (
        obj02.verbose
        == "<BaseCfgLine # 2 ' ip address 192.0.2.1 255.255.255.0' (no_children / family_endpoint: 2)>"
    )


def testVal_BaseCfgLine_is_comment_01():
    """Test BaseCfgLine().is_comment"""
    parse = CiscoConfParse(["! hostname Foo"])
    obj01 = parse.objs[0]
    assert obj01.is_comment is True

    parse = CiscoConfParse([" hostname !Foo"])
    obj02 = parse.objs[0]
    assert obj02.is_comment is False

    parse = CiscoConfParse([" hostname Foo!"])
    obj03 = parse.objs[0]
    assert obj03.is_comment is False


def testVal_BaseCfgLine_CiscoIOS_replace_01():
    """Ensure that we can call replace() without changing the original Cisco IOS configuration"""
    config = [
        "!",
        "hostname Example",
        "!",
        "interface GigabitEthernet1/0",
        " ip address 192.0.2.1 255.255.255.252",
        "!",
        "interface GigabitEthernet1/1",
        " ip address 192.0.2.5 255.255.255.252",
        "!",
        "interface GigabitEthernet1/2",
        " ip address 192.0.2.9 255.255.255.252",
        "!",
        "interface GigabitEthernet1/3",
        " ip address 192.0.2.11 255.255.255.252",
        "!",
        "end",
    ]

    parse = CiscoConfParse(config, auto_commit=True)
    # Ensure that the object exists...
    assert len(parse.find_objects(r"GigabitEthernet1/1")) == 1
    # Ensure that the object exists...
    assert len(parse.find_objects(r"GigabitEthernet1/2")) == 1

    # Execute the delete operation...
    for obj in parse.find_objects(r"GigabitEthernet1/1", reverse=True):
        newtext = obj.replace("GigabitEthernet1/1", "Loopback1")
        assert newtext == "interface Loopback1"

    # Ensure that the object was deleted...
    assert len(parse.find_objects(r"GigabitEthernet1/1")) == 1
    # Ensure that the object was deleted...
    assert len(parse.find_objects(r"Loopback1")) == 0


def testVal_BaseCfgLine_CiscoIOS_replace_text_01():
    """Ensure that we can call replace_text() and it will change the original Cisco IOS configuration"""
    config = [
        "!",
        "hostname Example",
        "!",
        "interface GigabitEthernet1/0",
        " ip address 192.0.2.1 255.255.255.252",
        "!",
        "interface GigabitEthernet1/1",
        " ip address 192.0.2.5 255.255.255.252",
        "!",
        "interface GigabitEthernet1/2",
        " ip address 192.0.2.9 255.255.255.252",
        "!",
        "interface GigabitEthernet1/3",
        " ip address 192.0.2.11 255.255.255.252",
        "!",
        "end",
    ]

    parse = CiscoConfParse(config, auto_commit=True)
    # Ensure that the object exists...
    assert len(parse.find_objects(r"GigabitEthernet1/1")) == 1
    # Ensure that the object exists...
    assert len(parse.find_objects(r"GigabitEthernet1/2")) == 1

    # Execute the delete operation...
    for obj in parse.find_objects(r"GigabitEthernet1/1", reverse=True):
        newtext = obj.replace_text("GigabitEthernet1/1", "Loopback1")
        assert newtext == "interface Loopback1"

    # Ensure that the object was deleted...
    assert len(parse.find_objects(r"GigabitEthernet1/1")) == 0
    # Ensure that the object was deleted...
    assert len(parse.find_objects(r"Loopback1")) == 1


def testVal_re_match_iter_typed_parent_default_type_norecurse():
    """Test that re_match_iter_typed(recurse=False) finds the parent and returns the default `result_type`, which is `str`"""
    config = """!
interface GigabitEthernet 1/1
 switchport mode trunk
 switchport trunk native vlan 911
 channel-group 25 mode active
!
!
class-map match-all IP_PREC_MEDIUM
 match ip precedence 2  3  4  5
class-map match-all IP_PREC_HIGH
 match ip precedence 6  7
class-map match-all TEST
class-map match-all TO_ATM
 match access-group name NOT_INTERNAL
class-map match-any ALL
 match any
!
!
policy-map EXTERNAL_CBWFQ
 class IP_PREC_HIGH
  priority percent 10
  police cir percent 10
    conform-action transmit
    exceed-action drop
 class IP_PREC_MEDIUM
  bandwidth percent 50
  queue-limit 100
 class class-default
  bandwidth percent 40
  queue-limit 100
policy-map SHAPE_HEIR
 class ALL
  shape average 630000
  service-policy EXTERNAL_CBWFQ
!
!"""
    cfg = CiscoConfParse(config.splitlines(), factory=True)
    obj = cfg.find_objects("^interface")[0]

    uut_result = obj.re_match_iter_typed(
        r"^interface\s+(\S.+)$",
        group=1,
        default="_no_match",
        recurse=False,
        debug=False,
    )
    # Check that base assumption is True... we are checking the right parent
    assert obj.text == "interface GigabitEthernet 1/1"
    assert uut_result == "GigabitEthernet 1/1"


def testVal_re_match_iter_typed_first_child_default_type_norecurse():
    """Test that re_match_iter_typed(recurse=False) finds the first child and returns the default `result_type`, which is `str`"""
    config = """!
interface GigabitEthernet 1/1
 switchport mode trunk
 switchport trunk native vlan 911
 channel-group 25 mode active
!
!
class-map match-all IP_PREC_MEDIUM
 match ip precedence 2  3  4  5
class-map match-all IP_PREC_HIGH
 match ip precedence 6  7
class-map match-all TEST
class-map match-all TO_ATM
 match access-group name NOT_INTERNAL
class-map match-any ALL
 match any
!
!
policy-map EXTERNAL_CBWFQ
 class IP_PREC_HIGH
  priority percent 10
  police cir percent 10
    conform-action transmit
    exceed-action drop
 class IP_PREC_MEDIUM
  bandwidth percent 50
  queue-limit 100
 class class-default
  bandwidth percent 40
  queue-limit 100
policy-map SHAPE_HEIR
 class ALL
  shape average 630000
  service-policy EXTERNAL_CBWFQ
!
!"""
    cfg = CiscoConfParse(config.splitlines(), factory=True)
    obj = cfg.find_objects("^interface")[0]

    uut_result = obj.re_match_iter_typed(
        r"switchport\s+mode\s+(\S+)$",
        group=1,
        default="_no_match",
        recurse=False,
        debug=False,
    )
    # Check that base assumption is True... we are checking the right parent
    assert obj.text == "interface GigabitEthernet 1/1"
    assert uut_result == "trunk"


def testVal_re_match_iter_typed_first_child_default_type_recurse():
    """Test that re_match_iter_typed(recurse=True) finds the first child and returns the default `result_type`, which is `str`"""
    config = """!
interface GigabitEthernet 1/1
 switchport mode trunk
 switchport trunk native vlan 911
 channel-group 25 mode active
!
!
class-map match-all IP_PREC_MEDIUM
 match ip precedence 2  3  4  5
class-map match-all IP_PREC_HIGH
 match ip precedence 6  7
class-map match-all TEST
class-map match-all TO_ATM
 match access-group name NOT_INTERNAL
class-map match-any ALL
 match any
!
!
policy-map EXTERNAL_CBWFQ
 class IP_PREC_HIGH
  priority percent 10
  police cir percent 10
    conform-action transmit
    exceed-action drop
 class IP_PREC_MEDIUM
  bandwidth percent 50
  queue-limit 100
 class class-default
  bandwidth percent 40
  queue-limit 100
policy-map SHAPE_HEIR
 class ALL
  shape average 630000
  service-policy EXTERNAL_CBWFQ
!
!"""
    cfg = CiscoConfParse(config.splitlines(), factory=True)
    obj = cfg.find_objects("^interface")[0]

    uut_result = obj.re_match_iter_typed(
        r"switchport\s+mode\s+(\S+)$",
        group=1,
        recurse=True,
        default="_no_match",
        debug=False,
    )
    # Check that base assumption is True... we are checking the right parent
    assert obj.text == "interface GigabitEthernet 1/1"
    assert uut_result == "trunk"


def testVal_re_match_iter_typed_child_deep_fail_norecurse():
    """Test that re_match_iter_typed(recurse=False) fails on a deep recurse through multiple children"""
    config = """!
interface GigabitEthernet 1/1
 switchport mode trunk
 switchport trunk native vlan 911
 channel-group 25 mode active
!
!
class-map match-all IP_PREC_MEDIUM
 match ip precedence 2  3  4  5
class-map match-all IP_PREC_HIGH
 match ip precedence 6  7
class-map match-all TEST
class-map match-all TO_ATM
 match access-group name NOT_INTERNAL
class-map match-any ALL
 match any
!
!
policy-map EXTERNAL_CBWFQ
 class IP_PREC_HIGH
  priority percent 10
  police cir percent 10
    conform-action transmit
    exceed-action drop
 class IP_PREC_MEDIUM
  bandwidth percent 50
  queue-limit 100
 class class-default
  bandwidth percent 40
  queue-limit 100
policy-map SHAPE_HEIR
 class ALL
  shape average 630000
  service-policy EXTERNAL_CBWFQ
!
!"""
    cfg = CiscoConfParse(config.splitlines(), factory=True)
    obj = cfg.find_objects(r"^policy.map\s+EXTERNAL_CBWFQ")[0]

    uut_result = obj.re_match_iter_typed(
        r"exceed\-action\s+(\S+)$",
        group=1,
        recurse=False,
        default="_no_match",
        debug=False,
    )
    # Check that base assumption is True... we are checking the right parent
    assert obj.text == "policy-map EXTERNAL_CBWFQ"
    assert uut_result == "_no_match"


def testVal_re_match_iter_typed_child_deep_pass_recurse():
    """Test that re_match_iter_typed(recurse=False) finds during a deep recurse through multiple levels of children"""
    config = """!
interface GigabitEthernet 1/1
 switchport mode trunk
 switchport trunk native vlan 911
 channel-group 25 mode active
!
!
class-map match-all IP_PREC_MEDIUM
 match ip precedence 2  3  4  5
class-map match-all IP_PREC_HIGH
 match ip precedence 6  7
class-map match-all TEST
class-map match-all TO_ATM
 match access-group name NOT_INTERNAL
class-map match-any ALL
 match any
!
!
policy-map EXTERNAL_CBWFQ
 class IP_PREC_HIGH
  priority percent 10
  police cir percent 10
    conform-action transmit
    exceed-action drop
 class IP_PREC_MEDIUM
  bandwidth percent 50
  queue-limit 100
 class class-default
  bandwidth percent 40
  queue-limit 100
policy-map SHAPE_HEIR
 class ALL
  shape average 630000
  service-policy EXTERNAL_CBWFQ
!
!"""
    cfg = CiscoConfParse(config.splitlines(), factory=True)
    obj = cfg.find_objects(r"^policy.map\s+EXTERNAL_CBWFQ")[0]

    uut_result = obj.re_match_iter_typed(
        r"exceed\-action\s+(\S+)$",
        group=1,
        recurse=True,
        default="_no_match",
        debug=False,
    )
    # Check that base assumption is True... we are checking the right parent
    assert obj.text == "policy-map EXTERNAL_CBWFQ"
    assert uut_result == "drop"


def testVal_re_match_iter_typed_second_child_default_type_recurse():
    """Test that re_match_iter_typed(recurse=False) finds the second child and returns the default `result_type`, which is `str`"""
    config = """!
interface GigabitEthernet 1/1
 switchport mode trunk
 switchport trunk native vlan 911
 channel-group 25 mode active
!
!
class-map match-all IP_PREC_MEDIUM
 match ip precedence 2  3  4  5
class-map match-all IP_PREC_HIGH
 match ip precedence 6  7
class-map match-all TEST
class-map match-all TO_ATM
 match access-group name NOT_INTERNAL
class-map match-any ALL
 match any
!
!
policy-map EXTERNAL_CBWFQ
 class IP_PREC_HIGH
  priority percent 10
  police cir percent 10
    conform-action transmit
    exceed-action drop
 class IP_PREC_MEDIUM
  bandwidth percent 50
  queue-limit 100
 class class-default
  bandwidth percent 40
  queue-limit 100
policy-map SHAPE_HEIR
 class ALL
  shape average 630000
  service-policy EXTERNAL_CBWFQ
!
!"""
    cfg = CiscoConfParse(config.splitlines(), factory=True)
    obj = cfg.find_objects("^interface")[0]

    uut_result = obj.re_match_iter_typed(
        r"switchport\s+trunk\s+native\s+vlan\s+(\S+)$",
        group=1,
        recurse=True,
        default="_no_match",
        debug=False,
    )
    # Check that base assumption is True... we are checking the right parent
    assert obj.text == "interface GigabitEthernet 1/1"
    assert uut_result == "911"


def testVal_re_match_iter_typed_second_child_int_type_recurse():
    """Test that re_match_iter_typed(recurse=False) finds the second child and returns the default `result_type`, which is `str`"""
    config = """!
interface GigabitEthernet 1/1
 switchport mode trunk
 switchport trunk native vlan 911
 channel-group 25 mode active
!
!
class-map match-all IP_PREC_MEDIUM
 match ip precedence 2  3  4  5
class-map match-all IP_PREC_HIGH
 match ip precedence 6  7
class-map match-all TEST
class-map match-all TO_ATM
 match access-group name NOT_INTERNAL
class-map match-any ALL
 match any
!
!
policy-map EXTERNAL_CBWFQ
 class IP_PREC_HIGH
  priority percent 10
  police cir percent 10
    conform-action transmit
    exceed-action drop
 class IP_PREC_MEDIUM
  bandwidth percent 50
  queue-limit 100
 class class-default
  bandwidth percent 40
  queue-limit 100
policy-map SHAPE_HEIR
 class ALL
  shape average 630000
  service-policy EXTERNAL_CBWFQ
!
!"""
    cfg = CiscoConfParse(config.splitlines(), factory=True)
    obj = cfg.find_objects("^interface")[0]

    uut_result = obj.re_match_iter_typed(
        r"switchport\s+trunk\s+native\s+vlan\s+(\S+)$",
        group=1,
        result_type=int,
        recurse=True,
        default="_no_match",
        debug=False,
    )
    # Check that base assumption is True... we are checking the right parent
    assert obj.text == "interface GigabitEthernet 1/1"
    assert uut_result == 911


def testVal_re_match_iter_typed_named_regex_group_second_child_int_type_recurse():
    """Test that re_match_iter_typed(recurse=False) finds the second child with a named regex"""
    config = """!
interface GigabitEthernet 1/1
 switchport mode trunk
 switchport trunk native vlan 911
 channel-group 25 mode active
!
!
class-map match-all IP_PREC_MEDIUM
 match ip precedence 2  3  4  5
class-map match-all IP_PREC_HIGH
 match ip precedence 6  7
class-map match-all TEST
class-map match-all TO_ATM
 match access-group name NOT_INTERNAL
class-map match-any ALL
 match any
!
!
policy-map EXTERNAL_CBWFQ
 class IP_PREC_HIGH
  priority percent 10
  police cir percent 10
    conform-action transmit
    exceed-action drop
 class IP_PREC_MEDIUM
  bandwidth percent 50
  queue-limit 100
 class class-default
  bandwidth percent 40
  queue-limit 100
policy-map SHAPE_HEIR
 class ALL
  shape average 630000
  service-policy EXTERNAL_CBWFQ
!
!"""
    cfg = CiscoConfParse(config.splitlines(), factory=True)
    obj = cfg.find_objects("^interface")[0]

    uut_result = obj.re_match_iter_typed(
        r"switchport\s+trunk\s+native\s+vlan\s+(?P<native_vlan>\S+)$",
        group=1,
        result_type=int,
        recurse=True,
        default="_no_match",
        debug=False,
    )
    # Check that base assumption is True... we are checking the right parent
    assert obj.text == "interface GigabitEthernet 1/1"
    assert uut_result == 911


def testVal_re_match_iter_typed_intf_norecurse():
    """Test that re_match_iter_typed(recurse=False) finds the parent and returns a `str`"""
    config = """!
interface GigabitEthernet 1/1
 switchport mode trunk
 switchport trunk native vlan 911
 channel-group 25 mode active
!
!
class-map match-all IP_PREC_MEDIUM
 match ip precedence 2  3  4  5
class-map match-all IP_PREC_HIGH
 match ip precedence 6  7
class-map match-all TEST
class-map match-all TO_ATM
 match access-group name NOT_INTERNAL
class-map match-any ALL
 match any
!
!
policy-map EXTERNAL_CBWFQ
 class IP_PREC_HIGH
  priority percent 10
  police cir percent 10
    conform-action transmit
    exceed-action drop
 class IP_PREC_MEDIUM
  bandwidth percent 50
  queue-limit 100
 class class-default
  bandwidth percent 40
  queue-limit 100
policy-map SHAPE_HEIR
 class ALL
  shape average 630000
  service-policy EXTERNAL_CBWFQ
!
!"""
    cfg = CiscoConfParse(config.splitlines(), factory=True)
    obj = cfg.find_objects("^interface")[0]

    uut_result = obj.re_match_iter_typed(
        r"^interface\s+(?P<intf>\S.+)$",
        groupdict={"intf": str},
        default="_no_match",
        recurse=False,
        debug=False,
    )
    # Check that base assumption is True... we are checking the right parent
    assert obj.text == "interface GigabitEthernet 1/1"
    assert uut_result["intf"] == "GigabitEthernet 1/1"


def testVal_re_match_iter_typed_vlan_recurse():
    """Test that re_match_iter_typed(recurse=False) finds the second child and returns an `int`"""
    config = """!
interface GigabitEthernet 1/1
 switchport mode trunk
 switchport trunk native vlan 911
 channel-group 25 mode active
!
!
class-map match-all IP_PREC_MEDIUM
 match ip precedence 2  3  4  5
class-map match-all IP_PREC_HIGH
 match ip precedence 6  7
class-map match-all TEST
class-map match-all TO_ATM
 match access-group name NOT_INTERNAL
class-map match-any ALL
 match any
!
!
policy-map EXTERNAL_CBWFQ
 class IP_PREC_HIGH
  priority percent 10
  police cir percent 10
    conform-action transmit
    exceed-action drop
 class IP_PREC_MEDIUM
  bandwidth percent 50
  queue-limit 100
 class class-default
  bandwidth percent 40
  queue-limit 100
policy-map SHAPE_HEIR
 class ALL
  shape average 630000
  service-policy EXTERNAL_CBWFQ
!
!"""
    cfg = CiscoConfParse(config.splitlines(), factory=True)
    obj = cfg.find_objects("^interface")[0]

    uut_result = obj.re_match_iter_typed(
        r"switchport\s+trunk\s+native\s+vlan\s+(?P<vlan>\S+)$",
        groupdict={"vlan": int},
        recurse=True,
        default="_no_match",
        debug=False,
    )
    # Check that base assumption is True... we are checking the right parent
    assert obj.text == "interface GigabitEthernet 1/1"
    assert uut_result["vlan"] == 911


def testVal_re_list_iter_typed_01():
    """Test that we get a correct list of matches for a simple use-case (casting as an IPv6Obj)"""
    config = [
        "!",
        "interface Serial1/0",
        " ip address 1.1.1.1 255.255.255.252",
        " ipv6 address dead:beef::11/64",
        " ipv6 address dead:beef::12/64",
        " ipv6 address negotiated",
        "!",
        "interface Serial2/0",
        " ip address 1.1.1.5 255.255.255.252",
        " ipv6 address dead:beef::21/64",
        " ipv6 address dead:beef::22/64",
        "!",
    ]
    parse = CiscoConfParse(config)
    obj = parse.find_objects(r"interface Serial1/0")[0]
    uut = obj.re_list_iter_typed(r"ipv6\s+address\s+(\S+?\/\d+)", result_type=IPv6Obj)
    assert isinstance(uut, list)
    assert len(uut) == 2
    assert uut[0] == IPv6Obj("dead:beef::11/64")
    assert uut[1] == IPv6Obj("dead:beef::12/64")


def testVal_re_list_iter_typed_02():
    """Test that we get an empty list if there are no regex matches"""
    config = [
        "!",
        "interface Serial1/0",
        " ip address 1.1.1.1 255.255.255.252",
        " ipv6 address dead:beef::11/64",
        " ipv6 address dead:beef::12/64",
        " ipv6 address negotiated",
        "!",
        "interface Serial2/0",
        " ip address 1.1.1.5 255.255.255.252",
        " ipv6 address dead:beef::21/64",
        " ipv6 address dead:beef::22/64",
        "!",
    ]
    parse = CiscoConfParse(config)
    obj = parse.find_objects(r"interface Serial1/0")[0]
    uut = obj.re_list_iter_typed(
        r"this_should_not_match_anything\s+(\S+?\/\d+)", result_type=IPv6Obj
    )
    assert isinstance(uut, list)
    assert len(uut) == 0


def testVal_last_family_linenum_01():
    """Test the last_family_linenum attribute"""
    parse = CiscoConfParse(["first"])
    assert parse.config_objs[0].last_family_linenum == 0


def testVal_last_family_linenum_02():
    """Test the last_family_linenum attribute after appending one brother element"""
    parse = CiscoConfParse(["first"])
    parse.config_objs.append("second")
    assert parse.config_objs[1].last_family_linenum == 1


def testVal_last_family_linenum_03():
    """Test the last_family_linenum attribute after appending a nephew element"""
    parse = CiscoConfParse(["first"])
    parse.config_objs.append("second")
    parse.config_objs.append(" second-child")
    assert parse.config_objs[0].last_family_linenum == 2


def testVal_last_family_linenum_04():
    """Test the last_family_linenum attribute after appending a lot of family"""
    parse = CiscoConfParse(["first"])
    parse.config_objs.append("second")
    parse.config_objs.append(" second-child")
    parse.config_objs.append("  second-child-child")
    parse.config_objs[1].append_to_family("third")
    assert parse.config_objs[1].last_family_linenum == 4


def testVal_append_to_family_01():
    """Test that default syntax of CiscoConfParse is IOS and it correctly appends an IOSCfgLine()"""
    parse = CiscoConfParse()
    parse.config_objs.append("first")

    assert isinstance(parse.config_objs[0], IOSCfgLine)


def testVal_append_to_family_02():
    """Test basic parent-append operations at the same indent-level and ensure that order is preserved."""
    parse = CiscoConfParse()
    parse.config_objs.append("first")
    obj = parse.find_objects("first")[0]
    obj.append_to_family("second")
    obj.append_to_family("third")

    assert parse.config_objs[0].text == "first"
    assert parse.config_objs[1].text == "second"
    assert parse.config_objs[2].text == "third"


def testVal_append_to_family_03():
    """Test parent-append operations and ensure that order is preserved, and children are assigned."""
    parse = CiscoConfParse(syntax="ios")
    parse.config_objs.append("first")
    obj = parse.find_objects("first")[0]
    obj.append_to_family("second")
    # Append a child out-of-order, but still a child of first
    obj.append_to_family(" first-child")

    assert isinstance(parse.config_objs[0], IOSCfgLine)
    assert parse.config_objs[0].text == "first"
    assert parse.config_objs[0].parent == parse.config_objs[0]

    assert isinstance(parse.config_objs[1], IOSCfgLine)
    assert parse.config_objs[1].text == " first-child"
    assert parse.config_objs[1].parent == parse.config_objs[0]

    assert isinstance(parse.config_objs[2], IOSCfgLine)
    assert parse.config_objs[2].text == "second"
    assert parse.config_objs[2].parent == parse.config_objs[2]


def testVal_append_to_family_04():
    """Test parent-append operations and ensure that order is preserved, and children are assigned / preserved."""
    parse = CiscoConfParse()
    parse.config_objs.append("first")
    obj01 = parse.find_objects("first")[0]
    obj01.append_to_family(" first-child")
    obj01.append_to_family(" second-child")

    obj02 = parse.find_child_objects(["first", " first-child"])[0]
    obj02.append_to_family("  first-child-child")

    assert parse.config_objs[0].text == "first"
    assert parse.config_objs[1].text == " first-child"
    assert parse.config_objs[2].text == "  first-child-child"
    assert parse.config_objs[3].text == " second-child"


def testVal_append_to_family_05():
    """Test parent-append operations and ensure that a NotImplementedError() is raised if a direct grandchild is appended with append_to_family()."""
    parse = CiscoConfParse()
    parse.config_objs.append("first")
    obj01 = parse.find_objects("first")[0]
    obj01.append_to_family(" first-child")
    with pytest.raises(NotImplementedError):
        obj01.append_to_family("  first-child-child")
