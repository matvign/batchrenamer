#!/usr/bin/env python3
import argparse
import glob
import os

from natsort import natsorted, ns

from batchren import renamer, helper
from tui import arrange_tui, selection_tui


def main(args, parser):
    if args.verbose:
        helper.printArgs(args)

    if not helper.check_optional(args):
        parser.print_usage()
        print("\nNo optional arguments set for renaming")
        return

    if args.esc:
        args.path = helper.escape_path(args.path, args.esc)

    try:
        # only include files
        files = natsorted([f for f in glob.iglob(args.path) if os.path.isfile(f)], alg=ns.PATH)
    except OSError as err:
        raise argparse.ArgumentParser.error('An error occurred while searching for files: ' + str(err))

    if not files:
        print('{:-^30}'.format(helper.BOLD + 'files found' + helper.END))
        print('no files found\n')
        return

    if args.verbose:
        print('{:-^30}'.format(helper.BOLD + 'files found' + helper.END))
        for n in files:
            print(n)
        print()

    if args.sel:
        files = selection_tui.main(files)
        if not files:
            return

    if args.sort == 'man':
        files = arrange_tui.main(files)
        if not files:
            return
    elif args.sort == 'desc':
        files.reverse()

    renamer.start_rename(args, files)
