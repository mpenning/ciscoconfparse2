from argparse import ArgumentParser, Namespace, FileType
from argparse import _SubParsersAction
from typing import List, Any, Optional
import shlex
import sys

from rich.console import Console as RichConsole
from loguru import logger
from typeguard import typechecked
import attrs

from ciscoconfparse2.ciscoconfparse2 import CiscoConfParse
from ciscoconfparse2.ciscoconfparse2 import Diff
from ciscoconfparse2.ccp_util import IPv4Obj, IPv6Obj

"""This file should not be used anywhere other than the hatch build system and pytest"""

@logger.catch(reraise=True)
def ccp_script_entry():
    """The ccp script entry point"""
    parser = ArgParser()
    args = parser.parse()

    CliApplication(args)


@attrs.define(repr=False)
class CliApplication:

    console: RichConsole
    subparser_name: str
    args: Namespace
    syntax: str
    output_format: str
    file_list: List[str]
    diff_method: str
    all_children: bool
    parse: CiscoConfParse
    ipgrep_file: Any
    subnet: str

    @logger.catch(reraise=True)
    @typechecked
    def __init__(self, args: Namespace):
        try:
            if isinstance(args.args, Namespace):
                pass
        except AttributeError:
            # If args.args doesn't exist, fake several of the
            # argparse.Namespace attributes for the diff command
            args.args = ""
            args.separator = ","
            args.output = "raw_text"

        self.diff_method = getattr(args, 'diff_method', "diff")
        self.all_children = getattr(args, 'all_children', False)
        self.syntax = getattr(args, 'syntax', "ios")
        self.output_format = getattr(args, 'output', "")
        self.file_list = getattr(args, 'file', [""])
        self.ipgrep_file = getattr(args, 'ipgrep_file', None)
        self.subnet = getattr(args, 'subnet', "0.0.0.0/32")

        # file_list will be None if ipgrep is called with STDIN
        if self.file_list is None:
            self.file_list = [""]

        self.console = RichConsole()
        self.args = args.args.split(args.separator)
        self.subparser_name = args.command

        if self.subparser_name != "ipgrep":
            self.print_command_header()

        for filename in self.file_list:

            # The default parse, empty configuration...
            self.parse = CiscoConfParse([""])

            # Conditionally print the file name header...
            if self.subparser_name != "diff" and self.subparser_name != "ipgrep":
                self.print_file_name_centered(filename)


            if self.subparser_name == "parent":
                self.parse = CiscoConfParse(
                            config=filename,
                            syntax=self.syntax,
                        )
                self.parent_command()

            elif self.subparser_name == "child":
                self.parse = CiscoConfParse(
                            config=filename,
                            syntax=self.syntax,
                        )
                self.child_command()

            elif self.subparser_name == "branch":
                self.parse = CiscoConfParse(
                            config=filename,
                            syntax=self.syntax,
                        )
                self.branch_command()

            elif self.subparser_name == "diff":
                # See the if clause, outdented one-level
                pass

            elif self.subparser_name == "ipgrep":

                # See the if clause, outdented one-level
                self.ipgrep_command(subnet = self.subnet,
                                    text = self.ipgrep_file.read())

            else:
                error = f"Unexpected subparser name: {self.subparser_name}"
                logger.critical(error)
                raise ValueError(error)

        if self.subparser_name == "diff":
            self.diff_command()

    @logger.catch(reraise=True)
    def parent_command(self) -> None:
        if self.output_format == "raw_text":
            for obj in self.parse.find_parent_objects(self.args):
                print(obj.text)
        else:
            error = f"--output {self.output_format} is not supported"
            logger.critical(error)
            raise NotImplementedError(error)

    @logger.catch(reraise=True)
    def child_command(self) -> None:
        if self.output_format == "raw_text":
            for obj in self.parse.find_child_objects(self.args):
                print(obj.text)
        else:
            error = f"--output {self.output_format} is not supported"
            logger.critical(error)
            raise NotImplementedError(error)

    @logger.catch(reraise=True)
    def branch_command(self) -> None:

        if self.output_format == "raw_text":

            if len(self.args) == 1:
                error = f"'ccp branch -o raw_text' requires at least two -a args.  Use 'ccp -o original' if calling with only one 'ccp branch -a' term"
                logger.critical(error)
                raise NotImplementedError(error)

            for branch in self.parse.find_object_branches(self.args):
                print([obj.text for obj in branch])

        elif self.output_format == "original":
            retval = set([])
            if len(self.args) == 1:
                # Special case for the CLI script... if there is
                # only one search term, find all children of it
                for ii in self.parse.find_parent_objects([self.args[0]]):
                    retval.add(ii)
                    for jj in ii.all_children:
                        retval.add(jj)

            elif len(self.args) > 1:
                # There are multiple search terms... limit results to the
                # matching arguments...
                for branch in self.parse.find_object_branches(self.args):
                    for obj in branch:
                        retval.add(obj)

            # Dump all results to stdout...
            for obj in sorted(retval):
                print(obj.text)

        else:
            error = f"--output {self.output_format} is not supported"
            logger.critical(error)
            raise NotImplementedError(error)

    @logger.catch(reraise=True)
    def diff_command(self) -> None:
        diff = Diff(
                   open(self.file_list[0]).read(),
                   open(self.file_list[1]).read()
               )

        if self.diff_method == "diff":

            for line in diff.get_diff():
                print(line)

        elif self.diff_method == "rollback":

            for line in diff.get_rollback():
                print(line)

        else:
            error = f"Unsupported diff method: {self.diff_method}"
            logger.critical(error)
            raise ValueError(error)

    @logger.catch(reraise=True)
    @typechecked
    def ipgrep_command(self,
                       subnet: str,
                       text: str,
                       version: int = 0,
                       resplit: Optional[str] = None) -> bool:
        """grep for a subnet in the text"""

        if not int(version) in set([0, 4, 6]):
            error = f"version: {version} must be one of: 0, 4, 6"
            logger.critical(error)
            raise ValueError(error)

        mode = -1
        if int(version) == 0:
            try:
                mode = 4
                _subnet = IPv4Obj(subnet)
            except:
                mode = 6
                _subnet = IPv6Obj(subnet)

            if mode == -1:
                error = f"subnet: {subnet} is not a valid IPv4 or IPv6 subnet"
                logger.critical(error)
                raise ValueError(error)

        elif int(version) == 4:
            mode = 4
            _subnet = IPv4Obj(subnet)

        elif int(version) == 6:
            mode = 6
            _subnet = IPv6Obj(subnet)

        else:
            error = f"version: {version} is not a valid version"
            logger.critical(error)
            raise ValueError(error)

        if mode == 4:
            retval = self.search_for_ipv4_addr(text = text,
                                               resplit = resplit,
                                               multiple_match = True)
            if retval == []:
                # retval == [] is a special case where the text
                # had an invalid ip address like 172.16.355555
                return False

            elif isinstance(retval, list):
                # Multiple IP address mode...
                found = False
                for addr in retval:
                    if addr in _subnet:
                        found = True
                        print(addr.ip)
                return found

            elif isinstance(retval, str):
                # First match IP address mode...
                if retval in _subnet:
                    print(retval.ip)
                    return True
                else:
                    return False

        elif mode == 6:
            retval = self.search_for_ipv6_addr(text = text,
                                               resplit = resplit,
                                               multiple_match = True)

            if retval == []:
                # retval == [] is a special case where the text
                # had an invalid ip address like 172.16.355555
                return False

            elif isinstance(retval, list):
                # Multiple IP address mode...
                found = False
                for addr in retval:
                    if addr in _subnet:
                        found = True
                        print(addr.ip)
                return found

            elif isinstance(retval, str):
                # First match IP address mode...
                if retval in _subnet:
                    print(retval.ip)
                    return True
                else:
                    return False

        else:
            error = f"mode: {mode} is invalid"
            logger.critical(error)
            raise ValueError(error)

    @logger.catch(reraise=True)
    @typechecked
    def search_for_ipv4_addr(self,
                             text: str,
                             resplit: Optional[str] = None,
                             multiple_match: bool = False):
        """grep for an IPv4 address in text, optionally splitting on a regex string in resplit"""
        retval = list()

        if resplit is None:
            # split on spaces
            words = text.split()
        else:
            words = re.split(resplit, text)

        for word in words:
            try:
                addr = IPv4Obj(word)
                retval.append(addr)
                if multiple_match is False:
                    return retval[0]
            except:
                pass

        return retval

    @logger.catch(reraise=True)
    @typechecked
    def search_for_ipv6_addr(self,
                             text: str,
                             resplit: Optional[str] = None,
                             multiple_match: bool = False):
        """grep for an IPv6 address in text, optionally splitting on a regex string in resplit"""
        retval = list()

        if resplit is None:
            # split on spaces
            words = text.split()
        else:
            words = re.split(resplit, text)

        for word in words:
            try:
                addr = IPv6Obj(word)
                retval.append(addr)
                if multiple_match is False:
                    return retval[0]
            except:
                pass

        return retval

    @logger.catch(reraise=True)
    def print_command_header(self) -> None:
        """Print the command header including what is searched and the search terms"""

        self.console.print(f"[green1]Syntax      [/green1]: [purple]{self.syntax}[/purple]")
        self.console.print(f"[green1]Returing    [/green1]: [purple]{self.subparser_name}[/purple] text")
        self.console.print(f"[green1]Ouput as    [/green1]: [purple]{self.output_format}[/purple]")

        if self.subparser_name != "diff":
            for idx, term in enumerate(self.args):
                if idx == 0:
                    self.console.print(f"  [green1]parent[/green1]: [turquoise2]{term}[/turquoise2]")
                else:
                    self.console.print(f"  [green1]child [/green1]: [red1]{term}[/red1]")

    @logger.catch(reraise=True)
    @typechecked
    def print_file_name_centered(self,
                                 filename: str) -> None:
        """Print the filename colored and centered"""

        _width = self.console.width
        prefix = "file:"
        _var_line = int((_width - len(prefix) - len(filename) - 3)/2.0) * "-"
        self.console.print(f"[green1]{_var_line}[/green1] file: [turquoise2]{filename}[/turquoise2] [green1]{_var_line}[/green1]")


@attrs.define(repr=False)
class ArgParser:
    """
    :param input_str: String list of arguments
    :type input_str: str
    """
    input_str: str = ""

    argv: List = None
    parser: ArgumentParser = None
    subparsers: _SubParsersAction = None

    @logger.catch(reraise=True)
    @typechecked
    def __init__(self, input_str: str = ""):
        if input_str == "":
            input_str = " ".join(sys.argv)

        self.input_str = input_str
        self.argv = [input_str]
        self.argv.extend(shlex.split(input_str))

        self.parser = None
        self.subparsers = None

        self.parser = ArgumentParser(
            prog="ccp",
            description="ciscoconfparse2 CLI script",
            add_help=True,
        )
        self.subparsers = self.parser.add_subparsers(
            help="commands",
            required=True,
            dest="command")

        self.build_command_parent()
        self.build_command_child()
        self.build_command_branch()
        self.build_command_diff()
        self.build_command_ipgrep()

    def __repr__(self) -> str:
        return f"""<ArgParser '{" ".join(self.argv)}'>"""

    @logger.catch(reraise=True)
    def parse(self) -> Namespace:
        return self.parser.parse_args()

    @logger.catch(reraise=True)
    def build_command_parent(self) -> None:
        """Build the parent command as a subparser"""
        parser = self.subparsers.add_parser(
            "parent",
            help="Find configuration parent text")

        parser_required = parser.add_argument_group("required")
        parser_required.add_argument(
            "-a", "--args",
            required=True,
            type=str,
            help="Find this text.")

        parser_required.add_argument(
            "file",
            nargs='+',
            type=str,
            help="Find text in this file glob.")

        parser_optional = parser.add_argument_group("optional")
        parser_optional.add_argument(
            "-s", "--syntax",
            required=False,
            choices=['ios', 'nxos', 'iosxr', 'asa', 'junos'],
            default='ios',
            help="Configuration file syntax, defaults to 'ios'")

        parser_optional.add_argument(
            "-S", "--separator",
            required=False,
            default=',',
            type=str,
            help="Parent field separator, defaults to a comma")

        parser_optional.add_argument(
            "-o", "--output",
            required=False,
            choices=['raw_text', 'json',],
            default='raw_text',
            type=str,
            help="Output format, defaults to raw_text")

        parser_optional.add_argument(
            "-A", "--all_children",
            required=False,
            action='store_true',
            default=False,
            help="Find all children")

    @logger.catch(reraise=True)
    def build_command_child(self) -> None:
        """Build the child command as a subparser"""
        parser = self.subparsers.add_parser(
            "child",
            help="Find configuration child text")

        parser_required = parser.add_argument_group("required")
        parser_required.add_argument(
            "-a", "--args",
            required=True,
            type=str,
            help="Find this text.")

        parser_required.add_argument(
            "file",
            nargs='+',
            type=str,
            help="Find text in this file glob.")

        parser_optional = parser.add_argument_group("optional")
        parser_optional.add_argument(
            "-s", "--syntax",
            required=False,
            choices=['ios', 'nxos', 'iosxr', 'asa', 'junos'],
            default='ios',
            help="Configuration file syntax, defaults to 'ios'")

        parser_optional.add_argument(
            "-S", "--separator",
            required=False,
            default=',',
            type=str,
            help="Child field separator, defaults to a comma")

        parser_optional.add_argument(
            "-o", "--output",
            required=False,
            choices=['raw_text', 'json',],
            default='raw_text',
            type=str,
            help="Output format, defaults to raw_text")

    @logger.catch(reraise=True)
    def build_command_branch(self) -> None:
        """Build the branch command as a subparser"""
        parser = self.subparsers.add_parser(
            "branch",
            help="Find configuration branch text")

        parser_required = parser.add_argument_group("required")
        parser_required.add_argument(
            "-a", "--args",
            required=True,
            type=str,
            help="Find this text.")

        parser_required.add_argument(
            "file",
            nargs='+',
            type=str,
            help="Find text in this file glob.")

        parser_optional = parser.add_argument_group("optional")
        parser_optional.add_argument(
            "-s", "--syntax",
            required=False,
            choices=['ios', 'nxos', 'iosxr', 'asa', 'junos'],
            default='ios',
            help="Configuration file syntax, defaults to 'ios'")

        parser_optional.add_argument(
            "-S", "--separator",
            required=False,
            default=',',
            type=str,
            help="Branch field separator, defaults to a comma")

        parser_optional.add_argument(
            "-o", "--output",
            required=False,
            choices=['raw_text', 'original', 'json',],
            default='raw_text',
            type=str,
            help="Output format, defaults to raw_text")

    @logger.catch(reraise=True)
    def build_command_diff(self) -> None:
        """Build the diff (of a config) command as a subparser"""
        parser = self.subparsers.add_parser(
            "diff",
            help="Show a diff")

        parser_required = parser.add_argument_group("required")
        parser_required.add_argument(
            "file",
            nargs=2,
            type=str,
            help="Diff text in these files.")

        parser_optional = parser.add_argument_group("optional")
        parser_optional.add_argument(
            "-m", "--method",
            required=False,
            choices=['diff', 'rollback', ],
            default='diff',
            type=str,
            help="Diff method, defaults to diff")

        parser_optional.add_argument(
            "-s", "--syntax",
            required=False,
            choices=['ios', 'nxos', 'iosxr', 'asa', 'junos'],
            default='ios',
            help="Configuration file syntax, defaults to 'ios'")

    @logger.catch(reraise=True)
    def build_command_ipgrep(self) -> None:
        """An IPv4 / IPv6 address in subnet grep command"""

        parser = self.subparsers.add_parser(
            "ipgrep",
            help="grep for an IPv4 / IPv6 addresses in a subnet")

        parser_required = parser.add_argument_group("required")

        # Accept either a file or STDIN
        # https://stackoverflow.com/a/11038508/667301
        parser_required.add_argument(
            "ipgrep_file",
            nargs = '?',
            type = FileType('r'),
            # Optionally handle stdin if no file is specified...
            # https://stackoverflow.com/a/61512890/667301
            default=(None if sys.stdin.isatty() else sys.stdin),
            help = "Grep for IPs in these files, defaults to STDIN.")

        parser_required.add_argument(
            "-s", "--subnet",
            type=str,
            help="Subnet address / mask")

if __name__ == "__main__":
    print(args)

