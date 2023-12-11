"""
ciscoconfparse2.py - Parse, Query, Build, and Modify IOS-style configs.

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

from collections.abc import Sequence
from collections import UserList
from typing import Any, Union
import inspect
import pathlib
import locale
import time
import copy
import sys
import re
import os


from deprecated import deprecated
from loguru import logger
import attrs
import hier_config
import yaml
import toml

from ciscoconfparse2.models_cisco import IOSRouteLine
from ciscoconfparse2.models_cisco import IOSIntfLine
from ciscoconfparse2.models_cisco import IOSAccessLine, IOSIntfGlobal
from ciscoconfparse2.models_cisco import IOSCfgLine

from ciscoconfparse2.models_nxos import NXOSHostnameLine, NXOSRouteLine
from ciscoconfparse2.models_nxos import NXOSAccessLine, NXOSIntfGlobal
from ciscoconfparse2.models_nxos import NXOSCfgLine, NXOSIntfLine
from ciscoconfparse2.models_nxos import NXOSvPCLine

from ciscoconfparse2.models_iosxr import IOSXRCfgLine, IOSXRIntfLine

from ciscoconfparse2.models_asa import ASAObjGroupNetwork
from ciscoconfparse2.models_asa import ASAObjGroupService
from ciscoconfparse2.models_asa import ASAHostnameLine
from ciscoconfparse2.models_asa import ASAObjNetwork
from ciscoconfparse2.models_asa import ASAObjService
from ciscoconfparse2.models_asa import ASAIntfGlobal
from ciscoconfparse2.models_asa import ASAIntfLine
from ciscoconfparse2.models_asa import ASACfgLine
from ciscoconfparse2.models_asa import ASAName
from ciscoconfparse2.models_asa import ASAAclLine

# from ciscoconfparse2.models_junos import JunosIntfLine
from ciscoconfparse2.models_junos import JunosCfgLine

from ciscoconfparse2.ccp_abc import BaseCfgLine

from ciscoconfparse2.ccp_util import fix_repeated_words
from ciscoconfparse2.ccp_util import enforce_valid_types
from ciscoconfparse2.ccp_util import junos_unsupported
from ciscoconfparse2.ccp_util import configure_loguru

from ciscoconfparse2.errors import ConfigListItemDoesNotExist
from ciscoconfparse2.errors import RequirementFailure
from ciscoconfparse2.errors import InvalidParameters

# Not using ccp_re yet... still a work in progress
# from ciscoconfparse2.ccp_util import ccp_re

ALL_IOS_FACTORY_CLASSES = [
    IOSIntfLine,
    IOSRouteLine,
    IOSAccessLine,
    IOSIntfGlobal,
    IOSCfgLine,        # IOSCfgLine MUST be last
]
ALL_NXOS_FACTORY_CLASSES = [
    NXOSIntfLine,
    NXOSRouteLine,
    NXOSAccessLine,
    NXOSvPCLine,
    NXOSHostnameLine,
    NXOSIntfGlobal,
    NXOSCfgLine,        # NXOSCfgLine MUST be last
]
ALL_IOSXR_FACTORY_CLASSES = [
    IOSXRIntfLine,
    IOSXRCfgLine,
]
ALL_ASA_FACTORY_CLASSES = [
    ASAIntfLine,
    ASAName,
    ASAObjNetwork,
    ASAObjService,
    ASAObjGroupNetwork,
    ASAObjGroupService,
    ASAIntfGlobal,
    ASAHostnameLine,
    ASAAclLine,
    ASACfgLine,        # ASACfgLine MUST be last
]
ALL_JUNOS_FACTORY_CLASSES = [
    ##########################################################################
    # JunosIntfLine is rather broken; JunosCfgLine should be enough
    ##########################################################################
    # JunosIntfLine,
    JunosCfgLine,      # JunosCfgLine MUST be last
]

# Indexing into CFGLINE is normally faster than serial if-statements...
CFGLINE = {
    "ios": IOSCfgLine,
    "nxos": NXOSCfgLine,
    "iosxr": IOSXRCfgLine,
    "asa": ASACfgLine,
    "junos": JunosCfgLine,
}

ALL_VALID_SYNTAX = (
    "ios",
    "nxos",
    "iosxr",
    "asa",
    "junos",
)

ALL_BRACE_SYNTAX = {
    "junos",
}


@logger.catch(reraise=True)
def get_version_number():
    """Read the version number from 'pyproject.toml', or use version 0.0.0 in odd circumstances."""
    # Docstring props: http://stackoverflow.com/a/1523456/667301
    # version: if-else below fixes Github issue #123

    version = "0.0.0"  # version read failed

    pyproject_toml_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "../pyproject.toml",
    )
    if os.path.isfile(pyproject_toml_path):
        # Retrieve the version number from pyproject.toml...
        toml_values = {}
        with open(pyproject_toml_path, encoding=ENCODING) as fh:
            toml_values = toml.loads(fh.read())
            version = toml_values["tool"]["poetry"].get("version", -1.0)

        if not isinstance(version, str):
            raise ValueError("The version parameter must be a string.")

    else:
        # This is required for importing from a zipfile... Github issue #123
        version = "0.0.0"  # __version__ read failed

    return version


ENCODING = None
ACTIVE_LOGURU_HANDLERS = None
__author_email__ = r"mike /at\ pennington [dot] net"
__author__ = f"David Michael Pennington <{__author_email__}>"
__copyright__ = f'2007-{time.strftime("%Y")}, {__author__}'
__license__ = "GPLv3"
__status__ = "Production"
__version__ = None


@logger.catch(reraise=True)
def initialize_globals():
    """Initialize ciscoconfparse2 global dunder-variables and a couple others."""
    global ENCODING
    #global ACTIVE_LOGURU_HANDLERS
    global __author_email__
    global __author__
    global __copyright__
    global __license__
    global __status__
    global __version__

    ENCODING = locale.getpreferredencoding()

    __author_email__ = r"mike /at\ pennington [dot] net"
    __author__ = f"David Michael Pennington <{__author_email__}>"
    __copyright__ = f'2007-{time.strftime("%Y")}, {__author__}'
    __license__ = "GPLv3"
    __status__ = "Production"
    try:
        __version__ = get_version_number()
    except BaseException as eee:
        __version__ = "0.0.0"
        error = f"{eee}: could not determine the ciscoconfparse2 version via get_version_number()."
        logger.critical(error)
        raise ValueError(error)

    # These are all the 'dunder variables' required...
    globals_dict = {
        "__author_email__": __author_email__,
        "__author__": __author__,
        "__copyright__": __copyright__,
        "__license__": __license__,
        "__status__": __status__,
        "__version__": __version__,
    }
    return globals_dict


@logger.catch(reraise=True)
def initialize_ciscoconfparse(read_only=False, debug=0):
    """Initialize ciscoconfparse2 global variables and configure logging."""
    globals_dict = initialize_globals()
    for key, value in globals_dict.items():
        # Example, this will set __version__ to content of 'value'
        #     from -> https://stackoverflow.com/a/3972978/667301
        globals()[key] = value

    # Re-configure loguru... not a perfect solution, but this should be good enough
    #     Ref Github Issue #281
    if globals_dict.get("ACTIVE_LOGURU_HANDLERS", None) is None:
        active_loguru_handlers = configure_loguru(read_only=read_only, active_handlers=None, debug=debug)
    else:
        active_loguru_handlers = configure_loguru(read_only=read_only, active_handlers=globals_dict["ACTIVE_LOGURU_HANDLERS"], debug=debug)

    globals()["ACTIVE_LOGURU_HANDLERS"] = active_loguru_handlers

    if debug > 0 and read_only is True:
        logger.info("DISABLED loguru enqueue parameter because read_only=True.")

    return globals_dict, active_loguru_handlers


# ALL ciscoconfparse2 global variables initizalization happens here...
_, ACTIVE_LOGURU_HANDLERS = initialize_ciscoconfparse()


@logger.catch(reraise=True)
def parse_line_braces(line_txt=None, comment_delimiters=None) -> tuple:
    """Internal helper-method for brace-delimited configs (typically JunOS, syntax='junos')."""
    # Removed config parameter assertions in 1.7.2...

    retval = ()

    enforce_valid_types(line_txt, (str,), "line_txt parameter must be a string.")
    enforce_valid_types(
        comment_delimiters, (list,), "comment_delimiters parameter must be a list."
    )
    if len(comment_delimiters) > 1:
        raise ValueError("len(comment_delimiters) must be one.")

    child_indent = 0
    this_line_indent = 0

    junos_re_str = r"""^
    (?:\s*
        (?P<braces_close_left>\})*(?P<line1>.*?)(?P<braces_open_right>\{)*;*
        |(?P<line2>[^\{\}]*?)(?P<braces_open_left>\{)(?P<condition2>.*?)(?P<braces_close_right>\});*\s*
        |(?P<line3>[^\{\}]*?);*\s*
    )\s*$
    """
    brace_re = re.compile(junos_re_str, re.VERBOSE)
    comment_re = re.compile(
        r"^\s*(?P<delimiter>[{0}]+)(?P<comment>[^{0}]*)$".format(
            re.escape(comment_delimiters[0])
        )
    )

    brace_match = brace_re.search(line_txt.strip())
    comment_match = comment_re.search(line_txt.strip())

    if isinstance(comment_match, re.Match):
        results = comment_match.groupdict()
        delimiter = results.get("delimiter", "")
        comment = results.get("comment", "")
        retval = (
            this_line_indent,
            child_indent,
            delimiter + comment
        )

    elif isinstance(brace_match, re.Match):
        results = brace_match.groupdict()

        # } line1 { foo bar this } {
        braces_close_left = bool(results.get("braces_close_left", ""))
        braces_open_right = bool(results.get("braces_open_right", ""))

        # line2
        braces_open_left = bool(results.get("braces_open_left", ""))
        braces_close_right = bool(results.get("braces_close_right", ""))

        # line3
        line1_str = results.get("line1", "")
        line2_str = results.get("line2", "")

        if braces_close_left and braces_open_right:
            # Based off line1
            #     } elseif { bar baz } {
            this_line_indent -= 1
            child_indent += 0
            line1 = results.get("line1", None)
            retval = (this_line_indent, child_indent, line1)

        elif bool(line1_str) and (braces_close_left is False) and (braces_open_right is False):
            # Based off line1:
            #     address 1.1.1.1
            this_line_indent -= 0
            child_indent += 0
            _line1 = results.get("line1", "").strip()
            # Strip empty braces here
            line1 = re.sub(r"\s*\{\s*\}\s*", "", _line1)
            retval = (this_line_indent, child_indent, line1)

        elif (line1_str == "") and (braces_close_left is False) and (braces_open_right is False):
            # Based off line1:
            #     return empty string
            this_line_indent -= 0
            child_indent += 0
            retval = (this_line_indent, child_indent, "")

        elif braces_open_left and braces_close_right:
            # Based off line2
            #    this { bar baz }
            this_line_indent -= 0
            child_indent += 0
            _line2 = results.get("line2", None) or ""
            condition = results.get("condition2", None) or ""
            if condition.strip() == "":
                line2 = _line2
            else:
                line2 = _line2 + " {" + condition + " }"
            retval = (this_line_indent, child_indent, line2)

        elif braces_close_left:
            # Based off line1
            #   }
            this_line_indent -= 1
            child_indent -= 1
            retval = (this_line_indent, child_indent, "")

        elif braces_open_right:
            # Based off line1
            #   this that foo {
            this_line_indent -= 0
            child_indent += 1
            line = results.get("line1", None) or ""
            retval = (this_line_indent, child_indent, line)

        elif (line2_str != "") and (line2_str is not None):
            this_line_indent += 0
            child_indent += 0
            retval = (this_line_indent, child_indent, "")

        else:
            error = f'Cannot parse `{line_txt}`'
            logger.error(error)
            raise ValueError(error)

    else:
        error = f'Cannot parse `{line_txt}`'
        logger.error(error)
        raise ValueError(error)

    return retval


# This method was on ConfigList()
@logger.catch(reraise=True)
def cfgobj_from_text(
    text_list, txt, idx, syntax=None, comment_delimiters=None, factory=None
):
    """Build cfgobj from configuration text syntax, and factory inputs."""

    if not isinstance(txt, str):
        error = f"cfgobj_from_text(txt=`{txt}`) must be a string"
        logger.error(error)
        raise InvalidParameters(error)

    if not isinstance(idx, int):
        error = f"cfgobj_from_text(idx=`{idx}`) must be an int"
        logger.error(error)
        raise InvalidParameters(error)

    if not isinstance(comment_delimiters, list):
        error = f"cfgobj_from_text(comment_delimiters=`{comment_delimiters}`) must be a list of string comment chars"
        logger.error(error)
        raise InvalidParameters(error)

    if not isinstance(factory, bool):
        error = f"cfgobj_from_text(factory=`{factory}`) must be a boolean"
        logger.error(error)
        raise InvalidParameters(error)

    # if not factory is **faster** than factory is False
    if syntax in ALL_VALID_SYNTAX and not factory:
        obj = CFGLINE[syntax](
            all_lines=text_list,
            line=txt,
            comment_delimiters=comment_delimiters,
        )
        if isinstance(obj, BaseCfgLine):
            obj.linenum = idx
        else:
            error = f"{CFGLINE[syntax]}(txt=`{txt}`) must return an instance of BaseCfgLine(), but it returned {obj}"
            logger.error(error)
            raise ValueError(error)

    # if factory is **faster** than if factory is True
    elif syntax in ALL_VALID_SYNTAX and factory:
        obj = config_line_factory(
            all_lines=text_list,
            line=txt,
            comment_delimiters=comment_delimiters,
            syntax=syntax,
        )
        if isinstance(obj, BaseCfgLine):
            obj.linenum = idx
        else:
            error = f"config_line_factory(line=`{txt}`) must return an instance of BaseCfgLine(), but it returned {obj}"
            logger.error(error)
            raise ValueError(error)

    else:
        err_txt = (
            f"Cannot classify config list item `{txt}` into a proper configuration object line"
        )
        logger.error(err_txt)
        raise ValueError(err_txt)

    return obj


@logger.catch(reraise=True)
def build_space_tolerant_regex(linespec):
    r"""SEMI-PRIVATE: Accept a string, and return a string with all spaces replaced with '\s+'."""
    # Define backslash with manual Unicode...
    backslash = "\x5c"
    # escaped_space = "\\s+" (not a raw string)
    escaped_space = (backslash + backslash + "s+").translate("utf-8")

    enforce_valid_types(linespec, (str,), "linespec parameter must be a string.")
    if isinstance(linespec, str):
        linespec = re.sub(r"\s+", escaped_space, linespec)

    elif isinstance(linespec, Sequence):
        for idx, tmp in enumerate(linespec):
            # Ensure this list element is a string...
            if not isinstance(tmp, str):
                raise ValueError("tmp parameter must be a string.")
            linespec[idx] = re.sub(r"\s+", escaped_space, tmp)

    return linespec


@logger.catch(reraise=True)
def assign_parent_to_closing_braces(input_list=None, keep_blank_lines=False):
    """Accept a list of brace-delimited BaseCfgLine() objects; these objects should not already have a parent assigned.  Walk the list of BaseCfgLine() objects and assign the 'parent' attribute BaseCfgLine() objects to the closing config braces.  Return the list of objects (with the assigned 'parent' attributes).

    Closing Brace Assignment Example
    --------------------------------

    line number 1
    line number 2 {
        line number 3 {
            line number 4
            line number 5 {
                line number 6
                line number 7
                line number 8
            }            # Assign this closing-brace's parent as line 5
        }                # Assign this closing-brace's parent as line 3
    }                    # Assign this closing-brace's parent as line 2
    line number 11
    """
    if input_list is None:
        raise ValueError("Cannot modify.  The input_list is None")

    input_condition = isinstance(input_list, Sequence)
    if input_condition is True and len(input_list) > 0:
        opening_brace_objs = []
        for obj in input_list:
            if isinstance(obj, BaseCfgLine) and isinstance(obj.text, str):
                # These rstrip() are one of two fixes, intended to catch user error such as
                # the problems that the submitter of Github issue #251 had.
                # CiscoConfParse() could not read his configuration because he submitted
                # a multi-line string...
                #
                # This check will explicitly catch some problems like that...
                if len(obj.text.rstrip()) >= 1 and obj.text.rstrip()[-1] == "{":
                    opening_brace_objs.append(obj)

                elif len(obj.text.strip()) >= 1 and obj.text.strip()[0] == "}":
                    if len(opening_brace_objs) >= 1:
                        obj.parent = opening_brace_objs.pop()
                    else:
                        raise ValueError

    return input_list


# This method was copied from the same method in git commit below...
# https://raw.githubusercontent.com/mpenning/ciscoconfparse/bb3f77436023873da344377d3c839387f5131e7f/ciscoconfparse/ciscoconfparse2.py
@logger.catch(reraise=True)
def convert_junos_to_ios(input_list=None, stop_width=4, comment_delimiters=None, debug=0):
    """Accept `input_list` containing a list of junos-brace-formatted-string config lines.  This method strips off semicolons / braces from the string lines in `input_list` and returns the lines in a new list where all lines are explicitly indented as IOS would (as if IOS understood braces)."""

    if comment_delimiters is None:
        comment_delimiters = []

    if not isinstance(input_list, list):
        error = "convert_junos_to_ios() `input_list` must be a non-empty python list"
        logger.error(error)
        raise InvalidParameters(error)

    if not isinstance(stop_width, int):
        error = "convert_junos_to_ios() `stop_width` must be an integer"
        logger.error(error)
        raise InvalidParameters(error)

    if not isinstance(comment_delimiter, list):
        error = "convert_junos_to_ios() `comment_delimiters` must be a list"
        logger.error(error)
        raise InvalidParameters(error)

    if not isinstance(debug, int):
        error = "convert_junos_to_ios() `debug` must be an integer"
        logger.error(error)
        raise InvalidParameters(error)

    # Note to self, I made this regex fairly junos-specific...
    input_condition_01 = isinstance(input_list, list) and len(input_list) > 0
    input_condition_02 = "{" not in set(comment_delimiter)
    input_condition_03 = "}" not in set(comment_delimiter)
    if not (input_condition_01 and input_condition_02 and input_condition_03):
        error = "convert_junos_to_ios() input conditions failed"
        logger.error(error)
        raise ValueError(error)

    lines = []
    offset = 0
    STOP_WIDTH = stop_width
    for idx, tmp in enumerate(input_list):
        if debug > 0:
            logger.debug(f"Parse line {idx + 1}:'{tmp.strip()}'")
        (this_line_indent, child_indent, line) = parse_line_braces(
            tmp.strip(), comment_delimiters=[comment_delimiter]
        )
        lines.append((" " * STOP_WIDTH * (offset + this_line_indent)) + line.strip())
        offset += child_indent

    return lines

@attrs.define(repr=False)
class ConfigList(UserList):
    """A custom list to hold :class:`~ccp_abc.BaseCfgLine` objects.  Most users will never need to use this class directly."""
    initlist: Union[list, tuple] = None
    comment_delimiters: list = None
    debug: int = None
    factory: bool = None
    ignore_blank_lines: bool = None
    syntax: str = None
    auto_commit: bool = False

    ccp_ref: Any = None
    dna: str = "ConfigList"
    commit_checkpoint: int = 0
    CiscoConfParse: Any = None

    @logger.catch(reraise=True)
    def __init__(
        self,
        initlist=None,
        comment_delimiters=None,
        debug=0,
        factory=False,
        ignore_blank_lines=True,
        # syntax="__undefined__",
        syntax="ios",
        auto_commit=False,
        **kwargs
    ):
        """Initialize the class.

        Parameters
        ----------
        initlist : list
            A list of parsed :class:`~models_cisco.IOSCfgLine` objects
        comment_delimiters : list
            A list of string comment delimiters.  This should only be changed when parsing non-Cisco configurations.  ``comment_delimiters`` defaults to ['!'] for Cisco configurations.
        debug : int
            ``debug`` defaults to 0, and should be kept that way unless you're working on a very tricky config parsing problem.  Debug output is not particularly friendly
        ignore_blank_lines : bool
            ``ignore_blank_lines`` defaults to True; when this is set True, ciscoconfparse2 ignores blank configuration lines.  You might want to set ``ignore_blank_lines`` to False if you intentionally use blank lines in your configuration (ref: Github Issue #3).
        syntax : str
            Use a valid syntax string for the syntax of this config list.
        auto_commit : bool
            Set True if you want configuration changes to auto-commit; default is False.  ``auto_commit`` cannot handle all changes automatically.

        Returns
        -------
        An instance of an :class:`~ciscoconfparse2.ConfigList` object.

        """

        # Use this with UserList() instead of super()
        UserList.__init__(self)

        if initlist is None:
            initlist = list()
        elif not isinstance(initlist, Sequence):
            # IMPORTANT This check MUST come near the top of ConfigList()...
            raise ValueError

        #######################################################################
        # initialize the list with the correct BaseCfgLine() instances
        #######################################################################
        initobjs = list()
        for ii in initlist:
            if isinstance(ii, str):
                if bool(factory) is False:
                    obj = CFGLINE[syntax](
                        all_lines=[],
                        line=ii,
                        comment_delimiters=comment_delimiters,
                    )
                else:
                    obj = config_line_factory(
                        all_lines=[],
                        line=ii,
                        comment_delimiters=comment_delimiters,
                        syntax=syntax,
                    )
                initobjs.append(obj)
            elif isinstance(ii, BaseCfgLine):
                initobjs.append(ii)
            else:
                raise ValueError()

        #######################################################################
        # Parse out CiscoConfParse and ccp_ref keywords...
        #     FIXME the CiscoConfParse attribute / parameter should go away
        #     use self.ccp_ref instead of self.CiscoConfParse
        #######################################################################

        # This assert is one of two fixes, intended to catch user error such as
        # the problems that the submitter of Github issue #251 had.
        # CiscoConfParse() could not read his configuration because he submitted
        # a multi-line string...
        #
        # This check will explicitly catch some problems like that...

        if syntax not in ALL_VALID_SYNTAX:
            raise RequirementFailure()

        # NOTE a string is a invalid sequence... this guards against bad inputs
        if not isinstance(initlist, Sequence):
            error = f"ConfigList(initlist) {type(initlist)} is not valid; `initlist` must be a valid Sequence."
            logger.critical(error)
            raise InvalidParameters(error)

        ciscoconfparse_kwarg_val = kwargs.get("CiscoConfParse", None)
        ccp_ref_kwarg_val = kwargs.get("ccp_ref", None)
        if ciscoconfparse_kwarg_val is not None:
            logger.warning(
                "The CiscoConfParse keyword will be deprecated soon.  Please use ccp_ref instead",
            )
        ccp_value = ccp_ref_kwarg_val or ciscoconfparse_kwarg_val

        self.initlist = initlist
        self.comment_delimiters = comment_delimiters
        self.factory = factory
        self.ignore_blank_lines = ignore_blank_lines
        self.syntax = syntax
        self.auto_commit = auto_commit
        self.debug = debug

        self.ccp_ref = ccp_value
        self.dna = "ConfigList"
        self.commit_checkpoint = 0
        self.CiscoConfParse = (
            ccp_value  # FIXME - CiscoConfParse attribute should go away soon
        )

        # Support input configuration as either a list or a generator instance
        #
        # as of python 3.9, getattr() below is slightly faster than
        #     isinstance(initlist, Sequence)
        if False:
            self.data = self.bootstrap(initlist, debug=debug)

        if True:
            # Removed this portion of __init__() in 1.7.16...
            if getattr(initlist, "__iter__", False) is not False:
                self.data = self.bootstrap(initlist)

            else:
                self.data = []

        if self.debug > 0:
            message = f"Create ConfigList() with {len(self.data)} elements"
            logger.info(message)

        # Internal structures
        if syntax == "asa":
            self._RE_NAMES = re.compile(
                r"^\s*name\s+(\d+\.\d+\.\d+\.\d+)\s+(\S+)",
            )
            self._RE_OBJNET = re.compile(r"^\s*object-group\s+network\s+(\S+)")
            self._RE_OBJSVC = re.compile(r"^\s*object-group\s+service\s+(\S+)")
            self._RE_OBJACL = re.compile(r"^\s*access-list\s+(\S+)")
            self._network_cache = {}

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def __repr__(self):
        return """<ConfigList, syntax='{}', comment_delimiters={}, conf={}>""".format(
            self.syntax,
            self.comment_delimiters,
            self.data,
        )

    @logger.catch(reraise=True)
    def __iter__(self):
        return iter(self.data)

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def __lt__(self, other):
        return self.data < self.__cast(other)

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def __le__(self, other):
        return self.data < self.__cast(other)

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def __eq__(self, other):
        return self.data == self.__cast(other)

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def __gt__(self, other):
        return self.data > self.__cast(other)

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def __ge__(self, other):
        return self.data >= self.__cast(other)

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def __cast(self, other):
        return other._list if isinstance(other, ConfigList) else other

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def __len__(self):
        return len(self.data)

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def __getitem__(self, ii):
        if isinstance(ii, slice):
            return self.__class__(self.data[ii])
        else:
            return self.data[ii]

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def __setitem__(self, ii, val):
        self.data[ii] = val

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def __delitem__(self, ii):
        del self.data[ii]
        self.data = self.bootstrap(self.text, debug=self.debug)

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def __add__(self, other):
        raise NotImplementedError()
        if isinstance(other, ConfigList):
            return self.__class__(self.data + other._list)
        elif isinstance(other, type(self.data)):
            return self.__class__(self.data + other)
        return self.__class__(self.data + list(other))

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def __radd__(self, other):
        raise NotImplementedError()
        if isinstance(other, ConfigList):
            return self.__class__(other.data + self.data)
        elif isinstance(other, type(self.data)):
            return self.__class__(other + self.data)
        return self.__class__(list(other) + self.data)

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def __iadd__(self, other):
        raise NotImplementedError()
        if isinstance(other, ConfigList):
            self.data += other.data
        elif isinstance(other, type(self.data)):
            self.data += other
        else:
            self.data += list(other)

        if bool(self.auto_commit):
            # The config is not safe unless this is called after the append
            self.ccp_ref.atomic()

        return self

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def __mul__(self, val):
        raise NotImplementedError()
        return self.__class__(self.data * val)

    __rmul__ = __mul__

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def __imul__(self, val):
        raise NotImplementedError()
        self.data *= val
        return self

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def __copy__(self):
        inst = self.__class__.__new__(self.__class__)
        inst.__dict__.update(self.__dict__)
        # Create a copy and avoid triggering descriptors
        inst.__dict__["_list"] = self.__dict__["_list"][:]
        return inst

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def __str__(self):
        return self.__repr__()

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def __enter__(self):
        # Add support for with statements...
        # FIXME: *with* statements dont work
        yield from self.data

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def __exit__(self, *args, **kwargs):
        # FIXME: *with* statements dont work
        self.data[0].confobj.CiscoConfParse.atomic()

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def __getattribute__(self, arg):
        """Call arg on ConfigList() object, and if that fails, call arg from the ccp_ref attribute"""
        # Try a method call on ASAConfigList()

        # Rewrite self.CiscoConfParse to self.ccp_ref
        if arg == "CiscoConfParse":
            arg = "ccp_ref"

        try:
            return object.__getattribute__(self, arg)
        except BaseException:
            calling_function = inspect.stack()[1].function
            caller = inspect.getframeinfo(inspect.stack()[1][0])

            ccp_ref = object.__getattribute__(self, "ccp_ref")
            ccp_method = ccp_ref.__getattribute__(arg)
            message = """{2} doesn't have an attribute named "{3}". {0}() line {1} called `__getattribute__('{4}')`.""".format(
                calling_function, caller.lineno, ccp_ref, ccp_method, arg
            )
            raise NotImplementedError(message)
            logger.warning(message)
            return ccp_method

    # This method is on ConfigList()
    @property
    @logger.catch(reraise=True)
    def search_safe(self):
        """This is a seatbelt to ensure that configuration searches are safe; searches are not safe if the ConfigList() has changed without a commit.  As such, this method checks the current version of ConfigList().checkpoint and compares it to the last known ConfigList().commit_checkpoint.  If they are the same, return True.  ConfigList().commit_checkpoint should only written by CiscoConfParse().atomic()"""
        return self.get_checkpoint() == self.commit_checkpoint

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def commit(self):
        self.ccp_ref.commit()

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def get_checkpoint(self):
        """Return an integer representing a unique version of this ConfigList() and its contents."""
        total = 0
        for idx, obj in enumerate(self.data):
            if isinstance(obj, BaseCfgLine):
                #total += hash(obj.text) * hash(obj.linenum)
                total += obj.get_unique_identifier()
            else:
                error = f"{self} is an unexpected type {type(self)}"
                error.critical(error)
                raise NotImplementedError(error)
        return total

    # This method is on ConfigList()
    @property
    @logger.catch(reraise=True)
    def as_text(self):
        """Return the configuration as a list of text lines"""
        retval = list()
        for ii in self.data:
            if isinstance(ii, BaseCfgLine):
                retval.append(ii.text)
            elif isinstance(ii, str):
                retval.append(ii)
            else:
                error = f"ConfigList() expected a BaseCfgLine() or str, but found {type(ii)}"
                logger.critical(error)
                raise ValueError(error)
        return retval

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def append(self, val):
        if self.debug >= 1:
            logger.debug("    ConfigList().append(val={}) was called.".format(val))

        if bool(self.factory) is False:
            obj = CFGLINE[self.syntax](
                all_lines=self.as_text,
                line=val,
                comment_delimiters=self.comment_delimiters,
            )
        else:
            obj = config_line_factory(
                all_lines=self.as_text,
                line=val,
                comment_delimiters=self.comment_delimiters,
                syntax=self.syntax,
            )

        #self.data.append(obj)
        self.data.insert(len(self.data), obj)

        if bool(self.auto_commit):
            # The config is not safe unless this is called after the append
            self.ccp_ref.atomic()

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def pop(self, ii=-1):
        retval = self.data.pop(ii)

        if bool(self.auto_commit):
            # The config is not safe unless this is called after the append
            self.ccp_ref.atomic()

        return retval

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def remove(self, val):

        if isinstance(val, str):
            idx = self.as_text.index(val)
        else:
            idx = self.data.index(val)

        # Remove all child objects...
        for obj in self.data[idx].all_children:
            self.data.remove(obj)
        # Remove the parent...
        self.data.pop(idx)

        if False:
            # Rebuild the family relationships
            self.data = self.bootstrap(self.as_text, debug=self.debug)

        if bool(self.auto_commit):
            # The config is not safe unless this is called after the append
            self.ccp_ref.atomic()

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def clear(self):
        self.data.clear()

        if bool(self.auto_commit):
            # The config is not safe unless this is called after the append
            self.ccp_ref.atomic()

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def copy(self):
        return self.__class__(self)

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def count(self, val):
        return self.data.count(val)

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def index(self, val, *args):

        #######################################################################
        # first search by text and linenum if val is a BaseCfgLine() instance
        #######################################################################
        if isinstance(val, BaseCfgLine):
            for idx, obj in enumerate(self.data):

                if obj.get_unique_identifier() == val.get_unique_identifier():
                    return idx

        error = f"{val} is not in this ConfigList()"
        logger.error(error)
        raise ConfigListItemDoesNotExist(error)

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def reverse(self):
        self.data.reverse()

        if bool(self.auto_commit):
            # The config is not safe unless this is called after the append
            self.ccp_ref.atomic()

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def sort(self, _unknown_arg, *args, **kwds):
        self.data.sort(*args, **kwds)

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def extend(self, other):
        if isinstance(other, ConfigList):
            self.data.extend(other._list)
        else:
            self.data.extend(other)

        self.data = self.bootstrap(self.as_text, debug=self.debug)

        if bool(self.auto_commit):
            # The config is not safe unless this is called after the append
            self.ccp_ref.atomic()

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def insert_before(self, exist_val=None, new_val=None, atomic=False):
        """
        Insert new_val before all occurances of exist_val.

        Parameters
        ----------
        exist_val : str
            An existing text value.  This may match multiple configuration entries.
        new_val : str
            A new value to be inserted in the configuration.
        atomic : bool
            A boolean that controls whether the config is reparsed after the insertion (default False)

        Returns
        -------
        list
            An ios-style configuration list (indented by stop_width for each configuration level).

        Examples
        --------

        >>> parse = CiscoConfParse(config=["a a", "b b", "c c", "b b"])
        >>> # Insert 'g' before any occurance of 'b'
        >>> retval = parse.insert_before("b b", "X X")
        >>> parse.commit()
        >>> parse.ioscfg
        ... ["a a", "X X", "b b", "c c", "X X", "b b"]
        >>>
        """

        calling_fn_index = 1
        calling_filename = inspect.stack()[calling_fn_index].filename
        calling_function = inspect.stack()[calling_fn_index].function
        calling_lineno = inspect.stack()[calling_fn_index].lineno
        error = "FATAL CALL: in {} line {} {}(exist_val='{}', new_val='{}')".format(
            calling_filename,
            calling_lineno,
            calling_function,
            exist_val,
            new_val,
        )
        if isinstance(new_val, str) and new_val.strip() == "" and self.ignore_blank_lines is True:
            logger.warning(f"`new_val`=`{new_val}`")
            error = "Cannot insert a blank line if `ignore_blank_lines` is True"
            logger.error(error)
            raise InvalidParameters(error)

        # exist_val MUST be a string
        if isinstance(exist_val, str) is True and exist_val != "":
            pass

        # Matches "IOSCfgLine", "NXOSCfgLine" and "ASACfgLine"... (and others)
        elif isinstance(exist_val, BaseCfgLine):
            exist_val = exist_val.text

        else:
            logger.error(error)
            raise ValueError(error)

        # new_val MUST be a string
        if isinstance(new_val, str) is True:
            pass

        elif isinstance(new_val, BaseCfgLine):
            new_val = new_val.text

        else:
            logger.error(error)
            raise ValueError(error)

        if self.factory is False:
            new_obj = CFGLINE[self.syntax](
                all_lines=self.data,
                line=new_val,
                comment_delimiters=[self.comment_delimiter],
            )

        elif self.factory is True:
            new_obj = config_line_factory(
                all_lines=self.data,
                line=new_val,
                comment_delimiters=[self.comment_delimiter],
                syntax=self.syntax,
            )

        else:
            logger.error(error)
            raise ValueError(error)

        # Find all config lines which need to be modified... store in all_idx

        all_idx = [
            idx
            for idx, list_obj in enumerate(self.data)
            if re.search(exist_val, list_obj.text)
        ]
        for idx in sorted(all_idx, reverse=True):
            # insert at idx - 0 implements 'insert_before()'...
            self.data.insert(idx, new_obj)

        if atomic:
            # Reparse the whole config as a text list
            self.data = self.bootstrap(self.as_text)

        else:
            ## Just renumber lines...
            self.reassign_linenums()

        if bool(self.auto_commit):
            # The config is not safe unless this is called after the append
            self.ccp_ref.atomic()

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def insert_after(self, exist_val=None, new_val=None, atomic=False, new_val_indent=-1):
        """
        Insert new_val after all occurances of exist_val.

        Parameters
        ----------
        exist_val : str
            An existing configuration string value (used as the insertion reference point)
        new_val : str
            A new value to be inserted in the configuration.
        atomic : bool
            A boolean that controls whether the config is reparsed after the insertion (default False)
        new_val_indent : int
            The indent for new_val

        Returns
        -------
        list
            An ios-style configuration list (indented by stop_width for each configuration level).

        Examples
        --------

        >>> parse = CiscoConfParse(config=["a a", "b b", "c c", "b b"])
        >>> # Insert 'g' before any occurance of 'b'
        >>> retval = parse.config_objs.insert_after("b b", "X X")
        >>> parse.commit()
        >>> parse.ioscfg
        ... ["a a", "b b", "X X", "c c", "b b", "X X"]
        >>>
        """

        #        inserted_object = False
        #        for obj in self.ccp_ref.find_objects(exist_val):
        #            logger.debug("Inserting '%s' after '%s'" % (new_val, exist_val))
        #            print("IDX", obj.index)
        #            obj.insert_after(new_val)
        #            inserted_object = True
        #        return inserted_object

        calling_fn_index = 1
        calling_filename = inspect.stack()[calling_fn_index].filename
        calling_function = inspect.stack()[calling_fn_index].function
        calling_lineno = inspect.stack()[calling_fn_index].lineno
        err_txt = "FATAL CALL: in {} line {} {}(exist_val='{}', new_val='{}')".format(
            calling_filename,
            calling_lineno,
            calling_function,
            exist_val,
            new_val,
        )
        if isinstance(new_val, str) and new_val.strip() == "" and self.ignore_blank_lines is True:
            logger.warning(f"`new_val`=`{new_val}`")
            error = "Cannot insert a blank line if `ignore_blank_lines` is True"
            logger.error(error)
            raise InvalidParameters(error)

        # exist_val MUST be a string
        if isinstance(exist_val, str) is True and exist_val != "":
            pass

        # Matches "IOSCfgLine", "NXOSCfgLine" and "ASACfgLine"... (and others)
        elif isinstance(exist_val, BaseCfgLine):
            exist_val = exist_val.text

        else:
            logger.error(err_txt)
            raise ValueError(err_txt)

        # new_val MUST be a string or BaseCfgLine
        if isinstance(new_val, str) is True:
            pass

        elif isinstance(new_val, BaseCfgLine):
            new_val = new_val.text

        else:
            logger.error(err_txt)
            raise ValueError(err_txt)

        if self.factory is False:
            new_obj = CFGLINE[self.syntax](
                all_lines=self.data,
                line=new_val,
                comment_delimiters=[self.comment_delimiter],
            )

        elif self.factory is True:
            new_obj = config_line_factory(
                all_lines=self.data,
                line=new_val,
                comment_delimiters=[self.comment_delimiter],
                syntax=self.syntax,
            )

        else:
            logger.error(err_txt)
            raise ValueError(err_txt)

        # Find all config lines which need to be modified... store in all_idx

        all_idx = [
            idx
            for idx, list_obj in enumerate(self.data)
            if re.search(exist_val, list_obj._text)
        ]
        for idx in sorted(all_idx, reverse=True):
            self.data.insert(idx + 1, new_obj)

        if atomic is True:
            # Reparse the whole config as a text list
            self.data = self.bootstrap(self.as_text)
        else:
            # Just renumber lines...
            self.reassign_linenums()

        if bool(self.auto_commit):
            # The config is not safe unless this is called after the append
            self.ccp_ref.atomic()

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def insert(self, ii, val):
        if not isinstance(ii, int):
            error = f"The ConfigList() index must be an integer, but ConfigList().insert() got {type(ii)}"
            logger.critical(error)
            raise ValueError(error)

        # Get the configuration line text if val is a BaseCfgLine() instance
        if isinstance(val, BaseCfgLine):
            # only work with plain text to ensure that all objects are the
            # correct object type, below
            val = val.text

        # Coerce a string into the appropriate object
        if isinstance(val, str):
            if self.factory:
                obj = config_line_factory(
                    text=val,
                    comment_delimiters=self.comment_delimiters,
                    syntax=self.syntax,
                )

            elif self.factory is False:
                obj = CFGLINE[self.syntax](
                    text=val,
                    comment_delimiters=self.comment_delimiters,
                )

            else:
                error = f'''insert() cannot insert {type(val)} "{val}" with factory={self.factory}'''
                logger.critical(error)
                raise ValueError(error)
        else:
            error = f'''insert() cannot insert {type(val)} "{val}"'''
            logger.critical(error)
            raise TypeError(error)

        # Insert the object at index ii
        self.data.insert(ii, obj)

        if False:
            self.data = self.bootstrap(self.as_text, debug=self.debug)

        if bool(self.auto_commit):
            # The config is not safe unless this is called after the append
            self.ccp_ref.atomic()


    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def config_hierarchy(self):
        """Walk this configuration and return the following tuple
        at each parent 'level': (list_of_parent_sibling_objs, list_of_nonparent_sibling_objs)

        """
        parent_siblings = []
        nonparent_siblings = []

        for obj in self.ccp_ref.find_objects(r"^\S+"):
            if obj.is_comment:
                continue
            elif len(obj.children) == 0:
                nonparent_siblings.append(obj)
            else:
                parent_siblings.append(obj)

        return parent_siblings, nonparent_siblings

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def _banner_mark_regex(self, regex):
        """
        Use the regex input parameter to identify all banner parent
        objects. Find banner object children and formally build references
        between banner parent / child objects.

        Set the blank_line_keep attribute for all banner parent / child objs
        Banner blank lines are automatically kept.
        """
        # Build a list of all banner parent objects...
        banner_objs = list(
            filter(lambda obj: regex.search(obj.text), self.data),
        )

        banner_re_str = r"^(?:(?P<btype>(?:set\s+)*banner\s\w+\s+)(?P<bchar>\S))"
        for parent in banner_objs:
            # blank_line_keep for Github Issue #229
            parent.blank_line_keep = True

            ## Parse out the banner type and delimiting banner character
            mm = re.search(banner_re_str, parent.text)
            if mm is not None:
                mm_results = mm.groupdict()
                (banner_lead, bannerdelimit) = (
                    mm_results["btype"].rstrip(),
                    mm_results["bchar"],
                )
            else:
                (banner_lead, bannerdelimit) = ("", None)

            if self.debug > 0:
                logger.debug("banner_lead = '{}'".format(banner_lead))
                logger.debug("bannerdelimit = '{}'".format(bannerdelimit))
                logger.debug(
                    "{} starts at line {}".format(
                        banner_lead,
                        parent.linenum,
                    ),
                )

            idx = parent.linenum
            while bannerdelimit is not None:
                ## Check whether the banner line has both begin and end delimter
                if idx == parent.linenum:
                    parts = parent.text.split(bannerdelimit)
                    if len(parts) > 2:
                        ## banner has both begin and end delimiter on one line
                        if self.debug > 0:
                            logger.debug(
                                "{} ends at line"
                                " {}".format(
                                    banner_lead,
                                    parent.linenum,
                                ),
                            )
                        break

                ## Use code below to identify children of the banner line
                idx += 1
                try:
                    obj = self.data[idx]
                    if obj.text is None:
                        if self.debug > 0:
                            logger.warning(
                                "found empty text while parsing '{}' in the banner".format(
                                    obj
                                ),
                            )
                    elif bannerdelimit in obj.text.strip():
                        # Hit the bannerdelimit char... Exit banner parsing here...
                        if self.debug > 0:
                            logger.debug(
                                "{} ends at line"
                                " {}".format(
                                    banner_lead,
                                    obj.linenum,
                                ),
                            )
                        # blank_line_keep for Github Issue #229
                        parent.children.append(obj)
                        parent.child_indent = 0
                        obj.parent = parent
                        break
                    else:
                        # all non-banner-parent lines should hit this condition
                        if self.debug > 0:
                            logger.debug("found banner child {}".format(obj))

                    parent.children.append(obj)
                    parent.child_indent = 0
                    obj.parent = parent
                    obj.blank_line_keep = True

                except IndexError:
                    break

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def _macro_mark_children(self, macro_parent_idx_list):
        """
        Set the blank_line_keep attribute for all banner parent / child objs.

        Macro blank lines are automatically kept.
        """
        # Mark macro children appropriately...
        for idx in macro_parent_idx_list:
            pobj = self.data[idx]
            # blank_line_keep for Github Issue #229
            pobj.blank_line_keep = True
            pobj.child_indent = 0

            # Walk the next configuration lines looking for the macro's children
            finished = False
            while not finished:
                idx += 1
                cobj = self.data[idx]
                # blank_line_keep for Github Issue #229
                cobj.blank_line_keep = True
                cobj.parent = pobj
                pobj.children.append(cobj)
                # If we hit the end of the macro, break out of the loop
                if cobj.text.rstrip() == "@":
                    finished = True

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def _maintain_bootstrap_parent_cache(self, parents_cache, indent, max_indent, is_config_line):
        """Find parent for a given indent level."""
        # Parent cache:
        # Maintain indent vs max_indent in a family and
        #     cache the parent until indent<max_indent

        # default parent is None
        parent = None
        if is_config_line and (indent < max_indent):
            # walk parents and intelligently prune parents at
            # equal or higher indent
            stale_parent_idxs = filter(
                lambda ii: ii >= indent,
                sorted(parents_cache.keys(), reverse=True),
            )

            # `del some_dict[key]` is the fastest way to delete keys
            #     See https://stackoverflow.com/a/3077179/667301
            for parent_idx in stale_parent_idxs:
                del parents_cache[parent_idx]
        else:
            # As long as the child indent hasn't gone backwards,
            #    we can use a cached parent
            parent = parents_cache.get(indent, None)

        return parents_cache, parent

    @logger.catch(reraise=True)
    def _build_bootstrap_parent_child(self, retval, parents_cache, parent, idx, indent, obj, debug,):
        candidate_parent = None
        candidate_parent_idx = None
        # If indented, walk backwards and find the parent...
        # 1.  Assign parent to the child
        # 2.  Assign child to the parent
        # 3.  Assign parent's child_indent
        # 4.  Maintain oldest_ancestor
        if (indent > 0) and (parent is not None):
            # Add the line as a child (parent was cached)
            self._add_child_to_parent(retval, idx, indent, parent, obj)
        elif (indent > 0) and (parent is None):
            # Walk backwards to find parent, and add the line as a child
            candidate_parent_idx = idx - 1
            while candidate_parent_idx >= 0:
                candidate_parent = retval[candidate_parent_idx]
                if (
                    candidate_parent.get_indent() < indent
                ) and candidate_parent.is_config_line:
                    # We found the parent
                    parent = candidate_parent
                    parents_cache[indent] = parent  # Cache the parent
                    break
                else:
                    candidate_parent_idx -= 1

            # Add the line as a child...
            self._add_child_to_parent(retval, idx, indent, parent, obj)

        else:
            if debug:
                logger.debug("    root obj assign: %s" % obj)

        return retval, parents_cache, parent

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def bootstrap(self, text_list=None, debug=0):
        """
        Accept a text list, and format into a list of *CfgLine() objects.

        Parent / child relationships are assigned in this method.

        This method returns a list of *CfgLine() objects.
        """
        if text_list is None:
            text_list = self.ccp_ref.text

        if not isinstance(text_list, Sequence):
            raise ValueError

        if self.debug >= 1:
            logger.info("    ConfigList().bootstrap() was called.")


        retval = []
        idx = None
        syntax = self.syntax

        max_indent = 0
        macro_parent_idx_list = []
        # a dict of parents, indexed by int() child-indent...
        parent = None
        parents_cache = {}
        for idx, txt in enumerate(text_list):
            if self.debug >= 1:
                logger.debug("    bootstrap() adding text cmd: '%s' at idx %s" % (txt, idx,))
            if not isinstance(txt, str):
                raise ValueError

            # Assign a custom *CfgLine() based on factory...
            obj = cfgobj_from_text(
                text_list,
                txt=txt,
                idx=idx,
                syntax=syntax,
                comment_delimiters=self.comment_delimiters,
                factory=self.factory,
            )
            obj.confobj = self
            indent = obj.get_indent()
            is_config_line = obj.is_config_line

            # list out macro parent line numbers...
            if txt[0:11] == "macro name " and syntax == "ios":
                macro_parent_idx_list.append(obj.linenum)

            parents_cache, parent = self._maintain_bootstrap_parent_cache(
                parents_cache, indent, max_indent, is_config_line
            )

            # If indented, walk backwards and find the parent...
            # 1.  Assign parent to the child
            # 2.  Assign child to the parent
            # 3.  Assign parent's child_indent
            # 4.  Maintain oldest_ancestor
            retval, parents_cache, parent = self._build_bootstrap_parent_child(
                retval, parents_cache, parent, idx, indent, obj, debug,
            )

            # Handle max_indent
            if (indent == 0) and is_config_line:
                # only do this if it's a config line...
                max_indent = 0
            elif indent > max_indent:
                max_indent = indent


            retval.append(obj)

        # Manually assign a parent on all closing braces
        self.data = assign_parent_to_closing_braces(input_list=retval)

        # Call _banner_mark_regex() to process banners in the returned obj
        # list.
        # Mark IOS banner begin and end config line objects...
        #
        # Build the banner_re regexp... at this point ios
        #    and nxos share the same method...
        if syntax not in ALL_BRACE_SYNTAX:
            banner_re = self._build_banner_re_ios()
            self._banner_mark_regex(banner_re)

            # We need to use a different method for macros than banners because
            #   macros don't specify a delimiter on their parent line, but
            #   banners call out a delimiter.
            self._macro_mark_children(macro_parent_idx_list)  # Process macros

        # change ignore_blank_lines behavior for Github Issue #229...
        #    Always allow a blank line if it's in a banner or macro...
        if self.ignore_blank_lines is True:
            retval = [
                obj
                for obj in self.data
                if obj.text.strip() != "" or obj.blank_line_keep is True
            ]
            self.data = retval

        return retval

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def _build_banner_re_ios(self):
        """Return a banner regexp for IOS (and at this point, NXOS)."""
        banner_str = {
            "login",
            "motd",
            "incoming",
            "exec",
            "telnet",
            "lcd",
        }
        banner_all = [r"^(set\s+)*banner\s+{}".format(ii) for ii in banner_str]
        banner_all.append(
            "aaa authentication fail-message",
        )  # Github issue #76
        banner_re = re.compile("|".join(banner_all))

        return banner_re

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def _add_child_to_parent(self, _list, idx, indent, parentobj, childobj):
        # parentobj could be None when trying to add a child that should not
        #    have a parent
        if parentobj is None:
            if self.debug >= 1:
                logger.debug("parentobj is None")
            return

        if self.debug >= 4:
            logger.debug(
                "Adding child '{}' to parent" " '{}'".format(childobj, parentobj),
            )
            logger.debug(
                "BEFORE parent.children - {}".format(
                    parentobj.children,
                ),
            )

        if childobj.is_comment and (_list[idx - 1].get_indent() > indent):
            # I *really* hate making this exception, but legacy
            #   ciscoconfparse2 never marked a comment as a child
            #   when the line immediately above it was indented more
            #   than the comment line
            pass
        elif childobj.parent is childobj:
            # Child has not been assigned yet
            parentobj.children.append(childobj)
            childobj.parent = parentobj
            childobj.parent.child_indent = indent
        else:
            pass

        if self.debug > 0:
            # logger.debug("     AFTER parent.children - {0}"
            #    .format(parentobj.children))
            pass

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def iter_with_comments(self, begin_index=0):
        for idx, obj in enumerate(self.data):
            if idx >= begin_index:
                yield obj

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def iter_no_comments(self, begin_index=0):
        for idx, obj in enumerate(self.data):
            if (idx >= begin_index) and (not obj.is_comment):
                yield obj

    # This method is on ConfigList()
    @logger.catch(reraise=True)
    def reassign_linenums(self):
        # Call this after any insertion or deletion
        for idx, obj in enumerate(self.data):
            obj.linenum = idx

    # This method is on ConfigList()
    @ property
    @logger.catch(reraise=True)
    def all_parents(self):
        return [obj for obj in self.data if obj.has_children]

    # This method is on ConfigList()
    @ property
    @logger.catch(reraise=True)
    def last_index(self):
        return self.__len__() - 1

    ##########################################################################
    # Special syntax='asa' methods...
    ##########################################################################

    # This method was on ASAConfigList(); now tentatively on ConfigList()
    @ property
    @logger.catch(reraise=True)
    def names(self):
        """Return a dictionary of name to address mappings"""
        if self.syntax != "asa":
            raise RequirementFailure()

        retval = {}
        name_rgx = self._RE_NAMES
        for obj in self.ccp_ref.find_objects(name_rgx):
            addr = obj.re_match_typed(name_rgx, group=1, result_type=str)
            name = obj.re_match_typed(name_rgx, group=2, result_type=str)
            retval[name] = addr
        return retval

    # This method was on ASAConfigList(); now tentatively on ConfigList()
    @ property
    @logger.catch(reraise=True)
    def object_group_network(self):
        """Return a dictionary of name to object-group network mappings"""
        if self.syntax != "asa":
            raise RequirementFailure()

        retval = {}
        obj_rgx = self._RE_OBJNET
        for obj in self.ccp_ref.find_objects(obj_rgx):
            name = obj.re_match_typed(obj_rgx, group=1, result_type=str)
            retval[name] = obj
        return retval

    # This method was on ASAConfigList(); now tentatively on ConfigList()
    @ property
    @logger.catch(reraise=True)
    def access_list(self):
        """Return a dictionary of ACL name to ACE (list) mappings"""
        if self.syntax != "asa":
            raise RequirementFailure()

        retval = {}
        for obj in self.ccp_ref.find_objects(self._RE_OBJACL):
            name = obj.re_match_typed(
                self._RE_OBJACL,
                group=1,
                result_type=str,
            )
            tmp = retval.get(name, [])
            tmp.append(obj)
            retval[name] = tmp
        return retval


#@attrs.define(repr=False)
class CiscoConfParse(object):
    """Parse Cisco IOS configurations and answer queries about the configs."""
    config: Union[str, list] = None
    syntax: str = "ios"
    encoding: str = locale.getpreferredencoding()
    loguru: bool = True
    comment_delimiters: list = []
    auto_indent_width: int = -1
    linesplit_rgx: str = r"\r*\n+"
    ignore_blank_lines: bool = False
    auto_commit: bool = None
    factory: bool = False
    debug: int = 0

    # Attributes
    config_objs: Any = None
    finished_config_parse: bool = False

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def __init__(
        self,
        config=None,
        syntax="ios",
        encoding=locale.getpreferredencoding(),
        loguru=True,
        comment_delimiters=None,
        auto_indent_width=-1,
        linesplit_rgx=r"\r*\n+",
        ignore_blank_lines=False,
        auto_commit=True,
        factory=False,
        debug=0,
    ):
        """
        Initialize CiscoConfParse.

        Parameters
        ----------
        config : list or str
            A list of configuration statements, or a configuration file path to be parsed
        syntax : str
            A string holding the configuration type.  Default: 'ios'.  Must be one of: 'ios', 'nxos', 'iosxr', 'asa', 'junos'.  Use 'junos' for any brace-delimited network configuration (including F5, Palo Alto, etc...).
        encoding : str
            A string holding the coding type.  Default is `locale.getpreferredencoding()`
        loguru : bool
            A bool indicating whether CiscoConfParse should execute with loguru enabled (default: True)
        comment_delimiters : list
            A list of string comment delimiters.  This should only be changed when parsing non-Cisco configurations, which do not use a '!' as the comment delimiter.  ``comment`` defaults to '!'.  This value can hold multiple characters in case the config uses multiple characters for comment delimiters; however, the comment delimiters are always assumed to be one character wide
        auto_indent_width : int
            ``auto_indent_width`` defaults to -1, and should be kept that way unless you're working on a very tricky config parsing problem.
        debug : int
            ``debug`` defaults to 0, and should be kept that way unless you're working on a very tricky config parsing problem.  Debug range goes from 0 (no debugging) to 5 (max debugging).  Debug output is not particularly friendly.
        factory : bool
            ``factory`` defaults to False; if set ``True``, it enables a beta-quality configuration classifier.
        linesplit_rgx : str
            ``linesplit_rgx`` is used when parsing configuration files to find where new configuration lines are.  It is best to leave this as the default, unless you're working on a system that uses unusual line terminations (for instance something besides Unix, OSX, or Windows)
        ignore_blank_lines : bool
            ``ignore_blank_lines`` defaults to False; when this is set True, ciscoconfparse2 ignores blank configuration lines.  You might want to set ``ignore_blank_lines`` to False if you intentionally use blank lines in your configuration, or you are parsing configurations which naturally have blank lines (such as Cisco Nexus configurations).
        auto_commit : bool
            A bool indicating whether CiscoConfParse should auto-commit config changes when possible; the default is ``True``, however, parsing very large configs may be faster with ``auto_commit=False``.


        Returns
        -------
        :class:`~ciscoconfparse2.CiscoConfParse`

        Examples
        --------
        This example illustrates how to parse a simple Cisco IOS configuration
        with :class:`~ciscoconfparse2.CiscoConfParse` into a variable called
        ``parse``.  This example also illustrates what the ``config_objs``
        and ``ioscfg`` attributes contain.

        >>> from ciscoconfparse2 import CiscoConfParse
        >>> config = [
        ...     'logging trap debugging',
        ...     'logging 172.28.26.15',
        ...     ]
        >>> parse = CiscoConfParse(config=config)
        >>> parse
        <CiscoConfParse: 2 lines / syntax: ios / comment delimiter: '!' / factory: False>
        >>> parse.config_objs
        <ConfigList, comment='!', conf=[<IOSCfgLine # 0 'logging trap debugging'>, <IOSCfgLine # 1 'logging 172.28.26.15'>]>
        >>> parse.ioscfg
        ['logging trap debugging', 'logging 172.28.26.15']
        >>>

        Attributes
        ----------
        comment_delimiter : str
            A string containing the comment-delimiter.  Default: "!"
        config_objs : :class:`~ciscoconfparse2.ConfigList`
            A custom list, which contains all parsed :class:`~models_cisco.IOSCfgLine` instances.
        debug : int
            An int to enable verbose config parsing debugs. Default 0.
        ioscfg : list
            A list of text configuration strings
        objs
            An alias for `config_objs`
        openargs : dict
            Returns a dictionary of valid arguments for `open()` (these change based on the running python version).
        syntax : str
            A string holding the configuration type.  Default: 'ios'.  Must be one of: 'ios', 'nxos', 'iosxr', 'asa', 'junos'.  Use 'junos' for any brace-delimited network configuration (including F5, Palo Alto, etc...).
        """
        if syntax not in ALL_VALID_SYNTAX:
            error = f"{syntax} is not a valid syntax."
            logger.error(error)
            raise InvalidParameters(error)

        if comment_delimiters is None:
            comment_delimiters = self.get_comment_delimiters(syntax=syntax)
        elif isinstance(comment_delimiters, list):
            for comment_delimiter in comment_delimiters:
                if not isinstance(comment_delimiter, str):
                    error = f"`{comment_delimiter}` is not a valid string comment_delimiter"
                    logger.critical(error)
                    raise InvalidParameters(error)
                elif not len(comment_delimiter) == 1:
                    error = f"`{comment_delimiter}` must be a single string character."
                    logger.critical(error)
                    raise InvalidParameters(error)
        elif not isinstance(comment_delimiters, list):
            error = "'comment_delimiters' must be a list of string comment delimiters"
            logger.critical(error)
            raise InvalidParameters(error)

        if int(auto_indent_width) <= 0:
            auto_indent_width = int(self.get_auto_indent_from_syntax(syntax=syntax))

        ######################################################################
        # Log an error if parsing with `ignore_blank_lines=True` and
        #     `factory=False`
        ######################################################################
        if ignore_blank_lines is True and factory is True:
            error = "ignore_blank_lines and factory are not supported together."
            logger.error(error)
            raise NotImplementedError(error)

        ######################################################################
        # Reconfigure loguru if read_only is True
        ######################################################################
        if loguru is False:
            active_loguru_handlers = configure_loguru(read_only=loguru, active_handlers=globals()["ACTIVE_LOGURU_HANDLERS"], debug=debug)
            globals()["ACTIVE_LOGURU_HANDLERS"] = active_loguru_handlers
            if debug > 0:
                logger.warning(f"Disabled loguru enqueue because loguru={loguru}")

        if not (isinstance(syntax, str) and (syntax in ALL_VALID_SYNTAX)):
            error = f"'{syntax}' is an unknown syntax"
            logger.error(error)
            raise ValueError(error)

        # all IOSCfgLine object instances...
        self.finished_config_parse = False

        self.syntax = syntax
        self.encoding = encoding or ENCODING
        self.loguru = bool(loguru)
        self.comment_delimiters = comment_delimiters
        self.auto_indent_width = int(auto_indent_width)
        self.debug = int(debug)
        self.factory = bool(factory)
        self.linesplit_rgx = linesplit_rgx
        self.ignore_blank_lines = ignore_blank_lines
        self.auto_commit = auto_commit

        self.config_objs = None


        # Convert an None config into an empty list
        if config is None:
            config = []

        if len(config) > 0:
            try:
                correct_element_types = []
                for ii in config:
                    # Check whether the elements are the correct types...
                    if isinstance(ii, (str, BaseCfgLine)):
                        correct_element_types.append(True)
                    else:
                        correct_element_types.append(False)

                elements_have_len = all(correct_element_types)
            except AttributeError:
                elements_have_len = False
            except TypeError:
                elements_have_len = False
        else:
            elements_have_len = None

        if elements_have_len is False:
            error = "All ConfigList elements must have a length()"
            logger.error(error)
            raise InvalidParameters(error)

        # Read the configuration lines and detect invalid inputs...
        # tmp_lines = self._get_ccp_lines(config=config, logger=logger)
        if isinstance(config, (str, pathlib.Path,)):
            tmp_lines = self.read_config_file(filepath=config, linesplit_rgx=r"\r*\n")
        elif isinstance(config, Sequence):
            tmp_lines = config
        else:
            error = f"Cannot read config from {config}"
            logger.critical(error)
            raise ValueError(error)

        # conditionally strip off junos-config braces and other syntax
        #     parsing issues...
        config_lines = self.handle_ccp_brace_syntax(tmp_lines=tmp_lines, syntax=syntax)
        if self.check_ccp_input_good(config=config_lines, logger=logger) is False:
            error = f"Cannot parse config=`{tmp_lines}`"
            logger.critical(error)
            raise ValueError(error)

        if self.debug > 0:
            logger.info("assigning self.config_objs = ConfigList()")

        self.config_objs = ConfigList(
            initlist=config_lines,
            comment_delimiters=comment_delimiters,
            debug=debug,
            factory=factory,
            ignore_blank_lines=ignore_blank_lines,
            syntax=syntax,
            ccp_ref=self,
            auto_commit=auto_commit,
        )

        ######################################################################
        # Set the commit checkpoint after the initial parse... this
        # avoids the need to manually call CiscoConfParse.commit()
        # after parsing
        ######################################################################
        self.commit()

        # IMPORTANT this MUST not be a lie :-)...
        self.finished_config_parse = True

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def handle_ccp_brace_syntax(self, tmp_lines=None, syntax=None):
        """Deal with brace-delimited syntax issues, such as conditionally discarding junos closing brace-lines."""

        if syntax not in ALL_VALID_SYNTAX:
            error = f"{syntax} parser factory is not yet enabled; use factory=False"
            logger.critical(error)
            raise InvalidParameters(error)

        if not isinstance(tmp_lines, (list, tuple)):
            error = f"handle_ccp_brace_syntax(tmp_lines={tmp_lines}) must not be None"
            logger.error(error)
            raise InvalidParameters(error)

        ######################################################################
        # Explicitly handle all brace-parsing factory syntax here...
        ######################################################################
        if syntax == "junos":
            config_lines = convert_junos_to_ios(tmp_lines, comment_delimiters=["#"])
        elif syntax in ALL_VALID_SYNTAX:
            config_lines = tmp_lines
        else:
            error = f"handle_ccp_brace_syntax(syntax=`{syntax}`) is not yet supported"
            logger.error(error)
            raise InvalidParameters(error)

        return config_lines

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def get_comment_delimiters(self, syntax=None):
        """Return a list of comment delimiters for the 'syntax' string in question"""
        if not isinstance(syntax, str):
            error = "The 'syntax' parameter must be a string"
            logger.error(error)
            raise InvalidParameters(error)

        if syntax not in ALL_VALID_SYNTAX:
            error = f"syntax='{syntax}' is not yet supported"
            logger.error(error)
            raise InvalidParameters(error)

        comment_delimiters = []
        if syntax == "ios":
            comment_delimiters = ['!']
        elif syntax == "asa":
            comment_delimiters = ['!']
        elif syntax == "iosxr":
            comment_delimiters = ['!']
        elif syntax == "nxos":
            comment_delimiters = ['!']
        elif syntax == "junos":
            comment_delimiters = ['#']
        else:
            error = "Unexpected condition in get_comment_delimiters()"
            logger.critical(error)
            raise NotImplementedError(error)

        return comment_delimiters

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def get_auto_indent_from_syntax(self, syntax=None):
        """Return an auto indent for the 'syntax' string in question"""
        if not isinstance(syntax, str):
            error = "The 'syntax' parameter must be a string"
            logger.error(error)
            raise InvalidParameters(error)

        if syntax not in ALL_VALID_SYNTAX:
            error = f"syntax='{syntax}' is not yet supported"
            logger.error(error)
            raise InvalidParameters(error)

        indent_width = -1
        if syntax == "ios":
            indent_width = 1
        elif syntax == "asa":
            indent_width = 1
        elif syntax == "iosxr":
            indent_width = 1
        elif syntax == "nxos":
            indent_width = 2
        elif syntax == "junos":
            indent_width = 4
        else:
            error = "Unexpected condition in get_auto_indent_from_syntax()"
            logger.critical(error)
            raise NotImplementedError(error)

        return int(indent_width)

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def __repr__(self):
        """Return a string that represents this CiscoConfParse object instance.  The number of lines embedded in the string is calculated from the length of the config_objs attribute."""
        if self.config_objs is None:
            num_lines = 0
        elif isinstance(self.config_objs, Sequence):
            num_lines = len(self.config_objs)
        return (
            "<CiscoConfParse: %s lines / syntax: %s / comment delimiters: %s / factory: %s / ignore_blank_lines: %s / encoding: '%s' / auto_commit: %s>"
            % (
                num_lines,
                self.syntax,
                self.comment_delimiters,
                self.factory,
                self.ignore_blank_lines,
                self.encoding,
                self.auto_commit,
            )
        )

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def read_config_file(self, filepath=None, linesplit_rgx=r"\r*\n+"):
        """Read the config lines from the filepath.  Return the list of text configuration commands or raise an error."""

        if self.finished_config_parse is not False:
            raise RequirementFailure()

        valid_path_variable = False
        if filepath is None:
            error = "Filepath: None is invalid"
            logger.critical(error)
            raise FileNotFoundError(error)
        elif isinstance(filepath, (str, pathlib.Path,)):
            valid_path_variable = True

        if valid_path_variable and not os.path.exists(filepath):
            error = f"Filepath: {filepath} does not exist"
            logger.critical(error)
            raise FileNotFoundError(error)

        config_lines = None

        _encoding = self.openargs['encoding']
        if valid_path_variable is True and os.path.isfile(filepath) is True:
            # config string - assume a filename...
            if self.debug > 0:
                logger.debug(f"reading config from the filepath named '{filepath}'")

        elif valid_path_variable is True and os.path.isfile(filepath) is False:
            if self.debug > 0:
                logger.debug(f"filepath not found - '{filepath}'")
            try:
                _ = open(file=filepath, **self.openargs)
            except FileNotFoundError:
                error = f"""FATAL - Attempted to open(file='{filepath}', mode='r', encoding="{_encoding}"); the filepath named:"{filepath}" does not exist."""
                logger.critical(error)
                raise FileNotFoundError(error)

            except OSError:
                error = f"""FATAL - Attempted to open(file='{filepath}', mode='r', encoding="{_encoding}"); OSError opening "{filepath}"."""
                logger.critical(error)
                raise OSError(error)

            except BaseException:
                logger.critical(f"Cannot open {filepath}")
                raise BaseException

        else:
            error = f'Unexpected condition processing filepath: {filepath}'
            logger.critical(error)
            raise ValueError(error)

        # Read the file from disk and return the list of config statements...
        try:
            with open(file=filepath, **self.openargs) as fh:
                text = fh.read()
            rgx = re.compile(linesplit_rgx)
            config_lines = rgx.split(text)
            return config_lines

        except OSError:
            error = f"CiscoConfParse could not open() the filepath named '{filepath}'"
            logger.critical(error)
            raise OSError(error)

        except BaseException as eee:
            error = f"FATAL - {eee}"
            logger.critical(error)
            raise eee

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def check_ccp_input_good(self, config=None, logger=None, linesplit_rgx=r"\r*\n+"):
        """The config parameter is a sequence of text config commands.  Return True or False based on whether the config can be parsed."""

        if self.finished_config_parse is not False:
            raise RequirementFailure()

        if isinstance(config, Sequence):
            # Here we assume that `config` is a list of text config lines...
            #
            # config list of text lines...
            if self.debug > 0:
                logger.debug(
                    f"parsing config stored in the config variable: `{config}`"
                )
            return True

        else:
            return False

    #########################################################################
    # This method is on CiscoConfParse()
    #      do NOT wrap this method in logger.catch() - github issue #249
    #########################################################################
    @property
    @logger.catch(reraise=True)
    def openargs(self):
        """Fix Py3.5 deprecation of universal newlines - Ref Github #114; also see https://softwareengineering.stackexchange.com/q/298677/23144."""
        if sys.version_info >= (
            3,
            6,
        ):
            retval = {"mode": "r", "newline": None, "encoding": self.encoding}
        else:
            retval = {"mode": "rU", "encoding": self.encoding}
        return retval

    # This method is on CiscoConfParse()
    @property
    @logger.catch(reraise=True)
    def text(self):
        """Return a list containing all text configuration statements; it is an alias for ``CiscoConfParse().ioscfg``."""
        return [ii.text for ii in self.config_objs]

    if False:
        # This method is on CiscoConfParse()
        @property
        @logger.catch(reraise=True)
        def ioscfg(self):
            """Return a list containing all text configuration statements."""
            # I keep ioscfg to emulate legacy ciscoconfparse2 behavior
            #
            # FYI: map / methodcaller is not significantly faster than a list
            #     comprehension, below...
            # See https://stackoverflow.com/a/51519942/667301
            # from operator import methodcaller
            # get_text_attr = methodcaller('text')
            # return list(map(get_text_attr, self.config_objs))
            #
            return [ii.text for ii in self.config_objs]

    # This method is on CiscoConfParse()
    @property
    @logger.catch(reraise=True)
    def objs(self):
        """CiscoConfParse().objs is an alias for the CiscoConfParse().config_objs property; it returns a ConfigList() of config-line objects."""
        if self.config_objs is None:
            error = (
                "config_objs is set to None.  config_objs should be a ConfigList() of configuration-line objects"
            )
            logger.error(error)
            raise ValueError(error)
        return self.config_objs

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def atomic(self):
        """Use :func:`~ciscoconfparse2.CiscoConfParse.atomic` to manually fix up ``config_objs`` relationships after modifying a parsed configuration.  This method is slow; try to batch calls to :func:`~ciscoconfparse2.CiscoConfParse.atomic()` if possible.

        Warnings
        --------
        If you modify a configuration after parsing it with :class:`~ciscoconfparse2.CiscoConfParse`, you *must* call :func:`~ciscoconfparse2.CiscoConfParse.commit` or :func:`~ciscoconfparse2.CiscoConfParse.atomic` before searching the configuration again with methods such as :func:`~ciscoconfparse2.CiscoConfParse.find_objects`.  Failure to call :func:`~ciscoconfparse2.CiscoConfParse.commit` or :func:`~ciscoconfparse2.CiscoConfParse.atomic` on config modifications could lead to unexpected search results.

        See Also
        --------
        :func:`~ciscoconfparse2.CiscoConfParse.commit`.
        """
        self.config_objs.data = self.config_objs.bootstrap(debug=self.debug)
        self.config_objs.commit_checkpoint = self.config_objs.get_checkpoint()

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def commit(self):
        """Alias for calling the :func:`~ciscoconfparse2.CiscoConfParse.atomic` method.  This method is slow; try to batch calls to :func:`~ciscoconfparse2.CiscoConfParse.commit()` if possible.

        Warnings
        --------
        If you modify a configuration after parsing it with :class:`~ciscoconfparse2.CiscoConfParse`, you *must* call :func:`~ciscoconfparse2.CiscoConfParse.commit` or :func:`~ciscoconfparse2.CiscoConfParse.atomic` before searching the configuration again with methods such as :func:`~ciscoconfparse2.CiscoConfParse.find_objects`.  Failure to call :func:`~ciscoconfparse2.CiscoConfParse.commit` or :func:`~ciscoconfparse2.CiscoConfParse.atomic` on config modifications could lead to unexpected search results.

        See Also
        --------
        :func:`~ciscoconfparse2.CiscoConfParse.atomic`.
        """
        self.atomic()  # atomic() calls self.config_objs.bootstrap


    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def _find_child_object_branches(
        self,
        parent_obj,
        childspec,
        regex_flags,
        allow_none=True,
        debug=0,
    ):
        # I'm not using parent_obj.re_search_children() because
        # re_search_children() doesn't return None for no match...

        # As of version 1.6.16, allow_none must always be True...
        if allow_none is not True:
            raise ValueError("allow_none parameter must always be True.")

        if debug > 1:
            msg = f"""Calling _find_child_object_branches(
parent_obj={parent_obj},
childspec='{childspec}',
regex_flags='{regex_flags}',
allow_none={allow_none},
debug={debug},
)"""
            logger.info(msg)

        # Get the child objects from parent objects
        if parent_obj is None:
            children = self._find_line_OBJ(
                linespec=childspec,
                exactmatch=False,
            )
        else:
            children = parent_obj.children

        # Find all child objects which match childspec...
        segment_list = [
            cobj
            for cobj in children
            if re.search(childspec, cobj.text, regex_flags)
        ]
        # Return [None] if no children matched...
        if len(segment_list) == 0:
            segment_list = [None]

        if debug > 1:
            logger.info(f"    _find_child_object_branches() returns segment_list={segment_list}")
        return segment_list

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def find_object_branches(
        self,
        branchspec=(),
        regex_flags=0,
        allow_none=True,
        regex_groups=False,
        empty_branches=False,
        ignore_ws=False,
        escape_chars=False,
        debug=0,
    ):
        r"""Iterate over a tuple of regular expressions in `branchspec` and return matching objects in a list of lists (consider it similar to a table of matching config objects). `branchspec` expects to start at some ancestor and walk through the nested object hierarchy (with no limit on depth).

        Previous CiscoConfParse() methods only handled a single parent regex and single child regex (such as :func:`~ciscoconfparse2.CiscoConfParse.find_objects`).

        Transcend past one-level of parent-child relationship parsing to include multiple nested 'branches' of a single family (i.e. parents, children, grand-children, great-grand-children, etc).  The result of handling longer regex chains is that it flattens what would otherwise be nested loops in your scripts; this makes parsing heavily-nested configuratations like Juniper, Palo-Alto, and F5 much simpler.  Of course, there are plenty of applications for "flatter" config formats like IOS.

        Return a list of lists (of object 'branches') which are nested to the same depth required in `branchspec`.  However, unlike most other CiscoConfParse() methods, return an explicit `None` if there is no object match.  Returning `None` allows a single search over configs that may not be uniformly nested in every branch.

        Deprecation notice for the allow_none parameter
        -----------------------------------------------

        allow_none is deprecated and no longer a configuration option, as of version 1.6.16.
        Going forward, allow_none will always be considered True.

        Parameters
        ----------
        branchspec : tuple
            A tuple of python regular expressions to be matched.
        regex_flags :
            Chained regular expression flags, such as `re.IGNORECASE|re.MULTILINE`
        regex_groups : bool (default False)
            If True, return a tuple of re.Match groups instead of the matching configuration objects.
        empty_branches : bool (default False)
            If True, return a list of None statements if there is no match; before version 1.9.49, this defaulted True.
        debug : int
            Set debug > 0 for debug messages

        Returns
        -------
        list
            A list of lists of matching :class:`~ciscoconfparse2.IOSCfgLine` objects

        Examples
        --------
        >>> from operator import attrgetter
        >>> from ciscoconfparse2 import CiscoConfParse
        >>> config = [
        ...     'ltm pool FOO {',
        ...     '  members {',
        ...     '    k8s-05.localdomain:8443 {',
        ...     '      address 192.0.2.5',
        ...     '      session monitor-enabled',
        ...     '      state up',
        ...     '    }',
        ...     '    k8s-06.localdomain:8443 {',
        ...     '      address 192.0.2.6',
        ...     '      session monitor-enabled',
        ...     '      state down',
        ...     '    }',
        ...     '  }',
        ...     '}',
        ...     'ltm pool BAR {',
        ...     '  members {',
        ...     '    k8s-07.localdomain:8443 {',
        ...     '      address 192.0.2.7',
        ...     '      session monitor-enabled',
        ...     '      state down',
        ...     '    }',
        ...     '  }',
        ...     '}',
        ...     ]
        >>> parse = CiscoConfParse(config=config, syntax='junos', comment='#')
        >>>
        >>> branchspec = (r'ltm\spool', r'members', r'\S+?:\d+', r'state\sup')
        >>> branches = parse.find_object_branches(branchspec=branchspec)
        >>>
        >>> # We found three branches
        >>> len(branches)
        3
        >>> # Each branch must match the length of branchspec
        >>> len(branches[0])
        4
        >>> # Print out one object 'branch'
        >>> branches[0]
        [<IOSCfgLine # 0 'ltm pool FOO'>, <IOSCfgLine # 1 '    members' (parent is # 0)>, <IOSCfgLine # 2 '        k8s-05.localdomain:8443' (parent is # 1)>, <IOSCfgLine # 5 '            state up' (parent is # 2)>]
        >>>
        >>> # Get the a list of text lines for this branch...
        >>> [ii.text for ii in branches[0]]
        ['ltm pool FOO', '    members', '        k8s-05.localdomain:8443', '            state up']
        >>>
        >>> # Get the config text of the root object of the branch...
        >>> branches[0][0].text
        'ltm pool FOO'
        >>>
        >>> # Note: `None` in branches[1][-1] because of no regex match
        >>> branches[1]
        [<IOSCfgLine # 0 'ltm pool FOO'>, <IOSCfgLine # 1 '    members' (parent is # 0)>, <IOSCfgLine # 6 '        k8s-06.localdomain:8443' (parent is # 1)>, None]
        >>>
        >>> branches[2]
        [<IOSCfgLine # 10 'ltm pool BAR'>, <IOSCfgLine # 11 '    members' (parent is # 10)>, <IOSCfgLine # 12 '        k8s-07.localdomain:8443' (parent is # 11)>, None]
        """

        if self.config_objs.search_safe is False:
            error = "The configuration has changed since the last commit; a config search is not safe."
            logger.critical(error)
            raise NotImplementedError(error)

        # As of verion 1.6.16, allow_none is always True.  See the Deprecation
        # notice above...
        if allow_none is not True:
            warning = "The allow_none parameter is deprecated as of version 1.6.16.  Going forward, allow_none is always True."
            logger.warning(warning)
            allow_none = True

        if isinstance(branchspec, list):
            branchspec = tuple(branchspec)

        if isinstance(branchspec, tuple):
            if branchspec == ():
                error = "find_object_branches(): branchspec must not be empty"
                logger.error(error)
                raise ValueError(error)

        else:
            error = "find_object_branches(): Please enclose the branchspec regular expressions in a Python tuple"
            logger.error(error)
            raise ValueError(error)

        branches = []
        # iterate over the regular expressions in branchspec
        for idx, childspec in enumerate(branchspec):
            # FIXME: Insert debugging here...
            if idx == 0:
                # Get matching 'root' objects from the config
                next_kids = self._find_child_object_branches(
                    parent_obj=None,
                    childspec=childspec,
                    regex_flags=regex_flags,
                    allow_none=True,
                    debug=debug,
                )
                # Start growing branches from the segments we received...
                branches = [[kid] for kid in next_kids]

            else:
                new_branches = []
                for branch in branches:
                    # Extend existing branches into the new_branches
                    if branch[-1] is not None:
                        # Find children to extend the family branch...
                        next_kids = self._find_child_object_branches(
                            parent_obj=branch[-1],
                            childspec=childspec,
                            regex_flags=regex_flags,
                            allow_none=True,
                            debug=debug,
                        )

                        for kid in next_kids:
                            # Fork off a new branch and add each matching kid...
                            tmp = copy.copy(branch)
                            tmp.append(kid)
                            new_branches.append(tmp)
                    else:
                        branch.append(None)
                        new_branches.append(branch)

                # Ensure we have the most recent branches...
                branches = new_branches

        branches = new_branches

        # If regex_groups is True, assign regexp matches to the return matrix.
        if regex_groups is True:
            return_matrix = []
            # branchspec = (r"^interfaces", r"\s+(\S+)", r"\s+(unit\s+\d+)", r"family\s+(inet)", r"address\s+(\S+)")
            # for idx_matrix, row in enumerate(self.find_object_branches(branchspec)):
            for _, row in enumerate(branches):
                if not isinstance(row, Sequence):
                    raise RequirementFailure()

                # Before we check regex capture groups, allocate an "empty return_row"
                #   of the correct length...
                return_row = [(None,)] * len(branchspec)

                # Populate the return_row below...
                #     return_row will be appended to return_matrix...
                for idx, element in enumerate(row):
                    if element is None:
                        return_row[idx] = (None,)

                    else:
                        regex_result = re.search(branchspec[idx], element.text)
                        if regex_result is not None:
                            # Save all the regex capture groups in matched_capture...
                            matched_capture = regex_result.groups()
                            if len(matched_capture) == 0:
                                # If the branchspec groups() matches are a
                                # zero-length tuple, populate this return_row
                                # with the whole element's text
                                return_row[idx] = (element.text,)
                            else:
                                # In this case, we found regex capture groups
                                return_row[idx] = matched_capture
                        else:
                            # No regex capture groups b/c of no regex match...
                            return_row[idx] = (None,)

                return_matrix.append(return_row)

            branches = return_matrix

        # We could have lost or created an extra branch if these aren't the
        # same length
        retval = list()
        if bool(empty_branches) is False:
            for branch in branches:
                ###############################################################
                # discard the branch if it contains None (element that did
                # not match)
                ###############################################################
                if not all(branch):
                    continue
                retval.append(branch)
        else:
            retval = branches
        return retval

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def find_objects(self, linespec, exactmatch=False, ignore_ws=False, reverse=False):
        """Find all :class:`~models_cisco.IOSCfgLine` objects whose text matches ``linespec`` and return the :class:`~models_cisco.IOSCfgLine` objects in a python list.

        Parameters
        ----------
        linespec : str
            A string or python regular expression, which should be matched
        exactmatch : bool
            Defaults to False.  When set True, this option requires ``linespec`` match the whole configuration line, instead of a portion of the configuration line.
        ignore_ws : bool
            boolean that controls whether whitespace is ignored.  Default is False.
        reverse : bool
            boolean that controls whether the order of the results is reversed.  Default is False.

        Returns
        -------
        list
            A list of matching :class:`~ciscoconfparse2.IOSCfgLine` objects

        Examples
        --------
        This example illustrates the use of :func:`~ciscoconfparse2.CiscoConfParse.find_objects`

        >>> from ciscoconfparse2 import CiscoConfParse
        >>> config = [
        ...     '!',
        ...     'interface Serial1/0',
        ...     ' ip address 1.1.1.1 255.255.255.252',
        ...     '!',
        ...     'interface Serial1/1',
        ...     ' ip address 1.1.1.5 255.255.255.252',
        ...     '!',
        ...     ]
        >>> parse = CiscoConfParse(config=config)
        >>>
        >>> parse.find_objects(r'^interface')
        [<IOSCfgLine # 1 'interface Serial1/0'>, <IOSCfgLine # 4 'interface Serial1/1'>]
        >>>

        """
        if self.config_objs.search_safe is False:
            error = "The configuration has changed since the last commit; a config search is not safe."
            logger.critical(error)
            raise NotImplementedError(error)

        if self.debug > 0:
            logger.info(
                "find_objects('%s', exactmatch=%s) was called" % (linespec, exactmatch),
            )

        if ignore_ws:
            linespec = build_space_tolerant_regex(linespec)

        retval = self._find_line_OBJ(linespec, exactmatch)
        if bool(reverse):
            retval.reverse()
        return retval

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def find_parent_objects_orig(
        self,
        parentspec,
        childspec=None,
        ignore_ws=False,
        recurse=True,
        escape_chars=False,
    ):
        """
        Return a list of parent :class:`~models_cisco.IOSCfgLine` objects,
        which matched the ``parentspec`` and whose children match ``childspec``.
        Only the parent :class:`~models_cisco.IOSCfgLine` objects will be
        returned.

        Parameters
        ----------
        parentspec : str or list
            Text regular expression for the :class:`~models_cisco.IOSCfgLine` object to be matched; this must match the parent's line
        childspec : str
            Text regular expression for the line to be matched; this must match the child's line
        ignore_ws : bool
            boolean that controls whether whitespace is ignored
        recurse : bool
            Set True if you want to search all children (children, grand children, great grand children, etc...)
        escape_chars : bool
            Set True if you want to escape characters before searching

        Returns
        -------
        list
            A list of matching parent :class:`~models_cisco.IOSCfgLine` objects

        Examples
        --------
        This example uses :func:`~ciscoconfparse2.find_parent_objects()` to
        find all ports that are members of access vlan 300 in following
        config...

        .. code::

        !
        interface FastEthernet0/1
            switchport access vlan 532
            spanning-tree vlan 532 cost 3
        !
        interface FastEthernet0/2
            switchport access vlan 300
            spanning-tree portfast
        !
        interface FastEthernet0/3
            duplex full
            speed 100
            switchport access vlan 300
            spanning-tree portfast
        !

        The following interfaces should be returned:

        .. code::

        interface FastEthernet0/2
        interface FastEthernet0/3

        We do this by quering `find_objects_w_child()`; we set our
        parent as `^interface` and set the child as `switchport access
        vlan 300`.

        .. code-block:: python
        :emphasize-lines: 20

        >>> from ciscoconfparse2 import CiscoConfParse
        >>> config = ['!',
        ...           'interface FastEthernet0/1',
        ...           ' switchport access vlan 532',
        ...           ' spanning-tree vlan 532 cost 3',
        ...           '!',
        ...           'interface FastEthernet0/2',
        ...           ' switchport access vlan 300',
        ...           ' spanning-tree portfast',
        ...           '!',
        ...           'interface FastEthernet0/3',
        ...           ' duplex full',
        ...           ' speed 100',
        ...           ' switchport access vlan 300',
        ...           ' spanning-tree portfast',
        ...           '!',
        ...     ]
        >>> p = CiscoConfParse(config=config)
        >>> p.find_parent_objects('^interface',
        ...     'switchport access vlan 300')
        ...
        [<IOSCfgLine # 5 'interface FastEthernet0/2'>, <IOSCfgLine # 9 'interface FastEthernet0/3'>]
        >>>
        """
        if isinstance(parentspec, BaseCfgLine):
            parentspec = parentspec.text
        elif isinstance(parentspec, str):
            pass
        elif isinstance(parentspec, (list, tuple)):
            if len(parentspec) > 1:
                _results = set()
                for _idx, _ in enumerate(parentspec[0:-1]):
                    _parentspec = parentspec[_idx]
                    _childspec = parentspec[_idx + 1]
                    _values = self.find_parent_objects(
                        _parentspec,
                        _childspec,
                        ignore_ws=ignore_ws,
                        recurse=recurse,
                        escape_chars=escape_chars
                    )
                    if len(_values) == 0:
                        ######################################################
                        # If any _childspec fails to match, we will hit this
                        # condition when that failure happens.
                        ######################################################
                        return []
                    else:
                        # Add the parent of this set of values
                        _ = [_results.add(ii) for ii in _values]
                # Sort the de-duplicated results
                return sorted(_results)
            else:
                error = f"`parentspec` {type(parentspec)} must be longer than one element."
                logger.error(error)
                raise InvalidParameters(error)
        else:
            error = f"Received unexpected `parentspec` {type(parentspec)}"
            logger.error(error)
            raise InvalidParameters(error)

        if isinstance(childspec, BaseCfgLine):
            parentspec = childspec.text

        if ignore_ws:
            parentspec = build_space_tolerant_regex(parentspec)
            childspec = build_space_tolerant_regex(childspec)

        if escape_chars is True:
            ###################################################################
            # Escape regex to avoid embedded parenthesis problems
            ###################################################################
            parentspec = re.escape(parentspec)
            childspec = re.escape(childspec)

        return list(
            filter(
                lambda x: x.re_search_children(childspec, recurse=recurse),
                self.find_objects(parentspec),
            ),
        )

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def find_parent_objects(
        self,
        parentspec,
        childspec=None,
        ignore_ws=False,
        recurse=True,
        escape_chars=False,
    ):
        """
        Return a list of parent :class:`~models_cisco.IOSCfgLine` objects,
        which matched the ``parentspec`` and whose children match ``childspec``.
        Only the parent :class:`~models_cisco.IOSCfgLine` objects will be
        returned.

        Parameters
        ----------
        parentspec : str, list or tuple
            Text regular expression for the :class:`~models_cisco.IOSCfgLine` object to be matched; this must match the parent's line
        childspec : str
            Text regular expression for the line to be matched; this must match the child's line
        ignore_ws : bool
            boolean that controls whether whitespace is ignored
        recurse : bool
            Set True if you want to search all children (children, grand children, great grand children, etc...).  This is considered True if parentspec is a list or tuple.
        escape_chars : bool
            Set True if you want to escape characters before searching

        Returns
        -------
        list
            A list of matching parent :class:`~models_cisco.IOSCfgLine` objects

        Examples
        --------
        This example uses :func:`~ciscoconfparse2.find_parent_objects()` to
        find all ports that are members of access vlan 300 in following
        config...

        .. code::

        !
        interface FastEthernet0/1
            switchport access vlan 532
            spanning-tree vlan 532 cost 3
        !
        interface FastEthernet0/2
            switchport access vlan 300
            spanning-tree portfast
        !
        interface FastEthernet0/3
            duplex full
            speed 100
            switchport access vlan 300
            spanning-tree portfast
        !

        The following interfaces should be returned:

        .. code::

        interface FastEthernet0/2
        interface FastEthernet0/3

        We do this by quering `find_objects_w_child()`; we set our
        parent as `^interface` and set the child as `switchport access
        vlan 300`.

        .. code-block:: python
        :emphasize-lines: 20

        >>> from ciscoconfparse2 import CiscoConfParse
        >>> config = ['!',
        ...           'interface FastEthernet0/1',
        ...           ' switchport access vlan 532',
        ...           ' spanning-tree vlan 532 cost 3',
        ...           '!',
        ...           'interface FastEthernet0/2',
        ...           ' switchport access vlan 300',
        ...           ' spanning-tree portfast',
        ...           '!',
        ...           'interface FastEthernet0/3',
        ...           ' duplex full',
        ...           ' speed 100',
        ...           ' switchport access vlan 300',
        ...           ' spanning-tree portfast',
        ...           '!',
        ...     ]
        >>> p = CiscoConfParse(config=config)
        >>> p.find_parent_objects('^interface',
        ...     'switchport access vlan 300')
        ...
        [<IOSCfgLine # 5 'interface FastEthernet0/2'>, <IOSCfgLine # 9 'interface FastEthernet0/3'>]
        >>>
        """
        if self.config_objs.search_safe is False:
            error = "The configuration has changed since the last commit; a config search is not safe."
            logger.critical(error)
            raise NotImplementedError(error)

        if isinstance(parentspec, BaseCfgLine):
            parentspec = parentspec.text
        elif isinstance(parentspec, str):
            pass
        elif isinstance(parentspec, (list, tuple)):
            _result = set()
            _tmp = self.find_object_branches(
                parentspec,
                ignore_ws=ignore_ws,
                escape_chars=escape_chars
            )
            for _obj_branch in _tmp:
                # add the parent of that object branch to the result set
                _result.add(_obj_branch[0])

            if len(_result) == 0:
                ######################################################
                # If any _parentspec fails to match, we will hit this
                # condition when that failure happens.
                ######################################################
                return []
            else:
                # Sort and return the de-duplicated results
                return sorted(_result)
        else:
            error = f"Received unexpected `parentspec` {type(parentspec)}"
            logger.error(error)
            raise InvalidParameters(error)

        #######################################################################
        # Handle the case where parentspec is not a list or tuple
        #######################################################################
        if isinstance(childspec, BaseCfgLine):
            parentspec = childspec.text

        if ignore_ws:
            parentspec = build_space_tolerant_regex(parentspec)
            childspec = build_space_tolerant_regex(childspec)

        if escape_chars is True:
            ###################################################################
            # Escape regex to avoid embedded parenthesis problems
            ###################################################################
            parentspec = re.escape(parentspec)
            childspec = re.escape(childspec)

        return list(
            filter(
                lambda x: x.re_search_children(childspec, recurse=recurse),
                self.find_objects(parentspec),
            ),
        )

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def find_parent_objects_wo_child(self, parentspec, childspec, ignore_ws=False, recurse=False, escape_chars=False):
        r"""Return a list of parent :class:`~models_cisco.IOSCfgLine` objects, which matched the ``parentspec`` and whose children did not match ``childspec``.  Only the parent :class:`~models_cisco.IOSCfgLine` objects will be returned.  For simplicity, this method only finds oldest_ancestors without immediate children that match.

        Parameters
        ----------
        parentspec : str
            Text regular expression for the :class:`~models_cisco.IOSCfgLine` object to be matched; this must match the parent's line
        childspec : str
            Text regular expression for the line to be matched; this must match the child's line
        ignore_ws : bool
            boolean that controls whether whitespace is ignored
        recurse : bool
            boolean that controls whether to recurse through children of children
        escape_chars : bool
            boolean that controls whether to escape characters before searching

        Returns
        -------
        list
            A list of matching parent configuration lines

        Examples
        --------
        This example finds all ports that are autonegotiating in the following config...

        .. code::

           !
           interface FastEthernet0/1
            switchport access vlan 532
            spanning-tree vlan 532 cost 3
           !
           interface FastEthernet0/2
            switchport access vlan 300
            spanning-tree portfast
           !
           interface FastEthernet0/2
            duplex full
            speed 100
            switchport access vlan 300
            spanning-tree portfast
           !

        The following interfaces should be returned:

        .. code::

           interface FastEthernet0/1
           interface FastEthernet0/2

        We do this by quering `find_parent_objects_wo_child()`; we set our
        parent as `^interface` and set the child as `speed\s\d+` (a
        regular-expression which matches the word 'speed' followed by
        an integer).

        .. code-block:: python
           :emphasize-lines: 19

           >>> from ciscoconfparse2 import CiscoConfParse
           >>> config = ['!',
           ...           'interface FastEthernet0/1',
           ...           ' switchport access vlan 532',
           ...           ' spanning-tree vlan 532 cost 3',
           ...           '!',
           ...           'interface FastEthernet0/2',
           ...           ' switchport access vlan 300',
           ...           ' spanning-tree portfast',
           ...           '!',
           ...           'interface FastEthernet0/3',
           ...           ' duplex full',
           ...           ' speed 100',
           ...           ' switchport access vlan 300',
           ...           ' spanning-tree portfast',
           ...           '!',
           ...     ]
           >>> p = CiscoConfParse(config=config)
           >>> p.find_parent_objects_wo_child(r'^interface', r'speed\s\d+')
           [<IOSCfgLine # 1 'interface FastEthernet0/1'>, <IOSCfgLine # 5 'interface FastEthernet0/2'>]
           >>>
        """
        if self.config_objs.search_safe is False:
            error = "The configuration has changed since the last commit; a config search is not safe."
            logger.critical(error)
            raise NotImplementedError(error)

        if isinstance(parentspec, BaseCfgLine):
            parentspec = parentspec.text
        elif isinstance(parentspec, (list, tuple)):
            ##################################################################
            # Catch unsupported parentspec type here
            ##################################################################
            error = f"find_parent_objects_wo_child() `parentspec` does not support a {type(parentspec)}"
            logger.error(error)
            raise InvalidParameters(error)
        if isinstance(childspec, BaseCfgLine):
            parentspec = childspec.text

        if ignore_ws is True:
            parentspec = build_space_tolerant_regex(parentspec)
            childspec = build_space_tolerant_regex(childspec)

        if escape_chars is True:
            ###################################################################
            # Escape regex to avoid embedded parenthesis problems
            ###################################################################
            parentspec = re.escape(parentspec)
            childspec = re.escape(childspec)

        return [
            obj
            for obj in self.find_objects(parentspec)
            if not obj.re_search_children(childspec, recurse=recurse)
        ]

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def find_child_objects(
            self,
            parentspec,
            childspec=None,
            ignore_ws=False,
            recurse=True,
            escape_chars=False
    ):
        r"""Parse through the children of all parents matching parentspec,
        and return a list of child objects, which matched the childspec.

        Parameters
        ----------
        parentspec : str or list
            Text regular expression for the line to be matched; this must match the parent's line
        childspec : str
            Text regular expression for the line to be matched; this must match the child's line
        ignore_ws : bool
            boolean that controls whether whitespace is ignored
        escape_chars : bool
            boolean that controls whether characters are escaped before searching

        Returns
        -------
        list
            A list of matching child objects

        Examples
        --------
        This example finds the object for "ge-0/0/0" under "interfaces" in the
        following config...

        .. code::

            interfaces
                ge-0/0/0
                    unit 0
                        family ethernet-switching
                            port-mode access
                            vlan
                                members VLAN_FOO
                ge-0/0/1
                    unit 0
                        family ethernet-switching
                            port-mode trunk
                            vlan
                                members all
                            native-vlan-id 1
                vlan
                    unit 0
                        family inet
                            address 172.16.15.5/22


        The following object should be returned:

        .. code::

            <IOSCfgLine # 7 '    ge-0/0/1' (parent is # 0)>

        We do this by quering `find_child_objects()`; we set our
        parent as `^\s*interface` and set the child as
        `^\s+ge-0/0/1`.

        .. code-block:: python
           :emphasize-lines: 22,23

           >>> from ciscoconfparse2 import CiscoConfParse
           >>> config = ['interfaces',
           ...           '    ge-0/0/0',
           ...           '        unit 0',
           ...           '            family ethernet-switching',
           ...           '                port-mode access',
           ...           '                vlan',
           ...           '                    members VLAN_FOO',
           ...           '    ge-0/0/1',
           ...           '        unit 0',
           ...           '            family ethernet-switching',
           ...           '                port-mode trunk',
           ...           '                vlan',
           ...           '                    members all',
           ...           '                native-vlan-id 1',
           ...           '    vlan',
           ...           '        unit 0',
           ...           '            family inet',
           ...           '                address 172.16.15.5/22',
           ...     ]
           >>> p = CiscoConfParse(config=config)
           >>> p.find_child_objects('^\s*interfaces',
           ... r'\s+ge-0/0/1')
           [<IOSCfgLine # 7 '    ge-0/0/1' (parent is # 0)>]
           >>>

        """
        if self.config_objs.search_safe is False:
            error = "The configuration has changed since the last commit; a config search is not safe."
            logger.critical(error)
            raise NotImplementedError(error)

        if isinstance(parentspec, BaseCfgLine):
            parentspec = parentspec.text
        elif isinstance(parentspec, str):
            pass
        elif isinstance(parentspec, (list, tuple)):
            if len(parentspec) > 0:
                _result = set()
                _tmp = self.find_object_branches(
                    parentspec,
                    ignore_ws=ignore_ws,
                    escape_chars=escape_chars
                )
                for _obj_branch in _tmp:
                    # add the child of that object branch to the result set
                    _result.add(_obj_branch[-1])

                if len(_result) == 0:
                    ######################################################
                    # If any _childspec fails to match, we will hit this
                    # condition when that failure happens.
                    ######################################################
                    return []
                # Sort the de-duplicated results
                return sorted(_result)
            else:
                error = f"`parentspec` {type(parentspec)} must have at least one element."
                logger.error(error)
                raise InvalidParameters(error)
        else:
            error = f"Received unexpected `parentspec` {type(parentspec)}"
            logger.error(error)
            raise InvalidParameters(error)

        #######################################################################
        # Handle the case where parentspec is not a list or tuple
        #######################################################################
        if isinstance(childspec, BaseCfgLine):
            parentspec = childspec.text

        if ignore_ws:
            parentspec = build_space_tolerant_regex(parentspec)
            childspec = build_space_tolerant_regex(childspec)

        if escape_chars is True:
            ######################################################################
            # Escape regex to avoid embedded parenthesis problems
            ######################################################################
            parentspec = re.escape(parentspec)
            childspec = re.escape(childspec)

        retval = set()
        parents = self.find_objects(parentspec)
        if recurse is False:
            for parent in parents:
                ##############################################################
                # If recurse is False, only search direct children
                ##############################################################
                for child in parent.children:
                    if child.re_match(rf"({childspec})", default=False):
                        retval.add(child)
        else:
            for parent in parents:
                ##############################################################
                # If recurse is True, search all children including children
                #    of the children
                ##############################################################
                for child in parent.all_children:
                    if child.re_match(rf"({childspec})", default=False):
                        retval.add(child)

        return sorted(retval)

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def re_search_children(self, regexspec, recurse=False):
        """Use ``regexspec`` to search for root parents in the config with text matching regex.  If `recurse` is False, only root parent objects are returned.  A list of matching objects is returned.

        This method is very similar to :func:`~ciscoconfparse2.CiscoConfParse.find_objects` (when `recurse` is True); however it was written in response to the use-case described in `Github Issue #156 <https://github.com/mpenning/ciscoconfparse/issues/156>`_.

        Parameters
        ----------
        regexspec : str
            A string or python regular expression, which should be matched.
        recurse : bool
            Set True if you want to search all objects, and not just the root parents

        Returns
        -------
        list
            A list of matching :class:`~models_cisco.IOSCfgLine` objects which matched.  If there is no match, an empty :py:func:`list` is returned.

        """
        ## I implemented this method in response to Github issue #156
        if recurse is False:
            # Only return the matching oldest ancestor objects...
            return [obj for obj in self.find_objects(regexspec) if (obj.parent is obj)]
        else:
            # Return any matching object
            return [obj for obj in self.find_objects(regexspec)]

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def re_match_iter_typed(
        self,
        regexspec,
        group=1,
        result_type=str,
        default="",
        untyped_default=False,
    ):
        r"""Use ``regexspec`` to search the root parents in the config
        and return the contents of the regular expression group, at the
        integer ``group`` index, cast as ``result_type``; if there is no
        match, ``default`` is returned.

        Note
        ----
        Only the first regex match is returned.

        Parameters
        ----------
        regexspec : str
            A string or python compiled regular expression, which should be matched.  This regular expression should contain parenthesis, which bound a match group.
        group : int
            An integer which specifies the desired regex group to be returned.  ``group`` defaults to 1.
        result_type : type
            A type (typically one of: ``str``, ``int``, ``float``, or :class:`~ccp_util.IPv4Obj`).         All returned values are cast as ``result_type``, which defaults to ``str``.
        default : any
            The default value to be returned, if there is no match.  The default is an empty string.
        untyped_default : bool
            Set True if you don't want the default value to be typed

        Returns
        -------
        ``result_type``
            The text matched by the regular expression group; if there is no match, ``default`` is returned.  All values are cast as ``result_type``.  The default result_type is `str`.


        Examples
        --------
        This example illustrates how you can use
        :func:`~ciscoconfparse2.re_match_iter_typed` to get the
        first interface name listed in the config.

        >>> import re
        >>> from ciscoconfparse2 import CiscoConfParse
        >>> config = [
        ...     '!',
        ...     'interface Serial1/0',
        ...     ' ip address 1.1.1.1 255.255.255.252',
        ...     '!',
        ...     'interface Serial2/0',
        ...     ' ip address 1.1.1.5 255.255.255.252',
        ...     '!',
        ...     ]
        >>> parse = CiscoConfParse(config=config)
        >>> parse.re_match_iter_typed(r'interface\s(\S+)')
        'Serial1/0'
        >>>

        The following example retrieves the hostname from the configuration

        >>> from ciscoconfparse2 import CiscoConfParse
        >>> config = [
        ...     '!',
        ...     'hostname DEN-EDGE-01',
        ...     '!',
        ...     'interface Serial1/0',
        ...     ' ip address 1.1.1.1 255.255.255.252',
        ...     '!',
        ...     'interface Serial2/0',
        ...     ' ip address 1.1.1.5 255.255.255.252',
        ...     '!',
        ...     ]
        >>> parse = CiscoConfParse(config=config)
        >>> parse.re_match_iter_typed(r'^hostname\s+(\S+)')
        'DEN-EDGE-01'
        >>>

        """
        ## iterate through root objects, and return the matching value
        ##  (cast as result_type) from the first object.text that matches regex

        # if (default is True):
        ## Not using self.re_match_iter_typed(default=True), because I want
        ##   to be sure I build the correct API for match=False
        ##
        ## Ref IOSIntfLine.has_dtp for an example of how to code around
        ##   this while I build the API
        #    raise NotImplementedError

        for cobj in self.config_objs:
            # Only process parent objects at the root of the tree...
            if cobj.parent is not cobj:
                continue

            mm = re.search(regexspec, cobj.text)
            if mm is not None:
                return result_type(mm.group(group))
        ## Ref Github issue #121
        if untyped_default:
            return default
        else:
            return result_type(default)

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def save_as(self, filepath):
        """Save a text copy of the configuration at ``filepath``; this
        method uses the OperatingSystem's native line separators (such as
        ``\\r\\n`` in Windows)."""
        try:
            with open(filepath, "w", encoding=self.encoding) as newconf:
                for line in self.as_text:
                    newconf.write(line + "\n")
            return True
        except BaseException as ee:
            logger.error(str(ee))
            raise ee

    ### The methods below are marked SEMI-PRIVATE because they return an object
    ###  or iterable of objects instead of the configuration text itself.

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def _find_line_OBJ(self, linespec, exactmatch=False):
        """SEMI-PRIVATE: Find objects whose text matches the linespec"""

        if self.config_objs is None:
            err = "config_objs is None. self.config_objs logic failed."
            raise ValueError(err)

        if self.debug >= 2:
            logger.debug(
                "Looking for match of linespec='%s', exactmatch=%s"
                % (linespec, exactmatch),
            )

        # NOTE TO SELF: do not remove _find_line_OBJ(); used by Cisco employees
        if not exactmatch:
            # Return objects whose text attribute matches linespec
            linespec_re = re.compile(linespec)
        elif exactmatch:
            # Return objects whose text attribute matches linespec exactly
            linespec_re = re.compile("^%s$" % linespec)

        return list(
            filter(lambda obj: linespec_re.search(obj.text), self.config_objs),
        )

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def _find_sibling_OBJ(self, lineobject):
        """SEMI-PRIVATE: Takes a singe object and returns a list of sibling
        objects"""
        siblings = lineobject.parent.children
        return siblings

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def _find_all_child_OBJ(self, lineobject):
        """SEMI-PRIVATE: Takes a single object and returns a list of
        decendants in all 'children' / 'grandchildren' / etc... after it.
        It should NOT return the children of siblings"""
        # sort the list, and get unique objects
        retval = set(lineobject.children)
        for candidate in lineobject.children:
            if candidate.has_children:
                for child in candidate.children:
                    retval.add(child)
        retval = sorted(retval)
        return retval

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def _unique_OBJ(self, objectlist):
        """SEMI-PRIVATE: Returns a list of unique objects (i.e. with no
        duplicates).
        The returned value is sorted by configuration line number
        (lowest first)"""
        retval = set()
        for obj in objectlist:
            retval.add(obj)
        return sorted(retval)

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def _objects_to_uncfg(self, objectlist, unconflist):
        # Used by req_cfgspec_excl_diff()
        retval = []
        unconfdict = {}
        for unconf in unconflist:
            unconfdict[unconf] = "DEFINED"
        for obj in self._unique_OBJ(objectlist):
            if unconfdict.get(obj, None) == "DEFINED":
                retval.append(obj.uncfgtext)
            else:
                retval.append(obj.text)
        return retval


@attrs.define(repr=False)
class Diff(object):

    @logger.catch(reraise=True)
    def __init__(self, hostname=None, old_config=None, new_config=None, syntax='ios'):
        """
        Initialize Diff().

        Parameters
        ----------
        hostname : None
            An empty parameter, which seems to be optional for the diff backend
        old_config : str
            A string containing text configuration statements representing the most-recent config. Default value: `None`. If a filepath is provided, load the configuration from the file.
        new_config : str
            A string containing text configuration statements representing the desired config. Default value: `None`. If a filepath is provided, load the configuration from the file.
        syntax : str
            A string holding the configuration type.  Default: 'ios'.

        Returns
        -------
        :class:`~ciscoconfparse2.Diff()`
        """

        ######################################################################
        # Handle hostname
        ######################################################################
        if hostname is not None:
            error = f"hostname='{hostname}' is not supported"
            logger.error(error)

        ######################################################################
        # Handle old_config
        ######################################################################
        if old_config is None:
            old_config = []
        elif isinstance(old_config, str) and len(old_config.splitlines()) == 1 and os.path.isfile(old_config):
            # load the old config from a file as a string...
            old_config = open(old_config).read()
        elif isinstance(old_config, str):
            pass
        elif isinstance(old_config, (list, tuple)):
            old_config = os.linesep.join(old_config)
        else:
            error = f"old_config {type(old_config)} must be a network configuration in a string, or a filepath to the configuration"
            logger.error(error)
            raise ValueError(error)

        ######################################################################
        # Handle new_config
        ######################################################################
        if new_config is None:
            new_config = []
        elif isinstance(new_config, str) and len(new_config.splitlines()) == 1 and os.path.isfile(new_config):
            # load the new config from a file as a list...
            new_config = open(new_config).read().splitlines()
        elif isinstance(new_config, str):
            pass
        elif isinstance(new_config, (list, tuple)):
            new_config = os.linesep.join(new_config)
        else:
            error = f"new_config {type(new_config)} must be a network configuration in a string, or a filepath to the configuration"
            logger.error(error)
            raise ValueError(error)

        ######################################################################
        # Handle syntax
        ######################################################################
        if syntax != 'ios':
            error = f"syntax='{syntax}' is not supported"
            logger.error(error)
            raise NotImplementedError(error)

        ###################################################################
        # For now, we will not use options_ios.yml... see
        #     https://github.com/netdevops/hier_config/blob/master/tests/fixtures/options_ios.yml
        ###################################################################
        # _ represents ios options as a dict... for now we use an empty
        # dict below...
        try:
            _ = yaml.load(open('./options_ios.yml'), Loader=yaml.SafeLoader)
        except FileNotFoundError:
            pass
        # For now, we use {} instead of `options_ios.yml`
        self.host = hier_config.Host('example_hostname', 'ios', {})

        # Old configuration
        self.host.load_running_config(old_config)
        # New configuration
        self.host.load_generated_config(new_config)

    @logger.catch(reraise=True)
    def diff(self):
        """
        diff() returns the list of required configuration statements to go from the old_config to the new_config
        """
        retval = []
        diff_config = self.host.remediation_config()
        for obj in diff_config.all_children_sorted():
            retval.append(obj.cisco_style_text())
        return retval

    @logger.catch(reraise=True)
    def rollback(self):
        """
        rollback() returns the list of required configuration statements to rollback from the new_config to the old_config
        """
        retval = []
        rollback_config = self.host.rollback_config()
        for obj in rollback_config.all_children_sorted():
            retval.append(obj.cisco_style_text())
        return retval




#########################################################################3


class DiffObject(object):
    """This object should be used at every level of hierarchy"""

    @logger.catch(reraise=True)
    def __init__(self, level, nonparents, parents):
        self.level = level
        self.nonparents = nonparents
        self.parents = parents

    @logger.catch(reraise=True)
    def __repr__(self):
        return "<DiffObject level: {}>".format(self.level)


class CiscoPassword(object):
    @logger.catch(reraise=True)
    def __init__(self, ep=""):
        self.ep = ep

    @logger.catch(reraise=True)
    def decrypt(self, ep=""):
        """Cisco Type 7 password decryption.  Converted from perl code that was
        written by jbash [~at~] cisco.com; enhancements suggested by
        rucjain [~at~] cisco.com"""

        xlat = (
            0x64,
            0x73,
            0x66,
            0x64,
            0x3B,
            0x6B,
            0x66,
            0x6F,
            0x41,
            0x2C,
            0x2E,
            0x69,
            0x79,
            0x65,
            0x77,
            0x72,
            0x6B,
            0x6C,
            0x64,
            0x4A,
            0x4B,
            0x44,
            0x48,
            0x53,
            0x55,
            0x42,
            0x73,
            0x67,
            0x76,
            0x63,
            0x61,
            0x36,
            0x39,
            0x38,
            0x33,
            0x34,
            0x6E,
            0x63,
            0x78,
            0x76,
            0x39,
            0x38,
            0x37,
            0x33,
            0x32,
            0x35,
            0x34,
            0x6B,
            0x3B,
            0x66,
            0x67,
            0x38,
            0x37,
        )

        dp = ""
        regex = re.compile("^(..)(.+)")
        ep = ep or self.ep
        if not (len(ep) & 1):
            result = regex.search(ep)
            try:
                s, e = int(result.group(1)), result.group(2)
            except ValueError:
                # typically get a ValueError for int( result.group(1))) because
                # the method was called with an unencrypted password.  For now
                # SILENTLY bypass the error
                s, e = (0, "")
            for ii in range(0, len(e), 2):
                # int( blah, 16) assumes blah is base16... cool
                magic = int(re.search(".{%s}(..)" % ii, e).group(1), 16)
                # Wrap around after 53 chars...
                newchar = "%c" % (magic ^ int(xlat[int(s % 53)]))
                dp = dp + str(newchar)
                s = s + 1
        # if s > 53:
        #    logger.warning("password decryption failed.")
        return dp


@logger.catch(reraise=True)
def config_line_factory(all_lines=None, line=None, comment_delimiters=None, syntax="ios", debug=0):
    """A factory method to assign a custom BaseCfgLine() subclass based on `all_lines`, `line`, `comment_delimiters`, and `syntax` parameters."""
    # Complicted & Buggy
    # classes = [j for (i,j) in globals().iteritems() if isinstance(j, TypeType) and issubclass(j, BaseCfgLine)]
    if not isinstance(all_lines, list):
        error = f"config_line_factory(all_lines=`{all_lines}`) must be a list, but we got {type(all_lines)}"
        logger.error(error)
        raise InvalidParameters(error)

    if not isinstance(line, str):
        error = f"config_line_factory(text=`{line}`) must be a string, but we got {type(line)}"
        logger.error(error)
        raise InvalidParameters(error)

    if not isinstance(comment_delimiters, list):
        error = f"config_line_factory(comment_delimiters=`{comment_delimiters}`) must be a list of chars, but we got {type(comment_delimiters)}"
        logger.error(error)
        raise InvalidParameters(error)

    if not isinstance(syntax, str):
        error = f"config_line_factory(syntax=`{syntax}`) must be a string, but we got {type(syntax)}"
        logger.error(error)
        raise InvalidParameters(error)

    if not isinstance(debug, int):
        error = f"config_line_factory(debug=`{debug}`) must be an integer, but we got {type(debug)}"
        logger.error(error)
        raise InvalidParameters(error)

    if syntax not in ALL_VALID_SYNTAX:
        error = f"`{syntax}` is an unknown syntax"
        logger.error(error)
        raise ValueError(error)

    ##########################################################################
    # Select which list of factory classes will be used
    ##########################################################################
    factory_classes = None
    if syntax == "ios":
        factory_classes = ALL_IOS_FACTORY_CLASSES
    elif syntax == "nxos":
        factory_classes = ALL_NXOS_FACTORY_CLASSES
    elif syntax == "iosxr":
        factory_classes = ALL_IOSXR_FACTORY_CLASSES
    elif syntax == "asa":
        factory_classes = ALL_ASA_FACTORY_CLASSES
    elif syntax == "junos":
        factory_classes = ALL_JUNOS_FACTORY_CLASSES
    else:
        error = f"Cannot find a factory class list for syntax=`{syntax}`"
        logger.error(error)
        raise InvalidParameters(error)

    ##########################################################################
    # Walk all the classes and return the first class that
    # matches `.is_object_for(text)`.
    ##########################################################################
    try:
        for cls in factory_classes:
            if debug > 0:
                logger.debug(f"Consider config_line_factory() CLASS {cls}")
            if cls.is_object_for(all_lines=all_lines, line=line):
                basecfgline_subclass = cls(
                    all_lines=all_lines, line=line,
                    comment_delimiters=comment_delimiters,
                )  # instance of the proper subclass
                return basecfgline_subclass
    except ValueError:
        error = f"ciscoconfparse2.py config_line_factory(all_lines={all_lines}, line=`{line}`, comment_delimiters=[`{comment_delimiter}`], syntax=`{syntax}`) could not find a subclass of BaseCfgLine()"
        logger.error(error)
        raise ValueError(error)
    except Exception as eee:
        error = f"ciscoconfparse2.py config_line_factory(all_lines={all_lines}, line=`{line}`, comment_delimiters=[`{comment_delimiter}`], syntax=`{syntax}`): {eee}"

    if debug > 0:
        logger.debug("config_line_factory() is returning a default of IOSCfgLine()")
    return IOSCfgLine(all_lines=all_lines, line=line, comment_delimiters=comment_delimiters)


def parse_global_options():
    import optparse

    pp = optparse.OptionParser()
    pp.add_option(
        "-c",
        dest="config",
        help="Config file to be parsed",
        metavar="FILENAME",
    )
    pp.add_option(
        "-m",
        dest="method",
        help="Command for parsing",
        metavar="METHOD",
    )
    pp.add_option(
        "--a1",
        dest="arg1",
        help="Command's first argument",
        metavar="ARG",
    )
    pp.add_option(
        "--a2",
        dest="arg2",
        help="Command's second argument",
        metavar="ARG",
    )
    pp.add_option(
        "--a3",
        dest="arg3",
        help="Command's third argument",
        metavar="ARG",
    )
    (opts, args) = pp.parse_args()

    if opts.method == "decrypt":
        pp = CiscoPassword()
        print(pp.decrypt(opts.arg1))
        exit(1)
    elif opts.method == "help":
        print("Valid methods and their arguments:")
        print("   decrypt:                arg1=encrypted_passwd")
        exit(1)
    else:
        import doctest

        doctest.testmod()
        exit(0)

    if len(diff) > 0:
        for line in diff:
            print(line)
    else:
        opt_error = "ciscoconfparse2 was called with unknown parameters"
        logger.error(opt_error)
        raise RuntimeError(opt_error)


# TODO: Add unit tests below
if __name__ == "__main__":
    parse_global_options()
