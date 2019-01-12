#!/usr/bin/env python3
import argparse
import glob
import os
import re

from natsort import natsorted, ns

from batchren import renamer
from batchren.seqObj import SequenceObj
from batchren._version import __version__

BOLD = '\033[1m'
END = '\033[0m'


def printArgs(args):
    print('{:-^30}'.format(BOLD + 'arguments' + END))
    for argname, argval in sorted(vars(args).items()):
        if argval is False:
            continue
        if argval is not None:
            print('    {}: {}'.format(argname, argval))
    print()
    # print(args, '\n')


def checkOptSet(args):
    notfilter = {'dryrun', 'quiet', 'verbose', 'path'}
    argdict = vars(args)

    for argname, argval in argdict.items():
        if argname in notfilter or argval is False:
            continue
        if argval is not None:
            return True
    return False


def main(args):
    if args.verbose:
        printArgs(args)

    if not checkOptSet(args):
        print("no optional arguments set for renaming")
        return

    try:
        # only include files
        files = natsorted([f for f in glob.iglob(args.path) if os.path.isfile(f)], alg=ns.PATH)
    except OSError as err:
        parser.error('A error occurred while searching for files... ' + err)

    if not files:
        print('{:-^30}'.format(BOLD + 'files found' + END))
        print('no files found\n')
        return

    if args.verbose:
        print('{:-^30}'.format(BOLD + 'files found' + END))
        for n in files:
            print(n)
        print()

    renamer.start_rename(args, files)


def expanddir(path):
    '''
    Custom type for directories.
    Add '*' if path is a directory or if path ends with '/'
    '''
    if path[-1] == '/':
        return path + '*'
    elif os.path.isdir(path):
        return os.path.join(path, '*')
    return path


def illegalextension(ext):
    '''
    Custom type for extensions.
    Give an error if argument contains '/' or '\'
    '''
    err1 = 'argument -ext/--extension: illegal character found in extension'
    if '/' in ext or '\\' in ext:
        parser.error(err1)
    return ext


def trim(arg):
    return arg.strip()


# enforce length of translate must be equal
class TranslateAction(argparse.Action):
    '''
    Custom action for translate. Accept two arguments.
    Give an error if both values are empty.
    Give an error if there aren't two arguments.
    Give an error if argument lengths aren't equal.
    Convert output into a tuple.
    '''
    def __call__(self, parser, namespace, values, option_string=None):
        err0 = 'argument -tr/--translate: argument values are empty'
        # err1 = 'argument -tr/--translate: expected two arguments'
        err2 = 'argument -tr/--translate: arguments must be equal length'
        # if len(values) != 2:
        #     parser.error(err1)
        if sum(1 for n in values if not n):
            parser.error(err0)
        if len(values[0]) != len(values[1]):
            parser.error(err2)
        namespace.translate = tuple(values)


class SliceAction(argparse.Action):
    '''
    Custom action for slices. Accept one argument with slice format.
    Give an error if we cannot convert to slice object.
    Give an error if any of the values aren't integers.
    '''
    def __call__(self, parser, namespace, values, option_string=None):
        err0 = 'argument -sl/--slice: argument value is empty'
        err1 = 'argument -sl/--slice: too many arguments for slicing'
        err2 = 'argument -sl/--slice: non-numeric character in slice'
        if not values:
            parser.error(err0)
        try:
            sl = slice(*[int(x.strip()) if x.strip() else None for x in values.split(':')])
        except TypeError:
            parser.error(err1)
        except ValueError:
            parser.error(err2)
        namespace.slice = sl


class ShaveAction(argparse.Action):
    '''
    Custom action for shave. Accept one argument in 'head:tail' format.
    Slice values must be positive integers. Create two slice object from values.
    Give an error if any non-numeric character.
    Give an error if more than two values.
    Give an error if both values are None.
    Give an error if any values are negative.
    '''
    def __call__(self, parser, namespace, values, option_string=None):
        err0 = 'argument -sh/--shave: argument value is empty'
        err1 = 'argument -sh/--shave: non-numeric character in shave'
        err2 = 'argument -sh/--shave: too many values for shaving'
        err3 = 'argument -sh/--shave: too few values for shaving'
        err4 = 'argument -sh/--shave: negative value in shave'
        if not values:
            parser.error(err0)
        try:
            sl = [int(x.strip()) if x.strip() else None for x in values.split(':')]
        except ValueError:
            parser.error(err1)
        if len(sl) > 2:
            parser.error(err2)
        elif len(sl) == 1:
            sl.append(None)
        if sum(1 for x in sl if x is not None and x < 0):
            # check for negative values
            parser.error(err4)
        if not sum(1 for x in sl if x is not None):
            # check if all values are None
            parser.error(err3)
        head = slice(sl[0], None, None) if sl[0] is not None else slice(None)
        tail = slice(None, -sl[1], None) if sl[1] is not None else slice(None)
        namespace.shave = (head, tail)


class RegexAction(argparse.Action):
    '''
    Custom action for regex. Accept up to three arguments.
    If three arguments, replace the nth instance of first by second.
    If two arguments, replace all instances of first by second.
    If one argument, remove all instances of first.
    Second argument default is '', third argument default is 0.
    '''
    def __call__(self, parser, namespace, values, option_string=None):
        err0 = 'argument -re/--regex: pattern argument is empty'
        err1 = 'argument -re/--regex: expected at least one argument'
        err2 = 'argument -re/--regex: expected up to three arguments'
        err3 = 'argument -re/--regex: non-numeric character in count argument'
        err4 = 'argument -re/--regex: bad regex input '
        if len(values) < 1:
            parser.error(err1)
        elif len(values) > 3:
            parser.error(err2)
        if not values[0]:
            parser.error(err0)

        try:
            reg_exp = re.compile(values[0])
            repl_val = values[1] if len(values) > 1 else ''
            repl_count = int(values[2].strip()) if len(values) == 3 else 0
        except re.error as err:
            # error from compiling regex
            parser.error(err4 + err.args[0])
        except ValueError:
            # error from converting count into int
            parser.error(err3)
        namespace.regex = (reg_exp, repl_val, repl_count)


class BracketAction(argparse.Action):
    '''
    Custom action for a bracket remover. Accept multiple arguments.
    Create different patterns with regex depending on bracket type.
    Allow an extra argument to target the nth bracket.
    '''
    def __call__(self, parser, namespace, values, option_string=None):
        choices = ['curly', 'round', 'square']
        err1 = 'argument -bracr/bracket_remove: expected at least one argument'
        err2 = 'argument -bracr/bracket_remove: expected at most two arguments'
        err3 = 'argument -bracr/bracket_remove: invalid choice for bracket type'
        err4 = 'argument -bracr/bracket_remove: bracket target is not a number'
        err5 = 'argument -bracr/bracket_remove: cannot remove negative bracket match'
        repl_count = 0
        if len(values) < 1:
            parser.error(err1)
        elif len(values) > 2:
            parser.error(err2)

        if values[0] not in choices:
            parser.error(err3)

        try:
            repl_count = int(values[1]) if len(values) == 2 else 0
            if repl_count < 0:
                # don't allow negative bracket match
                parser.error(err5)
        except ValueError:
            # values[1] cannot be converted to an int
            parser.error(err4)

        namespace.bracr = (values[0], repl_count)


class SequenceAction(argparse.Action):
    '''
    Custom action for sequence. Accept one argument.
    Try creating a sequence object and raise errors on exceptions.
    '''
    def __call__(self, parser, namespace, values, option_string=None):
        msg = 'argument -seq/--sequence: '
        err1 = 'missing file formatter %f'
        try:
            seqObj = SequenceObj(values)
        except ValueError as verr:
            parser.error(msg + verr.args[0])
        except TypeError as terr:
            parser.error(msg + terr.args[0])
        else:
            namespace.sequence = seqObj


class CustomFormatter(argparse.HelpFormatter):
    '''
    Custom formatter for argparse.
    Skip long optionals that have parameters.
    Replace metavars for specific arguments.
    '''
    def _hack_metavar(self, option_string, args_string):
        # ugly hack to override specific metavars
        if option_string == '--translate':
            return 'CHARS CHARS'
        elif option_string == '--regex':
            return 'PATTERN [REPL] [COUNT]'
        elif option_string == '-bracr':
            return '{curly,round,square} [COUNT]'
        else:
            return args_string

    def _format_action_invocation(self, action):
        if not action.option_strings:
            metavar, = self._metavar_formatter(action, action.dest)(1)
            return metavar
        else:
            parts = []
            # default for optionals without parameters:
            #    -s, --long
            if action.nargs == 0:
                parts.extend(action.option_strings)

            # default for optional with parameters:
            #    -s ARGS, --long ARGS
            # change to:
            #    -s, ARGS
            else:
                default = action.dest.upper()
                args_string = self._format_args(action, default)
                for option_string in action.option_strings:
                    if option_string[:2] == '--':
                        # skip long optionals with parameters
                        continue
                    parts.append('%s' % option_string)
                args_string = self._hack_metavar(option_string, args_string)
                parts[-1] += ' %s' % args_string
            return ', '.join(parts)


parser = argparse.ArgumentParser(
    prog='batchren',
    usage='python3 %(prog)s.py path [options]',
    formatter_class=CustomFormatter,
    description='Batch Renamer - a script for renaming files',
    epilog="note: all special characters should be escaped using quotes. If hyphen is in beginning of argument, use -arg='-val'",
    prefix_chars='-',           # only allow arguments with minus (default)
    fromfile_prefix_chars='@'   # allow arguments from file input
)
outgroup = parser.add_mutually_exclusive_group()

parser.add_argument('-sp', '--spaces', nargs='?', const='_',
                    metavar='REPL',
                    help='replace whitespaces with specified (default: _)')
parser.add_argument('-tr', '--translate', nargs=2, action=TranslateAction,
                    help='translate characters from one to another')
parser.add_argument('-sl', '--slice', action=SliceAction,
                    metavar='start:end:step',
                    help='slice a portion of the filename')
parser.add_argument('-sh', '--shave', type=trim, action=ShaveAction,
                    metavar='head:tail',
                    help='shave head and/or tail from string')
parser.add_argument('-bracr', nargs='*', type=trim, action=BracketAction,
                    help='remove contents of bracket type')
parser.add_argument('-c', '--case',
                    choices=['upper', 'lower', 'swap', 'cap'],
                    type=trim,
                    help='convert filename case')
parser.add_argument('-pre', '--prepend', metavar='STR',
                    help='prepend string to filename')
parser.add_argument('-post', '--postpend', metavar='STR',
                    help='append string to filename')
parser.add_argument('-ext', '--extension', metavar='EXT', type=illegalextension,
                    help="change last file extension (e.g. mp4, '')")
parser.add_argument('-re', '--regex', nargs='*', action=RegexAction,
                    help='specify pattern to remove/replace')
parser.add_argument('-seq', '--sequence', action=SequenceAction,
                    help='apply a sequence to files')
parser.add_argument('--dryrun', action='store_true',
                    help='run without renaming any files')
outgroup.add_argument('-q', '--quiet', action='store_true',
                    help='skip output, but show confirmations')
outgroup.add_argument('-v', '--verbose', action='store_true',
                    help='show detailed output')
parser.add_argument('--version', action='version', version=__version__)
parser.add_argument('path', nargs='?', default='*', type=expanddir,
                    help='target file/directory')
args = parser.parse_args()

if __name__ == '__main__':
    main(args)
    print('Exiting...')