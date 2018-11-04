#!/usr/bin/env python3
import os
import re
from collections import deque, OrderedDict

from natsort import natsorted, ns


# errorcodes for printing rentable
issues = {
    0: 'no filters applied',
    1: 'name cannot be empty',
    2: 'name cannot start with .',
    3: 'name cannot start with /',
    4: 'multiple names conflicting',
    5: 'file already exists'
}


class seqObj:
    def __init__(self, curdir='', optstr='', minval=1, mode=1):
        self.min = int(minval)
        self.count = minval
        self.curdir = curdir
        self.optstr = optstr
        self.mode = mode

    def __call__(self, inputdir, bname):
        if inputdir != self.curdir:
            self.curdir = inputdir
            self.count = self.min

        if self.mode:
            new_name = '{}{}{:02d}'.format(bname, self.optstr, self.count)
        else:
            new_name = '{:02d}{}{}'.format(self.count, self.optstr, bname)
        self.count += 1
        return new_name


def askQuery(question, default="yes"):
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


# split filepath into dir, basename and extension
def partfile(filepath):
    dirpath, filename = os.path.split(filepath)
    bname, ext = os.path.splitext(filename)
    return (dirpath, bname, ext[1:])


# recombine dir, basename and extension
def joinpart(dirpath, bname, ext):
    newname = bname

    # join truthy extension with file name
    if ext:
        newname += '.' + ext

    # join truthy dirpath with file name
    # otherwise, the new name is just the file itself
    if dirpath:
        newname = os.path.join(dirpath, newname)

    return newname


# function to run filters
def runfilters(filters, dirpath, filename):
    newname = filename
    for runf in filters:
        if isinstanceof(runf, seqObj):
            newname = runf(dirpath, filename)
        else:
            newname = runf(filename)

    return newname


# create filters in a list
def initfilters(args):
    filters = []

    if args.regex:
        reg_expr = re.compile(args.regex[0])
        regex_re = lambda x: re.sub(reg_expr, args.regex[1], x)
        filters.append(regex_re)

    if args.slice:
        slash = lambda x: x[args.slice]
        filters.append(slash)

    # args.shave

    # args.sequence

    if args.translate:
        translmap = str.maketrans(*args.translate)
        translate = lambda x: x.translate(translmap)
        filters.append(translate)

    if args.spaces:
        space = lambda x: x.replace(' ', args.spaces)
        filters.append(space)

    # note: find better method to remove brackets
    if args.bracket_remove:
        brac_re = re.compile(r'[\{\[\(].*?[\{\]\)]')
        brac_trans = str.maketrans('', '', '{}[]()')
        bracr = lambda x: re.sub(brac_re, '', x).translate(brac_trans)
        filters.append(bracr)

    if args.case:
        if args.case == 'upper':
            case = lambda x: x.upper()
        elif args.case == 'lower':
            case = lambda x: x.lower()
        elif args.case == 'swap':
            case = lambda x: x.swapcase()
        elif args.case == 'cap':
            # capitalise every word
            # e.g. hello world -> Hello World
            case = lambda x: str.title(x)
        filters.append(case)

    if args.prefix:
        prefix = lambda x: args.prefix+x
        filters.append(prefix)

    if args.postfix:
        postfix = lambda x: x+args.postfix
        filters.append(postfix)

    return filters


def renfilter(args, fileset):
    # create table of renames/conflicts
    rentable = {
        'renames': {
            # dest: src
        },
        'conflicts': {
            # dest: {
            #   srcs: [src]
            #   err: {} set of issue codes
            # }
        }
    }

    filters = initfilters(args)
    for src in natsorted(fileset, alg=ns.PATH):

        # split filepath into dir, basename and extension
        dirpath, bname, ext = partfile(src)

        # run filters on the basename
        for runf in filters:
            bname = runf(bname)

        # change extension, allow empty extensions
        if args.extension is not None:
            ext = args.extension

        # remove whitespace on left and right
        bname = bname.strip()
        ext   = ext.strip()

        # recombine file names
        dest = joinpart(dirpath, bname, ext)

        # place entry into the right place
        if dest in rentable['conflicts']:
            # this name is already in conflict
            # add src to conflicts
            rentable['conflicts'][dest]['srcs'].append(src)
            rentable['conflicts'][dest]['err'].add(4)

        elif dest in rentable['renames']:
            # this name is taken, invalidate both names
            temp = rentable['renames'][dest]
            del rentable['renames'][dest]
            rentable['conflicts'][dest] = {'srcs': [temp, src], 'err': {4}}

        elif dest == src:
            # no filters applied, move to conflicts
            rentable['conflicts'][dest] = {'srcs': [src], 'err': {0}}

        elif bname == '':
            # disallow empty names
            rentable['conflicts'][dest] = {'srcs': [src], 'err': {1}}

        elif bname[0] == '.':
            # disallow names starting with '.'
            rentable['conflicts'][dest] = {'srcs': [src], 'err': {2}}

        elif bname[0] == '/':
            # disallow names starting with '/'
            rentable['conflicts'][dest] = {'srcs': [src], 'err': {3}}

        else:
            if os.path.exists(dest) and dest not in fileset:
                # name already exists and not in files found.
                # this is is an unresolvable conflict
                # dirs and hidden files aren't included in fileset
                rentable['conflicts'][dest] = { 'srcs': [src], 'err':[5]}
            else:
                # if file doesn't exist, then safe to rename
                # if file exists, but is in fileset, then this could
                # be a resolvable renaming conflict.
                # i.e. if file "dest" is being renamed to something else,
                # this operation should be safe.
                rentable['renames'][dest] = src

    return rentable


'''
print out contents of rentable, showing files that can be
safely renamed and files that are in conflict.
sort contents for display reasons.
return sorted contents of what can be renamed (produces tuples)
'''
def print_rentable(rentable, quiet, verbose):
    ren  = rentable['renames']
    conf = rentable['conflicts']

    if not quiet:
        # skip this if quiet
        print('{:-^30}'.format('issues/conflicts'))
        conflicts = OrderedDict(natsorted(conf.items(), key=lambda x:x[0], alg=ns.PATH))
        if conflicts:
            print('the following files will NOT be renamed')
        else:
            print('no conflicts found')

        for dest, obj in conflicts.items():
            srcOut = natsorted(obj['srcs'], alg=ns.PATH)

            for s in srcOut:
                print("'{}'".format(s), end=' ')
                if verbose:
                    # show the erroneous dest file
                    print(" --> '{}'".format(dest))
                else:
                    print()

            if verbose:
                # give reasons for why this can't be renamed
                errLst = ', '.join([issues[e] for e in obj['err']])
                print('    {}'.format(errLst))
        print()

    # always show this output
    # produces tuples (dest, src) sorted by src
    print('{:-^30}'.format('rename'))
    renames = natsorted(ren.items(), key=lambda x:x[1], alg=ns.PATH)
    if renames:
        print('the following files can be renamed:')
    else:
        print('no files to rename')

    for dest, src in renames:
        print("'{}' rename to '{}'".format(src, dest))
    print()

    return renames


def getFreeFile(dest):
    count = 1
    while(True):
        temp = dest + ' ' + str(count)
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
                print("conflict detected, temporarily \
                    renaming '{}' to '{}'".format(src, temp))
            if rename_file(src, temp):
                q.append((dest, temp))
        else:
            # no conflict, just rename
            if args.verbose and not \
                askQuery("rename ['{}'] to ['{}']?".format(src, dest)):
                continue
            rename_file(src, dest)

    print('Finished renaming...')


def rename_file(src, dest):
    try:
        os.rename(src, dest)
    except Exception as err:
        # continue renaming other files if error
        # print(err)
        print('An error, skipping this file...')
        return False
    else:
        return True


def start_rename(args, fileset):
    rentable = renfilter(args, fileset)
    q = print_rentable(rentable, args.quiet, args.verbose)

    if q and askQuery('Proceed with renaming?'):
        run_rename(q, args)