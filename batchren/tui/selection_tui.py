#!/usr/bin/env python3
import urwid

from batchren._version import __version__

version = 'batchren ' + __version__


def create_checkbox(text):
    box = urwid.Padding(urwid.CheckBox(text), left=2)
    return urwid.AttrMap(box, 'buttn', 'buttnf')


class FileListBox(urwid.ListBox):
    def __init__(self, files):
        super().__init__([create_checkbox(f) for f in files])

    def get_selected(self):
        return [item.base_widget.label for item in self.body if item.base_widget.state]

    def toggle_all(self, state):
        for item in self.body:
            item.base_widget.set_state(state)
        self.focus_position = 0


class FileSelector:
    def __init__(self, files):
        self.status = True
        self.palette = [
            ('titlebar', 'black', 'light gray'),
            ('titlebar-divide', 'black', 'black'),
            ('select button', 'dark green, bold', 'black'),
            ('reset button', 'dark green, bold', 'black'),
            ('quit button', 'dark red, bold', 'black'),
            ('abort button', 'dark red, bold', 'black'),
            ('reversed', 'standout', ''),
            ('buttn', 'light gray', 'black'),
            ('buttnf', 'light gray', 'black', 'bold'),
        ]
        header_cols = urwid.Columns([
            ('weight', 5, urwid.Text(version)),
            ('weight', 7, urwid.Text(u'manual file selection'))
        ])

        self.body = FileListBox(files)
        self.header = urwid.Pile([
            urwid.AttrMap(urwid.Padding(header_cols, left=2), 'titlebar'),
            urwid.AttrMap(urwid.Divider(), 'titlebar-divide')
        ])
        self.footer = urwid.Text([
            ('select button', u'(a)'), u':select all  ',
            ('reset button', u'(r)'), u':unselect all  ',
            ('quit button', u'(q)'), u':save and quit  ',
            ('abort button', u'(c)'), u':abort batchren  ',
        ])
        self.view = urwid.Frame(header=self.header,
            body=self.body,
            footer=self.footer)

    def unhandled_input(self, key):
        if key in ('a', 'A'):
            # send a signal to select all files
            self.body.toggle_all(True)
        elif key in ('r', 'R'):
            # send a signal to unselect all files
            self.body.toggle_all(False)
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
            # operation success, return selected files
            return self.body.get_selected()
        else:
            # operation aborted, return None
            print('Batch rename was aborted')
            return None


def main(files):
    tui = FileSelector(files)
    return tui.main()


if __name__ == '__main__':
    main()
