import os

import urwid

from batchren._version import __version__


def create_selectable(text, padding=0):
    sel = VariableSelectable(text)
    item = urwid.AttrMap(urwid.Padding(sel, left=padding), None, focus_map='reversed')
    return item


class VariableSelectable(urwid.SelectableIcon):
    '''
    SelectableIcon that toggles focus
    '''
    def __init__(self, text, cursor_position=1):
        self.enable_focus = True
        super(VariableSelectable, self).__init__(text, cursor_position)

    def toggle_focus(self):
        self.enable_focus = not self.enable_focus

    def selectable(self):
        return self.enable_focus


class ControlBox(urwid.ListBox):
    '''
    Listbox that enables and disables focus on some items
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
        super(ControlBox, self).__init__(body)

    def keypress(self, size, key):
        key = super(ControlBox, self).keypress(size, key)
        if key == 'esc':
            pos = self.focus_position
            self.body[pos].toggle_focus()   # disable selection on filelistbox
            self.toggle_icons()             # enable selection on directory icons
            self.focus_position -= 1
        if key == 'enter':
            pos = self.focus_position
            self.body[pos + 1].toggle_focus()   # enable selection on filelistbox
            self.toggle_icons()                 # disable selection on directory icons
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


class FileListBox(urwid.ListBox):
    def __init__(self, dirpath, files):
        self.dirpath = dirpath
        self.files = files

        self.activepos = None  # which pos we're moving
        self.toggle = False  # are we moving something
        self.enable_focus = False

        lst = [create_selectable(f, 4) for f in self.files]
        body = urwid.SimpleFocusListWalker(lst)
        super(FileListBox, self).__init__(body)

    def keypress(self, size, key):
        key = super(FileListBox, self).keypress(size, key)
        if key != 'enter':
            return key

        if self.toggle:
            # move activepos to current focus position
            lst = self.body
            item = lst.pop(self.activepos)
            lst.insert(self.focus_position, item)
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


stylesheet = [
    # stylesheet for the app
    ('titlebar', 'black', 'white'),
    ('reset button', 'dark green, bold', 'black'),
    ('quit button', 'dark red, bold', 'black'),
    ('abort button', 'dark red, bold', 'black'),
    ('reversed', 'standout', ''),
    ('resetting', 'dark blue', 'black')
]

version = 'batchren ' + __version__

# create columns for the header for the header
header_cols = urwid.Columns([
    ('weight', 5, urwid.Text(version)),
    ('weight', 7, urwid.Text(u'manual file reorder'))
])

header = urwid.Pile([
    urwid.AttrMap(urwid.Padding(header_cols, left=2), 'titlebar'),
    urwid.Divider()
])

menu = urwid.Text([
    ('reset button', u'(r)'), u':reset  ',
    ('quit button', u'(q)'), u':save and quit  ',
    ('abort button', u'(c)'), u':abort batchren  ',
])


def main(files):
    def handle_input(key):
        if key == 'R' or key == 'r':
            # send a signal to reset files
            app.widget.body.reset()
        elif key == 'C' or key == 'c':
            # send a signal to abort batchren
            app.abort = True
            raise urwid.ExitMainLoop()
        elif key == 'Q' or key == 'q':
            # send a signal to return contents of body
            raise urwid.ExitMainLoop()

    body = ControlBox(files)
    layout = urwid.Frame(header=header, body=body, footer=menu)
    app = urwid.MainLoop(layout, stylesheet, unhandled_input=handle_input)
    app.abort = False
    app.run()

    if app.abort:
        print('batchren operation was aborted')
        return None
    else:
        ret = app.widget.body.get_output()
        return ret