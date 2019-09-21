#!/usr/bin/env python3
import os

import urwid

from batchren._version import __version__

version = 'batchren ' + __version__


def create_selectable(text, padding=0):
    if not text:
        text = 'current working directory'
    sel = VariableSelectable(text)
    item = urwid.AttrMap(urwid.Padding(sel, left=padding), None, focus_map='reversed')
    return item


class VariableSelectable(urwid.SelectableIcon):
    '''
    SelectableIcon that toggles focus
    '''
    def __init__(self, text):
        self.enable_focus = True
        curs_pos = len(text) + 1
        super().__init__(text, cursor_position=curs_pos)

    def toggle_focus(self):
        self.enable_focus = not self.enable_focus

    def selectable(self):
        return self.enable_focus


class FileListBox(urwid.ListBox):
    def __init__(self, dirpath, files):
        self.dirpath = dirpath
        self.files = files

        self.activepos = None
        self.toggle = False
        self.enable_focus = False

        lst = [create_selectable(f, 4) for f in self.files]
        body = urwid.SimpleFocusListWalker(lst)
        super().__init__(body)

    def keypress(self, size, key):
        key = super().keypress(size, key)
        if key != 'enter':
            return key

        if self.toggle:
            # move activepos to current focus position
            cur_pos = self.focus_position + 1 if len(self.body) == 1 else self.focus_position
            item = self.body.pop(self.activepos)
            self.body.insert(cur_pos, item)
            self.activepos = None
        elif not self.toggle:
            self.activepos = self.focus_position
        self.toggle = not self.toggle

    def selectable(self):
        return self.enable_focus

    def toggle_focus(self):
        self.activepos = None
        self.toggle = False
        self.enable_focus = not self.enable_focus

    def reset(self):
        self.body[:] = [create_selectable(f, 4) for f in self.files]
        self.activepos = None
        self.toggle = False
        self.enable_focus = False
        self.focus_position = 0

    def get_output(self):
        return [os.path.join(self.dirpath, wdgt.base_widget.text) for wdgt in self.body]


class DirectoryListBox(urwid.ListBox):
    '''
    DirectoryListBox that enables/disables focus
    for contained listboxes
    '''
    def __init__(self, files):
        self.toggle = False
        d = {}
        for f in files:
            dirpath, filename = os.path.split(f)
            if dirpath in d:
                d[dirpath].append(filename)
            else:
                d[dirpath] = [filename]

        lst = []
        for key, val in d.items():
            # add a selectableicon, listbox and a blank space
            icon = create_selectable(key)
            lstbox = urwid.BoxAdapter(FileListBox(key, val), height=len(val))
            lst.extend([icon, lstbox, urwid.Divider()])
        body = urwid.SimpleFocusListWalker(lst)
        super().__init__(body)

    def keypress(self, size, key):
        key = super().keypress(size, key)
        if key == 'esc':
            if not self.toggle:
                return key
            pos = self.focus_position
            self.body[pos].toggle_focus()
            self.toggle_icons()
            self.focus_position -= 1

        if key == 'enter':
            pos = self.focus_position
            self.body[pos + 1].toggle_focus()
            self.toggle_icons()
            self.focus_position += 1
        return key

    def toggle_icons(self):
        # enable/disable all directory icons
        self.toggle = not self.toggle
        for n in range(0, len(self.body), 3):
            self.body[n].base_widget.toggle_focus()

    def reset(self):
        if self.toggle:
            # reenable disabled directory icons
            self.toggle_icons()
        self.focus_position = 0
        for n in range(1, len(self.body), 3):
            self.body[n].reset()  # reset all filelistboxes

    def get_output(self):
        lst = []
        for n in range(1, len(self.body), 3):
            lst.extend(self.body[n].get_output())
        return lst


class FileArranger:
    def __init__(self, files):
        self.status = True
        self.original = files
        self.palette = [
            ('titlebar', 'black', 'light gray'),
            ('titlebar-divide', 'black', 'black'),
            ('green button', 'dark green, bold', 'black'),
            ('red button', 'dark red, bold', 'black'),
            ('reversed', 'standout', ''),
        ]
        header_cols = urwid.Columns([
            ('weight', 5, urwid.Text(version)),
            ('weight', 7, urwid.Text(u'manual file reorder'))
        ])

        self.body = DirectoryListBox(files)
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
            return self.body.get_output()
        else:
            # operation aborted, return None
            print('Batch rename was aborted')
            return None


def main(files):
    tui = FileArranger(files)
    return tui.main()
