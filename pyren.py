#!/usr/bin/env python3

import argparse
import os
import sys

import glob

from tabulate import tabulate
from _version import __version__
import renamer


#   glob into directories e.g. dir/ -> dir/*
def expanddir(dir):
    if dir[-1] == '/':
        return dir + '*'

    return dir


def main(args):
    #   set of affirmative inputs
    confirmset = set(['yes', 'ye', 'y', ''])

    #   only include files
    filelist = [f for f in glob.glob(args.dir) if os.path.isfile(f)]
    filelist = sorted(filelist)

    if args.debug:
        print(args)
        print(filelist)
        return

    return

    renlist = renamer.renlist(args, filelist)

    #   check for renaming conflicts and
    #   report in a table.
    conflicts = tabulate(renlist, headers="keys")
    renames = tabulate(renlist, headers="keys")


'''
Argparse options
fromfile_prefix_chars='@', allow arguments from file input
prefix_chars='-', only allow arguments with minus (default)
'''

parser = argparse.ArgumentParser(
    prog='pyRen',
    usage='%(prog)s [options]',
    description='PyRen - a script for renaming files',
    epilog='Current version: v' + __version__,
    prefix_chars='-'
)

parser.add_argument('-sp', '--spaces', nargs='?', const='_', metavar='REPL',
                    help='replace whitespaces (default: _)')
parser.add_argument('-case', '--case', choices=['upper', 'lower', 'swap', 'cap'],
                    help='convert filenames to upper/lower case')
parser.add_argument('-brac-s', '--bracket-style', choices=['round', 'square'],
                    help='convert bracket style')
parser.add_argument('-app', '--append', metavar='STR',
                    help='append string to filename')
parser.add_argument('-pre', '--prepend', metavar='STR',
                    help='prepend string to filename')
parser.add_argument('-ext', '--extension', metavar='EXT',
                    help="change last file extension (e.g. mp4, '')")
parser.add_argument('-r', '--recursive', action='store_true',
                    help='allow recursive file searching (use with **)')
parser.add_argument('--debug', action='store_true',
                    help='show input arguments')
parser.add_argument('-q', '--quiet', action='store_true',
                    help='skip output, but show confirmations')
parser.add_argument('-v', '--verbose', action='store_true',
                    help='show detailed output')
parser.add_argument('--version', action='version', version=__version__)
parser.add_argument('dir', nargs='?', default='*', type=expanddir,
                    help='target directory (use quotes if wildcards)')
args = parser.parse_args()

if __name__ == '__main__':
    main(args)
