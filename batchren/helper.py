#!/usr/bin/env python3
import os
import re

BOLD = '\033[1m'
END = '\033[0m'


def printArgs(args):
    print('{:-^30}'.format(BOLD + 'arguments' + END))
    for argname, argval in sorted(vars(args).items()):
        if argval is False:
            continue
        if argval is not None:
            print('    {}: {}'.format(argname, argval))
    print()
    # print(args, '\n')


def check_optional(args):
    notfilter = {'dryrun', 'quiet', 'verbose', 'path', 'sort', 'sel', 'esc'}
    argdict = vars(args)

    for argname, argval in argdict.items():
        if argname in notfilter or argval is False:
            continue
        if argval is not None:
            return True
    return False


def escape_path(path, args):
    magic_check = re.compile('([%s])' % args)
    magic_check_bytes = re.compile(b'([%a])' % args)

    drive, pathname = os.path.splitdrive(path)
    if isinstance(pathname, bytes):
        pathname = magic_check_bytes.sub(br'[\1]', pathname)
    else:
        pathname = magic_check.sub(r'[\1]', pathname)

    return drive + pathname