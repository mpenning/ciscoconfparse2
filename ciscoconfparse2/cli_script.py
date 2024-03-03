from argparse import ArgumentParser, Namespace
from argparse import _SubParsersAction
from typing import List, Any
import shlex
import glob
import sys

from rich.console import Console as RichConsole
from loguru import logger
from typeguard import typechecked
import attrs

from ciscoconfparse2.ciscoconfparse2 import CiscoConfParse
from ciscoconfparse2.ciscoconfparse2 import Diff

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

        try:
            if isinstance(args.method, str):
                self.diff_method = args.method
            else:
                error = f"diff method must be a string"
                logger.critical(error)
                raise ValueError(error)

        except AttributeError:
            self.diff_method = "diff"

        self.console = RichConsole()
        self.args = args.args.split(args.separator)
        self.subparser_name = args.command
        self.syntax = args.syntax
        self.output_format = args.output
        self.file_list = args.file

        self.print_command_header()

        for filename in self.file_list:

            if self.subparser_name != "diff":
                self.print_file_name_centered(filename)

            parse = CiscoConfParse(
                        config=filename,
                        syntax=self.syntax,
                    )

            if self.subparser_name == "parent":
                if self.output_format == "raw_text":
                    for obj in parse.find_parent_objects(self.args):
                        print(obj.text)
                else:
                    error = f"--output {self.output_format} is not supported"
                    logger.critical(error)
                    raise NotImplementedError(error)

            elif self.subparser_name == "child":
                if self.output_format == "raw_text":
                    for obj in parse.find_child_objects(self.args):
                        print(obj.text)
                else:
                    error = f"--output {self.output_format} is not supported"
                    logger.critical(error)
                    raise NotImplementedError(error)

            elif self.subparser_name == "branch":
                if self.output_format == "raw_text":
                    for branch in parse.find_object_branches(self.args):
                        print([obj.text for obj in branch])
                else:
                    error = f"--output {self.output_format} is not supported"
                    logger.critical(error)
                    raise NotImplementedError(error)

            elif self.subparser_name == "diff":
                # See the if clause, outdented one-level
                pass

            else:
                error = f"Unexpected subparser name: {self.subparser_name}"
                logger.critical(error)
                raise ValueError(error)

            print()

        if self.subparser_name == "diff":
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
            choices=['raw_text', 'json', 'yaml',],
            default='raw_text',
            type=str,
            help="Output format, defaults to raw_text")

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
            choices=['raw_text', 'json', 'yaml',],
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
            help="Child field separator, defaults to a comma")

        parser_optional.add_argument(
            "-o", "--output",
            required=False,
            choices=['raw_text', 'json', 'yaml',],
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

if __name__ == "__main__":
    print(args)

