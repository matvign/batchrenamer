#!/usr/bin/env python3

import re
import string

#   filters in a list
def initfilters(args):
    filters = []

    if args.append:
        lmdaAppend = lambda x: x+args.append
        filters.append(lmdaAppend)

    if args.prepend:
        lmdaPrepend = lambda x: args.prepend+x
        filters.append(lmdaPrepend)

    if args.case:
        if args.case == 'upper':
            lmdaCase = lambda x: x.upper()
        elif args.case == 'lower':
            lmdaCase = lambda x: x.lower()
        elif args.case == 'swap':
            lmdaCase = lambda x: x.swapcase()
        elif args.case == 'cap':
            #   capitalise every word
            #   e.g. hello world -> Hello World
            lmdaCase = lambda x: string.capwords(x)
        filters.append(lmdaCase)

    if args.spaces:
        lmdaSpace = lambda x: x.replace(' ', args.spaces)
        filters.append(lmdaSpace)

    if args.bracket-style:
        if args.bracket-style == 'round':
            lmdaBracStyle = lambda x: (x.replace('[', '')).replace(']', '')
        elif args.bracket-style == 'square':
            lmdaBracStyle = lambda x: (x.replace('(', '')).replace(')', '')

        filters.append(lmdaBracStyle)

    return filters


def filter(origname, filters):
    newname = origname

    #   run each filter on file
    for runf in filters:
        newname = runf(newname)

    return newname


def renlist(args, filelist):
    #   create table of status -> oldname -> newname
    renlist = {'Status': [], 'Original': [], 'Rename': []}

    #   list of filters to run on each file
    filters = initfilters(args)

    #   run filters on each file
    for f in filelist:

        #   split into (relative) dirpath and filename
        #   e.g. testdir/testfiles/file -> ['testdir/testfiles'] and file
        dirpath = f.rsplit('/', 1)[:-1]
        filename = f.rsplit('/', 1)[-1]

        #   split ext from filename
        #   file.bla.txt -> file.bla and txt
        name = filename.rsplit('.', 1)[:-1]
        ext = filename.rsplit('.', 1)[-1]

        name = filter(name, filters)

        #   apply additional filters (extensions, other?)
        if args.extension:
            ext = args.extension

        #   recombine file string
        name += '.' + ext

        dirpath.append(name)
        dirpath = "/".join(dirpath)

        diff = 1 if f != dirpath else 0

        renlist['Status'].append(diff)
        renlist['Original'].append(f)
        renlist['Rename'].append(dirpath)

    return renlist