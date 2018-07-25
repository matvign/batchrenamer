#!/usr/bin/env python3

import re
from os import path

symbolmap = {
    'dot': '.',
    'underscore': '_',
    'dash': '-',
    'space': ' ',
    'bar': '|'
}


# function to run filters
def runfilters(filters, filename):
    newname = filename
    for runf in filters:
        newname = runf(newname)

    return newname


# split filepath into dir, basename and extension
def partfile(filename):
        dirpath, dirname = path.split(filename)
        return (dirpath, *path.splitext(dirname))


# recombine dir, basename and extension
def combinepart(dirpath, bname, ext):
    newname = bname

    # join non-null extension with file name
    if ext:
        newname += ext

    # join non-null dirpath with file name
    # otherwise, the new name is just the file itself
    if dirpath:
        newname = path.join(dirpath, newname)

    return newname


# create lambda filters in a list
def initfilters(args):
    filters = []

    if args.spaces:
        lmdaSpace = lambda x: x.replace(' ', args.spaces)
        filters.append(lmdaSpace)

    if args.separator:
        if args.separator[0] != args.separator[1]:
            lmbdaSeparator = lambda x: x.replace(sepr, repl)
            filters.append(lmbdaSeparator)

    if args.bracket_style:
        if args.bracket_style == 'round':
            lmdaBracStyle = lambda x: (x.replace('[', '(')).replace(']', '')
        elif args.bracket_style == 'square':
            lmdaBracStyle = lambda x: (x.replace('(', '[')).replace(')', ']')
        filters.append(lmdaBracStyle)

    if args.case:
        if args.case == 'upper':
            lmdaCase = lambda x: x.upper()
        elif args.case == 'lower':
            lmdaCase = lambda x: x.lower()
        elif args.case == 'swap':
            lmdaCase = lambda x: x.swapcase()
        elif args.case == 'cap':
            # capitalise every word
            # e.g. hello world -> Hello World
            lmdaCase = lambda x: str.title(x)
        filters.append(lmdaCase)

    if args.prefix:
        lmdaPrepend = lambda x: args.prefix+x
        filters.append(lmdaPrepend)

    if args.postfix:
        lmdaAppend = lambda x: x+args.postfix
        filters.append(lmdaAppend)


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
    for count, src in enumerate(fileset, counter):

        # split filepath into dir, basename and extension
        (dirpath, bname, ext) = partfile(src)

        # run filters on the basename
        for runf in filters:
            bname = runf(bname)

        # apply enumerator to end of filename
        # 0 padded numbers if single digit
        if args.enumerate:
            bname += '{:02d}'.format(count)

        # change extension
        if args.extension:
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
            rentable['conflicts'][dest].extend([src])

        elif dest in rentable['renames']:
            # this name is taken, invalidate both names
            temp = rentable['renames'][dest]
            del rentable['renames'][dest]
            rentable['conflicts'][dest] = [temp, src]

        else:
            if src == dest:
                # no filters applied, move it to conflicts
                rentable['conflicts'][dest] = [src]
            else:
                if path.isfile(dest) and dest not in fileset:
                        # name already exists and not in files found
                        # dirs are never included in fileset
                        # so files will never be renamed to dirs
                        # since file won't be renamed, auto conflict
                        rentable['conflicts'][dest] = [src]
                else:
                    # if file exists, then we haven't processed it yet
                    # just move it to renames and let the above handle it
                    # file doesn't exist, add to renames (until removed)
                    rentable['renames'][dest] = src

    return rentable