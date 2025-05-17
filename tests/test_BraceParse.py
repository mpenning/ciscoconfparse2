r"""test_BraceParse.py - Parse, Query, Build, and Modify IOS-style configs

Copyright (C) 2024-2025     David Michael Pennington

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

import os
import sys

sys.path.insert(0, "..")

import pytest
from ciscoconfparse2.ciscoconfparse2 import BraceParse

THIS_TEST_PATH = os.path.dirname(os.path.abspath(__file__))


def testValues_find_objects_list_01(parse_fixture_j03):
    """Ensure that find_objects() accepts a list input"""
