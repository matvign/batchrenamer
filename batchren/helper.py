#!/usr/bin/env python3
import os
import re

BOLD = '\033[1m'
END = '\033[0m'


def askQuery():
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False, "q": False}

    while True:
        choice = input('Proceed with renaming? [y/n] ').lower()
        if choice == '':
            return True
        elif choice in valid:
            return valid[choice]
        else:
            print("Please respond with 'yes' or 'no'")


def print_nofiles():
    print('{:-^30}'.format(BOLD + 'files found' + END))
    print('no files found\n')


def print_found(files):
    print('{:-^30}'.format(BOLD + 'files found' + END))
    for n in files:
        print(n)
    print()


def print_args(args):
    print('{:-^30}'.format(BOLD + 'arguments' + END))
    for argname, argval in sorted(vars(args).items()):
        if argval is False:
            continue
        if argval is not None:
            print('    {}: {}'.format(argname, argval))
    print()
    # print(args, '\n')


def escape_path(path, args):
    magic_check = re.compile('([%s])' % args)
    magic_check_bytes = re.compile(b'([%a])' % args)

    drive, pathname = os.path.splitdrive(path)
    if isinstance(pathname, bytes):
        pathname = magic_check_bytes.sub(br'[\1]', pathname)
    else:
        pathname = magic_check.sub(r'[\1]', pathname)

    return drive + pathname
