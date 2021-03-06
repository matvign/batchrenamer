#!/usr/bin/env python3
import re
from datetime import datetime
from enum import Enum
from itertools import zip_longest
from os.path import getmtime


class SequenceType(Enum):
    FILE = 0
    RAW = 1
    SEQ = 2
    MDATE = 3
    MTIME = 4


class StringSequence:
    def __init__(self, args):
        self.rules = []
        self.curdir = None
        self.args = args
        self._parse_args(args)

    def __call__(self, filepath, dirpath, filename):
        if self.curdir is None:
            self.curdir = dirpath
        st = ""
        for t, r in self.rules:
            if t == SequenceType.SEQ:
                if self.curdir != dirpath:
                    self.curdir = dirpath
                    st += r.send("reset")
                else:
                    st += next(r)
            elif t == SequenceType.FILE:
                st += filename
            elif t == SequenceType.MDATE:
                st += r(filepath)
            elif t == SequenceType.MTIME:
                st += r(filepath)
            elif t == SequenceType.RAW:
                st += r
        return st

    def __str__(self):
        return self.get_argstr()

    def get_argstr(self):
        return self.args

    def get_rules(self):
        return self.rules

    def _num_generator(self, depth=2, start=1, end=None, step=1):
        """Generator function for numbers given a depth, start, end, step\n
        Resets are supported. If reset, go back to start.\n
        If end > start, or step = 0 values will always be start.
        """
        start = start if start is not None else 1
        step = step if step is not None else 1
        i = start
        while True:
            ret = "{:0{depth}d}".format(i, depth=depth)
            val = yield ret
            if val == "reset":
                i = start
            else:
                i += step
                if end and i > end:
                    i = start

    def _alpha_generator(self, depth=1, start="a", end=None):
        """Generator function for letters given a depth, start, end.\n
        Start is where sequencing begins. Consists only of letters.\n
        End is where sequencing ends. Consists only of letters.\n
        Depth determines how much end should repeat.\n
        Lowercase increments to uppercase, but NOT vice-versa.
        """
        # convert start, end into list of chars
        start = list(start) if start is not None else ["a"]
        f = lambda x: "z" if x.islower() else "Z"
        end = depth * list(end) if end is not None else depth * list(map(f, start))

        if len(start) < len(end):
            # fill start with starting char a
            # a:zzz --> aaa:zzz
            start, end = zip_longest(*zip_longest(start, end, fillvalue="a"))
        elif len(start) > len(end):
            # fill end with None
            # aaa:z --> aaa:z--
            start, end = zip_longest(*zip_longest(start, end))

        def do_increment(ch, start_ch, end_ch):
            """Perform character increment depending on start/end character.\n
            if (a - Z) increment until z, then switch to uppercase
                and reset when = end
            otherwise just increment.\n
            if (A - z) don't increment.\n
            if (a - None) don't increment.\n
            if (A - None) don't increment.
            """
            if start_ch.islower() and end_ch.isupper():
                if ch.islower():
                    return chr(ord(ch) + 1) if ch != "z" else "A"
            elif start_ch.isupper() and end_ch.islower():
                return ch
            return chr(ord(ch) + 1) if ch < end_ch else start_ch

        st = list(start)
        while True:
            val = yield "".join(st)
            if val == "reset":
                st = list(start)
            else:
                for count, item in reversed(list(enumerate(st))):
                    start_ch, end_ch = start[count], end[count]
                    if end_ch:
                        tmp = do_increment(item, start_ch, end_ch)
                        if st[count] != tmp:
                            # stop incrementing list if we've incremented something
                            st[count] = tmp
                            if tmp != start_ch:
                                break

    def _md_generator(self, arg):
        """Return modification date of file """
        tstamp = getmtime(arg)
        return datetime.fromtimestamp(tstamp).strftime("%Y-%m-%d")

    def _mt_generator(self, arg):
        """Return modification time of file """
        tstamp = getmtime(arg)
        return datetime.fromtimestamp(tstamp).strftime("%H.%M.%S")

    def _parse_num(self, args):
        """Parse the arguments as a number sequence.\n
        %n[depth]:start:end:step\n
        Raise error if:\n
        -   depth value is not a number
        -   too many arguments (>4)
        -   argument is not a positive number
        """
        msg1 = "invalid depth for number sequence"
        msg2 = "too many arguments for number sequence"
        msg3 = "non-positive integer value in number sequence"
        seq_args = args.split(":")
        matchobj = re.match(r"^(n)(\d*)$", seq_args[0])
        if not matchobj:
            raise ValueError(msg1)
        elif len(seq_args) > 4:
            raise TypeError(msg2)
        depth = int(matchobj.group(2)) if matchobj.group(2) else 2
        try:
            sl = [int(x.strip()) if x.strip() else None for x in seq_args[1:]]
        except ValueError as err:
            raise ValueError(msg3)

        if any(n and n < 0 for n in sl):
            # check for negative numbers, skip None values
            raise ValueError(msg3)
        gen = self._num_generator(depth, *sl)
        self.rules.append((SequenceType.SEQ, gen))

    def _parse_alpha(self, args):
        """Parse the arguments as an alphabetical sequence.\n
        %a[depth]:start:end\n
        Raise error if:\n
        -   depth value is not a number
        -   too many arguments (>3)
        -   argument contains non-alphabetical character(s)
        """
        msg1 = "invalid depth for alphabetical sequence"
        msg2 = "too many arguments for alphabetical sequence"
        msg3 = "argument contains non-alphabetical character(s)"
        seq_args = args.split(":")
        matchobj = re.match(r"^(a)(\d*)$", seq_args[0])
        if not matchobj:
            raise ValueError(msg1)
        elif len(seq_args) > 3:
            raise TypeError(msg2)
        depth = int(matchobj.group(2)) if matchobj.group(2) else 1
        sl = []
        for x in seq_args[1:]:
            if x == "":
                sl.append(None)
            else:
                if not re.match("^[a-zA-Z]+$", x):
                    raise ValueError(msg3)
                sl.append(x)
        gen = self._alpha_generator(depth, *sl)
        self.rules.append((SequenceType.SEQ, gen))

    def _parse_seq(self, arg):
        # %a[depth]:start:end or
        # %n[depth]:start:end:step
        msg = "invalid sequence formatter "
        val = arg[1:]  # remove % from arg
        if not val:
            # arg was %, just add it as raw string
            self.rules.append((SequenceType.RAW, "%"))
        elif val[0] == "n":
            self._parse_num(val)
        elif val[0] == "a":
            self._parse_alpha(val)
        else:
            # raise error or add as raw string??
            raise ValueError(msg + arg)

    def _parse_args(self, args):
        """Process each part of the sequence and it into a sequence rule.\n
        e.g. txt//%f/%n2/ -> [txt, '', %f, %n2, '']
        """
        for n in args.split("/"):
            if not n:
                continue

            if n == "%f":
                # '' is a dummy value for consistency
                self.rules.append((SequenceType.FILE, ""))
            elif n == "%md":
                self.rules.append((SequenceType.MDATE, self._md_generator))
            elif n == "%mt":
                self.rules.append((SequenceType.MTIME, self._mt_generator))
            elif n == "%n":
                # create a default num sequence
                numgen = self._num_generator()
                self.rules.append((SequenceType.SEQ, numgen))
            elif n == "%a":
                # create a default alphabetical sequence
                alphagen = self._alpha_generator()
                self.rules.append((SequenceType.SEQ, alphagen))
            elif n[0] != "%":
                # add raw string
                self.rules.append((SequenceType.RAW, n))
            else:
                # this is a sequence with arguments, parse it
                self._parse_seq(n)
