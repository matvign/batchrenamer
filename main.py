#!/usr/bin/env python3
import argparse
import glob
import os

from natsort import natsorted, ns

from batchren import renamer
from batchren.seqObj import SequenceObj
from batchren._version import __version__


def printArgs(args):
    print('{:-^30}'.format(renamer.BOLD + 'arguments' + renamer.END))
    for argname, argval in sorted(vars(args).items()):
        if argval is False:
            continue
        if argval is not None:
            print('    {}: {}'.format(argname, argval))
    print()
    # print(args, '\n')


def checkOptsSet(args):
    notfilter = {'quiet', 'verbose', 'path'}
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

    if not checkOptsSet(args):
        print("no optional arguments set for renaming")
        return

    try:
        # exclude directories
        fileset = {f for f in glob.iglob(args.path) if os.path.isfile(f)}
    except Exception as e:
        print(e)
        return

    if not fileset:
        print('{:-^30}'.format(renamer.BOLD + 'files found' + renamer.END))
        print('no files found\n')
        return

    if args.verbose:
        print('{:-^30}'.format(renamer.BOLD + 'files found' + renamer.END))
        for n in natsorted(fileset, alg=ns.PATH):
            print(n)
        print()

    renamer.start_rename(args, fileset)


# glob into directories e.g. dir/ -> dir/*
def expanddir(path):
    if path[-1] == '/':
        return path + '*'
    elif os.path.isdir(path):
        return os.path.join(path, '*')
    return path


def illegalextension(ext):
    err1 = "argument -ext/--extension: illegal character found in extension"
    if '/' in ext or '\\' in ext:
        parser.error(err1)
    return ext


# enforce length of translate must be equal
class TranslateAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        err1 = 'argument -tr/--translate: expected two arguments'
        err2 = 'argument -tr/--translate: arguments must be equal length'
        if (len(values) != 2):
            parser.error(err1)

        if len(values[0]) != len(values[1]):
            parser.error(err2)
        namespace.translate = tuple(values)


# produce slice object from string
class SliceAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        err1 = 'argument -sl/--slice: too many arguments for slicing'
        err2 = 'argument -sl/--slice: non-numeric character in slice'
        # to keep it simple, have '::' as our format
        try:
            sl = slice(
                *map(lambda x: int(x.strip()) if x.strip() else None, values.split(':'))
            )
        except TypeError:
            parser.error(err1)
        except ValueError:
            parser.error(err2)
        namespace.slice = sl


# custom action, only accept one or two arguments
class RegexAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        err1 = 'argument -re/--regex: expected one or two arguments'
        if (len(values) > 2):
            parser.error(err1)

        if (len(values) == 1):
            values.append('')
        namespace.regex = values


# sequence action, store some format for sequences
class SequenceAction(argparse.Action):
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
            if seqObj.is_valid():
                namespace.sequence = seqObj
            else:
                parser.error(msg + err1)


class CustomFormatter(argparse.HelpFormatter):
    # ugly hack to override specific metavars
    def _hack_metavar(self, option_string, args_string):
        if option_string == '--translate':
            return 'CHARS CHARS'
        elif option_string == '--spaces':
            return 'CHARS'
        elif option_string == '--regex':
            return 'REGEX [REGEX]'
        else:
            return args_string

    def _format_action_invocation(self, action):
        if not action.option_strings:
            metavar, = self._metavar_formatter(action, action.dest)(1)
            return metavar
        else:
            parts = []
            # if the Optional doesn't take a value, format is:
            #    -s, --long
            if action.nargs == 0:
                parts.extend(action.option_strings)

            # if the Optional takes a value, format is:
            #    -s ARGS, --long ARGS
            # change to
            #    -s, --long ARGS
            else:
                default = action.dest.upper()
                args_string = self._format_args(action, default)
                for option_string in action.option_strings:
                    if option_string[:2] == '--':
                        continue
                    parts.append('%s' % option_string)
                args_string = self._hack_metavar(option_string, args_string)
                parts[-1] += ' %s' % args_string
            return ', '.join(parts)


'''
Argparse options
fromfile_prefix_chars='@', allow arguments from file input
prefix_chars='-', only allow arguments with minus (default)
'''
parser = argparse.ArgumentParser(
    prog='batchren',
    usage='python3 %(prog)s.py path [options]',
    formatter_class=CustomFormatter,
    description='Batch Renamer - a script for renaming files',
    epilog='note: all special characters should be escaped using quotes',
    prefix_chars='-',
    fromfile_prefix_chars='@'
)
outgroup = parser.add_mutually_exclusive_group()

parser.add_argument('-sp', '--spaces', nargs='?', const='_', metavar='REPL',
                    help='replace whitespaces with specified (default: _)')
parser.add_argument('-tr', '--translate', nargs='*', action=TranslateAction,
                    metavar='CHARS',
                    help='translate characters from one to another')
parser.add_argument('-sl', '--slice', action=SliceAction,
                    metavar='start:end:step',
                    help='slice a portion of the filename')
parser.add_argument('-c', '--case',
                    choices=['upper', 'lower', 'swap', 'cap'],
                    help='convert filename case')
parser.add_argument('-bracr', action='store_true',
                    help='remove brackets and their contents')
parser.add_argument('-pre', '--prepend', metavar='STR',
                    help='prepend string to filename')
parser.add_argument('-post', '--postpend', metavar='STR',
                    help='append string to filename')
parser.add_argument('-ext', '--extension', metavar='EXT', type=illegalextension,
                    help="change last file extension (e.g. mp4, '')")
parser.add_argument('-re', '--regex', nargs='+', action=RegexAction,
                    help='specify pattern to replace')
parser.add_argument('-seq', '--sequence', action=SequenceAction,
                    help='apply a sequence to files')
outgroup.add_argument('-q', '--quiet', action='store_true',
                    help='skip output, but show confirmations')
outgroup.add_argument('-v', '--verbose', action='store_true',
                    help='show detailed output')
parser.add_argument('--version', action='version', version=__version__)
parser.add_argument('path', nargs='?', default='*', type=expanddir,
                    help='target directory')
args = parser.parse_args()

if __name__ == '__main__':
    main(args)
    print('Exiting...')