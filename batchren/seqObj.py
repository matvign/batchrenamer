import re


class SequenceObj:
    def __init__(self, args):
        self.presence = False
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

    def is_valid(self):
        return self.presence

    def _num_generator(self, depth=2, start=1, end=None, step=1):
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

    def _alpha_generator(self):
        pass

    def _parse_num(self, arg):
        '''
        parse the sequence as a number sequence
        do not allow negative values
        '''
        msg1 = 'invalid width for number sequence'
        msg2 = 'too many arguments for number sequence'
        msg3 = 'non-positive integer value in number sequence'
        args = arg.split(':')
        groupobj = re.match(r'^(n)(\d*)$', args[0])
        if not groupobj:
            raise ValueError(msg1)
        elif len(args) > 4:
            raise TypeError(msg2)

        depth = int(groupobj.group(2)) if groupobj.group(2) else 2
        # convert strings to ints, empty strings to None
        try:
            sl = [*map(
                lambda x: int(x.strip()) if x.strip() else None, args[1:]
            )]
        except ValueError as err:
            raise ValueError(msg3)
        if sum(1 for n in sl if n and n < 0):
            raise ValueError(msg3)
        gen = self._num_generator(depth, *sl)
        self.rules.append(("seq", gen))

    def _parse_seq(self, arg):
        msg = 'invalid sequence formatter '
        val = arg[1:]
        if not val:
            raise ValueError(msg + arg)
        elif val[0] == 'n':
            self._parse_num(val)
        elif val[0] == 'a':
            pass
        else:
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
                self.rules.append(("file", ''))
                self.presence = True
            elif n == '%n':
                # create a default num sequence
                gen = self._num_generator()
                self.rules.append(("seq", gen))
            elif n == '%a':
                # create a default alphabetical sequence
                pass
            elif n[0] != '%':
                # add raw string
                self.rules.append(("raw", n))
            else:
                self._parse_seq(n)