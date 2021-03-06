#!/usr/bin/env python3
import argparse
import glob
import os
import re
import sre_constants
import textwrap

from natsort import natsorted, ns

from batchren import _version
from batchren import helper, renamer, StringSeq
from batchren.tui import arrange_tui, selection_tui


def glob_files(pattern):
    files = [f for f in glob.iglob(pattern, recursive=True) if os.path.isfile(f)]
    return natsorted(files, reverse=False, alg=ns.PATH)


def check_optional(args):
    notfilter = {"dryrun", "quiet", "verbose", "path", "sort", "sel", "esc", "raw"}
    argdict = vars(args)

    for argname, argval in argdict.items():
        if argname in notfilter or argval is False:
            continue
        if argval is not None:
            return True
    return False


def expand_dir(path):
    """Function to process directory option\n
    Add '*' if path is a directory, otherwise return path unaltered.
    """
    path = os.path.normpath(path)
    if os.path.isdir(path):
        return os.path.join(path, "*")
    return path


def validate_ext(ext):
    """Validate extension option\n
    Give an error if argument contains '/' or backslash
    """
    err1 = "illegal character in extension"
    if "/" in ext or "\\" in ext:
        raise argparse.ArgumentTypeError(err1)
    return ext


def validate_esc(esc):
    """Validate esc options\n
    Give an error if the characters aren't '*?[]'
    """
    esc = esc.replace("]", "[")
    argset = set(esc)
    charset = {"*", "?", "["}
    if argset.difference(charset):
        err = "input character is not '*?[]'"
        raise argparse.ArgumentTypeError(err)

    return "".join(argset)


def trim(arg):
    return arg.strip()


class TranslateAction(argparse.Action):
    """batchren -tr CHARS CHARS\n
    Custom action for translate. Accept two arguments.\n
    Return argument as a tuple.\n
    Give an error if:\n
    -   both values are empty
    -   there aren't two arguments (achieved through nargs=2)
    -   argument lengths aren't equal
    """
    def __call__(self, parser, namespace, values, option_string=None):
        argtype = "argument -tr/--translate: "
        err0 = "argument values are empty"
        err1 = "arguments must be equal length"
        # argparse handles arguments errors for argument length != 2
        if not all(values):
            parser.error(argtype + err0)
        if len(values[0]) != len(values[1]):
            parser.error(argtype + err1)
        namespace.translate = tuple(values)


class SliceAction(argparse.Action):
    """batchren -sl start:end:step\n
    Custom action for slices. Accept argument separated by semicolons.\n
    Give an error if:\n
    -   argument value is empty
    -   cannot convert to slice object (too many arguments)
    -   value is not integer
    """
    def __call__(self, parser, namespace, values, option_string=None):
        argtype = "argument -sl/--slice: "
        err0 = "argument value is empty"
        err1 = "too many arguments for slicing"
        err2 = "non-numeric character in slice"
        if not values:
            parser.error(argtype + err0)
        try:
            sl = slice(*[int(x.strip()) if x.strip() else None for x in values.split(":")])
        except TypeError:
            parser.error(argtype + err1)
        except ValueError:
            parser.error(argtype + err2)
        namespace.slice = sl


class ShaveAction(argparse.Action):
    """batchren -sh head:tail\n
    Custom action for shave. Accept one argument separated by semicolon.\n
    Slice values must be positive integers. Create two slice objects from args.\n
    Give an error if:\n
    -   argument value is empty
    -   more than two values
    -   any non-numeric character
    -   both values are None
    -   any values are negative
    """
    def __call__(self, parser, namespace, values, option_string=None):
        argtype = "argument -sh/--shave: "
        err0 = "argument value is empty"
        err1 = "non-numeric character in shave"
        err2 = "too many values for shaving"
        err3 = "too few values for shaving"
        err4 = "negative value in shave"
        if not values:
            parser.error(argtype + err0)

        try:
            sl = [int(x.strip()) if x.strip() else None for x in values.split(":")]
        except ValueError:
            parser.error(argtype + err1)

        if len(sl) > 2:
            parser.error(argtype + err2)
        elif len(sl) == 1:
            sl.append(None)

        if any(x is not None and x < 0 for x in sl):
            # check for any negative values
            parser.error(argtype + err4)
        if all(x is None for x in sl):
            # check if all values are None
            parser.error(argtype + err3)
        head = slice(sl[0], None, None) if sl[0] is not None else slice(None)
        tail = slice(None, -sl[1], None) if sl[1] is not None else slice(None)
        namespace.shave = (head, tail)


class RegexAction(argparse.Action):
    """batchren -re PATTERN REPL COUNT\n
    Custom action for regex. Accept up to three arguments.\n
    If one argument, remove instances of PATTERN.\n
    If two arguments, replace all instances PATTERN by REPL.\n
    If three arguments, replace COUNT'th instance of PATTERN BY REPL.\n
    Second argument default is '', third argument default is 0.\n
    Give an error if:\n
    -   pattern argument is empty
    -   no arguments/too many arguments (>3)
    -   regex/sre compile error
    -   if value is not an integer >= 0
    """
    def __call__(self, parser, namespace, values, option_string=None):
        argtype = "argument -re/--regex: "
        err0 = "pattern argument is empty"
        err1 = "expected at least one argument"
        err2 = "expected up to three arguments"
        err3 = "non-numeric character in count argument"
        err4 = "bad regex input "
        if len(values) < 1:
            parser.error(argtype + err1)
        elif len(values) > 3:
            parser.error(argtype + err2)
        if not values[0]:
            parser.error(argtype + err0)

        try:
            regexp = re.compile(values[0])
            val = values[1] if len(values) > 1 else ""
            count = int(values[2].strip()) if len(values) == 3 else 0
        except re.error as err:
            # error from compiling regex
            parser.error(argtype + err4 + str(err))
        except sre_constants.error as sre_err:
            # extra compilation error for regex
            parser.error(argtype + err4 + str(sre_err))
        except ValueError:
            # error from converting count into int
            parser.error(argtype + err3)
        namespace.regex = (regexp, val, count)


class BracketAction(argparse.Action):
    """batchren -bracr {arsc} COUNT\n
    Custom action for a bracket remover.\n
    Remove specified brackets and content types depending on arguments.\n
    If no argument, remove all brackets types and their contents.\n
    If one argument, remove instances of specified bracket type(s).\n
    If two arguments, remove COUNT'th instance of specified bracket type(s).\n
    Give an error if:\n
    -   too many arguments (>2)
    -   invalid bracket type
    -   bracket target is not an integer >= 0
    """
    def __call__(self, parser, namespace, values, option_string=None):
        choices = re.compile(r"^[arsc]+$")
        argtype = "argument -bracr/--bracket_remove: "
        err1 = "expected at most two arguments"
        err2 = "invalid match for bracket type(s)"
        err3 = "cannot remove negative bracket match"
        err4 = "bracket target is not a number"

        if len(values) > 2:
            parser.error(argtype + err1)

        if len(values) > 0:
            if not re.match(choices, values[0]):
                parser.error(argtype + err2)
            values[0] = "".join(dict.fromkeys(list(values[0])))
        else:
            values[0] = "a"

        try:
            repl_count = int(values[1]) if len(values) == 2 else 0
            if repl_count < 0:
                # don't allow negative bracket match
                parser.error(argtype + err3)
        except ValueError:
            # values[1] cannot be converted to an int
            parser.error(argtype + err4)

        namespace.bracket_remove = (values[0], repl_count)


class SequenceAction(argparse.Action):
    """batchren -seq SEQUENCE\n
    Custom action for sequence. Accept one argument.\n
    Attempt to parse SEQUENCE into a seqObj.\n
    Raise errors on exceptions.
    """
    def __call__(self, parser, namespace, values, option_string=None):
        argtype = "argument -seq/--sequence: "
        try:
            seq = StringSeq.StringSequence(values)
        except ValueError as v_err:
            parser.error(argtype + str(v_err))
        except TypeError as t_err:
            parser.error(argtype + str(t_err))
        else:
            namespace.sequence = seq


class CustomFormatter(argparse.RawTextHelpFormatter):
    """Custom formatter for argparse.\n
    Skip long optionals that have parameters.\n
    Replace metavars for specific arguments.\n
    Use argparse.RawTextHelpFormatter to use textwrap
    """
    def _hack_metavar(self, option_string, args_string):
        # ugly hack to override specific metavars
        if option_string == "--translate":
            return "CHARS CHARS"
        elif option_string == "--regex":
            return "PATTERN [REPL] [COUNT]"
        elif option_string == "--bracket_remove":
            return "{arsc} [COUNT]"
        else:
            return args_string

    def _format_action_invocation(self, action):
        if not action.option_strings:
            default = self._get_default_metavar_for_positional(action)
            metavar, = self._metavar_formatter(action, default)(1)
            return metavar

        else:
            parts = []
            long_options = ["--sort", "--esc", "--raw"]
            if action.nargs == 0:
                # if the optional doesn't take a value, format is:
                #    -s, --long
                parts.extend(action.option_strings)

            else:
                # default for optionals with short and long options w/parameters
                #    -s ARGS, --long ARGS
                #
                # Change behaviour to:
                # if the optional only has a long option
                #    --long ARGS
                # elif the optional has short and long options w/parameters
                #    -s, ARGS
                #
                # default = name of argument in upper case
                # args_string = default metavar
                # action.option_strings = '-seq, '--sequence'
                default = self._get_default_metavar_for_optional(action)
                args_string = self._format_args(action, default)

                for option_string in action.option_strings:
                    if option_string in long_options:
                        # include long options that don't have short options
                        pass
                    elif option_string[:2] == "--":
                        # show only short optional
                        continue
                    parts.append("%s" % option_string)
                args_string = self._hack_metavar(option_string, args_string)
                parts.append("%s" % args_string)

            return ", ".join(parts)


parser = argparse.ArgumentParser(
    prog="batchren",
    usage="%(prog)s path [options]",
    formatter_class=CustomFormatter,
    description="Batch Renamer - a script for renaming files",
    epilog=textwrap.dedent("""\
    note: file patterns with special characters should be escaped with quotes.
    Visit https://github.com/matvign/batchrenamer for examples.
    """),
    prefix_chars="-",           # only allow arguments with minus (default)
    fromfile_prefix_chars="@",  # allow arguments from file input
)

verbositygroup = parser.add_mutually_exclusive_group()

parser.add_argument("-sp", "--spaces", nargs="?", const="_",
                    metavar="REPL",
                    help="replace whitespace with specified (default: _)")
parser.add_argument("-tr", "--translate", nargs=2, action=TranslateAction,
                    help="translate characters from one to another")
parser.add_argument("-c", "--case",
                    choices=["upper", "lower", "swap", "cap"],
                    type=trim,
                    help="convert filename case")
parser.add_argument("-sl", "--slice", action=SliceAction,
                    metavar="start:end:step",
                    help="rename to character slice of file")
parser.add_argument("-sh", "--shave", type=trim, action=ShaveAction,
                    metavar="head:tail",
                    help="remove characters from head and/or tail of file")
parser.add_argument("-bracr", "--bracket_remove", nargs="*", type=trim, action=BracketAction,
                    help="remove bracket type and its contents")
parser.add_argument("-re", "--regex", nargs="*", action=RegexAction,
                    help="specify pattern to remove/replace")
parser.add_argument("-pre", "--prepend", metavar="STR",
                    help="prepend string to filename")
parser.add_argument("-post", "--postpend", metavar="STR",
                    help="append string to filename")
parser.add_argument("-seq", "--sequence", action=SequenceAction,
                    help="apply a sequence to files")
parser.add_argument("-ext", "--extension", metavar="EXT", type=validate_ext,
                    help="change last file extension (e.g. mp4, '')")
parser.add_argument("--esc", nargs="?", const="*?[]", type=validate_esc,
                    help="escape literal characters ('*?[]')")
parser.add_argument("--raw", action="store_true",
                    help="treat extension as filename and preserve whitespace")
parser.add_argument("--sort", choices=["asc", "desc", "man"], default="asc",
                    help="rename files found in specific order")
parser.add_argument("--sel", action="store_true",
                    help="manually select files from pattern match")
parser.add_argument("--dryrun", action="store_true",
                    help="run without renaming any files")
verbositygroup.add_argument("-q", "--quiet", action="store_true",
                    help="skip output, but show confirmations")
verbositygroup.add_argument("-v", "--verbose", action="store_true",
                    help="show detailed output")
parser.add_argument("--version", action="version", version=_version.__version__)
parser.add_argument("path", nargs="?", default="*", type=expand_dir,
                    help="target file/directory")


def main():
    args = parser.parse_args()
    if args.verbose:
        helper.print_args(args)

    if not check_optional(args):
        parser.print_usage()
        print("\nNo optional arguments set for renaming")
        return

    if args.esc:
        args.path = helper.escape_path(args.path, args.esc)

    try:
        files = glob_files(args.path)
    except OSError as err:
        raise argparse.ArgumentParser.error("An error occurred while searching for files: " + str(err))

    if not files:
        helper.print_nofiles()
        return

    if args.sel:
        files = selection_tui.main(files)
        if files is None:
            return
        elif files == []:
            print("No files selected")
            return

    if args.sort == "man":
        files = arrange_tui.main(files)
        if not files:
            return
    elif args.sort == "desc":
        files.reverse()

    if args.verbose:
        helper.print_found(files)

    renamer.start_rename(files, args)
