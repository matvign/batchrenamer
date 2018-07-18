#!/usr/bin/env python3

import re
import string
from os import path

symbolmap = {
    'dot': '.',
    'underscore': '_',
    'dash': '-',
    'space': ' ',
    'bar': '|'
}


#   function to run filters
def runfilters(filters, filename):
    newname = filename
    for runf in filters:
        newname = runf(newname)

    return newname


#   split filepath into dir, basename and extension
def splitfilepath(filename):
        dirpath = path.dirname(filename)
        nametpl = path.splitext(path.basename(filename))

        return (dirpath, *nametpl)


#   recombine dir, basename and extension
def combinepaths(dirpath, bname, ext):
    newname = bname

    #   join non-null ext with file name
    if ext:
        newname += ext

    #   join non-null dirpath with file name
    #   otherwise, the new name is just the file itself
    if dirpath:
        newname = "/".join([dirpath, newname])

    return newname


#   create lambda filters in a list
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


def renlist(args, filelist):
    #   create table of status, original, newname
    rentable = []

    #   initialise counter for enumerating files
    count = 1
    if args.enumerate:
        count = args.enumerate

    #   initialise and run filters
    filters = initfilters(args)
    for count, f in enumerate(filelist, count):

        #   split filepath into dir, basename and extension
        nametpl = splitfilepath(f)
        (dirpath, bname, ext) = nametpl

        #   run filters on the basename
        for runf in filters:
            bname = runf(bname)

        #   apply enumerator to end of filename
        #   0 padded numbers if single digit
        if args.enumerate:
            bname += '{:02d}'.format(count)

        #   Always remove whitespace on left and right
        bname = bname.strip()

        #   change extension
        if args.extension:
            ext = args.extension

        #   recombine file names and add to table
        newname = combinepaths(dirpath, bname, ext)
        nentry = [f, newname]
        rentable.append(nentry)

    return rentable