#!/usr/bin/env python3

import argparse
import os
import glob
from collections import deque, OrderedDict

from _version import __version__
import renamer


def query_yes_no(question, default="yes"):
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False, "q": False }

    if default is None:
        prompt = "[y/n] "
    elif default == "yes":
        prompt = "[Y/n] "
    elif default == "no":
        prompt = "[y/N] "
    else:
        raise ValueError('invalid default answer: {}'.format(default))

    while True:
        print(question, prompt, end='')
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            print("Please respond with 'yes' or 'no'")


'''
print out contents of rentable, showing files that can be
safely renamed and files that are in conflict.
sort contents for display reasons.
return sorted contents of what can be renamed (produces tuples)
'''
def display_rentable(rentable, quiet):
    ren  = rentable['renames']
    conf = rentable['conflicts']

    # do not show if quiet
    # use an ordereddict to sort naming conflicts
    # i.e. c,b,a --> a,b,c want to be renamed to d
    if not quiet:
        print('\n{:-^30}'.format('issues/conflicts'))
        sconf = OrderedDict(sorted(conf.items(), key=lambda x:x[0]))
        
        if sconf:
            print('the following files will not be renamed')
        else:
            print('no conflicts found')

        for n in sconf:
            sconf[n].sort()
            if len(sconf[n]) == 1:
                print('{} no filters applied'.format(sconf[n]))
            else:
                print('{} conflicting rename with [{}]'.format(sconf[n], n))
        print()

    # always show this
    # produce tuples sorted by original names (src)
    print('{:-^30}'.format('rename'))
    sren = sorted(ren.items(), key=lambda x:x[1])
    if sren:
        print('the following files can be renamed:')
    else:
        print('no files to rename')

    for dest, src in sren:
        print('[{}] rename to [{}]'.format(src, dest))
    print()

    return sren


def run_rename(queue):
    q = queue
    while q:
        dest, src = q.popleft()
        if os.path.exists(dest):
            if args.verbose:
                print('conflict detected... ', end='')
            count = 1
            while(True):
                if os.path.exists(dest+'_'+str(count)):
                    count += 1
                else:
                    temp = dest + '_' + str(count)
                    if args.verbose:
                        print('temporarily renaming {} to {}'.format(src, temp))
                    os.rename(src, temp)
                    q.append((dest, temp))
                    break
        else:
            # no conflict, just rename
            if args.verbose and not \
                query_yes_no('rename [{}] to [{}]?'.format(src, dest)):
                next
            os.rename(src, dest)

    print('rename complete!')


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
        for n in sorted(fileset):
            print('    {}'.format(n))

    # run filters and get output in form of a table
    rentable = renamer.renfilter(args, fileset)

    # print contents of rentable and create a queue from it
    q = deque(display_rentable(rentable, args.quiet))
    
    if q and query_yes_no('Proceed with renaming?'):
        # start renaming if q non-empty and answer is yes
        run_rename(q)


# glob into directories e.g. dir/ -> dir/*
def expanddir(dir):
    if dir[-1] == '/':
        return dir + '*'
    elif os.path.isdir(dir):
        return os.path.join(dir, '*')

    return dir


def uniq_separator(separator):
    sepr, repl = separator[0], separator[1]
    if sepr == repr:
        msg = 'both choices must be unique'
        raise argparse.ArgumentTypeError(msg)

    return separator


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
    prefix_chars='-',
    fromfile_prefix_chars='@'
)
outgroup = parser.add_mutually_exclusive_group()
bracgroup = parser.add_mutually_exclusive_group()

parser.add_argument('-sp', '--spaces', nargs='?', const='.', metavar='REPL',
                    help='replace whitespaces with specified (default: .)')
parser.add_argument('-sep', '--separator', nargs=2, 
                    choices=['space', 'dot', 'underscore', 'dash', 'bar'],
                    metavar='',
                    help="replace dot, space, underscore, dash or bar with another")
parser.add_argument('-c', '--case', choices=['upper', 'lower', 'swap', 'cap'],
                    metavar='',
                    help='convert filename case (upper/lower/swap/cap)')
bracgroup.add_argument('-bracs', '--bracket-style', choices=['round', 'square'],
                    metavar='',
                    help='convert bracket style (round/square)')
bracgroup.add_argument('-bracr', '--bracket-remove', action='store_true',
                    help='remove brackets and their contents')
parser.add_argument('-pre', '--prefix', metavar='STR',
                    help='prepend string to filename')
parser.add_argument('-post', '--postfix', metavar='STR',
                    help='append string to filename')
parser.add_argument('-enum', '--enumerate', nargs='?', type=int, const=1,
                    help='append number to end of files')
parser.add_argument('-ext', '--extension', metavar='EXT',
                    help="change last file extension (e.g. mp4, '')")
parser.add_argument('-re', '--regex', action='store_true',
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