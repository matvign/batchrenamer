#!/usr/bin/env python3

import re
import string
import os

symbolmap = {
    "dot": ".",
    "underscore": "_",
    "dash": "-",
    "space": " ",
    "bar": "|",
    "round": "()",
    "square": "[]"
}


#   filters in a list
def initfilters(args):
    filters = []

    if args.spaces:
        lmdaSpace = lambda x: x.replace(' ', args.spaces)
        filters.append(lmdaSpace)

    if args.separator:
        if args.separator[0] != args.separator[1]:
            sepr = symbolmap[args.separator[0]]
            repl = symbolmap[args.separator[1]]

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
    #   create table of status -> oldname -> newname
    renlist = []

    #   Initialise counter for enumerating files
    count = 1
    if args.enumerate:
        count = args.enumerate

    #   Initialise and run filters
    filters = initfilters(args)
    for count, f in enumerate(filelist, count):

        dirpath = os.path.dirname(f)
        nametpl = os.path.splitext(os.path.basename(f))
        
        bname = nametpl[0]
        ext   = nametpl[1]

        bname = filter(bname, filters)

        #   apply enumerator to end of filename
        if args.enumerate:
            bname += count

        #   apply additional filters
        if args.extension:
            ext = args.extension

        #   Recombine all strings
        if ext:
            bname += ext
        dirpath = "/".join([dirpath, bname])

        diff = 1 if f != dirpath else 0

        nentry = [diff, f, dirpath]
        renlist.append(nentry)

    return renlist