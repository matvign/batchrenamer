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


def query_yes_no(default="yes"):
    question = 'Proceed with renaming?'
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False, "q": False }

    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError('invalid default answer: {}'.format(default))

    while True:
        print(question, prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            print("Please respond with 'yes' or 'no'")


def gen_infotable(rentable):
    #   dest is what we rename to
    infotable = {
        'renames': {
            #   dest: src
        },
        'conflicts': {
            #   dest: [srcs]
        }
    }

    for src, dest in rentable:
        if dest in infotable['conflicts']:
            #   if this name is in conflict already
            #   add src to infotable['conflicts'][dest]
            infotable['conflicts'][dest].extend([src])

        elif dest in infotable['renames']:
            #   if something else wants this name invalidate both
            temp = infotable['renames'][dest]
            del infotable['renames'][dest]
            infotable['conflicts'][dest] = [temp, src]

        else:
            if src == dest:
                #   no change, move it to conflicts
                infotable['conflicts'][dest] = [src]
            else:
                #   add to renames (until potentially removed)
                infotable['renames'][dest] = src

    return infotable


'''
show naming conflicts and things that can be renamed
return what can be renamed
'''
def print_infotable(infotable, quiet):
    ren  = infotable['renames']
    conf = infotable['conflicts']

    #   do not show if quiet
    #   use an ordereddict to sort naming conflicts
    #   i.e. c,b,a --> a,b,c want to be renamed to d
    if not quiet:
        print('\n{:-^30}\nThe following files will not be renamed:'\
            .format('issues/conflicts'))
        sconf = OrderedDict(sorted(conf.items(), key=lambda x:x[0]))
        for n in sconf:
            sconf[n].sort()
            if len(sconf[n]) == 1:
                print('{} no filters applied'.format(sconf[n]))
            else:
                print('{} conflicting rename with [{}]'.format(sconf[n], n))
        print()

    #   always show this
    #   sort by values. note that values are original filenames
    #   produces a tuple
    print('{:-^30}\nThe following files will be renamed:'.format('rename'))
    sren = sorted(ren.items(), key=lambda x:x[1])
    for n in sren:
        print('{} rename to [{}]'.format(n[1], n[0]))
    print()

    return sren


def main(args):
    #   exclude directories
    filelist = [f for f in glob.glob(args.dir) if os.path.isfile(f)]
    filelist = sorted(filelist)
        
    #   show arguments used
    if args.verbose:
        print('{:-^30}'.format('arguments'))
        argdict = sorted(vars(args).items())
        for k, v in argdict:
            if v:
                print('{:4}{}: {}'.format('', k, v))
        print()

    #   do not show this if args.quiet
    #   i.e. everything else sees this except quiet
    if not args.quiet:
        print('{:-^30}'.format('files found'))
        for n in filelist:
            print('{:4}{}'.format('',n))

    #   get table of original -> rename
    #   analyse to find things that have to be renamed and conflicts
    rentable = renamer.renlist(args, filelist)
    infotable = gen_infotable(rentable)

    #   print contents of infotable and create a queue from it
    d = deque(print_infotable(infotable, args.quiet))

    if not d:
        print('nothing to rename\nexiting...')
    else:
        #   get prompt
        query_yes_no()

        #   start renaming
        pass


'''
Argparse options
fromfile_prefix_chars='@', allow arguments from file input
prefix_chars='-', only allow arguments with minus (default)
'''

parser = argparse.ArgumentParser(
    prog='pyren',
    usage='%(prog)s [options]',
    description='Python Batch Renamer - a script for renaming files',
    epilog='Current version: v' + __version__,
    prefix_chars='-'
)
group = parser.add_mutually_exclusive_group()

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
group.add_argument('-q', '--quiet', action='store_true',
                    help='skip output, but show confirmations')
group.add_argument('-v', '--verbose', action='store_true',
                    help='show detailed output')
parser.add_argument('--console', action='store_true',
                    help='use interactive console')
parser.add_argument('--version', action='version', version=__version__)
parser.add_argument('dir', nargs='?', default='*', type=expanddir,
                    help='target directory (use quotes if using wildcards)')
args = parser.parse_args()

if __name__ == '__main__':
    main(args)
