#!/usr/bin/env python3
import os
import re
import sre_constants
import sys
from collections import deque

from natsort import natsorted, ns

from batchren import helper, StringSeq


issues = {
    # issuecodes for rentable
    0: "name is unchanged",
    1: "name cannot be empty",
    2: "name cannot start with '.'",
    3: "name cannot exceed 255 characters",
    4: "cannot change file to directory",
    5: "cannot change location of file",
    6: "shared name conflict",
}


def partfile(path, raw=False):
    """Split directory into directory, basename and/or extension """
    dirpath, filename = os.path.split(path)
    if not raw:
        # default, extract extensions
        basename, ext = os.path.splitext(filename)
    else:
        # raw, don't extract extension
        basename, ext = filename, ""

    return (dirpath, basename, ext)


def joinparts(dirpath, basename, ext, raw=False):
    """Combine directory path, basename and extension """
    path = basename
    if not raw:
        # default, process filename before applying extension
        path = path.strip()

    if ext:
        # remove spaces, strip and collapse dots from extension
        # remove trailing dots from filename before adding extension
        ext = re.sub(r"\.+", ".", ext.replace(" ", "").strip("."))
        path = path.rstrip(".") + "." + ext

    # raw, process filename after applying extension
    path = path.strip()
    if dirpath:
        path = os.path.join(dirpath, path)

    return path


def initfilters(args):
    """Create functions in a list """
    filters = []
    if args.regex:
        try:
            repl = _repl_decorator(*args.regex)
        except re.error as re_err:
            sys.exit("A regex compilation error occurred: " + str(re_err))
        except sre_constants.error as sre_err:
            sys.exit("A regex compilation error occurred: " + str(sre_err))
        filters.append(repl)

    if args.bracket_remove:
        if args.bracket_remove[0] == "curly":
            regexp = re.compile(r"\{.*?\}")
        elif args.bracket_remove[0] == "round":
            regexp = re.compile(r"\(.*?\)")
        elif args.bracket_remove[0] == "square":
            regexp = re.compile(r"\[.*?\]")

        bracr = _repl_decorator(regexp, "", args.bracket_remove[1])
        filters.append(bracr)

    if args.slice:
        slash = lambda x: x[args.slice]
        filters.append(slash)

    if args.shave:
        shave = lambda x: x[args.shave[0]][args.shave[1]]
        filters.append(shave)

    if args.translate:
        translmap = str.maketrans(*args.translate)
        translate = lambda x: x.translate(translmap)
        filters.append(translate)

    if args.spaces is not None:
        space = lambda x: re.sub(r"\s+", args.spaces, x)
        filters.append(space)

    if args.case:
        if args.case == "upper":
            case = lambda x: x.upper()
        elif args.case == "lower":
            case = lambda x: x.lower()
        elif args.case == "swap":
            case = lambda x: x.swapcase()
        elif args.case == "cap":
            case = lambda x: str.title(x)
        filters.append(case)

    if args.sequence:
        filters.append(args.sequence)

    if args.prepend is not None:
        prepend = lambda x: args.prepend + x
        filters.append(prepend)

    if args.postpend is not None:
        postpend = lambda x: x + args.postpend
        filters.append(postpend)

    return filters


def _repl_decorator(pattern, repl="", count=0):
    """Decorator function for regex replacement\n
    Return one of two functions:\n
        1. Normal re.sub
        2. re.sub with counter to remove nth instance.
    """
    def repl_all(x):
        return re.sub(pattern, repl, x)

    def repl_nth(x):
        f = re.sub(pattern, replacer, x, count)
        replacer._count = 1
        return f

    def replacer(matchobj):
        """Function to be used with re.sub\n
        Replace string match with repl if count = count\n
        Otherwise return the string match\n
        """
        if matchobj.group() and replacer._count == count:
            res = repl
        else:
            res = matchobj.group()
        replacer._count += 1
        return res

    # initialise function attribute to one for use as a counter
    replacer._count = 1

    return repl_all if not count else repl_nth


def start_rename(files, args):
    src_files = files
    dest_files = files

    filters = initfilters(args)
    dest_files = get_renames(dest_files, filters, args.extension, args.raw)
    rentable = generate_rentable(src_files, dest_files)
    q = print_rentable(rentable, args.quiet, args.verbose)
    if q and helper.askQuery():
        rename_queue(q, args.dryrun, args.verbose)


def get_renames(src_files, filters, ext, raw):
    """Rename list of files with a list of functions """
    dest_files = []
    for src in src_files:
        dest = runfilters(src, filters, ext, raw)
        dest_files.append(dest)

    return dest_files


def runfilters(path, filters, extension=None, raw=False):
    """Rename file with a list of functions """
    dirpath, bname, ext = partfile(path, raw)
    for runf in filters:
        try:
            if isinstance(runf, StringSeq.StringSequence):
                bname = runf(path, dirpath, bname)
            else:
                bname = runf(bname)
        except re.error as re_err:
            sys.exit("A regex error occurred: " + str(re_err))
        except OSError as os_err:
            # except oserror from sequences
            sys.exit("A filesystem error occurred: " + str(os_err))
        except Exception as exc:
            sys.exit("An unforeseen error occurred: " + str(exc))

    # change extension, allow '' as an extension
    if extension is not None:
        ext = extension

    # recombine as basename+ext, path+basename+ext
    res = joinparts(dirpath, bname, ext, raw)
    return res


def generate_rentable(src_files, dest_files):
    """Generate a table of files that can and cannot be renamed """
    if len(src_files) != len(dest_files):
        raise ValueError("src list and dest list must have the same length")

    fileset = set(src_files)
    rentable = {
        "renames": {},
        "conflicts": {},
        "unresolvable": set()
    }

    for src, dest in zip(src_files, dest_files):
        errset = set()
        if dest in rentable["conflicts"]:
            # this name is already in conflict, add src to conflicts
            rentable["conflicts"][dest]["srcs"].append(src)
            rentable["conflicts"][dest]["err"].add(6)
            errset = rentable["conflicts"][dest]["err"]
            cascade(rentable, src)

        elif dest in rentable["renames"]:
            # this name is taken, invalidate both names
            if dest == src:
                errset.add(0)
            errset.add(6)

            tmp = rentable["renames"][dest]
            del rentable["renames"][dest]
            rentable["conflicts"][dest] = {"srcs": [tmp, src], "err": errset}
            for n in rentable["conflicts"][dest]["srcs"]:
                cascade(rentable, n)

        elif dest in rentable["unresolvable"]:
            # file won't be renamed, assign to unresolvable
            errset.add(6)
            rentable["conflicts"][dest] = {"srcs": [src], "err": errset}
            cascade(rentable, src)

        else:
            src_dir, _ = os.path.split(src)
            dest_dir, dest_bname = os.path.split(dest)

            if dest not in fileset and os.path.exists(dest):
                # file exists but not in fileset, assign to unresolvable
                errset.add(6)

            if dest == src:
                # name hasn't changed, don't rename this
                errset.add(0)

            if src_dir != dest_dir:
                if dest and dest[-1] == "/":
                    # cannot change file to directory
                    errset.add(4)
                else:
                    # cannot change location of file
                    errset.add(5)

            if dest_bname == "":
                # name is empty, don't rename this
                errset.add(1)
            elif dest_bname[0] == ".":
                # . is reserved in unix
                errset.add(2)

            if len(dest_bname) > 255:
                errset.add(3)

            if errset:
                rentable["conflicts"][dest] = {"srcs": [src], "err": errset}
                cascade(rentable, src)

        if not errset:
            rentable["renames"][dest] = src

    return rentable


def cascade(rentable, target):
    """Search through rename table and cascade file errors.\n
    If dest has an error then src won't be renamed.\n
    Mark src as unresolvable and cascade anything else
    that wants to rename to src.
    """
    ndest = target
    while True:
        rentable["unresolvable"].add(ndest)
        if ndest in rentable["renames"]:
            tmp = rentable["renames"][ndest]
            del rentable["renames"][ndest]
            rentable["conflicts"][ndest] = {"srcs": [tmp], "err": {6}}
            ndest = tmp
            continue
        return


def print_rentable(rentable, quiet=False, verbose=False):
    """Print contents of table.\n
    -   quiet: don't show errors
    -   verbose: show detailed errors
    -   verbose and no errors: show message
    -   not verbose and no errors: show nothing
    -   not verbose and errors: show unrenamable files

    Always show output for renames
    """
    ren = rentable["renames"]
    conf = rentable["conflicts"]
    unres = rentable["unresolvable"]

    if quiet:
        # do nothing if quiet
        pass

    elif verbose:
        print("{:-^30}".format(helper.BOLD + "issues/conflicts" + helper.END))
        if unres:
            # show detailed output if there were conflicts
            print("the following files have conflicts")
            if "" in conf:
                # workaround for empty values with ns.PATH
                conflicts = [("", conf.pop("")), *natsorted(conf.items(), key=lambda x: x[0], alg=ns.PATH)]
            else:
                conflicts = natsorted(conf.items(), key=lambda x: x[0], alg=ns.PATH)

            for dest, obj in conflicts:
                srcOut = natsorted(obj["srcs"], alg=ns.PATH)
                print(", ".join([repr(str(e)) for e in srcOut]))
                print("--> '{}'\nerror(s): ".format(dest), end="")
                print(", ".join([issues[e] for e in obj["err"]]), "\n")
        else:
            # otherwise show a message
            print("no conflicts found", "\n")

    elif unres:
        # show files that can't be renamed if not verbose or quiet
        print("{:-^30}".format(helper.BOLD + "issues/conflicts" + helper.END))
        print("the following files will NOT be renamed")
        print(*["'{}'".format(s) for s in natsorted(unres, alg=ns.PATH)], "", sep="\n")

    # always show files that will be renamed
    # return list of tuples (dest, src) sorted by src
    print("{:-^30}".format(helper.BOLD + "rename" + helper.END))
    renames = natsorted(ren.items(), key=lambda x: x[1], alg=ns.PATH)
    if renames:
        print("the following files can be renamed:")
        for dest, src in renames:
            print("'{}' rename to '{}'".format(src, dest))
    else:
        print("no files to rename")
    print()

    return renames


def getFreeName(dest):
    dirpath, basename, ext = partfile(dest)
    count = 1
    while(True):
        tmpname = "{}_{}".format(basename, count)
        ndest = joinparts(dirpath, tmpname, ext)
        if not os.path.exists(ndest):
            return ndest
        count += 1


def name_gen():
    count = 0
    dirpath = ""
    while True:
        ret = os.path.join(dirpath, "tmp{}".format(count))
        if os.path.exists(ret):
            count += 1
            continue
        val = yield ret
        if not val:
            dirpath = ""
        else:
            dirpath = val
        count += 1


def rename_queue(queue, dryrun=False, verbose=False):
    """Rename src to dest from a list of tuples [(dest, src), ...] """
    n = name_gen()
    next(n)
    q = deque(queue)
    msg = "Conflict detected, temporarily renaming"
    if dryrun:
        print("Running with dryrun, files will NOT be renamed")
    while q:
        dest, src = q.popleft()
        if os.path.exists(dest):
            dirpath, _ = os.path.split(dest)
            tmp = n.send(dirpath)
            if verbose or dryrun:
                print(msg, "'{}' to '{}'".format(src, tmp))
            if not dryrun:
                rename_file(src, tmp)
            q.append((dest, tmp))
        else:
            # no conflict, just rename
            if verbose or dryrun:
                print("rename '{}' to '{}'".format(src, dest))
            if not dryrun:
                rename_file(src, dest)

    print("Finished renaming...")


def rename_file(src, dest):
    try:
        os.rename(src, dest)
    except OSError as err:
        sys.exit("An error occurred while renaming: " + str(err))
    except Exception as exc:
        sys.exit("An unforeseen error occurred while renaming: " + str(exc))
