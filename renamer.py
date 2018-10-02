#!/usr/bin/env python3
import os
import re
from collections import deque, OrderedDict

from natsort import natsorted, ns


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


# split filepath into dir, basename and extension
def partfile(filepath):
    dirpath, filename = os.path.split(filepath)
    bname, ext = os.path.splitext(filename)
    return (dirpath, bname, ext[1:])


# recombine dir, basename and extension
def joinpart(dirpath, bname, ext):
    newname = bname

    # join non-null extension with file name
    if ext:
        newname += '.' + ext

    # join non-null dirpath with file name
    # otherwise, the new name is just the file itself
    if dirpath:
        newname = os.path.join(dirpath, newname)

    return newname


# function to run filters
def runfilters(filters, filename):
    newname = filename
    for runf in filters:
        newname = runf(newname)

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
            # dest: [srcs]
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
            # this name is already in conflicts
            # add src to conflicts
            rentable['conflicts'][dest].append(src)

        elif dest in rentable['renames']:
            # this name is taken, invalidate both names
            temp = rentable['renames'][dest]
            del rentable['renames'][dest]
            rentable['conflicts'][dest] = [temp, src]

        else:
            if dest == '':
                # filename is empty, move to conflicts
                rentable['conflicts'][dest] = [src]

            elif dest == '.' or dest == '..':
                # filename is . or .., move to conflicts
                rentable['conflicts'][dest] = [src]

            elif dest == src:
                # no filters applied, move to conflicts
                rentable['conflicts'][dest] = [src]

            else:
                if os.path.exists(dest) and dest not in fileset:
                    # name already exists and not in files found
                    # dirs are never included in fileset
                    # so files will never be renamed to dirs
                    # since file won't be renamed, auto conflict
                    rentable['conflicts'][dest] = [src]
                else:
                    # if file exists, then we haven't processed it yet
                    # just move it to renames and let the above handle it
                    # if file doesn't exist, add to renames
                    rentable['renames'][dest] = src

    return rentable


'''
print out contents of rentable, showing files that can be
safely renamed and files that are in conflict.
sort contents for display reasons.
return sorted contents of what can be renamed (produces tuples)
'''
def print_rentable(rentable, quiet):
    ren  = rentable['renames']
    conf = rentable['conflicts']

    # do not show if quiet
    # use an ordereddict to sort naming conflicts
    # i.e. c,b,a --> a,b,c want to be renamed to d
    if not quiet:
        print('{:-^30}'.format('issues/conflicts'))
        conflicts = OrderedDict(natsorted(conf.items(), key=lambda x:x[0], alg=ns.PATH))
        if conflicts:
            print('the following files will not be renamed')
        else:
            print('no conflicts found')
        
        for dest, srcs in conflicts.items():
            if dest == '':
                print('cannot rename {} to empty string'.format(natsorted(srcs, alg=ns.PATH)))
            elif dest == '.' or dest == '..':
                print('cannot rename {} to dot files'.format(natsorted(srcs, alg=ns.PATH)))
            else:
                if len(srcs) == 1:
                    print('{} no filters applied'.format(srcs))
                else:
                    print('{} conflicting rename with [\'{}\']'.format(natsorted(srcs, alg=ns.PATH), dest))
        print()

    # always show this
    # produces tuples sorted by original names (src)
    print('{:-^30}'.format('rename'))
    renames = natsorted(ren.items(), key=lambda x:x[1], alg=ns.PATH)
    if renames:
        print('the following files can be renamed:')
    else:
        print('no files to rename')

    for dest, src in renames:
        print('[\'{}\'] rename to [\'{}\']'.format(src, dest))
    print()

    return renames


def run_rename(queue, args):
    q = queue
    while q:
        dest, src = q.popleft()
        if os.path.exists(dest):
            if args.verbose:
                print('conflict detected... ', end='')
            count = 1
            while(True):
                temp = dest + ' ' + str(count)
                if os.path.exists(temp):
                    count += 1
                else:
                    if args.verbose:
                        print('temporarily renaming \'{}\' to \'{}\''.format(src, temp))
                    os.rename(src, temp)
                    q.append((dest, temp))
                    break
        else:
            # no conflict, just rename
            if args.verbose and not \
                query_yes_no('rename [\'{}\'] to [\'{}\']?'.format(src, dest)):
                next
            os.rename(src, dest)

    print('rename complete!')


def start_rename(args, fileset):
    rentable = renfilter(args, fileset)
    q = deque(print_rentable(rentable, args.quiet))

    if q and query_yes_no('Proceed with renaming?'):
        run_rename(q, args)