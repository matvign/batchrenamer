#!/usr/bin/env python3
import os
import re

BOLD = "\033[1m"
END = "\033[0m"


def askQuery():
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False, "q": False}

    while True:
        choice = input("Proceed with renaming? [y/n] ").lower()
        if choice == "":
            return True
        elif choice in valid:
            return valid[choice]
        else:
            print("Please respond with 'yes' or 'no'")


def print_nofiles():
    print("{:-^30}".format(BOLD + "files found" + END))
    print("no files found\n")


def print_found(files):
    print("{:-^30}".format(BOLD + "files found" + END))
    for fname in files:
        print(fname)
    print()


def print_args(args):
    print("{:-^30}".format(BOLD + "arguments" + END))
    for argname, argval in sorted(vars(args).items()):
        if argval is False:
            continue
        if argval is not None:
            print("    {}: {}".format(argname, argval))
    print()
    # print(args, '\n')


def bracket_map(expression):
    bracket_types = ("round", "square", "curly")
    open_map, close_map = {}, {}

    if "a" in expression:
        open_map = dict(zip(tuple("([{"), bracket_types))
        close_map = dict(zip(tuple(")]}"), bracket_types))

    else:
        for ch in expression:
            if ch == "r":
                open_map["("] = "round"
                close_map[")"] = "round"
            elif ch == "s":
                open_map["["] = "square"
                close_map["]"] = "square"
            elif ch == "c":
                open_map["{"] = "curly"
                close_map["}"] = "curly"

    return (open_map, close_map)


def bracket_remove(expression, open_map, close_map, count):
    stack = { "round": [], "square": [], "curly": [] }
    indices = []

    # find indices of matched/unmatched brackets using three stacks
    for index, char in enumerate(expression):
        if char in open_map:
            stack[open_map[char]].append(index)
        elif char in close_map:
            if not stack[close_map[char]]:
                # unmatched closing bracket, move index of closing bracket from stack
                indices.append((index, index))
                continue

            # matched closing bracket, remove index of closing bracket from stack
            i = stack[close_map[char]].pop()
            indices.append((i, index))

    # move indices of any remaining unmatched open braces
    for k, v in stack.items():
        for vi in v:
            indices.append((vi, vi))

    if not indices:
        # no indices to remove, just return the expression
        return expression

    indices = sorted(indices, key=lambda x: x[0])
    if not count:
        indices = join_indices(indices)

    # remove indices matching matched/unmatched indices
    s = list(expression)
    cur_index = len(indices)
    while(indices):
        start, end = indices.pop()

        if not count:
            del s[start:end+1]
        elif count and cur_index == count:
            if start != end:
                del s[start:end + 1]
        cur_index -= 1

    return "".join(s)


def join_indices(indices):
    # join overlapping indices
    indices = sorted(indices, key=lambda x: x[0])
    min_start, max_end = indices[0]

    remove_indices = [indices[0]]
    for start, end in indices[1:]:
        if start > max_end:
            remove_indices.append((start, end))
            min_start, max_end = start, end
        elif end > max_end:
            remove_indices[-1] = (min_start, end)
            max_end = end

    return remove_indices


def escape_path(path, args):
    magic_check = re.compile("([%s])" % args)
    magic_check_bytes = re.compile(b"([%a])" % args)

    drive, pathname = os.path.splitdrive(path)
    if isinstance(pathname, bytes):
        pathname = magic_check_bytes.sub(br"[\1]", pathname)
    else:
        pathname = magic_check.sub(r"[\1]", pathname)

    return drive + pathname
