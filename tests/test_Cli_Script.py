r"""test_Cli_Script.py - Parse, Query, Build, and Modify IOS-style configs

     Copyright (C) 2024      David Michael Pennington

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

from ciscoconfparse2.cli_script import CliApplication
from ciscoconfparse2.cli_script import ccp_script_entry

#find_ip46_addr_matches()
def testValues_ccp_script_entry_cliapplication_01():
    """Ensure that ccp_script_entry return value is an instance of CliApplication()"""
    cliapp = ccp_script_entry("ccp_faked ipgrep -s 172.16.1.5/32 fixtures/configs/sample_01.ios")
    assert isinstance(cliapp, CliApplication)

def testValues_ccp_script_entry_cliapplication_args_01():
    """Ensure that CliApplication().args is a single-element list"""
    cliapp = ccp_script_entry("ccp_faked ipgrep -s 172.16.1.5/32 fixtures/configs/sample_01.ios")
    assert cliapp.args == ['']

def testValues_ccp_script_entry_cliapplication_ipgrep_01():
    """Ensure that CliApplication() ipgrep with the unique flag set is a list of six IP addresses"""
    cliapp = ccp_script_entry("ccp_faked ipgrep -s 172.16.1.5/32 fixtures/configs/sample_01.ios")
    assert len(cliapp.stdout) == 6
    assert cliapp.unique is False
    assert cliapp.subnet == '172.16.1.5/32'
    assert cliapp.stdout == ['172.16.1.5',
                             '172.16.1.5',
                             '172.16.1.5',
                             '172.16.1.5',
                             '172.16.1.5',
                             '172.16.1.5',]

def testValues_ccp_script_entry_cliapplication_ipgrep_02():
    """Ensure that CliApplication() ipgrep with the unique flag set is a list of one IP address"""
    cliapp = ccp_script_entry("ccp_faked ipgrep -u -s 172.16.1.5/32 fixtures/configs/sample_01.ios")
    assert len(cliapp.stdout) == 1
    assert cliapp.unique is True
    assert cliapp.subnet == '172.16.1.5/32'
    assert cliapp.stdout == ['172.16.1.5',]

def testValues_ccp_script_entry_cliapplication_branch_01():
    """Ensure that CliApplication() branch as original output flag set is a list of one IP address"""
    cliapp = ccp_script_entry("ccp_faked branch -o original -a 'interface Null0' fixtures/configs/sample_01.ios")
    assert len(cliapp.stdout) == 2
    assert cliapp.output_format == 'original'
    assert cliapp.args == ['interface Null0']
    assert cliapp.stdout == ['interface Null0',
                             ' no ip unreachables',]

def testValues_ccp_script_entry_cliapplication_branch_02():
    """Ensure that CliApplication() branch as original output flag set is a list of one IP address"""
    cliapp = ccp_script_entry("ccp_faked branch -a 'interface Null0,unreachables' fixtures/configs/sample_01.ios")
    assert len(cliapp.stdout) == 2
    assert cliapp.output_format == 'raw_text'
    assert cliapp.args == ['interface Null0', 'unreachables']
    assert cliapp.stdout == ['interface Null0', ' no ip unreachables',]

def testValues_ccp_script_entry_cliapplication_parent_01():
    """Ensure that CliApplication() parent as original output flag set is a list of one IP address"""
    cliapp = ccp_script_entry("ccp_faked parent -a 'interface Null0' fixtures/configs/sample_01.ios")
    assert len(cliapp.stdout) == 1
    assert cliapp.output_format == 'raw_text'
    assert cliapp.args == ['interface Null0']
    assert cliapp.stdout == ['interface Null0']

def testValues_ccp_script_entry_cliapplication_child_01():
    """Ensure that CliApplication() parent as original output flag set is a list of one IP address"""
    cliapp = ccp_script_entry("ccp_faked child -a 'interface Null0,unreachables' fixtures/configs/sample_01.ios")
    assert len(cliapp.stdout) == 1
    assert cliapp.output_format == 'raw_text'
    assert cliapp.args == ['interface Null0', 'unreachables']
    assert cliapp.stdout == [' no ip unreachables']
