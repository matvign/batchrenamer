#!/usr/bin/env python3

import argparse
import os
import glob

from collections import deque, OrderedDict

from _version import __version__
import renamer


#   glob into directories e.g. dir/ -> dir/*
def expanddir(dir):
    if dir[-1] == '/':
        return dir + '*'

    return dir


#   give information about what to rename
#   return the things that can be renamed
def printinfotable(infotable):
    ren  = infotable['renames']
    conf = infotable['conflicts']

    sconf = OrderedDict(sorted(ren.items(), key=lambda x:x[0]))
    for n in sconf:
        sconf[n].sort()
        if len(sconf[n]) == 1:
            print('[{}] no filters applied'.format(n))
        else:
            print('[{}] conflicting rename with {}'.format())

    sren = sorted(ren.items(), key=lambda x:x[1])
    for n in sren:
        print('[{}] rename to [{}]'.format(n[1], n[0]))

    return sren


def main(args):
    #   set of affirmative inputs
    confirmset = set(['yes', 'ye', 'y', ''])

    print("searching files...", ' ')
    #   exclude directories
    filelist = [f for f in glob.glob(args.dir) if os.path.isfile(f)]
    filelist = sorted(filelist)

    if args.debug:
        print(args)

    #   table of original -> rename
    rentable = renamer.renlist(args, filelist)

    #   summarise things to rename, conflicts, etc
    infotable = geninfotable(rentable)


def geninfotable(rentable):
    infotable = {
        'renames': {
            #   dest: src
        },
        'conflicts': {
            #   dest: [srcs]
        }
    }

    for n in rentable:
        if n[1] in infotable['conflicts']:
            #   if this name is in conflict already
            #   add n[0] to infotable['conflicts'][n[1]]
            infotable['conflicts'][n[1]].extend([n[0]])

        elif n[1] in infotable['renames']:
            #   if something else wants this name already
            #   invalidate both
            temp = infotable['renames'][n[1]]
            del infotable['renames'][n[1]]
            infotable['conflicts'][n[1]] = [temp, n[0]]

        else:
            if n[0] == n[1]:
                #   no change, move it to conflicts
                infotable['conflicts'][n[1]] = [n[0]]
            else:
                #   move to renames (until potentially removed)
                infotable['renames'][n[1]] = [n[0]]

    return infotable


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
parser.add_argument('-c', '--case', choices=['upper', 'lower', 'swap', 'cap'],
                    metavar='',
                    help='convert filename case (upper/lower/swap/cap)')
parser.add_argument('-bracs', '--bracket-style', choices=['round', 'square'],
                    metavar='',
                    help='convert bracket style (round/square)')
parser.add_argument('-bracr', '--bracket-remove', action='store_true',
                    help='remove brackets and their contents')
parser.add_argument('-app', '--append', metavar='STR',
                    help='append string to filename')
parser.add_argument('-pre', '--prepend', metavar='STR',
                    help='prepend string to filename')
parser.add_argument('-enum', '--enumerate', nargs=1,
                    help='append number to end of file')
parser.add_argument('-ext', '--extension', metavar='EXT',
                    help="change last file extension (e.g. mp4, '')")
parser.add_argument('-re', '--regex', action='store_true',
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
