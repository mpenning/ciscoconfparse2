r"""ccp_abc.py - Parse, Query, Build, and Modify IOS-style configurations
Copyright (C) 2023-2025 David Michael Pennington

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

import math
import re
from collections.abc import Sequence
from typing import Any, List, Union

import attrs
from loguru import logger

from ciscoconfparse2.ccp_util import junos_unsupported
from ciscoconfparse2.errors import (
    ConfigListItemDoesNotExist,
    InvalidParameters,
    InvalidTypecast,
)

DEFAULT_TEXT = "__undefined__"


@logger.catch(reraise=True)
def get_brace_termination(line: str) -> str:
    """
    Get the brace termination string from the ``line`` parameter.

    :return: The brace termination string for this ``line``.
    :rtype: str

    .. code-block:: python

        >>> get_brace_termination("http { }")
        '{ }'
        >>>
        >>> get_brace_termination("ltm virtual ACME { ")
        '{'
        >>> get_brace_termination("    } ")
        '}'
        >>>
    """
    brace_chars = {"{", "}"}
    reversed_line = list(line.strip())
    reversed_line.reverse()

    _retval = []
    brace_open = False
    # Walk backwards in the configuration line and get all brace termination
    for char in reversed_line:
        if char == "}":
            brace_open = True

        if char in brace_chars or char.isspace():
            if brace_open and char.isspace():
                _retval.append(char)
            elif char in brace_chars:
                _retval.append(char)

        if brace_open and char == "{":
            brace_open = False

    # Go back to a normal left-to-right string...
    _retval.reverse()
    return "".join(_retval).strip()


#
# -------------  Config Line ABC
#


# Set slots False to ensure that BaseCfgLine() has a __dict__
@attrs.define(repr=False, kw_only=True, slots=False)
class BaseCfgLine:
    """Base configuration object for all configuration line instances; in most cases, the configuration line will be a subclass of this object."""

    all_text: Any = None
    all_lines: Any = None
    line: str = DEFAULT_TEXT
    _text: str = DEFAULT_TEXT
    linenum: int = -1
    parent: Any = None
    child_indent: int = 0
    _children: list = []
    confobj: Any = None  # Reference to the list object which owns it
    blank_line_keep: bool = False  # CiscoConfParse() uses blank_line_keep

    # __implementing __setstate__ for loguru picking problems...
    __setstate__: Any = None

    feature: str = None
    _brace_termination: str = ""

    @logger.catch(reraise=True)
    def __init__(self, all_lines=None, line=DEFAULT_TEXT, **kwargs):
        """Accept an IOS line number and initialize family relationship attributes"""

        # Hack to accept old parameter names instead of finding all the places
        # where `all_text` and `text` are used and renaming attributes all
        # over the place
        if isinstance(kwargs.get("all_text", None), list):
            # The all_text kwarg is now called all_lines
            all_lines = kwargs.get("all_text")
        if isinstance(kwargs.get("text", None), str):
            # The text kwarg is now called line
            line = kwargs.get("text")
        if isinstance(kwargs.get("linenum", None), int):
            linenum = kwargs.get("linenum")
        else:
            linenum = -1
        if isinstance(kwargs.get("children", None), list):
            children = kwargs.get("children")
        else:
            children = []
        if isinstance(kwargs.get("child_indent", None), int):
            child_indent = kwargs.get("child_indent")
        else:
            child_indent = 0
        if kwargs.get("confobj", None) is not None:
            confobj = kwargs.get("confobj")
        else:
            confobj = None

        if isinstance(kwargs.get("comment_delimiters", None), list):
            error = "BaseCfgLine() does not accept a comment_delimiters parameter"
            logger.critical(error)
            raise InvalidParameters(error)

        self._text = line
        self._children = children
        self.linenum = linenum
        self.parent = self  # by default, assign parent as itself
        self.child_indent = child_indent
        self.confobj = confobj
        self.blank_line_keep = False  # CiscoConfParse() uses blank_line_keep

        self.all_text = all_lines
        self.all_lines = all_lines
        self.line = self._text

        # Implementing __setstate__ for loguru picking problems...
        self.__setstate__ = None

        self.feature = ""
        self._brace_termination = ""

        # FIXME
        #   Bypass @text.setter method for now...  @text.setter writes to
        #   self._text, but currently children do not associate correctly if
        #   @text.setter is used as-is...
        # self.text = text

    # On BaseCfgLine()
    @logger.catch(reraise=True)
    def __repr__(self):
        try:
            this_linenum = self.linenum
        except BaseException:
            this_linenum = None

        try:
            parent_linenum = self.parent.linenum
        except BaseException:
            parent_linenum = this_linenum

        if not self.is_child:
            return f"<{self.classname} # {this_linenum} '{self.text}'>"
        else:
            return f"<{self.classname} # {this_linenum} '{self.text}' (parent is # {parent_linenum})>"

    # On BaseCfgLine()
    @logger.catch(reraise=True)
    def __str__(self):
        return self.text

    # On BaseCfgLine()
    @logger.catch(reraise=True)
    def __contains__(self, arg: str) -> bool:
        """Implement 'arg in self' for this class"""
        return arg in self.text

    # On BaseCfgLine()
    @logger.catch(reraise=True)
    def __getitem__(self, subscript) -> str:
        """Implement string slicing on the object"""
        if isinstance(subscript, slice):
            # Use the subscript object from the slicing index
            #     credit - https://stackoverflow.com/a/34372150/667301
            #     i.e. obj[0:5]
            return self.text[subscript.start : subscript.stop : subscript.step]
        else:
            #     i.e. obj[0]
            return self.text[subscript]

    # On BaseCfgLine()
    @logger.catch(reraise=True)
    def __iter__(self) -> str:
        yield from self.text

    # On BaseCfgLine()
    @logger.catch(reraise=True)
    def __len__(self) -> int:
        return len(self._text)

    # On BaseCfgLine()
    @logger.catch(reraise=True)
    def __hash__(self) -> int:
        """
        :return: A unique identifier for this object
        :rtype: int

        .. note::

           Also see :py:meth:`BaseCfgLine.get_unique_identifier`.
        """
        return self.get_unique_identifier()

    # On BaseCfgLine()
    @logger.catch(reraise=True)
    def __eq__(self, val):
        if not getattr(val, "get_unique_identifier", False):
            return False

        try:
            #   try / except is much faster than isinstance();
            #   I added hash_arg() inline below for speed... whenever I change
            #   self.__hash__() I *must* change this
            # FIXME
            return self.get_unique_identifier() == val.get_unique_identifier()
        except BaseException as eee:
            logger.error(eee)
            return False

    # On BaseCfgLine()
    @logger.catch(reraise=True)
    def __gt__(self, val):
        if self.linenum > val.linenum:
            return True
        return False

    # On BaseCfgLine()
    @logger.catch(reraise=True)
    def __lt__(self, val):
        # Ref: http://stackoverflow.com/a/7152796/667301
        if self.linenum < val.linenum:
            return True
        return False

    # On BaseCfgLine()
    @logger.catch(reraise=True)
    def get_unique_identifier(self) -> int:
        """
        :return: A unique number for the BaseCfgLine object
        :rtype: int
        """
        linenum = getattr(self, "linenum", None)
        _text = getattr(self, "text", DEFAULT_TEXT)
        return hash(linenum) * hash(_text)

    # On BaseCfgLine()
    @property
    @logger.catch(reraise=True)
    def indent(self) -> int:
        """
        :return: Padding of the number of left spaces of the ``text`` property
        :rtype: int
        """
        return len(self._text) - len(self.text.lstrip())

    # On BaseCfgLine()
    @property
    @logger.catch(reraise=True)
    def is_comment(self) -> bool:
        """Return True if the line is a comment"""
        if not isinstance(self.confobj, Sequence):
            # Comments are only valid in a real configuration list; otherwise
            # there is no syntax hint to determine whether the line is a
            # comment... just return None in this case...
            return None

        if isinstance(self._text, str):
            if len(self._text.lstrip()) > 0:
                first_char = self._text.lstrip()[0]
                if first_char in self.confobj.comment_delimiters:
                    return True
        return False

    # On BaseCfgLine()
    @property
    @logger.catch(reraise=True)
    def text(self) -> str:
        """
        :return: Configuration text
        :rtype: str
        """
        _text = getattr(self, "_text", DEFAULT_TEXT)
        return _text

    # On BaseCfgLine()
    @text.setter
    @logger.catch(reraise=True)
    def text(self, value: str) -> None:
        """
        Set the value of the configuration text for the BaseCfgLine().

        This method sets the :py:attr:`ccp_abc.BaseCfgLine.brace_termination` attribute.

        :return: Configuration text
        :rtype: None
        """
        is_comment = getattr(self, "is_comment", None)
        if isinstance(value, str):
            self._text = self.safe_escape_curly_braces(value)

            if is_comment is True:
                # VERY IMPORTANT: due to old behavior, comment parents MUST be self
                #
                self.parent = self
        else:
            error = f"BaseCfgLine() does not support 'text' assignment of {type(value)}"
            logger.error(error)
            raise InvalidParameters(error)

    # On BaseCfgLine()
    @property
    @logger.catch(reraise=True)
    def brace_termination(self) -> str:
        """
        :return: The brace termination string for this BaseCfgLine()
        :rtype: str
        """
        _brace_termination = getattr(self, "_brace_termination", "")
        return _brace_termination

    # On BaseCfgLine()
    @brace_termination.setter
    @logger.catch(reraise=True)
    def brace_termination(self, value: str) -> None:
        """
        :param value: The brace terminator string to be used with this BaseCfgLine().
        :type value: str
        :rtype: None
        """
        if isinstance(value, str):
            self._brace_termination = value
        else:
            error = f"BaseCfgLine() does not support 'brace_termination' assignment of {type(value)}"
            logger.error(error)
            raise InvalidParameters(error)

    @property
    @logger.catch(reraise=True)
    def children(self):
        """Return the direct children of this object"""

        if isinstance(self._children, list):
            return self._children
        else:
            error = f"Fatal: {type(self._children)} found as BaseCfgLine().children; it should be a list."
            logger.critical(error)
            raise NotImplementedError(error)

    @children.setter
    @logger.catch(reraise=True)
    def children(self, arg):
        if isinstance(arg, list):
            self._children = arg
            return self._children
        else:
            error = f"{type(arg)} cannot be assigned to BaseCfgLine().children"
            logger.critical(error)
            raise NotImplementedError(error)

    # On BaseCfgLine()
    @property
    @logger.catch(reraise=True)
    def is_intf(self):
        """subclasses will override this method"""
        raise NotImplementedError()

    # On BaseCfgLine()
    @is_intf.setter
    @logger.catch(reraise=True)
    def is_intf(self, value):
        raise NotImplementedError()

    # On BaseCfgLine()
    @property
    @logger.catch(reraise=True)
    def is_subintf(self):
        """subclasses will override this method"""
        raise NotImplementedError()

    # On BaseCfgLine()
    @is_subintf.setter
    @logger.catch(reraise=True)
    def is_subintf(self, value):
        raise NotImplementedError()

    # On BaseCfgLine()
    @property
    @logger.catch(reraise=True)
    def is_switchport(self):
        """subclasses will override this method"""
        raise NotImplementedError()

    # On BaseCfgLine()
    @is_switchport.setter
    @logger.catch(reraise=True)
    def is_switchport(self, value):
        raise NotImplementedError()

    # On BaseCfgLine()
    @property
    @logger.catch(reraise=True)
    def index(self):
        """Alias index to linenum"""
        return self.linenum

    # On BaseCfgLine()
    @logger.catch(reraise=True)
    def safe_escape_curly_braces(self, text):
        """Escape curly braces in strings since they could be misunderstood as
        f-string or string.format() delimiters...

        If BaseCfgLine receives line with curly-braces, this method can
        escape the curly braces so they are not mis-interpreted as python
        string formatting delimiters.
        """
        # Bypass escaping curly braces if there aren't any...
        if not ("{" in text) and not ("}" in text):
            return text

        assert ("{" in text) or ("}" in text)

        # Skip escaping curly braces if text already has double curly braces...
        if ("{{" in text) or ("}}" in text):
            return text

        text = text.replace("{", "{{")
        text = text.replace("}", "}}")
        return text

    # On BaseCfgLine()
    @property
    def dna(self):
        """Return the classname of this object"""
        return self.classname

    # On BaseCfgLine()
    @property
    def hash_children(self):
        """Return a unique hash of all children (if the number of children > 0)"""
        if len(self.all_children) > 0:
            return hash(tuple(self.all_children))
        else:
            return hash(())

    # On BaseCfgLine()
    @property
    def family_endpoint(self) -> int:
        """
        :return: The line number of the last child (or grandchild, etc)
        :rtype: int
        """
        assert isinstance(self.all_children, list)
        if self.all_children == []:
            return self.linenum
        else:
            return self.all_children[-1].linenum

    # On BaseCfgLine()
    @property
    def verbose(self) -> str:
        """
        :return: A string representation of this object
        :rtype: str
        """
        if self.has_children:
            return f"<{self.classname} # {self.linenum} '{self.text}' (child_indent: {self.child_indent} / len(children): {len(self.children)} / family_endpoint: {self.family_endpoint})>"

        else:
            return f"<{self.classname} # {self.linenum} '{self.text}' (no_children / family_endpoint: {self.family_endpoint})>"

    # On BaseCfgLine()
    @property
    def all_parents(self) -> list:
        """
        :return: A sequence of all parent objects, not including this object
        :rtype: List[BaseCfgLine]
        """
        if self.confobj is not None and self.confobj.search_safe is False:
            error = "The configuration has changed since the last commit; a config search is not safe."
            logger.critical(error)
            raise NotImplementedError(error)

        retval = set()
        this = self
        while this.parent != this:
            retval.add(this.parent)
            this = this.parent
        return sorted(retval)

    # On BaseCfgLine()
    @property
    def all_children(self) -> list:
        """
        :return: A sequence of all child objects, not including this object
        :rtype: List[BaseCfgLine]
        """
        retval = []
        if self.has_children:
            for child in self.children:
                retval.append(child)
                retval.extend(child.all_children)
        return sorted(retval)

    # On BaseCfgLine()
    @property
    def classname(self) -> str:
        """
        :return: The class name of this object
        :rtype: str
        """
        return self.__class__.__name__

    # On BaseCfgLine()
    @property
    def has_children(self) -> bool:
        """
        :return: Whether this object has children
        :rtype: bool
        """
        if isinstance(self.children, list) and len(self.children) > 0:
            return True
        return False

    # On BaseCfgLine()
    @property
    def is_config_line(self) -> bool:
        """Return a boolean for whether this is a config statement; returns False

        :return: Whether this object is a config line, blank line, or a comment.
        :rtype: bool
        """
        if len(self.text.lstrip()) > 0 and not self.is_comment:
            return True
        return False

    # On BaseCfgLine()
    @junos_unsupported
    def add_parent(self, parentobj: Any = None) -> bool:
        """
        Assign ``parentobj`` as the parent of this object.

        :return: True
        :rtype: bool
        """

        if parentobj is None:
            raise NotImplementedError()

        if not isinstance(parentobj, BaseCfgLine):
            raise NotImplementedError()

        self.parent = parentobj
        return True

    # On BaseCfgLine()
    @logger.catch(reraise=True)
    def delete(self) -> bool:
        """
        Delete this object, including from references in lists of child
        objects.  By default, if a parent object is deleted, the child
        objects are also deleted.

        :return: Whether the delete operation was a success.
        :rtype: bool

        .. note::

           When deleting objects, delete from the bottom of the configuration
           and work toward the beginning.  Failure to do this could result in
           a ``ConfigListItemDoesNotExist()`` error.

           Failure to commit after deleting objects will delete the object, but
           it leaves line number gaps.

        This example will delete all child objects; when deleting multiple
        objects, you should call
        :py:meth:`ciscoconfparse2.CiscoConfParse.find_objects` with
        ``reverse=True``.

        .. code-block:: python
           :emphasize-lines: 5

           >>> from ciscoconfparse2 import CiscoConfParse
           >>> config = ['a', ' child-b', 'c', ' child-d']
           >>> parse = CiscoConfParse(config)
           >>> for obj in parse.find_objects(r"child", reverse=True):
           ...     obj.delete()
           >>> parse.get_text()
           ['a', 'c']
           >>>
        """

        if self.confobj.debug >= 1:
            logger.info(f"{self}.delete() was called.")

        if self in self.confobj.data:
            # Build a set of all IOSCfgLine() object instances to be deleted...
            delete_these = {self}
        else:
            error = f"{self} instance no longer exists in the same place."
            logger.critical(error)
            raise ConfigListItemDoesNotExist(error)

        if self.confobj.debug >= 1:
            logger.debug(
                f"Executing <IOSCfgLine line #{self.linenum}>.delete(recurse=True)"
            )

        # NOTE - 1.5.30 changed this from iterating over self.children
        #        to self.all_children
        for child in self.all_children:
            delete_these.add(child)

        # reverse is important here so we can delete a range of line numbers
        # without clobbering the line numbers that haven't been deleted
        # yet...
        for obj in sorted(delete_these, reverse=True):
            linenum = obj.linenum
            if self.confobj.debug >= 1:
                logger.debug(f"    Deleting <IOSCfgLine(line # {linenum})>.")
            # If there has not been a commit between the last search
            # and delete, the line-number could be wrong...
            try:
                del self.confobj.data[linenum]
            except BaseException as eee:
                logger.critical(str(eee))
                raise eee

        #######################################################################
        # IMPORTANT: delete this object from it's parents' list of direct
        # children
        #######################################################################
        parentobj = self.parent
        for cobj in parentobj.children:
            if cobj is self:
                parentobj.children.remove(cobj)

        if self.confobj and self.confobj.auto_commit:
            self.confobj.ccp_ref.commit()
        elif self.confobj is None:
            raise NotImplementedError()

        return True

    # On BaseCfgLine()
    @logger.catch(reraise=True)
    def has_child_with(self, linespec: str, all_children: bool = False):
        """
        :param linespec: The string to search for
        :type linespec: str
        :param all_children: Whether to search all children (recursively)
        :type all_children: bool
        :type linespec: str
        :return: Whether ``linespec`` exists in any of children
        :rtype: bool
        """
        if not isinstance(all_children, bool):
            raise ValueError("has_child_with() all_children must be a boolean")

        # Old, crusty broken... fixed in 1.6.30...
        # return bool(filter(methodcaller("re_search", linespec), self.children))
        #
        # TODO - check whether using re_match_iter_typed() is faster than this:
        ll = linespec
        if all_children is False:
            offspring = self.children
        else:
            offspring = self.all_children

        length = len([ll for cobj in offspring if cobj.re_search(ll)])
        if length == 0:
            return False
        return True

    # On BaseCfgLine()
    @junos_unsupported
    @logger.catch(reraise=True)
    def insert_before(self, insertstr: str = None):
        """Usage: confobj.insert_before('! insert text before this confobj')"""
        # Fail if insertstr is not the correct object type...
        #   only strings and *CfgLine() are allowed...
        error = f"Cannot insert object type - {type(insertstr)}"
        if not isinstance(insertstr, str) and not isinstance(insertstr, BaseCfgLine):
            logger.error(error)
            raise NotImplementedError(error)

        retval = None
        if isinstance(insertstr, str) is True:
            retval = self.confobj.insert_before(exist_val=self.text, new_val=insertstr)

        elif isinstance(insertstr, BaseCfgLine) is True:
            retval = self.confobj.insert_before(
                exist_val=self.text, new_val=insertstr.text
            )

        else:
            raise ValueError(error)

        return retval

    # On BaseCfgLine()
    @junos_unsupported
    @logger.catch(reraise=True)
    def insert_after(self, insertstr=None):
        """Usage: confobj.insert_after('! insert text after this confobj')"""

        # Fail if insertstr is not the correct object type...
        #   only strings and *CfgLine() are allowed...
        error = f"Cannot insert object type - {type(insertstr)}"
        if not isinstance(insertstr, str) and not isinstance(insertstr, BaseCfgLine):
            logger.error(error)
            raise NotImplementedError(error)

        retval = None
        if self.confobj.debug >= 1:
            logger.debug(f"Inserting '{insertstr}' after '{repr(self)}'")

        if isinstance(insertstr, str) is True:
            # Handle insertion of a plain-text line
            retval = self.confobj.insert_after(exist_val=self.text, new_val=insertstr)

        elif isinstance(insertstr, BaseCfgLine):
            # Handle insertion of a configuration line obj such as IOSCfgLine()
            retval = self.confobj.insert_after(
                exist_val=self.text, new_val=insertstr.text
            )

        else:
            logger.error(error)
            raise ValueError(error)

        return retval

    # On BaseCfgLine()
    @logger.catch(reraise=True)
    def append_to_family(
        self, insertstr: str, indent: int = -1, auto_indent: bool = False
    ) -> None:
        """Append an :py:class:`~ciscoconfparse2.models_cisco.IOSCfgLine` object with ``insertstr``
        as a child at the top of the current configuration family.

        ``insertstr`` is inserted at the end of the family to ensure there are no
        unintended object relationships created during the change.

        :param insertstr: The text configuration to be appended
        :type insertstr: str
        :param indent: The text configuration to be appended, default to -1
        :type indent: int
        :param auto_indent: Automatically indent the child to :py:attr:`~ciscoconfparse2.CiscoConfParse.auto_indent_width`
        :type auto_indent: bool
        :return: None
        :rtype: None

        This example illustrates how you can use :py:func:`append_to_family` to add a
        ``carrier-delay`` to each interface.

        .. code-block:: python
           :emphasize-lines: 14

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
           >>> parse = CiscoConfParse(config)
           >>>
           >>> for obj in parse.find_objects(r'^interface', reverse=True):
           ...     obj.append_to_family(' carrier-delay msec 500')
           ...
           >>>
           >>> for line in parse.text:
           ...     print(line)
           ...
           !
           interface Serial1/0
            ip address 1.1.1.1 255.255.255.252
            carrier-delay msec 500
           !
           interface Serial1/1
            ip address 1.1.1.5 255.255.255.252
            carrier-delay msec 500
           !
           >>>
        """
        if isinstance(insertstr, BaseCfgLine):
            insertstr = insertstr.text

        # Get the value of auto_commit from the ConfigList()
        auto_commit = bool(self.confobj.auto_commit)
        auto_indent_width = self.confobj.ccp_ref.auto_indent_width

        if auto_indent is True and indent > 0:
            error = "indent and auto_indent are not supported together."
            logger.error(error)
            raise NotImplementedError(error)

        if self.confobj is None:
            error = "Cannot insert on a None BaseCfgLine().confobj"
            logger.critical(error)
            raise NotImplementedError(error)

        # This object is the parent
        insertstr_parent_indent = self.indent

        # Build the string to insert with proper indentation...
        if indent > 0:
            insertstr = (" " * indent) + insertstr.lstrip()
        elif bool(auto_indent) is True:
            insertstr = (
                " " * (auto_indent_width * insertstr_parent_indent + 1)
                + insertstr.lstrip()
            )
        else:
            # do not modify insertstr indent, or indentstr leading spaces
            pass

        # BaseCfgLine.append_to_family(), insert a single line after this
        #  object...
        this_obj = type(self)
        newobj = this_obj(line=insertstr)
        newobj_parent = self

        if isinstance(self, BaseCfgLine):
            try:
                if len(self.all_children) == 0 and len(self.children) == 0:
                    ###########################################################
                    # If all changes have been committed, insert the first
                    # child or object sibling here
                    ###########################################################

                    ###########################################################
                    # Walk all indents and find the last linenumber at that
                    # indent-level...
                    ###########################################################
                    last_parent_linenums = {}
                    for obj in self.confobj.data:
                        if self not in obj.lineage:
                            continue
                        obj_indent = self.classify_family_indent(obj.text)
                        if isinstance(last_parent_linenums.get(obj_indent, None), int):
                            if obj.linenum > last_parent_linenums[obj_indent]:
                                last_parent_linenums[obj_indent] = obj.linenum
                        else:
                            last_parent_linenums[obj_indent] = obj.linenum

                    ###########################################################
                    # Calculate the index number based on existing family
                    # structure
                    ###########################################################
                    this_indent = self.classify_family_indent(self.text)
                    new_family_indent = self.classify_family_indent(newobj.text)
                    if this_indent == new_family_indent:
                        if len(self.siblings) > 0:
                            _idx = self.siblings[-1].linenum + 1
                        else:
                            _idx = self.last_family_linenum + 1
                    elif this_indent + 1 == new_family_indent:
                        _idx = last_parent_linenums[this_indent] + 1
                        self.children.append(newobj)
                    else:
                        raise NotImplementedError()

                    retval = self.confobj.insert(_idx, newobj)

                    ###########################################################
                    # Append children as required...
                    ###########################################################
                    if self.classify_family_indent(insertstr) == 0:
                        pass
                    elif self.classify_family_indent(insertstr) == 1:
                        self.children.append(newobj)
                    elif self.classify_family_indent(insertstr) > 1:
                        raise NotImplementedError()

                    if auto_commit is True:
                        self.confobj.ccp_ref.commit()
                    return retval

                elif len(self.all_children) > 0 and len(self.children) == 0:

                    _idx = self.linenum + 1
                    retval = self.confobj.insert(_idx, newobj)
                    insertstr_family_indent = self.classify_family_indent(insertstr)
                    self.children.append(newobj)
                    if auto_commit is True:
                        self.confobj.ccp_ref.commit()
                    return retval

                elif len(self.all_children) > 0 and len(self.children) > 0:
                    ###########################################################
                    # Potentially append another child to the family
                    ###########################################################

                    insertstr_family_indent = self.classify_family_indent(insertstr)
                    if insertstr_family_indent == 0:
                        #######################################################
                        # Append a sibling for the children
                        #######################################################
                        _idx = self.linenum + len(self.children)

                    elif insertstr_family_indent > self.classify_family_indent(
                        self.text
                    ):
                        #######################################################
                        # Insert a child... do the children have children?
                        #######################################################
                        if len(self.children[-1].children) > 0:
                            _idx = self.linenum + len(self.all_children) + 1
                        else:
                            _idx = self.linenum + len(self.children) + 1

                    elif insertstr_family_indent < self.classify_family_indent(
                        self.text
                    ):
                        # inserstr is indented less than this object
                        raise NotImplementedError()

                    else:
                        # something unexpected happened
                        raise NotImplementedError()

                    classify_family_indent = self.classify_family_indent(insertstr)
                    if classify_family_indent == 1:
                        self.children.append(newobj)
                    elif classify_family_indent > 1:
                        raise NotImplementedError(
                            "Cannot append more than one child level"
                        )
                    retval = self.confobj.insert(_idx, newobj)

                    if auto_commit is True:
                        self.confobj.ccp_ref.commit()

                    return retval

                else:
                    ###########################################################
                    # If all changes have been committed, insert the first
                    # child here
                    ###########################################################

                    # Use newobj_parent.linenum instead of
                    # self.confobj.index(foo), which is rather fragile with
                    # this UserList...
                    _idx = self.linenum + 1

                    retval = self.confobj.insert(_idx, newobj)
                    retval = self.children.append(newobj)

                    if auto_commit is True:
                        self.confobj.ccp_ref.commit()
                    return retval

            except BaseException as eee:
                raise eee
        elif newobj_parent is not None:
            retval = self.confobj.insert(self.linenum + 1, newobj)
            if auto_commit is True:
                self.confobj.ccp_ref.commit()
            return retval
        else:
            error = f"Cannot find parent for {newobj} under this instance: {self}"
            logger.error(error)
            raise ValueError(error)

    # On BaseCfgLine()
    @logger.catch(reraise=True)
    def classify_family_indent(self, insertstr: str = None) -> int:
        """Look at the indent level of insertstr and return an integer for the auto_indent_width of insertstr relative to this object and auto_indent_width.

        - If insertstr is indented at the same level, return 0.
        - If insertstr is indented more, return a positive integer for how many ``auto_indent_width`` indents.
        - If insertstr is indented less, return a negative integer for how many ``auto_indent_width`` indents.
        - If insertstr is not indented on an integer multiple of ``auto_indent_width``, raise NotImplementedError.

        :return: An integer for the ``auto_indent_width`` of ``insertstr`` relative to this object and ``auto_indent_width``.
        :rtype: int
        """
        if not isinstance(insertstr, str):
            error = f"Received `insertstr` {type(insertstr)}, but expected a string"
            logger.critical(error)
            raise InvalidParameters(error)

        auto_indent_width = self.confobj.ccp_ref.auto_indent_width
        if not isinstance(auto_indent_width, int):
            error = f"CiscoConfParse().auto_indent_width must be an integer, but found {type(auto_indent_width)}"
            logger.critical(error)
            raise NotImplementedError(error)

        # Raise an error if the indent is not an even multiple of
        # auto_indent_width
        indent_width = len(insertstr) - len(insertstr.lstrip())
        indent_modulo = indent_width % auto_indent_width
        # Match on up to three decimal places...
        if not math.isclose(indent_modulo, 0.000, rel_tol=0, abs_tol=1e-3):
            error = f"`insertstr` is not an even multiple of `CiscoConfParse().auto_indent_width={auto_indent_width}`"
            logger.critical(error)
            raise NotImplementedError(error)

        if self.indent == indent_width:
            return 0
        elif self.indent < indent_width:
            this_val = indent_width / self.confobj.ccp_ref.auto_indent_width
            self_val = self.indent / self.confobj.ccp_ref.auto_indent_width
            return int(this_val - self_val)
        elif self.indent > indent_width:
            this_val = indent_width / self.confobj.ccp_ref.auto_indent_width
            self_val = self.indent / self.confobj.ccp_ref.auto_indent_width
            return int(this_val - self_val)
        else:
            error = "unexpected condition"
            logger.critical(error)
            raise NotImplementedError(error)

    # On BaseCfgLine()
    def replace(self, before, after, count=-1) -> str:
        """String replace ``before`` with ``after``

        If the optional argument count is given, only the first count occurrences are replaced.

        .. note::

           The original ``text`` in this object will be unmodified.

        :return: The replaced config string
        :rtype: str
        """
        return self._text.replace(before, after, count)

    # On BaseCfgLine()
    @logger.catch(reraise=True)
    def rstrip(self, chars: str = None) -> str:
        """Implement rstrip() on the BaseCfgLine().text

        .. note::

           The original ``text`` in this object will be unmodified.

        :return: The stripped ``text``
        :rtype: str
        """
        if chars is None:
            return self._text.rstrip()
        else:
            return self._text.rstrip(chars=chars)

    # On BaseCfgLine()
    @logger.catch(reraise=True)
    def lstrip(self, chars: str = None) -> str:
        """Implement lstrip() on the BaseCfgLine().text

        .. note::

           The original ``text`` in this object will be unmodified.

        :return: The stripped ``text``
        :rtype: str
        """
        if chars is None:
            return self._text.lstrip()
        else:
            return self._text.lstrip(chars=chars)

    # On BaseCfgLine()
    @logger.catch(reraise=True)
    def strip(self, chars: str = None) -> str:
        """Implement strip() on the BaseCfgLine().text

        .. note::

           The original ``text`` in this object will be unmodified.

        :return: The stripped ``text``
        :rtype: str
        """
        if chars is None:
            return self._text.strip()
        else:
            return self._text.strip(chars=chars)

    # On BaseCfgLine()
    @logger.catch(reraise=True)
    def split(self, sep: str = None, maxsplit: int = -1) -> list[str]:
        """
        Split ``text`` in-place

        .. note::

           The original ``text`` in this object will be unmodified.

        :param sep: Split text on the ``sep`` characters (by default, any whitespace)
        :type sep: str
        :param maxsplit: Maximum number of splits, default is -1 (no limit)
        :type maxsplit: int
        :return: A sequence of strings
        :rtype: List[str]
        """
        if sep is None:
            return self._text.split(maxsplit=maxsplit)
        else:
            return self._text.split(sep=sep, maxsplit=maxsplit)

    # On BaseCfgLine()
    @logger.catch(reraise=True)
    def get_regex_typed_dict(
        self,
        regex: re.Match = None,
        type_dict: dict = None,
        default: str = None,
        debug: bool = False,
    ) -> dict:
        r"""
        :return: Return a typed dict if ``regex`` is an re.Match() instance (with named match groups) and `type_dict` is a `dict` of types.  If a key in `type_dict` does not match, `default` is returned for that key.
        :rtype: dict

        These examples demonstrate how ``get_regex_typed_dict()`` works.

        .. code-block:: python

           >>> _uut_regex = r"^(?P<my_digit>[\d+])(?P<no_digit>[^\d+])"
           >>> _type_dict = {"my_digit", int, "no_digit": str}
           >>> _default = "_no_match"
           >>> get_regex_typed_dict(re.search(_uut_regex, "1a"), type_dict=_type_dict, default=_default)
           {'my_digit': 1, 'no_digit': 'a'}
           >>> get_regex_typed_dict(re.search(_uut_regex, "a1"), type_dict=_type_dict, default=_default)
           {'my_digit': '_no_match', 'no_digit': '_no_match'}
           >>> get_regex_typed_dict(re.search(_uut_regex, ""), type_dict=_type_dict, default=_default)
           {'my_digit': '_no_match', 'no_digit': '_no_match'}
           >>>
        """
        retval = {}
        if debug is True:
            logger.info(
                f"{self}.get_regex_typed_dict(`regex`={regex}, `type_dict`={type_dict}, `default`='{default}', debug={debug}) was called"
            )

        # If the `regex` is a string, compile so we can access match group info
        if isinstance(regex, str):
            regex = re.compile(regex)

        if isinstance(regex, re.Match) and isinstance(type_dict, dict):
            # If the `regex` matches, cast the results as the values
            # in `type_dict`...
            _groupdict = regex.groupdict()
            for _regex_key, _type in type_dict.items():
                retval[_regex_key] = _groupdict.get(_regex_key, default)
                if _type is not None and retval[_regex_key] != default:
                    retval[_regex_key] = _type(retval[_regex_key])
        elif regex is None and isinstance(type_dict, dict):
            # If the regex did not match, None is returned... and we should
            # assign the default to the regex key...
            for _regex_key in type_dict.keys():
                retval[_regex_key] = default
        else:
            error = f"`regex` must be the result of a regex match, and `type_dict` must be a dict of types; however we received `regex`: {type(regex)} and `type_dict`: {type(type_dict)}."
            logger.critical(error)
            raise InvalidTypecast(error)
        return retval

    # On BaseCfgLine()
    def replace_text(self, before, after, count=-1) -> str:
        """String replace ``before`` with ``after``

        If the optional argument count is given, only the first count occurrences are replaced.

        This method is substantially faster than ``BaseCfgLine().re_sub()`` for a similar replace operation.

        .. note::

           This will replace the config tex string in-place.

        :return: The replaced config string
        :rtype: str
        """
        self.text = self._text.replace(before, after, count)
        if self.confobj and self.confobj.auto_commit is True:
            self.confobj.ccp_ref.commit()
        return self._text

    # On BaseCfgLine()
    def re_sub(self, regex, replacergx, re_flags=0):
        """Replace all strings matching ``linespec`` with ``replacestr`` in the :class:`~ciscoconfparse2.models_cisco.IOSCfgLine` object; however, if the :class:`~ciscoconfparse2.models_cisco.IOSCfgLine` text matches ``ignore_rgx``, then the text is *not* replaced.

        Parameters
        ----------

        regex : str
            A string or python regular expression, which should be matched.
        replacergx : str
            A string or python regular expression, which should replace the text matched by ``regex``.
        ignore_rgx : str
            A string or python regular expression; the replacement is skipped if :class:`~ciscoconfparse2.models_cisco.IOSCfgLine` text matches ``ignore_rgx``.  ``ignore_rgx`` defaults to None, which means no lines matching ``regex`` are skipped.

        Returns
        -------

        str
            The new text after replacement

        Examples
        --------

        This example illustrates how you can use :func:`~ciscoconfparse2.models_cisco.IOSCfgLine.re_sub` to replace ``Serial1`` with
        ``Serial0`` in a configuration...

        .. code-block:: python
           :emphasize-lines: 15

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
           >>> parse = CiscoConfParse(config)
           >>>
           >>> for obj in parse.find_objects('Serial'):
           ...     print("OLD {}".format(obj.text))
           ...     obj.re_sub(r'Serial1', r'Serial0')
           ...     print("  NEW {}".format(obj.text))
           OLD interface Serial1/0
             NEW interface Serial0/0
           OLD interface Serial1/1
             NEW interface Serial0/1
           >>>
        """
        if self.confobj is not None and self.confobj.search_safe is False:
            error = "The configuration has changed since the last commit; a config search is not safe."
            logger.critical(error)
            raise NotImplementedError(error)

        idx = None
        if isinstance(self.confobj, Sequence):
            # Find the index of this object...
            idx = self.confobj.data.index(self)

        text_before_replace = self._text

        text_after_replace = re.sub(regex, replacergx, self._text, flags=re_flags)
        self.text = text_after_replace

        if self.confobj and text_before_replace != text_after_replace:
            # Substitute the modified object back into
            # the UserList...
            self.confobj[idx] = self

        # Only auto_commit if there was a text change
        if text_before_replace != text_after_replace:
            if self.confobj and self.confobj.auto_commit is True:
                self.confobj.ccp_ref.commit()

        return text_after_replace

    # On BaseCfgLine()
    def re_match(self, regex, group=1, default=""):
        r"""Use ``regex`` to search the :class:`~ciscoconfparse2.models_cisco.IOSCfgLine` text and return the regular expression group, at the integer index.

        :param regex: A string or python regular expression, which should be
                      matched.  This regular expression should contain
                      parenthesis, which bound a match group.
        :type regex: str
        :param group: An integer which specifies the desired regex group to
                      be returned, defaults to 1.
        :type group: int
        :param default: The default value to be returned, if there is no
                        match.  By default an empty string is returned if
                        there is no match.
        :type default: str
        :return: The text matched by the regular expression group; if there
                 is no match, ``default`` is returned.
        :rtype: str

        This example illustrates how you can use
        :py:meth:`~ciscoconfparse2.models_cisco.BaseCfgLine.re_match` to store the mask of the
        interface which owns "1.1.1.5" in a variable called ``netmask``.

        .. code-block:: python
           :emphasize-lines: 14

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
           >>> parse = CiscoConfParse(config)
           >>>
           >>> for obj in parse.find_objects(r'ip\saddress'):
           ...     netmask = obj.re_match(r'1\.1\.1\.5\s(\S+)')
           >>>
           >>> print("The netmask is", netmask)
           The netmask is 255.255.255.252
           >>>
        """
        if self.confobj is not None and self.confobj.search_safe is False:
            error = "The configuration has changed since the last commit; a config search is not safe."
            logger.critical(error)
            raise NotImplementedError(error)

        mm = re.search(regex, self.text)
        if mm is not None:
            return mm.group(group)
        return default

    # On BaseCfgLine()
    def re_search(self, regex, default="", debug=0):
        """Search :class:`~ciscoconfparse2.models_cisco.IOSCfgLine` with ``regex``

        Parameters
        ----------

        regex : str
            A string or python regular expression, which should be matched.
        default : str
            A value which is returned if :func:`~ciscoconfparse2.ccp_abc.re_search()` doesn't find a match while looking for ``regex``.

        Returns
        -------

        str
            The :class:`~ciscoconfparse2.models_cisco.IOSCfgLine` text which matched.  If there is no match, ``default`` is returned.
        """
        if self.confobj is not None and self.confobj.search_safe is False:
            error = "The configuration has changed since the last commit; a config search is not safe."
            logger.critical(error)
            raise NotImplementedError(error)

        retval = default
        # Shortcut with a substring match, if possible...
        if isinstance(regex, str) and (regex in self.text):
            if debug > 0:
                logger.debug(f"'{regex}' is a substring of '{self.text}'")
            retval = self.text
        elif re.search(regex, self.text) is not None:
            ## TODO: use re.escape(regex) on all regex, instead of bare regex
            if debug > 0:
                logger.debug(f"re.search('{regex}', '{self.text}') matches")
            retval = self.text
        return retval

    # On BaseCfgLine()
    def re_search_children(self, regex, recurse=False):
        """Use ``regex`` to search the text contained in the children of
        this :class:`~ciscoconfparse2.models_cisco.IOSCfgLine`.

        Parameters
        ----------

        regex : str
            A string or python regular expression, which should be matched.
        recurse : bool
            Set True if you want to search all children (children, grand children, great grand children, etc...)

        Returns
        -------

        list
            A list of matching :class:`~ciscoconfparse2.models_cisco.IOSCfgLine` objects which matched.  If there is no match, an empty :py:func:`list` is returned.
        """
        if self.confobj is not None and self.confobj.search_safe is False:
            error = "The configuration has changed since the last commit; a config search is not safe."
            logger.critical(error)
            raise NotImplementedError(error)

        if recurse is False:
            return [cobj for cobj in self.children if cobj.re_search(regex)]
        else:
            return [cobj for cobj in self.all_children if cobj.re_search(regex)]

    # On BaseCfgLine()
    @logger.catch(reraise=True)
    def re_match_typed(
        self,
        regex: Union[str, re.Pattern],
        group: int = 1,
        result_type: type = str,
        default: Any = "",
        untyped_default: bool = False,
        groupdict: dict = None,
    ) -> Any:
        r"""Use ``regex`` to search the :class:`~ciscoconfparse2.models_cisco.IOSCfgLine` text
        and return the contents of the regular expression group, at the
        integer ``group`` index, cast as ``result_type``; if there is no match,
        ``default`` is returned.

        :param regex: A string or python compiled regular expression, which should be matched.  This regular expression should contain parenthesis, which are bound to a match group.
        :type regex: Union[str, re.Pattern]
        :param group: Specify the desired regex group to be returned.  ``group`` defaults to 1; this is only used if ``groupdict`` is None.
        :type group: int
        :param result_type: A type (typically one of: ``str``, ``int``, ``float``, or :class:`~ciscoconfparse2.ccp_util.IPv4Obj`).  Unless ``groupdict`` is specified, all returned values are cast as ``result_type``, which defaults to ``str``.
        :type result_type: Type
        :param default: The default value to be returned, if there is no match.
        :type default: Any
        :param untyped_default: Set True if you don't want the default value to be typed; this is only used if ``groupdict`` is None.
        :type untyped_default: bool
        :param groupdict: Set to a dict of types if you want to match on regex group names; ``groupdict`` overrides the ``group``, ``result_type`` and ``untyped_default`` arguments.
        :type groupdict: dict
        :return: The text matched by the regular expression group; if there is no match, ``default`` is returned.  All values are cast as ``result_type``, unless `untyped_default` is True.
        :rtype: Any

        This example illustrates how you can use
        :func:`~ciscoconfparse2.models_cisco.IOSCfgLine.re_match_typed` to build an
        association between an interface name, and its numerical slot value.
        The name will be cast as :py:func:`str`, and the slot will be cast as
        :py:func:`int`.

        .. code-block:: python
           :emphasize-lines: 15,16,17,18,19

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
           >>> parse = CiscoConfParse(config)
           >>>
           >>> slots = dict()
           >>> for obj in parse.find_objects(r'^interface'):
           ...     name = obj.re_match_typed(regex=r'^interface\s(\S+)',
           ...         default='UNKNOWN')
           ...     slot = obj.re_match_typed(regex=r'Serial(\d+)',
           ...         result_type=int,
           ...         default=-1)
           ...     print("Interface {0} is in slot {1}".format(name, slot))
           ...
           Interface Serial1/0 is in slot 1
           Interface Serial2/0 is in slot 2
           >>>
        """
        if self.confobj is not None and self.confobj.search_safe is False:
            error = "The configuration has changed since the last commit; a config search is not safe."
            logger.critical(error)
            raise NotImplementedError(error)

        if groupdict is not None:
            raise NotImplementedError("groupdict is not supported at this time")

        mm = re.search(regex, self.text)
        if mm is not None:
            if mm.group(group) is not None:
                return result_type(mm.group(group))
        if untyped_default:
            return default
        else:
            return result_type(default)

    # On BaseCfgLine()
    @logger.catch(reraise=True)
    def re_match_iter_typed(
        self,
        regex: Union[str, re.Pattern],
        group: int = 1,
        result_type: type = str,
        default: Any = "",
        untyped_default: bool = False,
        groupdict: dict = None,
        recurse: bool = True,
        debug: bool = False,
    ) -> Any:
        r"""Use ``regex`` to search the children of
        :class:`~ciscoconfparse2.models_cisco.IOSCfgLine` text and return the contents of
        the regular expression group, at the integer ``group`` index, cast as
        ``result_type``; if there is no match, ``default`` is returned.

        :param regex: A string or python compiled regular expression, which should be matched.  This regular expression should contain parenthesis, which are bound to a match group.
        :type regex: Union[str, re.Pattern]
        :param group: Specify the desired regex group to be returned.  ``group`` defaults to 1; this is only used if ``groupdict`` is None.
        :type group: int
        :param result_type: A type (typically one of: ``str``, ``int``, ``float``, or :class:`~ciscoconfparse2.ccp_util.IPv4Obj`).  Unless ``groupdict`` is specified, all returned values are cast as ``result_type``, which defaults to ``str``.
        :type result_type: Type
        :param default: The default value to be returned, if there is no match.
        :type default: Any
        :param recurse: Set True if you want to search all children (children, grand children, great grand children, etc...), default to True.
        :type recurse: bool
        :param untyped_default: Set True if you don't want the default value to be typed; this is only used if ``groupdict`` is None.
        :type untyped_default: bool
        :param groupdict: Set to a dict of types if you want to match on regex group names; ``groupdict`` overrides the ``group``, ``result_type`` and ``untyped_default`` arguments.
        :type groupdict: dict
        :param debug: Set True if you want to debug ``re_match_iter_typed()`` activity
        :type debug: bool
        :return: The text matched by the regular expression group; if there is no match, ``default`` is returned.  All values are cast as ``result_type``, unless `untyped_default` is True.
        :rtype: Any

        .. note::

           This loops through the children (in order) and returns when the regex hits its first match.

        This example illustrates how you can use
        :func:`~ciscoconfparse2.models_cisco.IOSCfgLine.re_match_iter_typed` to build an
        :func:`~ciscoconfparse2.ccp_util.IPv4Obj` address object for each interface.

        .. code-block:: python
           :emphasize-lines: 17

           >>> import re
           >>> from ciscoconfparse2 import CiscoConfParse
           >>> from ciscoconfparse2.ccp_util import IPv4Obj
           >>> config = [
           ...     '!',
           ...     'interface Serial1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     '!',
           ...     'interface Serial2/0',
           ...     ' ip address 1.1.1.5 255.255.255.252',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config)
           >>> obj = parse.find_objects(r"interface Serial1/0")[0]
           >>> obj.text
           interface Serial1/0
           >>> addr_obj = obj.re_match_iter_typed(r"ip\s+address\s+(\d.+)", result_type=IPv4Obj)
           >>> print(obj.text, addr_obj)
           interface Serial1/0 <IPv4Obj 1.1.1.1/30>
           >>>
        """
        if self.confobj is not None and self.confobj.search_safe is False:
            error = "The configuration has changed since the last commit; a config search is not safe."
            logger.critical(error)
            raise NotImplementedError(error)

        # iterate through children, and return the matching value
        #  (cast as result_type) from the first child.text that matches regex
        # if (default is True):
        # Not using self.re_match_iter_typed(default=True), because I want
        #   to be sure I build the correct API for match=False
        #
        # Ref IOSIntfLine.has_dtp for an example of how to code around
        #   this while I build the API
        #    raise NotImplementedError
        if debug is True:
            logger.info(
                f"{self}.re_match_iter_typed(`regex`={regex}, `group`={group}, `result_type`={result_type}, `recurse`={recurse}, `untyped_default`={untyped_default}, `default`='{default}', `groupdict`={groupdict}, `debug`={debug}) was called"
            )

        if groupdict is None:
            if debug is True:
                logger.debug(
                    f"    {self}.re_match_iter_typed() is checking with `groupdict`=None"
                )

            # Return the result if the parent line matches the regex...
            mm = re.search(regex, self.text)
            if isinstance(mm, re.Match):
                return result_type(mm.group(group))

            if recurse is False:
                for cobj in self.children:
                    if debug is True:
                        logger.debug(
                            f"    {self}.re_match_iter_typed() is checking match of r'''{regex}''' on -->{cobj}<--"
                        )
                    mm = re.search(regex, cobj.text)
                    if isinstance(mm, re.Match):
                        return result_type(mm.group(group))
                ## Ref Github issue #121
                if untyped_default is True:
                    return default
                else:
                    return result_type(default)
            else:
                for cobj in self.all_children:
                    if debug is True:
                        logger.debug(
                            f"    {self}.re_match_iter_typed() is checking match of r'''{regex}''' on -->{cobj}<--"
                        )
                    mm = re.search(regex, cobj.text)
                    if isinstance(mm, re.Match):
                        return result_type(mm.group(group))
                ## Ref Github issue #121
                if untyped_default is True:
                    return default
                else:
                    return result_type(default)
        elif isinstance(groupdict, dict) is True:
            if debug is True:
                logger.debug(
                    f"    {self}.re_match_iter_typed() is checking with `groupdict`={groupdict}"
                )

            # Return the result if the parent line matches the regex...
            mm = re.search(regex, self.text)
            if isinstance(mm, re.Match):
                return self.get_regex_typed_dict(
                    regex=mm,
                    type_dict=groupdict,
                    default=default,
                    debug=debug,
                )

            if recurse is False:
                for cobj in self.children:
                    mm = re.search(regex, cobj.text)
                    return self.get_regex_typed_dict(
                        regex=mm,
                        type_dict=groupdict,
                        default=default,
                        debug=debug,
                    )
                return self.get_regex_typed_dict(
                    regex=mm,
                    type_dict=groupdict,
                    default=default,
                    debug=debug,
                )
            else:
                for cobj in self.all_children:
                    mm = re.search(regex, cobj.text)
                    if isinstance(mm, re.Match):
                        return self.get_regex_typed_dict(
                            regex=mm,
                            type_dict=groupdict,
                            default=default,
                            debug=debug,
                        )
                return self.get_regex_typed_dict(
                    regex=mm,
                    type_dict=groupdict,
                    default=default,
                    debug=debug,
                )
        else:
            error = (
                f"`groupdict` must be None or a `dict`, but we got {type(groupdict)}."
            )
            logger.critical(error)
            raise ValueError(error)

    # On BaseCfgLine()
    @logger.catch(reraise=True)
    def re_list_iter_typed(
        self,
        regex: Union[str, re.Pattern],
        group: int = 1,
        result_type: type = str,
        groupdict: dict = None,
        recurse: bool = True,
        debug: bool = False,
    ) -> list[Any]:
        r"""Use ``regex`` to search the children of
        :class:`~ciscoconfparse2.models_cisco.IOSCfgLine` text and return a list of the contents of
        objects matching the regular expression group, at the integer ``group`` index, cast as
        ``result_type``; if there is no match, default to an empty list.

        :param regex: A string or python compiled regular expression, which should be matched.  This regular expression should contain parenthesis, which are bound to a match group.
        :type regex: Union[str, re.Pattern]
        :param group: Specify the desired regex group to be returned.  ``group`` defaults to 1; this is only used if ``groupdict`` is None.
        :type group: int
        :param result_type: A type (typically one of: ``str``, ``int``, ``float``, or :class:`~ciscoconfparse2.ccp_util.IPv4Obj`).  Unless ``groupdict`` is specified, all returned values are cast as ``result_type``, which defaults to ``str``.
        :type result_type: Type
        :param recurse: Set True if you want to search all children (children, grand children, great grand children, etc...), default to True.
        :type recurse: bool
        :param groupdict: Set to a dict of types if you want to match on regex group names; ``groupdict`` overrides the ``group``, ``result_type`` and ``untyped_default`` arguments.
        :type groupdict: dict
        :param debug: Set True if you want to debug ``re_list_iter_typed()`` activity
        :type debug: bool
        :return: The text matched by the regular expression group; if there is no match, ``default`` is returned.  All values are cast as ``result_type``, unless `untyped_default` is True.
        :rtype: Any

        .. note::

           This loops through the children (in order) and returns a list of all matched text

        This example illustrates how you can use
        :func:`~ciscoconfparse2.models_cisco.IOSCfgLine.re_list_iter_typed` to build a list of
        :func:`~ciscoconfparse2.ccp_util.IPv6Obj` address objects for each interface.

        .. code-block:: python
           :emphasize-lines: 17

           >>> import re
           >>> from ciscoconfparse2 import CiscoConfParse
           >>> from ciscoconfparse2.ccp_util import IPv6Obj
           >>> config = [
           ...     '!',
           ...     'interface Serial1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     ' ipv6 address dead:beef::11/64',
           ...     ' ipv6 address dead:beef::12/64',
           ...     '!',
           ...     'interface Serial2/0',
           ...     ' ip address 1.1.1.5 255.255.255.252',
           ...     ' ipv6 address dead:beef::21/64',
           ...     ' ipv6 address dead:beef::22/64',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config)
           >>> obj = parse.find_objects(r"interface Serial1/0")[0]
           >>> obj.text
           interface Serial1/0
           >>> addr_objs = obj.re_list_iter_typed(r"ipv6\s+address\s+(\S.+)", result_type=IPv6Obj)
           >>> print(obj.text, addr_objs)
           interface Serial1/0 [<IPv6Obj dead:beef::11/64>, <IPv6Obj dead:beef::12/64>]
           >>>
        """
        if self.confobj is not None and self.confobj.search_safe is False:
            error = "The configuration has changed since the last commit; a config search is not safe."
            logger.critical(error)
            raise NotImplementedError(error)

        # iterate through children, and return all matching values
        #  (cast as result_type) from all child.text that match regex
        # if (default is True):
        # Not using self.re_list_iter_typed(default=True), because I want
        #   to be sure I build the correct API for match=False
        #
        if debug is True:
            logger.info(
                f"{self}.re_list_iter_typed(`regex`={regex}, `group`={group}, `result_type`={result_type}, `recurse`={recurse}, `groupdict`={groupdict}, `debug`={debug}) was called"
            )

        if groupdict is None:
            return self.re_list_iter_typed_groupdict_none(
                regex=regex,
                group=group,
                result_type=result_type,
                groupdict=groupdict,
                recurse=recurse,
                debug=debug,
            )
        elif isinstance(groupdict, dict) is True:
            return self.re_list_iter_typed_groupdict_dict(
                regex=regex,
                group=group,
                result_type=result_type,
                groupdict=groupdict,
                recurse=recurse,
                debug=debug,
            )
        else:
            error = (
                f"`groupdict` must be None or a `dict`, but we got {type(groupdict)}."
            )
            logger.critical(error)
            raise ValueError(error)

    @logger.catch(reraise=True)
    def re_list_iter_typed_groupdict_none(
        self,
        regex: Union[str, re.Pattern],
        group: int = 1,
        result_type: type = str,
        groupdict: dict = None,
        recurse: bool = True,
        debug: bool = False,
    ):
        if debug is True:
            logger.debug(
                f"    {self}.re_list_iter_typed_groupdict_none() is checking with `groupdict`=None"
            )

        if groupdict is not None:
            raise NotImplementedError(
                "re_list_iter_typed_groupdict_none() must be called without groupdict argument"
            )

        retval = []

        # Append to return values if the parent line matches the regex...
        mm = re.search(regex, self.text)
        if isinstance(mm, re.Match):
            retval.append(result_type(mm.group(group)))

        if recurse is False:
            for cobj in self.children:
                if debug is True:
                    logger.debug(
                        f"    {self}.re_list_iter_typed() is checking match of r'''{regex}''' on -->{cobj}<--"
                    )
                mm = re.search(regex, cobj.text)
                if isinstance(mm, re.Match):
                    retval.append(result_type(mm.group(group)))
        else:
            for cobj in self.all_children:
                if debug is True:
                    logger.debug(
                        f"    {self}.re_list_iter_typed() is checking match of r'''{regex}''' on -->{cobj}<--"
                    )
                mm = re.search(regex, cobj.text)
                if isinstance(mm, re.Match):
                    retval.append(result_type(mm.group(group)))
        return retval

    @logger.catch(reraise=True)
    def re_list_iter_typed_groupdict_dict(
        self,
        regex: Union[str, re.Pattern],
        group: int = 1,
        result_type: type = str,
        groupdict: dict = None,
        recurse: bool = True,
        debug: bool = False,
    ):
        if debug is True:
            logger.debug(
                f"    {self}.re_list_iter_typed() is checking with `groupdict`={groupdict}"
            )

        if not isinstance(groupdict, dict):
            raise NotImplementedError(
                "re_list_iter_typed_groupdict_dict() must be called with a dict in groupdict"
            )

        retval = None

        # Return the result if the parent line matches the regex...
        mm = re.search(regex, self.text)
        if isinstance(mm, re.Match):
            tmp = self.get_regex_typed_dict(
                regex=mm,
                type_dict=groupdict,
                debug=debug,
            )
            retval.append(tmp)

        if recurse is False:
            for cobj in self.children:
                mm = re.search(regex, cobj.text)
                tmp = self.get_regex_typed_dict(
                    regex=mm,
                    type_dict=groupdict,
                    debug=debug,
                )
                retval.append(tmp)
            return retval

        else:
            for cobj in self.all_children:
                mm = re.search(regex, cobj.text)
                if isinstance(mm, re.Match):
                    tmp = self.get_regex_typed_dict(
                        regex=mm,
                        type_dict=groupdict,
                        debug=debug,
                    )
                    retval.append(tmp)
            return retval

    # On BaseCfgLine()
    @property
    def family_text(self):
        """Return a list with this the text of this object, and
        with all children in the direct line.
        """
        retval = [self.text]
        retval.extend([ii.text for ii in self.all_children])
        return retval

    # On BaseCfgLine()
    @property
    @logger.catch(reraise=True)
    def last_family_linenum(self) -> int:
        """
        :return: Iterate through the family and find the last linenumber
                 of the last family member.  Return this object's
                 linenumber if there are no siblings.
        :rtype: int

        If this family was parsed, return 3 (index of the last family member)

        .. parsed-literal::

           first (idx: 0)
            first-child (idx: 1)
             first-child-child (idx: 2)
           second (idx: 3)  <-- return this index number

        If this family was parsed, return 3 (index of the last family member)

        .. parsed-literal::

           first (idx: 0)
           second (idx: 1)
            second-child (idx: 2)
             second-child-child (idx: 3)  <-- return this index number
        """
        ######################################################################
        # Find the last 'sibling' object of this object
        ######################################################################
        last_sibling = None
        this_indent = self.classify_family_indent(self.text)
        for obj in self.confobj.data:
            if self.classify_family_indent(obj.text) == this_indent:
                last_sibling = obj

        ######################################################################
        # Find the last 'sibling' object of this object
        ######################################################################
        if last_sibling is not None:
            if len(last_sibling.all_children) > 0:
                return last_sibling.all_children[-1].linenum
            else:
                return last_sibling.linenum
        else:
            return self.linenum

    # On BaseCfgLine()
    @property
    def lineage(self):
        """Iterate through to the oldest ancestor of this object, and return
        a list of all ancestors / children in the direct line.  Cousins or
        aunts / uncles are *not* returned.

        .. note::

           All children of this object are returned.
        """
        retval = self.all_parents
        retval.append(self)
        if self.children:
            retval.extend(self.all_children)
        return sorted(retval)

    # On BaseCfgLine()
    @property
    def geneology(self):
        """Iterate through to the oldest ancestor of this object, and return
        a list of all ancestors' objects in the direct line as well as this
        obj.  Cousins or aunts / uncles are *not* returned.

        .. note::

           Children of this object are *not* returned.
        """
        retval = sorted(self.all_parents)
        retval.append(self)
        return retval

    # On BaseCfgLine()
    @property
    def geneology_text(self):
        """Iterate through to the oldest ancestor of this object, and return
        a list of all ancestors' .text field for all ancestors in the direct
        line as well as this obj.  Cousins or aunts / uncles are *not*
        returned.

        .. note::

           Children of this object are *not* returned.
        """
        retval = [ii.text for ii in self.geneology]
        return retval

    # On BaseCfgLine()
    @property
    def is_parent(self):
        """Return True if this BaseCfgLine() instance has children"""
        return bool(self.has_children)

    # On BaseCfgLine()
    @property
    def is_child(self):
        """Return True if this BaseCfgLine() instance is a child of something"""
        parent = getattr(self, "parent", None)
        return not bool(parent == self)

    # On BaseCfgLine()
    @property
    def siblings(self):
        """Return a list of siblings for this BaseCfgLine() instance"""
        indent = self.indent
        return [obj for obj in self.parent.children if (obj.indent == indent)]

    # On BaseCfgLine()
    @classmethod
    def is_object_for(cls, line=""):
        """A base method to allow subclassing with an is_object_for() classmethod"""
        return False
