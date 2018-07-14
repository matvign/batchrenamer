#!/usr/bin/env python3

import re
import string
from os import path

symbolmap = {
    "dot": ".",
    "underscore": "_",
    "dash": "-",
    "space": " ",
    "bar": "|"
}


#   filters in a list
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
            #   capitalise every word
            #   e.g. hello world -> Hello World
            lmdaCase = lambda x: string.capwords(x)
        filters.append(lmdaCase)

    if args.append:
        lmdaAppend = lambda x: x+args.append
        filters.append(lmdaAppend)

    if args.prepend:
        lmdaPrepend = lambda x: args.prepend+x
        filters.append(lmdaPrepend)

    return filters


def filter(origname, filters):
    newname = origname

    #   run each filter on file
    for runf in filters:
        newname = runf(newname)

    return newname


def renlist(args, filelist):
    #   create table of status, original, newname
    rentable = []

    #   Initialise counter for enumerating files
    count = 1
    if args.enumerate:
        count = args.enumerate

    #   Initialise and run filters
    filters = initfilters(args)
    for count, f in enumerate(filelist, count):

        dirpath = path.dirname(f)
        nametpl = path.splitext(path.basename(f))
        bname = nametpl[0]
        ext   = nametpl[1]

        bname = filter(bname, filters)

        #   apply enumerator to end of filename
        #   0 padded format for single digits
        if args.enumerate:
            bname += '{:02d}'.format(count)

        #   apply extension
        if args.extension:
            ext = args.extension

        #   Recombine all strings
        #   Join non-null ext with file name
        if ext:
            bname += ext

        #   Join non-null dirpath with file name
        if dirpath:
            dirpath = "/".join([dirpath, bname])
        #   Otherwise, the dirpath is just the file itself
        else:
            dirpath = bname

        # status = 1 if f != dirpath else 0
        # nentry = [status, f, dirpath]
        nentry = [f, dirpath]
        rentable.append(nentry)

    return rentable