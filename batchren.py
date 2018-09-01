import argparse
import glob
import os
from collections import deque

from natsort import natsorted, ns

from _version import __version__
import renamer


def main(args):
    # exclude directories
    fileset = {f for f in glob.iglob(args.dir) if os.path.isfile(f)}

    # show arguments used
    if args.verbose:
        print('{:-^30}'.format('arguments'))
        for argname, argval in sorted(vars(args).items()):
            if argval:
                print('    {}: {}'.format(argname, argval))
        print()

    # do not show if quiet
    # i.e. everything sees this except quiet
    if not args.quiet:
        print('{:-^30}'.format('files found'))
        for n in natsorted(fileset, alg=ns.PATH):
            print('    {}'.format(n))

    # run filters and get output in form of a table
    rentable = renamer.renfilter(args, fileset)

    # print contents of rentable and create a queue from it
    q = deque(renamer.display_rentable(rentable, args.quiet))
    if q and renamer.query_yes_no('Proceed with renaming?'):
        # start renaming if q non-empty and answer is yes
        renamer.run_rename(q, args)


# glob into directories e.g. dir/ -> dir/*
def expanddir(dir):
    if dir[-1] == '/':
        return dir + '*'
    elif os.path.isdir(dir):
        return os.path.join(dir, '*')

    return dir


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
class SplitAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        err1 = 'argument -sl/--slice: too many arguments for slicing'
        err2 = 'argument -sl/--slice: non-numeric character in slice'
        # to keep it simple, have '::' as our format
        try:
            sl = slice(*map
                (lambda x: int(x.strip()) if x.strip() else None, values.split(':'))
            )
        except TypeError:
            parser.error(err1)
        except ValueError:
            parser.error(err2)

        namespace.slice = sl


# custom action, accept one or two arguments
class RegexAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        err1 = 'argument -re/--regex: expected one or two arguments'
        # combined with nargs='+', means one or two arguments
        if (len(values) > 2):
            parser.error(msg)

        if (len(values) == 1):
            values.append('');
        namespace.regex = values


'''
Argparse options
fromfile_prefix_chars='@', allow arguments from file input
prefix_chars='-', only allow arguments with minus (default)
'''
parser = argparse.ArgumentParser(
    prog='pyren',
    usage='%(prog)s [options]',
    description='Batch Renamer - a script for renaming files',
    epilog='note: you must use quotes to escape special characters',
    prefix_chars='-',
    fromfile_prefix_chars='@'
)
outgroup = parser.add_mutually_exclusive_group()

parser.add_argument('-sp', '--spaces', nargs='?', const='_', metavar='REPL',
                    help='replace whitespaces with specified (default: _)')
parser.add_argument('-tr', '--translate', nargs='*', action=TranslateAction,
                    metavar='CHARS',
                    help='translate characters from one to another')
parser.add_argument('-sl', '--slice', action=SplitAction,
                    metavar='start:end:step',
                    help='slice a portion of the filename')
parser.add_argument('-c', '--case', choices=['upper', 'lower', 'swap', 'cap'],
                    metavar='',
                    help='convert filename case (upper/lower/swap/cap)')
parser.add_argument('-bracr', '--bracket-remove', action='store_true',
                    help='remove brackets and their contents')
parser.add_argument('-pre', '--prefix', metavar='STR',
                    help='prepend string to filename')
parser.add_argument('-post', '--postfix', metavar='STR',
                    help='append string to filename')
parser.add_argument('-ext', '--extension', metavar='EXT',
                    help="change last file extension (e.g. mp4, '')")
parser.add_argument('-seq', '--sequence', nargs='?', type=int, const=1,
                    help='append number to end of files')
parser.add_argument('-re', '--regex', nargs='+', action=RegexAction,
                    help='specify regex for renaming')
outgroup.add_argument('-q', '--quiet', action='store_true',
                    help='skip output, but show confirmations')
outgroup.add_argument('-v', '--verbose', action='store_true',
                    help='show detailed output')
parser.add_argument('--version', action='version', version=__version__)
parser.add_argument('dir', nargs='?', default='*', type=expanddir,
                    help='target directory (use quotes if using wildcards)')
args = parser.parse_args()

if __name__ == '__main__':
    main(args)
    print('Exiting...')