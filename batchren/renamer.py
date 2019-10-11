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
    3: "name cannot contain '/'",
    4: "name cannot exceed 255 characters",
    5: "shared name conflict",
    6: "unresolvable conflict"
}


def partfile(path, mode=False):
    """Split directory into directory, basename and/or extension """
    dirpath, filename = os.path.split(path)
    if not mode:
        # default, extract extensions
        basename, ext = os.path.splitext(filename)
    else:
        # raw, don't extract extension
        basename, ext = filename, ""

    return (dirpath, basename, ext)


def joinparts(dirpath, basename, ext, mode=False):
    """
    Combine directory path, basename and extension.
    Strip spaces in basename
    Remove spaces and strip+collapse dots in extension
    Return the new filename and the full path
    """
    filename = basename
    if not mode:
        # default, process filename before applying extension
        filename = filename.strip()

    if ext:
        # remove spaces, strip and collapse dots from extension
        # remove trailing dots from filename and add extension
        ext = re.sub(r"\.+", ".", ext.replace(" ", "").strip("."))
        filename = filename.strip(".") + "." + ext

    if mode:
        # raw, process filename after applying extension
        filename = filename.strip()

    path = filename
    if dirpath:
        path = os.path.join(dirpath, filename)

    return (filename, path)


def initfilters(args):
    # create filters in a list
    filters = []
    if args.regex:
        try:
            regex_repl = _repl_decorator(*args.regex)
        except re.error as re_err:
            sys.exit("A regex compilation error occurred: " + str(re_err))
        except sre_constants.error as sre_err:
            sys.exit("A regex compilation error occurred: " + str(sre_err))
        filters.append(regex_repl)

    if args.bracket_remove:
        if args.bracket_remove[0] == "curly":
            reg_exp = re.compile(r"\{.*?\}")
        elif args.bracket_remove[0] == "round":
            reg_exp = re.compile(r"\(.*?\)")
        elif args.bracket_remove[0] == "square":
            reg_exp = re.compile(r"\[.*?\]")

        bracr = _repl_decorator(reg_exp, "", args.bracket_remove[1])
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
        space = lambda x: x.replace(" ", args.spaces)
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


def _repl_decorator(pattern, repl="", repl_count=0):
    """
    Return one of two functions:
    1. Normal re.sub
    2. re.sub with counter that removes nth instance.
       Use function attribute as a counter.
    """
    def repl_all(x):
        return re.sub(pattern, repl, x)

    def repl_nth(x):
        f = re.sub(pattern, replacer, x, repl_count)
        replacer._count = 1
        return f

    def replacer(matchobj):
        """
        Function to be used with re.sub.
        Replace string match with repl if count = count.
        Otherwise return the string match
        """
        if matchobj.group() and replacer._count == repl_count:
            res = repl
        else:
            res = matchobj.group()
        replacer._count += 1
        return res

    # initialise all replacer functions to one
    replacer._count = 1

    return repl_all if not repl_count else repl_nth


def start_rename(args, files):
    """
    Initialize filters and run filters on files
    Print rentable and give a prompt to start renaming
    """
    fileset = set(files)
    rentable = {
        "renames": {},
        "conflicts": {},
        "unresolvable": set()
    }

    filters = initfilters(args)
    for src in files:
        # split path into directory, basename and extension
        dirpath, bname, ext = partfile(src, args.raw)
        bname = runfilters(filters, src, dirpath, bname)

        # change extension, allow '' as an extension
        if args.extension is not None:
            ext = args.extension

        # recombine as basename+ext, path+basename+ext
        basename, dest = joinparts(dirpath, bname, ext, args.raw)
        assign_rentable(rentable, fileset, src, dest, basename)

    # print contents of rentable and return a sorted queue of files to rename
    q = print_rentable(rentable, quiet=args.quiet, verbose=args.verbose)
    if q and helper.askQuery():
        rename_queue(q, args)


def runfilters(filters, filepath, dirpath, basename):
    """
    Function to run filters.
    path is used for getting modification time in sequences.
    dirpath is used for resetting sequences on different directories.
    """
    newname = basename
    for runf in filters:
        try:
            if isinstance(runf, StringSeq.StringSequence):
                newname = runf(filepath, dirpath, newname)
            else:
                newname = runf(newname)
        except re.error as re_err:
            sys.exit("A regex error occurred: " + str(re_err))
        except OSError as os_err:
            # except oserror from sequences
            sys.exit("A filesystem error occurred: " + str(os_err))
        except Exception as exc:
            sys.exit("An unforeseen error occurred: " + str(exc))

    return newname


def assign_rentable(rentable, fileset, src, dest, bname):
    errset = set()
    if dest in rentable["conflicts"]:
        # this name is already in conflict, add src to conflicts
        rentable["conflicts"][dest]["srcs"].append(src)
        rentable["conflicts"][dest]["err"].add(5)
        errset = rentable["conflicts"][dest]["err"]
        cascade(rentable, src)

    elif dest in rentable["renames"]:
        # this name is taken, invalidate both names
        if dest == src:
            errset.add(0)
        errset.add(5)

        temp = rentable["renames"][dest]
        del rentable["renames"][dest]
        rentable["conflicts"][dest] = {"srcs": [temp, src], "err": errset}
        for n in rentable["conflicts"][dest]["srcs"]:
            cascade(rentable, n)

    elif dest in rentable["unresolvable"]:
        # file won't be renamed, assign to unresolvable
        errset.add(6)
        rentable["conflicts"][dest] = {"srcs": [src], "err": errset}
        cascade(rentable, src)

    else:
        if dest not in fileset and os.path.exists(dest):
            # file exists but not in fileset, assign to unresolvable
            errset.add(6)

        if dest == src:
            # name hasn't changed, don't rename this
            errset.add(0)

        if bname == "":
            # name is empty, don't rename this
            errset.add(1)
        elif bname[0] == ".":
            # . is reserved in unix
            errset.add(2)

        if "/" in bname:
            # / usually indicates some kind of directory
            errset.add(3)

        if len(bname) > 255:
            errset.add(4)

        if errset:
            rentable["conflicts"][dest] = {"srcs": [src], "err": errset}
            cascade(rentable, src)

    if not errset:
        rentable["renames"][dest] = src


def cascade(rentable, target):
    """
    If dest has an error, src won't be renamed.
    Mark src as unresolvable so nothing renames to it.
    Remove anything else that wants to rename to src.
    """
    ndest = target
    while True:
        rentable["unresolvable"].add(ndest)
        if ndest in rentable["renames"]:
            temp = rentable["renames"][ndest]
            del rentable["renames"][ndest]
            rentable["conflicts"][ndest] = {"srcs": [temp], "err": {6}}
            ndest = temp
            continue
        return


def print_rentable(rentable, quiet=False, verbose=False):
    """
    Print contents of rentable.
    For conflicts:
        if quiet: don't show error output
        if verbose: show detailed errors
        if verbose and no errors: show message
        if not verbose, no errors, show nothing
        if not verbose, errors, show unrenamable files
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


def rename_queue(queue, args):
    """Rename src to dest from a list of tuples [(dest, src), ...] """
    n = name_gen()
    next(n)
    q = deque(queue)
    msg = "Conflict detected, temporarily renaming"
    if args.dryrun:
        print("Running with dryrun, files will NOT be renamed")
    while q:
        dest, src = q.popleft()
        if os.path.exists(dest):
            # temp = getFreeName(dest)
            dirpath, _ = os.path.split(dest)
            tmp = n.send(dirpath)
            if args.verbose or args.dryrun:
                print(msg, "'{}' to '{}'".format(src, tmp))
            if not args.dryrun:
                rename_file(src, tmp)
            q.append((dest, tmp))
        else:
            # no conflict, just rename
            if args.verbose or args.dryrun:
                print("rename '{}' to '{}'".format(src, dest))
            if not args.dryrun:
                rename_file(src, dest)

    print("Finished renaming...")


def rename_file(src, dest):
    try:
        os.rename(src, dest)
    except OSError as err:
        sys.exit("An error occurred while renaming: " + str(err))
    except Exception as exc:
        sys.exit("An unforeseen error occurred while renaming: " + str(exc))
