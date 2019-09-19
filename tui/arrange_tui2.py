#!/usr/bin/env python3
import os

import urwid

from batchren._version import __version__

version = 'batchren ' + __version__


def _splitdir(files):
    d = {}
    for f in files:
        dirpath, filename = os.path.split(f)
        if dirpath in d:
            d[dirpath].append(filename)
        else:
            d[dirpath] = [filename]
    return d


class FileArranger:
    def __init__(self, files):
        self.status = True
        self.original = files
        self.palette = [
            ('titlebar', 'black', 'white'),
            ('titlebar-divide', 'black', 'black'),
            ('green button', 'dark green, bold', 'black'),
            ('red button', 'dark red, bold', 'black'),
            ('reversed', 'standout', ''),
        ]
        header_cols = urwid.Columns([
            ('weight', 5, urwid.Text(version)),
            ('weight', 7, urwid.Text(u'manual file reorder'))
        ])

        self.body = None
        self.header = urwid.Pile([
            urwid.AttrMap(urwid.Padding(header_cols, left=2), 'titlebar'),
            urwid.AttrMap(urwid.Divider(), 'titlebar-divide')
        ])
        self.footer = urwid.Text([
            ('green button', u'ENTER'), u':edit/reorder files  ',
            ('red button', u'ESC'), u':stop editing current directory  ',
            ('green button', u'(r)'), u':reset  ',
            ('red button', u'(q)'), u':save and quit  ',
            ('red button', u'(c)'), u':abort batchren  ',
        ])

        self.view = urwid.Frame(header=self.header,
            body=self.body,
            footer=self.footer)

    def unhandled_input(self, key):
        if key in ('r', 'R'):
            # send a signal to reset file order
            pass
        elif key in ('c', 'C'):
            # send a signal to abort batchren
            self.status = False
            raise urwid.ExitMainLoop()
        elif key in ('q', 'Q'):
            # send a signal to return contents of body
            self.status = True
            raise urwid.ExitMainLoop()

    def main(self):
        '''
        Run the program
        '''
        self.loop = urwid.MainLoop(self.view, self.palette,
            unhandled_input=self.unhandled_input)
        self.loop.run()

        if self.status:
            # operation success, return reordered files
            return []
        else:
            # operation aborted, return None
            print('Batch rename was aborted')
            return None


def main(files):
    tui = FileArranger(files)
    return tui.main()
