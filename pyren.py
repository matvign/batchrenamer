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

    #   process files for potential renaming
    renlist = renamer.renlist(args, filelist)
    print(tabulate(renlist, headers=["Status", "Original", "Rename"]))

    #   list of files that need to be renamed
    renames = [x for x in renlist if x[0] == 1]
    print(renames)

'''
Argparse options
fromfile_prefix_chars='@', allow arguments from file input
prefix_chars='-', only allow arguments with minus (default)
'''

parser = argparse.ArgumentParser(
    prog='pyren',
    usage='%(prog)s [options]',
    description='PyRen - a script for renaming files',
    epilog='Current version: v' + __version__,
    prefix_chars='-'
)

parser.add_argument('-sp', '--spaces', nargs='?', const='.', metavar='REPL',
                    help='replace whitespaces with specified (default: .)')
parser.add_argument('-sep', '--separator', nargs=2, 
                    choices=['space', 'dot', 'underscore', 'dash', 'bar'],
                    metavar='',
                    help="replace dot, space, underscore, dash or bar with another")
parser.add_argument('-case', '--case', choices=['upper', 'lower', 'swap', 'cap'],
                    metavar='',
                    help='convert filename case (upper/lower/swap/cap)')
parser.add_argument('-brac-s', '--bracket-style', choices=['round', 'square'],
                    metavar='',
                    help='convert bracket style (round/square)')
parser.add_argument('-brac-r', '--bracket-remove', action='store_true',
                    help='remove brackets and their contents')
parser.add_argument('-app', '--append', metavar='STR',
                    help='append string to filename')
parser.add_argument('-pre', '--prepend', metavar='STR',
                    help='prepend string to filename')
parser.add_argument('-enum', '--enumerate', nargs=1,
                    help='append number to end of file')
parser.add_argument('-ext', '--extension', metavar='EXT',
                    help="change last file extension (e.g. mp4, '')")
parser.add_argument('-regex', '--regex', action='store_true',
                    help='specify regex for renaming')
parser.add_argument('-q', '--quiet', action='store_true',
                    help='skip output, but show confirmations')
parser.add_argument('-v', '--verbose', action='store_true',
                    help='show detailed output')
parser.add_argument('--console', action='store_true',
                    help='use interactive console')
parser.add_argument('--debug', action='store_true',
                    help='show simulated output without renaming')
parser.add_argument('--version', action='version', version=__version__)
parser.add_argument('dir', nargs='?', default='*', type=expanddir,
                    help='target directory (use quotes if using wildcards)')
args = parser.parse_args()

if __name__ == '__main__':
    main(args)
