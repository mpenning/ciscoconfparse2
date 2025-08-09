r"""__init__.py - Parse, Query, Build, and Modify IOS-style configurations

Copyright (C) 2023 David Michael Pennington

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

import sys

from loguru import logger

from ciscoconfparse2.cli_script import ccp_script_entry

from ciscoconfparse2.ccp_util import PythonOptimizeCheck
from ciscoconfparse2.ciscoconfparse2 import *
from ciscoconfparse2.ccp_util import IPv4Obj
from ciscoconfparse2.ccp_util import IPv6Obj
from ciscoconfparse2.ccp_util import MACObj, EUI64Obj
from ciscoconfparse2.ccp_util import CiscoIOSInterface, CiscoIOSXRInterface
from ciscoconfparse2.ccp_util import CiscoRange
from ciscoconfparse2.ccp_util import run_this_posix_command
from ciscoconfparse2.ccp_util import ccp_logger_control
from ciscoconfparse2.ccp_util import configure_loguru
from ciscoconfparse2.ccp_util import as_text_list
from ciscoconfparse2.ccp_util import junos_unsupported
from ciscoconfparse2.ccp_util import log_function_call
from ciscoconfparse2.ccp_util import enforce_valid_types
from ciscoconfparse2.ccp_util import fix_repeated_words
from ciscoconfparse2.ccp_util import _get_ipv4
from ciscoconfparse2.ccp_util import _get_ipv6
from ciscoconfparse2.ccp_util import ip_factory
from ciscoconfparse2.ccp_util import collapse_addresses
from ciscoconfparse2.ccp_util import L4Object
from ciscoconfparse2.ccp_util import DNSResponse
from ciscoconfparse2.ccp_util import dns_query
from ciscoconfparse2.ccp_util import check_valid_ipaddress


from dns.resolver import Resolver
from dns.exception import DNSException

# Throw errors for PYTHONOPTIMIZE and `python -O ...` by executing
#     PythonOptimizeCheck()...
_ = PythonOptimizeCheck()
