import re
from itertools import zip_longest
from string import ascii_lowercase


class SequenceObj:
    def __init__(self, args):
        self.fbit = False
        self.rules = []
        self.curdir = None
        self.args = args
        self._parse_args(args)

    def __call__(self, filename, dirpath):
        if not self.curdir:
            self.curdir = dirpath
        st = ''
        for t, r in self.rules:
            if t == "seq":
                if self.curdir != dirpath:
                    self.curdir = dirpath
                    st += r.send('reset')
                else:
                    st += next(r)
            elif t == "file":
                st += filename
            elif t == "raw":
                st += r
        return st

    def __str__(self):
        return self.args

    def get_argstr(self):
        return self.args

    def get_rules(self):
        return self.rules

    def has_fileformat(self):
        return self.fbit

    def _num_generator(self, depth=2, start=1, end=None, step=1):
        '''
        Generator function for numbers given a depth, start, end, step
        Resets are supported. If reset, go back to start.
        If end > start, or step = 0 values will always be start. NOT a bug!
        '''
        start = start if start is not None else 1
        step = step if step is not None else 1
        i = start
        while True:
            ret = "{:0{depth}d}".format(i, depth=depth)
            val = yield ret
            if val == 'reset':
                i = start
            else:
                i += step
                if end and i > end:
                    i = start

    def _test_alpha_generator(self, depth=1, start='a', end='z'):
        '''
        Generator function for letters given a depth, start, end.
        Start is where sequencing begins. Consists only of letters.
        End is where sequencing ends. Consists only of letters.
        Depth determines how much end should repeat.
        '''
        start = start if start is not None else 'a'
        end = depth * end if end is not None else depth * 'z'
        if len(start) < len(end):
            # aa:zzz --> aaa:zzz
            start, end = zip_longest(*zip_longest(start, end, fillvalue='a'))
        elif len(start) > len(end):
            # aaaa:zz --> aaaa:zz--
            start, end = zip_longest(*zip_longest(start, end))

        def do_increment(ch, start_ch, end_ch):
            '''
            if (a - z) keep incrementing or reset when = end
            if (A - Z) keep incrementing or reset when = end
            if (a - Z) keep incrementing until z, then switch to uppercase
                and reset when = end
            if (A - z) don't increment at all
            '''
            if start_ch in ascii_lowercase and end_ch in ascii_lowercase:
                return chr(ord(ch) + 1) if ch < end_ch else start_ch
            elif start_ch not in ascii_lowercase and end_ch not in ascii_lowercase:
                return chr(ord(ch) + 1) if ch < end_ch else start_ch
            elif start_ch in ascii_lowercase and end_ch not in ascii_lowercase:
                if ch in ascii_lowercase:
                    return chr(ord(ch) + 1) if ch != 'z' else 'A'
                return chr(ord(ch) + 1) if ch < end_ch else start_ch
            return ch

        staticst, lst = ''.join(start[:-1]), start
        while True:
            val = yield (staticst + lst[-1])
            if val == 'reset':
                staticst, lst = ''.join(start[:-1]), start
            else:
                for count, item in reversed(list(enumerate(lst))):
                    start_ch, end_ch = start[count], end[count]
                    if end_ch:
                        lst[count] = do_increment(item, start_ch, end_ch)
                        if lst[count] != start_ch:
                            # rebuild staticst and stop looping if not a reset
                            staticst = ''.join(lst[:-1])
                            break

    def _alpha_generator(self, depth=1, start='a', end='z'):
        '''
        Generator function for letters given a depth, start, end.
        Resets are supported. If reset, go back to start with some depth.
        If end > start, go back to start e.g. z -> a.
        Length of sequence does not grow when reaching the end.
            depth = 2, az -> ba
            depth = 3, aaz -> aba, zaz -> zba, zzz -> aaa
        '''
        start = start if start is not None else 'a'
        end = end if end is not None else 'z'

        def init(start, depth):
            staticst = start * (depth - 1)
            return (start, staticst, [*staticst])

        i, staticst, lst = init(start, depth)
        while True:
            val = yield (staticst + i)
            if val == 'reset':
                i, staticst, lst = init(start, depth)
            else:
                i = chr(ord(i) + 1)
                if i > end:
                    i = start
                    for count, item in reversed(list(enumerate(lst))):
                        if item == end:
                            lst[count] = start
                        else:
                            lst[count] = chr(ord(item) + 1)
                            break
                    staticst = ''.join(lst)

    def _parse_num(self, arg):
        '''
        Parse the arguments as a number sequence
        %n[depth]:start:end
        Raise error if:
            depth value is not a number
            too many arguments (>4)
            argument is not a positive number
        '''
        msg1 = 'invalid depth for number sequence'
        msg2 = 'too many arguments for number sequence'
        msg3 = 'non-positive integer value in number sequence'
        args = arg.split(':')
        matchobj = re.match(r'^(n)(\d*)$', args[0])
        if not matchobj:
            raise ValueError(msg1)
        elif len(args) > 4:
            raise TypeError(msg2)
        depth = int(matchobj.group(2)) if matchobj.group(2) else 2
        try:
            sl = [int(x.strip()) if x.strip() else None for x in args[1:]]
        except ValueError as err:
            raise ValueError(msg3)
        if sum(1 for n in sl if n and n < 0):
            raise ValueError(msg3)
        gen = self._num_generator(depth, *sl)
        self.rules.append(("seq", gen))

    def _parse_alpha(self, arg):
        '''
        Parse the arguments as an alphabetical sequence
        %a[depth]:start:end
        Raise error if:
            depth value is not a number
            too many arguments (>3)
            argument contains non-alphabetical character(s)
        '''
        msg1 = 'invalid depth for alphabetical sequence'
        msg2 = 'too many arguments for alphabetical sequence'
        msg3 = 'argument contains non-alphabetical character(s)'
        args = [x.strip() if x.strip() else None for x in arg.split(':')]
        matchobj = re.match(r'^(a)(\d*)$', args[0])
        if not matchobj:
            raise ValueError(msg1)
        elif len(args) > 3:
            raise TypeError(msg2)
        depth = int(matchobj.group(2)) if matchobj.group(2) else 1
        if sum(1 for x in args[1:] if x and not x.isalpha()):
            raise ValueError(msg3)
        gen = self._alpha_generator(depth, *args[1:])
        self.rules.append(("seq", gen))

    def _parse_seq(self, arg):
        # %a[depth]:start:end or
        # %n[depth]:start:end:step
        msg = 'invalid sequence formatter '
        val = arg[1:]  # strip % from arg
        if not val:
            # arg was %, just add it as raw string
            self.rules.append(("raw", "%"))
        elif val[0] == 'n':
            self._parse_num(val)
        elif val[0] == 'a':
            self._parse_alpha(val)
        else:
            # raise error or add as raw string??
            raise ValueError(msg + arg)

    def _parse_args(self, args):
        '''
        process each part of the sequence
        and convert it into a rule
        txt//%f/%n2/ -> [txt, '', %f, %n2, '']
        '''
        for n in args.split('/'):
            if not n:
                continue

            if n == '%f':
                # '' is a dummy value for consistency
                self.rules.append(('file', ''))
                self.fbit = True
            elif n == '%n':
                # create a default num sequence
                numgen = self._num_generator()
                self.rules.append(("seq", numgen))
            elif n == '%a':
                # create a default alphabetical sequence
                alphagen = self._alpha_generator()
                self.rules.append(("seq", alphagen))
            elif n[0] != '%':
                # add raw string
                self.rules.append(("raw", n))
            else:
                # this is a sequence with arguments, parse it
                self._parse_seq(n)