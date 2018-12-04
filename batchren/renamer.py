#!/usr/bin/env python3
import os
import re
import sys
from collections import deque, OrderedDict

from natsort import natsorted, ns

from batchren.seqObj import SequenceObj

BOLD = '\033[1m'
END = '\033[0m'

# issuecodes for printing rentable
issues = {
    0: 'no filters applied',
    1: 'new name cannot be empty',
    2: 'new name cannot start with .',
    3: 'new name cannot contain /',
    4: 'shared name conflict',
    5: 'unresolvable conflict'
}


def askQuery(question):
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False, "q": False}

    while True:
        print(question, "[y/n] ", end='')
        choice = input().lower()
        if choice == '':
            return True
        elif choice in valid:
            return valid[choice]
        else:
            print("Please respond with 'yes' or 'no'")


# split filepath into dir, basename and extension
def partfile(filepath):
    dirpath, filename = os.path.split(filepath)
    bname, ext = os.path.splitext(filename)
    return (dirpath, bname, ext)


# recombine dir, basename and extension
def joinpart(dirpath, bname, ext):
    fname = bname.strip()
    if ext:
        ext = ext.replace(' ', '').strip('.')
        ext = '.' + re.sub(r'\.+', '.', ext)
        fname += ext

    newname = fname
    if dirpath:
        newname = os.path.join(dirpath, fname)

    return (fname, newname)


# function to run filters
def runfilters(filters, dirpath, filename):
    newname = filename
    for runf in filters:
        if isinstance(runf, SequenceObj):
            runf.update_curdir(dirpath)
            newname = runf(filename)
        else:
            newname = runf(filename)

    return newname


# create filters in a list
def initfilters(args):
    filters = []
    if args.regex:
        reg = re.compile(args.regex[0])
        regex_re = lambda x: re.sub(reg, args.regex[1], x)
        filters.append(regex_re)

    if args.slice:
        slash = lambda x: x[args.slice]
        filters.append(slash)

    # note: find better method to remove brackets
    if args.bracr:
        brac_re = re.compile(r'[\{\[\(].*?[\{\]\)]')
        brac_trans = str.maketrans('', '', '{}[]()')
        bracrf = lambda x: re.sub(brac_re, '', x).translate(brac_trans)
        filters.append(bracrf)

    if args.translate:
        translmap = str.maketrans(*args.translate)
        translate = lambda x: x.translate(translmap)
        filters.append(translate)

    if args.spaces:
        space = lambda x: x.replace(' ', args.spaces)
        filters.append(space)

    if args.case:
        if args.case == 'upper':
            case = lambda x: x.upper()
        elif args.case == 'lower':
            case = lambda x: x.lower()
        elif args.case == 'swap':
            case = lambda x: x.swapcase()
        elif args.case == 'cap':
            case = lambda x: str.title(x)
        filters.append(case)

    if args.sequence:
        filters.append(args.sequence)

    if args.prepend:
        prepend = lambda x: args.prepend + x
        filters.append(prepend)

    if args.postpend:
        postpend = lambda x: x + args.postpend
        filters.append(postpend)

    return filters


def renfilter(args, fileset):
    # create table of renames/conflicts
    rentable = {
        'renames': {},
        'conflicts': {},
        'unresolvable': set()
    }

    filters = initfilters(args)
    for src in natsorted(fileset, alg=ns.PATH):
        # split file into dir, basename and extension
        dirpath, bname, ext = partfile(src)
        for runf in filters:
            bname = runf(bname)

        # change extension, allow empty extensions
        if args.extension is not None:
            ext = args.extension

        # recombine as file+ext, path+file+ext
        bname, dest = joinpart(dirpath, bname, ext)
        assign_rentable(rentable, fileset, dest, bname, src)

    return rentable


def assign_rentable(rentable, fileset, dest, bname, src):
    errset = set()
    if dest in rentable['conflicts']:
        # this name is already in conflict, add src to conflicts
        rentable['conflicts'][dest]['srcs'].append(src)
        rentable['conflicts'][dest]['err'].add(4)
        errset = rentable['conflicts'][dest]['err']
        cascade(rentable, src)

    elif dest in rentable['renames']:
        # this name is taken, invalidate both names
        if dest == src:
            errset.add(0)
        errset.add(4)

        temp = rentable['renames'][dest]
        del rentable['renames'][dest]
        rentable['conflicts'][dest] = {'srcs': [temp, src], 'err': errset}
        for n in rentable['conflicts'][dest]['srcs']:
            cascade(rentable, n)

    elif dest in rentable['unresolvable']:
        # add dest that tries to rename to something that won't
        # be renamed
        errset.add(5)
        rentable['conflicts'][dest] = {'srcs': [src], 'err': errset}
        cascade(rentable, src)

    else:
        if dest not in fileset and os.path.exists(dest):
            # name exists and not in files found
            # which means it won't be renamed
            errset.add(4)

        if dest == src:
            errset.add(0)

        if bname == '':
            errset.add(1)

        if bname[0] == '.':
            errset.add(2)

        if '/' in bname:
            errset.add(3)

        if errset:
            rentable['conflicts'][dest] = {'srcs': [src], 'err': errset}
            cascade(rentable, src)

    if not errset:
        rentable['renames'][dest] = src


def cascade(rentable, target):
    '''
    when a conflict occurs the src can't be renamed.
    we need to render src unusable for anything that wants to
    rename to src, which can't be renamed.
    include src in rentable['unresolvable'] and add anything
    that renames to src
    '''
    ndest = target
    while True:
        rentable['unresolvable'].add(ndest)
        if ndest in rentable['renames']:
            temp = rentable['renames'][ndest]
            del rentable['renames'][ndest]
            rentable['conflicts'][ndest] = {'srcs': [temp], 'err': {5}}
            ndest = temp
            continue
        return


def print_rentable(rentable, quiet=False, verbose=False):
    '''
    print out contents of rentable, showing files that can be
    safely renamed and files that are in conflict.
    sort contents for display reasons.
    return sorted contents of what can be renamed (produces tuples)
    '''

    ren = rentable['renames']
    conf = rentable['conflicts']
    unres = rentable['unresolvable']

    if quiet:
        # do nothing if quiet
        pass

    elif verbose:
        print('{:-^30}'.format(BOLD + 'issues/conflicts' + END))
        print('the following files will NOT be renamed')
        if unres:
            # show detailed output if there were conflicts
            conflicts = OrderedDict(natsorted(conf.items(), key=lambda x: x[0], alg=ns.PATH))
            for dest, obj in conflicts.items():
                srcOut = natsorted(obj['srcs'], alg=ns.PATH)
                print(', '.join([repr(str(e)) for e in srcOut]))
                print("--> '{}'\nerrors: ".format(dest), end='')
                print(', '.join([issues[e] for e in obj['err']]), '\n')
        else:
            # otherwise show a message
            print('no conflicts found', '\n')

    elif unres:
        # don't show anything if there weren't conflicts
        # otherwise show files that can't be renamed
        print('{:-^30}'.format(BOLD + 'issues/conflicts' + END))
        print('the following files will NOT be renamed')
        print(*["'{}'".format(s) for s in sorted(unres)], sep='\n')
        print()

    # always show this output
    # produces tuples (dest, src) sorted by src
    print('{:-^30}'.format(BOLD + 'rename' + END))
    renames = natsorted(ren.items(), key=lambda x: x[1], alg=ns.PATH)
    if renames:
        print('the following files can be renamed:')
        for dest, src in renames:
            print("'{}' rename to '{}'".format(src, dest))
    else:
        print('no files to rename')
    print()

    return renames


def getFreeFile(dest):
    count = 1
    while(True):
        temp = dest + '_' + str(count)
        if os.path.exists(temp):
            count += 1
            continue
        return temp


def run_rename(queue, args):
    q = deque(queue)
    while q:
        dest, src = q.popleft()
        if os.path.exists(dest):
            temp = getFreeFile(dest)

            if args.verbose:
                print("conflict detected, temporarily renaming '{}' to '{}'".format(src, temp))
            rename_file(src, temp)
            q.append((dest, temp))
        else:
            # no conflict, just rename
            rename_file(src, dest)

    print('Finished renaming...')


def rename_file(src, dest):
    try:
        os.rename(src, dest)
    except Exception as err:
        # continue renaming other files if error
        print('A fatal error occurred...', err)
        sys.exit(1)


def start_rename(args, fileset):
    rentable = renfilter(args, fileset)
    q = print_rentable(rentable, args.quiet, args.verbose)

    if q and askQuery('Proceed with renaming?'):
        run_rename(q, args)