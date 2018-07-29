#!/usr/bin/env python3

import re
from os import path


# split filepath into dir, basename and extension
def partfile(filepath):
    dirpath, filename = path.split(filepath)
    bname, ext = path.splitext(filename)
    return (dirpath, bname, ext[1:])


# recombine dir, basename and extension
def combinepart(dirpath, bname, ext):
    newname = bname

    # join non-null extension with file name
    if ext:
        newname += '.' + ext

    # join non-null dirpath with file name
    # otherwise, the new name is just the file itself
    if dirpath:
        newname = path.join(dirpath, newname)

    return newname


# function to run filters
def runfilters(filters, filename):
    newname = filename
    for runf in filters:
        newname = runf(newname)

    return newname


# create filters in a list
def initfilters(args):

    # use a closure to retain scope of compiled re
    # use an additional translate to remove trailing brackets
    # note to self: find better re for bracket removing
    def bracr_re(x):
        rex = re.compile(x)
        def _clos_re(y):
            z = re.sub(rex, '', y)
            return z.translate(str.maketrans(trans))
        return _clos_re

    filters = []

    if args.slice:
        sl = args.slice
        slash = lambda x: x[sl]
        filters.append(slash)

    if args.translate:
        inpart = args.translate[0]
        outpart = args.translate[1]
        tranpart = str.maketrans(inpart, outpart)
        transOb = lambda x: x.translate(tranpart)
        filters.append(transOb)        

    if args.spaces:
        space = lambda x: x.replace(' ', args.spaces)
        filters.append(space)

    if args.bracket_style:
        if args.bracket_style == 'round':
            bracStyle = lambda x: x.replace('[', '(').replace(']', '')
        elif args.bracket_style == 'square':
            bracStyle = lambda x: x.replace('(', '[').replace(')', ']')
        filters.append(bracStyle)

    if args.bracket_remove:
        bracr = bracr_re(r'[\{\[\(].*?[\{\]\)]')
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

    # initialise counter for enumerating files
    counter = 1
    if args.enumerate:
        counter = args.enumerate

    # initialise and run filters
    filters = initfilters(args)
    for count, src in enumerate(sorted(fileset), counter):

        # split filepath into dir, basename and extension
        dirpath, bname, ext = partfile(src)

        # run filters on the basename
        for runf in filters:
            bname = runf(bname)

        # apply enumerator to end of filename
        # 0 padded numbers if single digit
        if args.enumerate:
            bname += '{:02d}'.format(count)

        # change extension
        # allow empty extension
        if args.extension is not None:
            ext = args.extension

        # always remove whitespace on left and right
        bname = bname.strip()
        ext   = ext.strip()

        # recombine file names
        dest = combinepart(dirpath, bname, ext)

        # place entry into the right place
        if dest in rentable['conflicts']:
            # this name is already in conflict
            # add src to rentable conflicts
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
                # no filters applied, move it to conflicts
                rentable['conflicts'][dest] = [src]
            else:
                if path.exists(dest) and dest not in fileset:
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