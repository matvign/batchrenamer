#!/usr/bin/env python3
import os
import re
import sys
from collections import deque

from natsort import natsorted, ns

from batchren import seqObj

BOLD = '\033[1m'
END = '\033[0m'

issues = {
    # issuecodes for rentable
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


def partfile(filepath):
    '''
    Split filepath into dir, base name and extension
    '''
    dirpath, filename = os.path.split(filepath)
    bname, ext = os.path.splitext(filename)
    # bname, ext = filename.split('.', 1)
    return (dirpath, bname, ext)


def joinpart(dirpath, bname, ext):
    '''
    Combine directory path, base name and extension.
    Remove spaces and dots on left and right side of extension.
    Collapse dots in extension.
    '''
    fname = bname.strip()
    if ext:
        ext = re.sub(r'\.+', '.', ext.replace(' ', '').strip('.'))
        fname += '.' + ext

    newname = fname
    if dirpath:
        newname = os.path.join(dirpath, fname)

    return (fname, newname)


def runfilters(filters, dirpath, bname):
    # function to run filters
    newname = bname
    for runf in filters:
        try:
            if isinstance(runf, seqObj.SequenceObj):
                newname = runf(newname, dirpath)
            else:
                newname = runf(newname)
        except re.error as re_err:
            sys.exit('bad regex: ' + re_err)

    return newname


def repl_decorator(pattern, repl='', repl_count=0):
    '''
    Return one of two different functions.
    1. Normal re.sub with exceptions.
    2. re.sub with counter that removes nth instance.
       Abuse function attributes for a counter.
    '''
    def replacer(matchobj):
        '''
        Function to be used with re.sub. Replace words only if count = count.
        Otherwise just replace with the match itself.
        '''
        if matchobj.group() and replacer.count == repl_count:
            ret = repl
        else:
            ret = matchobj.group()
        replacer.count += 1
        return ret
    replacer.count = 1

    def repl_nth(x):
        val = re.sub(pattern, replacer, x, repl_count)
        replacer.count = 1
        return val

    def repl_all(x):
        return re.sub(pattern, repl, x)

    return repl_all if not repl_count else repl_nth


def initfilters(args):
    # create filters in a list
    filters = []
    if args.regex:
        regex_repl = repl_decorator(*args.regex)
        filters.append(regex_repl)

    if args.slice:
        slash = lambda x: x[args.slice]
        filters.append(slash)

    if args.shave:
        shave = lambda x: x[args.shave[0]][args.shave[1]]
        filters.append(shave)

    if args.bracr:
        if args.bracr[0] == 'curly':
            reg_exp = re.compile(r'\{.*?\}')
        elif args.bracr[0] == 'round':
            reg_exp = re.compile(r'\(.*?\)')
        elif args.bracr[0] == 'square':
            reg_exp = re.compile(r'\[.*?\]')

        bracr = repl_decorator(reg_exp, '', args.bracr[1])
        filters.append(bracr)

    if args.translate:
        translmap = str.maketrans(*args.translate)
        translate = lambda x: x.translate(translmap)
        filters.append(translate)

    if args.spaces is not None:
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


def renfilter(args, files):
    '''
    Initialise filters and run them on filenames.
    Assign the new filename to a table of renames/conflicts.
    '''
    rentable = {
        'renames': {},
        'conflicts': {},
        'unresolvable': set()
    }
    fileset = set(files)

    filters = initfilters(args)
    for src in files:
        # split file into dir, basename and extension
        dirpath, bname, ext = partfile(src)
        bname = runfilters(filters, dirpath, bname)

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
        # file won't be renamed, assign to unresolvable
        errset.add(5)
        rentable['conflicts'][dest] = {'srcs': [src], 'err': errset}
        cascade(rentable, src)

    else:
        if dest not in fileset and os.path.exists(dest):
            # file exists but not in fileset, assign to unresolvable
            errset.add(5)

        if dest == src:
            # name hasn't changed, don't rename this
            errset.add(0)

        if bname == '':
            # name is empty, don't rename this
            errset.add(1)
        elif bname[0] == '.':
            # . is reserved in unix
            errset.add(2)

        if '/' in bname:
            # / usually indicates some kind of directory
            errset.add(3)

        if errset:
            rentable['conflicts'][dest] = {'srcs': [src], 'err': errset}
            cascade(rentable, src)

    if not errset:
        rentable['renames'][dest] = src


def cascade(rentable, target):
    '''
    If dest has an error, src won't be renamed.
    Mark src as unresolvable so nothing renames to it.
    Remove anything else that wants to rename to src.
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
    Print contents of rentable.
    For conflicts:
        if quiet: don't show error output
        if verbose: show detailed errors
        if verbose and no errors: show message
        if not verbose, no errors, show nothing
        if not verbose, errors, show unrenamable files
    Always show output for renames
    '''
    ren = rentable['renames']
    conf = rentable['conflicts']
    unres = rentable['unresolvable']

    if quiet:
        # do nothing if quiet
        pass

    elif verbose:
        print('{:-^30}'.format(BOLD + 'issues/conflicts' + END))
        if unres:
            # show detailed output if there were conflicts
            print('the following files have conflicts')
            if '' in conf:
                # bug with ns.path and empty values, instant crashes!!
                conflicts = natsorted(conf.items(), key=lambda x: x[0])
                conflicts = [conflicts[0], *natsorted(conflicts[1:], key=lambda x: x[0], alg=ns.PATH)]
            else:
                conflicts = natsorted(conf.items(), key=lambda x: x[0], alg=ns.PATH)

            for dest, obj in conflicts:
                srcOut = natsorted(obj['srcs'], alg=ns.PATH)
                print(', '.join([repr(str(e)) for e in srcOut]))
                print("--> '{}'\nerror(s): ".format(dest), end='')
                print(', '.join([issues[e] for e in obj['err']]), '\n')
        else:
            # otherwise show a message
            print('no conflicts found', '\n')

    elif unres:
        # don't show anything if there weren't conflicts
        # otherwise show files that can't be renamed
        print('{:-^30}'.format(BOLD + 'issues/conflicts' + END))
        print('the following files will NOT be renamed')
        print(*["'{}'".format(s) for s in natsorted(unres, alg=ns.PATH)], '', sep='\n')

    # always show this output
    # return list of tuples (dest, src) sorted by src
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
    msg = 'conflict detected, temporarily renaming'
    if args.dryrun:
        print('running with dryrun, files will NOT be renamed')
    while q:
        dest, src = q.popleft()
        if os.path.exists(dest):
            temp = getFreeFile(dest)
            if args.verbose or args.dryrun:
                print(msg, "'{}' to '{}'".format(src, temp))
            if not args.dryrun:
                rename_file(src, temp)
            q.append((dest, temp))
        else:
            # no conflict, just rename
            if args.verbose or args.dryrun:
                print("rename '{}' to '{}'".format(src, dest))
            if not args.dryrun:
                rename_file(src, dest)

    print('Finished renaming...')


def rename_file(src, dest):
    try:
        os.rename(src, dest)
    except OSError as err:
        sys.exit('An error occurred while renaming... ' + err)


def start_rename(args, fileset):
    rentable = renfilter(args, fileset)
    q = print_rentable(rentable, args.quiet, args.verbose)

    if q and askQuery('Proceed with renaming?'):
        run_rename(q, args)