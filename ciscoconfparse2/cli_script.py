"""This file should not be used anywhere other than the hatch build system and pytest"""

import re
import shlex
import sys
from argparse import Action, ArgumentParser, FileType, Namespace, _SubParsersAction
from typing import Any, List, Set, Union

import attrs
import macaddress
from loguru import logger
from rich.console import Console as RichConsole
from typeguard import typechecked

from ciscoconfparse2.ccp_util import EUI64Obj, IPv4Obj, IPv6Obj, MACObj
from ciscoconfparse2.ciscoconfparse2 import CiscoConfParse, Diff


@logger.catch(reraise=True)
@typechecked
def ccp_script_entry(cli_args: str = ""):
    """The ccp script entry point.  CLI args MUST include the actual ccp command"""

    if cli_args[0:9] == "ccp_faked":
        # Return retval only for pytest calls...
        return_retval = True

        # The first element of sys.argv is a string list of arguments
        sys.argv = [" ".join(cli_args.split()[1:])]  # sys.argv[0] is always
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
    argv: list
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
            help="commands", required=True, dest="command"
        )

        self.build_command_args_parent()
        self.build_command_args_child()
        self.build_command_args_branch()
        self.build_command_args_diff()
        self.build_command_args_ipgrep()
        self.build_command_args_macgrep()

    def __repr__(self) -> str:
        return f"""<ArgParser '{" ".join(self.argv)}'>"""

    @logger.catch(reraise=True)
    def parse(self) -> Namespace:
        """Return an argparse Namespace instance for the CLI arguments"""
        return self.parser.parse_args()

    @logger.catch(reraise=True)
    def build_command_args_parent(self) -> None:
        """Build the parent command as a subparser"""
        parser = self.subparsers.add_parser(
            "parent", help="Find configuration parent text"
        )

        parser_required = parser.add_argument_group("required")
        parser_required.add_argument(
            "-a", "--args", required=True, type=str, help="Find this text."
        )

        parser_required.add_argument(
            "file", nargs="+", type=str, help="Find text in this file glob."
        )

        parser_optional = parser.add_argument_group("optional")
        parser_optional.add_argument(
            "-s",
            "--syntax",
            required=False,
            choices=["ios", "nxos", "iosxr", "asa", "junos"],
            default="ios",
            help="Configuration file syntax, defaults to 'ios'",
        )

        parser_optional.add_argument(
            "-d",
            "--delimiter",
            required=False,
            default=",",
            type=str,
            help="-a Parent field delimiter, defaults to a comma",
        )

        parser_optional.add_argument(
            "-o",
            "--output",
            required=False,
            choices=[
                "raw_text",
                "json",
            ],
            default="raw_text",
            type=str,
            help="Output format, defaults to raw_text",
        )

        parser_optional.add_argument(
            "-A",
            "--all_children",
            required=False,
            action="store_true",
            default=False,
            help="Find all children",
        )

    @logger.catch(reraise=True)
    def build_command_args_child(self) -> None:
        """Build the child command as a subparser"""
        parser = self.subparsers.add_parser(
            "child", help="Find configuration child text"
        )

        parser_required = parser.add_argument_group("required")
        parser_required.add_argument(
            "-a", "--args", required=True, type=str, help="Find this text."
        )

        parser_required.add_argument(
            "file", nargs="+", type=str, help="Find text in this file glob."
        )

        parser_optional = parser.add_argument_group("optional")
        parser_optional.add_argument(
            "-s",
            "--syntax",
            required=False,
            choices=["ios", "nxos", "iosxr", "asa", "junos"],
            default="ios",
            help="Configuration file syntax, defaults to 'ios'",
        )

        parser_optional.add_argument(
            "-d",
            "--delimiter",
            required=False,
            default=",",
            type=str,
            help="Child field delimiter, defaults to a comma",
        )

        parser_optional.add_argument(
            "-o",
            "--output",
            required=False,
            choices=[
                "raw_text",
                "json",
            ],
            default="raw_text",
            type=str,
            help="Output format, defaults to raw_text",
        )

    @logger.catch(reraise=True)
    def build_command_args_branch(self) -> None:
        """Build the branch command as a subparser"""
        parser = self.subparsers.add_parser(
            "branch", help="Find configuration branch text"
        )

        parser_required = parser.add_argument_group("required")
        parser_required.add_argument(
            "-a", "--args", required=True, type=str, help="Find this text."
        )

        parser_required.add_argument(
            "file", nargs="+", type=str, help="Find text in this file glob."
        )

        parser_optional = parser.add_argument_group("optional")
        parser_optional.add_argument(
            "-s",
            "--syntax",
            required=False,
            choices=["ios", "nxos", "iosxr", "asa", "junos"],
            default="ios",
            help="Configuration file syntax, defaults to 'ios'",
        )

        parser_optional.add_argument(
            "-d",
            "--delimiter",
            required=False,
            default=",",
            type=str,
            help="Branch field delimiter, defaults to a comma",
        )

        parser_optional.add_argument(
            "-o",
            "--output",
            required=False,
            choices=[
                "raw_text",
                "original",
                "json",
            ],
            default="raw_text",
            type=str,
            help="Output format, defaults to raw_text",
        )

    @logger.catch(reraise=True)
    def build_command_args_diff(self) -> None:
        """Build the diff (of a config) command as a subparser"""
        parser = self.subparsers.add_parser("diff", help="Show a Cisco IOS-style diff")

        parser_required = parser.add_argument_group("required")
        parser_required.add_argument(
            "file", nargs=2, type=str, help="Diff text in these files."
        )

        parser_optional = parser.add_argument_group("optional")
        parser_optional.add_argument(
            "-m",
            "--method",
            required=False,
            choices=[
                "diff",
                "rollback",
            ],
            default="diff",
            type=str,
            help="Diff method, defaults to diff",
        )

        parser_optional.add_argument(
            "-s",
            "--syntax",
            required=False,
            choices=["ios", "nxos", "iosxr", "asa", "junos"],
            default="ios",
            help="Configuration file syntax, defaults to 'ios'",
        )

    @logger.catch(reraise=True)
    def build_command_args_ipgrep(self) -> None:
        """An IPv4 / IPv6 address in subnet grep command"""

        parser = self.subparsers.add_parser(
            "ipgrep", help="grep for IPv4 / IPv6 addresses contained in an IP subnet"
        )

        parser.add_argument_group("required")

        # Accept either a file or STDIN
        # https://stackoverflow.com/a/11038508/667301
        parser.add_argument(
            "ipgrep_file",
            nargs="?",
            type=FileType("r"),
            # Optionally handle stdin if no file is specified...
            # https://stackoverflow.com/a/61512890/667301
            default=(None if sys.stdin.isatty() else sys.stdin),
            help="Grep for IPs in these files, defaults to STDIN.",
        )

        parser_optional = parser.add_argument_group("optional")

        parser_optional.add_argument(
            "-s",
            "--subnets",
            type=str,
            action=OnlyOneArgument,
            default=None,
            help="Comma-separated IPv4 and/or IPv6 addresses or prefixes, such as '192.0.2.1,2001:db8::/32'.  If the mask is not specified, a host-mask assumed.",
        )

        parser_optional.add_argument(
            "-4",
            "--ipv4",
            default=False,
            action="store_true",
            help="Find all IPv4 addresses (cannot use with the --subnet argument)",
        )

        parser_optional.add_argument(
            "-6",
            "--ipv6",
            default=False,
            action="store_true",
            help="Find all IPv6 addresses (cannot use with the --subnet argument)",
        )

        parser_optional.add_argument(
            "-w",
            "--word_delimiter",
            default=r"\s+",
            help="Word delimiter regular expression, defaults to all whitespace.  Join multiple regex delimiters with a pipe character",
        )

        parser_optional.add_argument(
            "-c",
            "--show-cidr",
            default=False,
            action="store_true",
            help="Print the network / host mask in CIDR notation",
        )

        parser_optional.add_argument(
            "-n",
            "--show-networks",
            default=False,
            action="store_true",
            help="Only print the network portion of subnets instead of IP hosts (implies --show-cidr).  Hosts (i.e. IPv4 /32 and IPv6 /128 networks) are also included by default.",
        )

        parser_optional.add_argument(
            "-H",
            "--exclude-hosts",
            default=False,
            action="store_true",
            help="Exclude all hosts from output (should be used with --show-networks).",
        )

        parser_optional_exclusive = parser_optional.add_mutually_exclusive_group()

        parser_optional_exclusive.add_argument(
            "-l",
            "--line",
            action="store_true",
            default=False,
            help="Enable line mode (return lines instead of only returning the IP)",
        )

        parser_optional_exclusive.add_argument(
            "-u",
            "--unique",
            action="store_true",
            default=False,
            help="Only print unique IPs (remove duplicates).  Not used in --line mode.",
        )

    @logger.catch(reraise=True)
    def build_command_args_macgrep(self) -> None:
        """A mac address / EUI address grep command"""

        parser = self.subparsers.add_parser(
            "macgrep", help="grep for MAC / EUI addresses, optionally matching a regex"
        )

        parser_required = parser.add_argument_group("required")

        # Accept either a file or STDIN
        # https://stackoverflow.com/a/11038508/667301
        parser_required.add_argument(
            "macgrep_file",
            nargs="?",
            type=FileType("r"),
            # Optionally handle stdin if no file is specified...
            # https://stackoverflow.com/a/61512890/667301
            default=(None if sys.stdin.isatty() else sys.stdin),
            help="Grep for macs in these files, defaults to STDIN.",
        )

        parser_optional = parser.add_argument_group("optional")

        parser_optional.add_argument(
            "-r",
            "--regex",
            type=str,
            action=OnlyOneArgument,
            default=".",
            help="Comma-separated mac / EUI64 address regex, such as '^dead.beef', defaults to '.'.  Regular expressions match any valid format (i.e. dashes, commas, or periods in the address).",
        )

        parser_optional.add_argument(
            "-w",
            "--word_delimiter",
            default=r"\s+",
            help="Word delimiter regular expression, defaults to all whitespace.  Join multiple regex delimiters with a pipe character",
        )

        parser_optional_exclusive = parser_optional.add_mutually_exclusive_group()

        parser_optional_exclusive.add_argument(
            "-l",
            "--line",
            action="store_true",
            default=False,
            help="Enable line mode (return lines instead of only returning the IP)",
        )

        parser_optional_exclusive.add_argument(
            "-u",
            "--unique",
            action="store_true",
            default=False,
            help="Only print unique Macs (remove duplicates).  Not used in --line mode",
        )


@attrs.define(repr=False)
class CliApplication:
    """A class to represent this ciscoconfparse2 cli application"""

    arg_parser: ArgParser
    console: RichConsole
    subparser_name: str
    args: Namespace
    stdout: list[str]

    syntax: str
    output_format: str
    file_list: list[str]
    diff_method: str
    all_children: bool
    unique: bool
    line: bool
    word_delimiter: str
    ipgrep_file: Any
    macgrep_file: Any
    subnets: str
    ipv4: bool
    ipv6: bool
    show_cidr: bool
    show_networks: bool
    exclude_hosts: bool
    exclude_networks: bool
    mac_regex: str
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
            args.delimiter = ","
            args.output = "raw_text"

        self.arg_parser = arg_parser
        self.console = RichConsole()
        self.subparser_name = args.command
        self.args = args.args.split(args.delimiter)

        # stdout is a list of output lines we will print to stdout...
        self.stdout = []

        # Provide default values for args when the ArgumentParser config
        # could not do it upon initialization... such as the arg is not
        # valid for the specific CliApplication()
        self.syntax = getattr(args, "syntax", "ios")
        self.output_format = getattr(args, "output", "")
        self.file_list = getattr(args, "file", [""])
        self.diff_method = getattr(args, "diff_method", "diff")
        self.all_children = getattr(args, "all_children", False)
        self.unique = getattr(args, "unique", False)
        self.ipgrep_file = getattr(args, "ipgrep_file", None)
        self.macgrep_file = getattr(args, "macgrep_file", None)
        self.subnets = getattr(args, "subnets", "")
        self.ipv4 = getattr(args, "ipv4", False)
        self.ipv6 = getattr(args, "ipv6", False)
        self.show_cidr = getattr(args, "show_cidr", False)
        self.show_networks = getattr(args, "show_networks", False)
        self.exclude_hosts = getattr(args, "exclude_hosts", False)
        self.exclude_networks = getattr(args, "exclude_networks", False)
        self.mac_regex = getattr(args, "regex", ".")
        self.line = getattr(args, "line", False)
        self.word_delimiter = getattr(args, "word_delimiter", r"\s+")

        if self.show_networks:
            # --show-networks implies --show-cidr
            self.show_cidr = True

        # file_list will be None when using ipgrep...
        if self.file_list is None:
            self.file_list = [""]

        if self.subparser_name != "ipgrep" and self.subparser_name != "macgrep":
            self.print_command_header()

        for filename in self.file_list:

            # The default parse, empty configuration...
            self.parse = CiscoConfParse([""])

            # Conditionally print the file name header...
            if (
                self.subparser_name != "diff"
                and self.subparser_name != "ipgrep"
                and self.subparser_name != "macgrep"
            ):
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
                # See the if clause below, outdented one-level
                pass

            elif self.subparser_name == "ipgrep":

                if self.ipgrep_file is None:
                    error = "The ipgrep_file argument is required"
                    self.arg_parser.parser.error(error)

                # Overwrite the --subnets argument if --ipv4 or --ipv6 is used
                if self.subnets is None:
                    if self.ipv4 is True and self.ipv6 is False:
                        self.subnets = "0.0.0.0/0"
                    elif self.ipv4 is False and self.ipv6 is True:
                        self.subnets = "::/0"
                    elif self.ipv4 is True and self.ipv6 is True:
                        self.subnets = "0.0.0.0/0,::/0"
                else:
                    if self.ipv4 is True or self.ipv6 is True:
                        error = "--ipv4 and --ipv6 cannot be used with --subnets"
                        self.arg_parser.parser.error(error)

                # Ensure that we did not get an empty --subnets argument...
                if self.subnets == "":
                    error = "--subnets requires an IPv4 or IPv6 network and mask"
                    self.arg_parser.parser.error(error)

                # See the if clause, outdented one-level
                self.ipgrep_command(subnets=self.subnets, text=self.ipgrep_file.read())

            elif self.subparser_name == "macgrep":

                if self.macgrep_file is None:
                    error = "The macgrep_file argument is required"
                    self.arg_parser.parser.error(error)

                # See the if clause, outdented one-level
                self.macgrep_command(
                    mac_regex=self.mac_regex, text=self.macgrep_file.read()
                )

            else:
                error = f"This ccp subparser name is missing an if-clause: {self.subparser_name}"
                logger.critical(error)
                raise ValueError(error)

        if self.subparser_name == "diff":
            self.diff_command()

        self.print_all_stdout()

    @logger.catch(reraise=True)
    def print_all_stdout(self):
        """Write self.stdout to stdout"""
        for line in self.stdout:
            print(line)

    @logger.catch(reraise=True)
    def parent_command(self) -> None:
        """Implement the find_parent_objects() CLI command"""
        if self.output_format == "raw_text":
            for obj in self.parse.find_parent_objects(self.args):
                self.stdout.append(obj.text)
        else:
            error = f"--output {self.output_format} is not supported"
            logger.critical(error)
            raise NotImplementedError(error)

    @logger.catch(reraise=True)
    def child_command(self) -> None:
        """Implement the find_child_objects() CLI command"""
        if self.output_format == "raw_text":
            for obj in self.parse.find_child_objects(self.args):
                self.stdout.append(obj.text)
        else:
            error = f"--output {self.output_format} is not supported"
            logger.critical(error)
            raise NotImplementedError(error)

    @logger.catch(reraise=True)
    def branch_command(self) -> None:
        """Implement the CLI find_object_branches command"""

        if self.output_format == "raw_text":

            if len(self.args) == 1:
                error = "'ccp branch -o raw_text' requires at least two -a args.  Use 'ccp -o original' if calling with only one 'ccp branch -a' term"
                logger.critical(error)
                raise NotImplementedError(error)

            for branch in self.parse.find_object_branches(self.args):
                self.stdout.extend([obj.text for obj in branch])

        elif self.output_format == "original":
            retval = set()
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
        """Implement the CLI diff command"""

        with open(self.file_list[0]) as fh0:
            file0 = fh0.read()
        with open(self.file_list[1]) as fh1:
            file1 = fh1.read()
        diff = Diff(file0, file1)

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
    def ipgrep_command(
        self,
        subnets: Union[str, None],
        text: str,
    ) -> bool:
        """grep for a subnet in the text"""

        # Throw an error if ccp ipgrep -s is missing
        if subnets is None:
            error = "The -s, -4 or -6 argument is required"
            self.arg_parser.parser.error(error)

        retval = []

        _subnets = set()

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
            except Exception:
                pass

            if mode == -1:
                error = f"subnet: {subnet} is not a valid IPv4 or IPv6 subnet"
                logger.critical(error)
                raise ValueError(error)

            _subnets.add(_subnet)

        if not self.line:
            words = re.split(self.word_delimiter, text)
            retval = self.find_ip46_addr_matches(
                _subnets, potential_matches=words, unique_matches=self.unique
            )
        else:
            if self.show_cidr or self.show_networks:
                error = "The --show_cidr and --show_networks args are not supported with --line"
                self.arg_parser.parser.error(error)

            lines = text.splitlines()
            retval = self.find_ip46_line_matches(
                subnets=_subnets, potential_matches=lines, unique_matches=self.unique
            )
        if len(retval) == 0:
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
    def find_ip46_addr_matches(
        self,
        subnets: set[Union[IPv4Obj, IPv6Obj]],
        potential_matches: list[str],
        unique_matches: bool,
    ) -> list:
        """Walk the IPv4 / IPv6 instances in potential_matches, return the list of addrs matching subnet"""

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

                    if unique_matches:
                        append_addr = False

                        if self.show_cidr is False:
                            if (
                                self.show_networks is False
                                and str(addr.ip) not in retval
                            ):
                                append_addr = True
                            elif (
                                self.show_networks is True
                                and str(addr.as_cidr_net) not in retval
                            ):
                                append_addr = True
                        else:
                            if (
                                self.show_networks is False
                                and str(addr.as_cidr_addr) not in retval
                            ):
                                append_addr = True
                            elif (
                                self.show_networks is True
                                and str(addr.as_cidr_net) not in retval
                            ):
                                append_addr = True

                        # Append if not already in retval...
                        if append_addr:
                            if self.check_ip46_host_exclusion_args(addr):
                                continue
                            if self.check_ip46_net_exclusion_args(addr):
                                continue

                            if self.show_networks:
                                retval.append(addr.as_cidr_net)
                            elif not self.show_cidr and not self.show_networks:
                                retval.append(str(addr.ip))
                            elif not self.show_networks and self.show_cidr:
                                retval.append(addr.as_cidr_addr)

                    else:
                        if self.check_ip46_net_exclusion_args(addr):
                            continue
                        if self.check_ip46_host_exclusion_args(addr):
                            continue

                        # Append unconditionally...
                        if self.show_networks:
                            retval.append(addr.as_cidr_net)
                        elif not self.show_cidr and not self.show_networks:
                            retval.append(str(addr.ip))
                        elif not self.show_networks and self.show_cidr:
                            retval.append(addr.as_cidr_addr)
        return retval

    @logger.catch(reraise=True)
    @typechecked
    def check_ip46_host_exclusion_args(self, addr: Union[IPv4Obj, IPv6Obj]) -> bool:
        """Return True if addr is a host excluded by --exclude-hosts"""

        if self.exclude_hosts:
            if addr.version == 4 and addr.prefixlength == 32:
                # IPv4 Host, --exclude-hosts applies
                return True
            elif addr.version == 6 and addr.prefixlength == 128:
                # IPv6 Host, --exclude-hosts applies
                return True

            # Only do if we are not explicitly showing networks (instead of hosts)...
            elif not self.show_networks:
                # it's also a host if the network address not equal the ip address
                if str(addr.as_cidr_net) != str(addr.as_cidr_addr):
                    return True

        return False

    @logger.catch(reraise=True)
    @typechecked
    def check_ip46_net_exclusion_args(self, addr: Union[IPv4Obj, IPv6Obj]) -> bool:
        """Return True if addr is a network excluded by --exclude-networks"""

        if self.exclude_networks:

            if addr.version == 4 and addr.prefixlength == 32:
                # IPv4 Host, --exclude-networks does not apply
                # (even though technically a /32 is also a network)
                return False

            elif addr.version == 6 and addr.prefixlength == 128:
                # IPv6 Host, --exclude-networks does not apply
                # (even though technically a /128 is also a network)
                return False

            else:
                # Since we are showing networks, any address (on the
                # subnet number or not) should return True if the
                # cases above did not match.
                return True

        return False

    @logger.catch(reraise=True)
    @typechecked
    def find_ip46_line_matches(
        self,
        subnets: set[Union[IPv4Obj, IPv6Obj]],
        potential_matches: list[str],
        unique_matches: bool,
    ) -> list:
        """Walk the IPv4 / IPv6 instances in potential_matches, return the list of lines with a word matching subnet"""
        retval = []

        for line in potential_matches:
            append_line = False
            exclude_line = False

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

                    if exclude_line:
                        continue

                    if (addr.version == subnet.version) and (addr in subnet):
                        if self.check_ip46_net_exclusion_args(addr):
                            exclude_line = True
                            append_line = False
                        elif self.check_ip46_host_exclusion_args(addr):
                            exclude_line = True
                            append_line = False
                        else:
                            # append the line with the matching text.  This appends on
                            # the first match and breaks out of the loop
                            append_line = True

            if append_line:
                retval.append(line)
        return retval

    @logger.catch(reraise=True)
    @typechecked
    def macgrep_command(
        self,
        mac_regex: Union[str, None],
        text: str,
    ) -> bool:
        """grep for a mac / EUI addresses in the text"""

        retval = []

        mac_regex_strs = set()

        for _regex in mac_regex.split(","):
            mac_regex_strs.add(_regex)

        if not self.line:
            words = re.split(self.word_delimiter, text)
            retval = self.find_maceui_addr_matches(
                mac_regex_strs, potential_matches=words, unique_matches=self.unique
            )
        else:
            lines = text.splitlines()
            retval = self.find_maceui_line_matches(
                mac_regex_strs, potential_matches=lines, unique_matches=self.unique
            )

        if len(retval) == 0:
            # potential_matches == [] is a special case where the text
            # had an invalid ip address like 172.16.355555
            return False

        elif isinstance(retval, list):
            # Multiple IP address mode...
            for match in retval:
                self.stdout.append(match)

            return True

        else:
            error = "Something unexpected happened.  Please file this bug on github.com/mpenning/ciscoconfparse2"
            logger.critical(error)
            raise ValueError(error)

    @logger.catch(reraise=True)
    def find_maceui_addr_matches(
        self,
        mac_regex_strs: set[str],
        potential_matches: list[str],
        unique_matches: bool,
    ) -> list:
        """Walk the MAC / EUI64 instances in potential_matches, return the list of addrs matching mac_regex_strs"""
        retval = []

        for word in potential_matches:
            search = MACEUISearch(word)
            if search.mac_retval is not None:
                if search.search_all_formats(mac_regex_strs=mac_regex_strs):
                    mac_str = word
                    if unique_matches:
                        if mac_str not in retval:
                            retval.append(mac_str)
                    else:
                        retval.append(mac_str)
        return retval

    @logger.catch(reraise=True)
    def find_maceui_line_matches(
        self,
        mac_regex_strs: set[str],
        potential_matches: list[str],
        unique_matches: bool = False,
    ) -> list:
        """Walk the MAC / EUI64 instances in potential_matches, return the list of lines matching mac_regex_strs"""
        retval = []
        for line in potential_matches:
            line_appended = False
            for word in re.split(self.word_delimiter, line):
                if line_appended:
                    continue
                search = MACEUISearch(word)
                if search.mac_retval is not None:
                    if search.search_all_formats(mac_regex_strs=mac_regex_strs):
                        retval.append(line)
                        line_appended = True

        return retval

    @logger.catch(reraise=True)
    def print_command_header(self) -> None:
        """Print the command header including what is searched and the search terms"""

        self.console.print(
            f"[green1]Syntax      [/green1]: [purple]{self.syntax}[/purple]"
        )
        self.console.print(
            f"[green1]Returing    [/green1]: [purple]{self.subparser_name}[/purple] text"
        )
        self.console.print(
            f"[green1]Output as   [/green1]: [purple]{self.output_format}[/purple]"
        )

        if self.subparser_name != "diff":
            for idx, term in enumerate(self.args):
                if idx == 0:
                    self.console.print(
                        f"  [green1]parent[/green1]: [turquoise2]{term}[/turquoise2]"
                    )
                else:
                    self.console.print(
                        f"  [green1]child [/green1]: [red1]{term}[/red1]"
                    )

    @logger.catch(reraise=True)
    @typechecked
    def print_file_name_centered(self, filename: str) -> None:
        """Print the filename colored and centered"""

        _width = self.console.width
        prefix = "file:"
        _var_line = int((_width - len(prefix) - len(filename) - 3) / 2.0) * "-"
        self.console.print(
            f"[green1]{_var_line}[/green1] file: [turquoise2]{filename}[/turquoise2] [green1]{_var_line}[/green1]"
        )


@attrs.define(repr=False)
class MACEUISearch:
    """Accept one string word, and search it for all mac regex strings.  If there is a match, classify as matching a MAC / EUI64 word or not.  If a mac-address is found, store the resulting MACObj() or EUI64Obj() instance in mac_retval."""

    word: str
    mac_regex_strs: set[str]
    mac_retval: Union[None, MACObj, EUI64Obj]

    @logger.catch(reraise=True)
    @typechecked
    def __init__(self, word: str, mac_regex_strs: Union[None, set[str]] = None):
        self.word = word
        self.mac_regex_strs = mac_regex_strs
        self.mac_retval = None

        tmp = None
        # Find the longest MAC / EUI64 class for the word
        #
        # NOTE To handle the macaddress module ValueError, I have
        # to parse the words first as the macaddress module, then I
        # can re-parse as MACObj or EUI64Obj
        try:
            tmp = macaddress.parse(word, macaddress.MAC, macaddress.EUI64)
            if isinstance(tmp, macaddress.MAC):
                self.mac_retval = MACObj(word)
            elif isinstance(tmp, macaddress.EUI64):
                self.mac_retval = EUI64Obj(word)
        except ValueError:
            # There was an invalid MAC / EUI64 address in the word string
            self.mac_retval = None

    @logger.catch(reraise=True)
    @typechecked
    def search_all_formats(self, mac_regex_strs: set[str]) -> bool:
        """Search self.word for a mac addresses matching any of the strings in the mac_regex_strs set"""

        if self.mac_retval is None:
            return False

        # Search through all valid mac formats for a regex match (contained
        #    in the mac_regex_strs set of regex strings...)
        for rgx in mac_regex_strs:
            if re.search(rgx, self.mac_retval.dash, re.I):
                return True
            elif re.search(rgx, self.mac_retval.colon, re.I):
                return True
            elif re.search(rgx, self.mac_retval.cisco, re.I):
                return True
            elif re.search(rgx, self.mac_retval.dash.replace("-", ""), re.I):
                return True
        # return False if there was no match above...
        return False

    def __str__(self):
        if isinstance(self.mac_retval, MACObj):
            return f"""<MACEUISearch word: {self.word}, found: MAC {self.mac_retval.cisco}>"""
        elif isinstance(self.mac_retval, EUI64Obj):
            return f"""<MACEUISearch word: {self.word}, found: EUI64 {self.mac_retval.cisco}>"""
        else:
            return f"""<MACEUISearch word: {self.word}, found: None>"""

    def __repr__(self):
        return str(self)


class OnlyOneArgument(Action):
    """A custom argparse action to only allow one instance of a CLI flag argument"""

    def __call__(self, parser, namespace, values, option_string):
        if getattr(namespace, self.dest, self.default) is not self.default:
            parser.error(option_string + " must not appear multiple times.")
        setattr(namespace, self.dest, values)
