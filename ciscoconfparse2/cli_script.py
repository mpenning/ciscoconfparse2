from argparse import ArgumentParser, Namespace, FileType, Action
from argparse import _SubParsersAction
from typing import List, Any, Union, Optional
import shlex
import sys
import re

from rich.console import Console as RichConsole
from loguru import logger
from typeguard import typechecked
import attrs

from ciscoconfparse2.ciscoconfparse2 import CiscoConfParse
from ciscoconfparse2.ciscoconfparse2 import Diff
from ciscoconfparse2.ccp_util import IPv4Obj, IPv6Obj

"""This file should not be used anywhere other than the hatch build system and pytest"""

@logger.catch(reraise=True)
@typechecked
def ccp_script_entry(cli_args: str = ""):
    """The ccp script entry point.  CLI args MUST include the actual ccp command"""

    if cli_args[0:9] == 'ccp_faked':
        # Return retval only for pytest calls...
        return_retval = True

        # The first element of sys.argv is a string list of arguments
        sys.argv = [' '.join(cli_args.split()[1:])] # sys.argv[0] is always
                                                    # the whole list of CLI args
                                                    # (minus the actual ccp
                                                    # command)

        # Strip off 'ccp_faked' and add the rest of CLI arguments
        sys.argv.extend(shlex.split(cli_args)[1:])  # shlex adds the rest of argv
                                                    # one element per argument.
        # The ccp_fake test cases fall through here...
        parser = ArgParser()
    else:
        # Return retval only for pytest calls...
        return_retval = False

        # handle the normal ccp CLI application
        parser = ArgParser()

    args = parser.parse()

    # Run the application...
    cliapp = CliApplication(parser, args)

    if return_retval:
        # Only return the retval during unit tests...
        return cliapp
    else:
        return None

@attrs.define(repr=False)
class ArgParser:
    """
    :param input_str: String list of arguments
    :type input_str: str
    """
    input_str: str
    argv: List
    parser: ArgumentParser
    subparsers: _SubParsersAction

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
            help="-a Parent field separator, defaults to a comma")

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
            help="grep for IPv4 / IPv6 addresses contained in an IP subnet")

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
            "-s", "--subnets",
            type=str,
            action=OnlyOneArgument,
            help="Comma-separated IPv4 and/or IPv6 addresses or prefixes, such as '192.0.2.1,2001:db8::/32'.  If the mask is not specified, a host-mask assumed.")

        parser_optional = parser.add_argument_group("optional")

        parser_optional.add_argument(
            "-w", "--word_delimiter",
            default=r"\s+",
            help="Word delimiter regular expression, defaults to all whitespace.  Join multiple regex delimiters with a pipe character")

        parser_optional_exclusive = parser_optional.add_mutually_exclusive_group()

        parser_optional_exclusive.add_argument(
            "-l", "--line",
            action='store_true',
            default=False,
            help="Enable line mode (return lines instead of only returning the IP)")

        parser_optional_exclusive.add_argument(
            "-u", "--unique",
            action='store_true',
            default=False,
            help="Only print unique IPs (remove duplicates)")

@attrs.define(repr=False)
class CliApplication:

    arg_parser: ArgParser
    console: RichConsole
    subparser_name: str
    args: Namespace
    stdout: List[str]

    syntax: str
    output_format: str
    file_list: List[str]
    diff_method: str
    all_children: bool
    unique: bool
    line: bool
    word_delimiter: str
    ipgrep_file: Any
    subnets: str
    parse: CiscoConfParse

    @logger.catch(reraise=True)
    @typechecked
    def __init__(self, arg_parser, args: Namespace):
        try:
            args.args
        except AttributeError:
            # If args.args doesn't exist, fake several of the
            # argparse.Namespace attributes for the diff command
            args.args = ""
            args.separator = ","
            args.output = "raw_text"

        self.arg_parser = arg_parser
        self.console = RichConsole()
        self.subparser_name = args.command
        self.args = args.args.split(args.separator)

        # stdout is a list of output lines we will print to stdout...
        self.stdout = []

        # Provide default values for args when the ArgumentParser config
        # could not do it upon initialization... such as the arg is not
        # valid for the specific CliApplication()
        self.syntax = getattr(args, 'syntax', "ios")
        self.output_format = getattr(args, 'output', "")
        self.file_list = getattr(args, 'file', [""])
        self.diff_method = getattr(args, 'diff_method', "diff")
        self.all_children = getattr(args, 'all_children', False)
        self.unique = getattr(args, 'unique', False)
        self.ipgrep_file = getattr(args, 'ipgrep_file', None)
        self.subnets = getattr(args, 'subnets', "0.0.0.0/32,::0/0")
        self.line = getattr(args, 'line', False)
        self.word_delimiter = getattr(args, 'word_delimiter', r"\s+")

        # file_list will be None when using ipgrep...
        if self.file_list is None:
            self.file_list = [""]

        if self.subparser_name != "ipgrep":
            self.print_command_header()

        for filename in self.file_list:

            # The default parse, empty configuration...
            self.parse = CiscoConfParse([""])

            # Conditionally print the file name header...
            if self.subparser_name != "diff" and self.subparser_name != "ipgrep":
                self.print_file_name_centered(filename)


            if self.subparser_name == "parent":
                self.parse = CiscoConfParse(config=filename,
                                            syntax=self.syntax,)
                self.parent_command()

            elif self.subparser_name == "child":
                self.parse = CiscoConfParse(config=filename,
                                            syntax=self.syntax,)
                self.child_command()

            elif self.subparser_name == "branch":
                self.parse = CiscoConfParse(config=filename,
                                            syntax=self.syntax,)
                self.branch_command()

            elif self.subparser_name == "diff":
                # See the if clause below, outdented one-level
                pass

            elif self.subparser_name == "ipgrep":

                if self.ipgrep_file is None:
                    error = "The ipgrep_file argument is required"
                    self.arg_parser.parser.error(error)

                # See the if clause, outdented one-level
                self.ipgrep_command(subnets = self.subnets,
                                    text = self.ipgrep_file.read())

            else:
                error = f"Unexpected subparser name: {self.subparser_name}"
                logger.critical(error)
                raise ValueError(error)

        if self.subparser_name == "diff":
            self.diff_command()

        self.print_all_stdout()

    @logger.catch(reraise=True)
    def print_all_stdout(self):
        for line in self.stdout:
            print(line)

    @logger.catch(reraise=True)
    def parent_command(self) -> None:
        if self.output_format == "raw_text":
            for obj in self.parse.find_parent_objects(self.args):
                self.stdout.append(obj.text)
        else:
            error = f"--output {self.output_format} is not supported"
            logger.critical(error)
            raise NotImplementedError(error)

    @logger.catch(reraise=True)
    def child_command(self) -> None:
        if self.output_format == "raw_text":
            for obj in self.parse.find_child_objects(self.args):
                self.stdout.append(obj.text)
        else:
            error = f"--output {self.output_format} is not supported"
            logger.critical(error)
            raise NotImplementedError(error)

    @logger.catch(reraise=True)
    def branch_command(self) -> None:

        if self.output_format == "raw_text":

            if len(self.args) == 1:
                error = "'ccp branch -o raw_text' requires at least two -a args.  Use 'ccp -o original' if calling with only one 'ccp branch -a' term"
                logger.critical(error)
                raise NotImplementedError(error)

            for branch in self.parse.find_object_branches(self.args):
                self.stdout.extend([obj.text for obj in branch])

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
                self.stdout.append(obj.text)

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
                self.stdout.append(line)

        elif self.diff_method == "rollback":

            for line in diff.get_rollback():
                self.stdout.append(line)

        else:
            error = f"Unsupported diff method: {self.diff_method}"
            logger.critical(error)
            raise ValueError(error)

    @logger.catch(reraise=True)
    @typechecked
    def ipgrep_command(self,
                       subnets: Union[str, None],
                       text: str,) -> bool:
        """grep for a subnet in the text"""

        # Throw an error if ccp ipgrep -s is missing
        if subnets is None:
            error = "The -s argument is required"
            self.arg_parser.parser.error(error)

        retval = []

        _subnets = set([])

        for subnet in subnets.split(","):
            mode = -1
            try:
                _subnet = IPv4Obj(subnet)
                mode = 4
            except Exception:
                pass

            try:
                _subnet = IPv6Obj(subnet)
                mode = 6
            except Exception as eee:
                pass
                

            if mode == -1:
                error = f"subnet: {subnet} is not a valid IPv4 or IPv6 subnet"
                logger.critical(error)
                raise ValueError(error)
            else:
                _subnets.add(_subnet)

        if not self.line:
            words = re.split(self.word_delimiter, text)
            retval = self.find_ip46_addr_matches(_subnets,
                                                 potential_matches = words,
                                                 unique_matches = self.unique)
        else:
            lines = text.splitlines()
            retval = self.find_ip46_line_matches(subnets = _subnets,
                                                 potential_matches = lines,
                                                 unique_matches = self.unique)
        if retval == []:
            # potential_matches == [] is a special case where the text
            # had an invalid ip address like 172.16.355555
            return False

        elif isinstance(retval, list):
            # Multiple IP address mode...
            for match in retval:
                self.stdout.append(match)

            return True

        else:
            error = f"mode: {mode} is invalid"
            logger.critical(error)
            raise ValueError(error)

    @logger.catch(reraise=True)
    @typechecked
    def find_ip46_addr_matches(self,
                               subnets: set[Union[IPv4Obj, IPv6Obj]],
                               potential_matches: List[str],
                               unique_matches: bool) -> List:
        """Walk the IPv4 / IPv6 instances in potential_matches, return the list of addrs matching subnet"""
        found = False
        retval = []

        for tmp in potential_matches:
            for subnet in subnets:
                try:
                    if subnet.version == 4:
                        addr = IPv4Obj(tmp)
                    else:
                        addr = IPv6Obj(tmp)
                except Exception:
                    # We didn't get a proper address... bail on this iteration
                    continue
                if (addr.version == subnet.version) and (addr in subnet):
                    found = True
                    if unique_matches:
                        # Append if not already in retval...
                        if str(addr.ip) not in retval:
                            retval.append(str(addr.ip))
                    else:
                        # Append unconditionally
                        retval.append(str(addr.ip))
        return retval

    @logger.catch(reraise=True)
    @typechecked
    def find_ip46_line_matches(self,
                               subnets: set[Union[IPv4Obj, IPv6Obj]],
                               potential_matches: List[str],
                               unique_matches: bool) -> List:
        """Walk the IPv4 / IPv6 instances in potential_matches, return the list of lines with a word matching subnet"""
        found = False
        retval = []

        for line in potential_matches:
            line_appended = False
            # Split words on whitespace...
            words = re.split(self.word_delimiter, line)
            for word in words:
                for subnet in subnets:
                    try:
                        if subnet.version == 4:
                            addr = IPv4Obj(word)
                        else:
                            addr = IPv6Obj(word)
                    except Exception:
                        # We didn't get a proper address... bail on this iteration
                        continue

                    if (addr.version == subnet.version) and (addr in subnet):
                        found = True
                        # append the line with the matching text.  This appends on
                        # the first match and breaks out of the loop
                        if not line_appended:
                            retval.append(line)
                            line_appended = True
                            break
        return retval

    @logger.catch(reraise=True)
    def print_command_header(self) -> None:
        """Print the command header including what is searched and the search terms"""

        self.console.print(f"[green1]Syntax      [/green1]: [purple]{self.syntax}[/purple]")
        self.console.print(f"[green1]Returing    [/green1]: [purple]{self.subparser_name}[/purple] text")
        self.console.print(f"[green1]Output as   [/green1]: [purple]{self.output_format}[/purple]")

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

class OnlyOneArgument(Action):
    """A custom argparse action to only allow one instance of a CLI flag argument"""
    def __call__(self, parser, namespace, values, option_string):
        if getattr(namespace, self.dest, self.default) is not self.default:
            parser.error(option_string + " must not appear multiple times.")
        setattr(namespace, self.dest, values)

