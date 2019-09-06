import urwid

from batchren._version import __version__


stylesheet = [
    ('titlebar', 'black', 'white'),
    ('titlebar-divide', 'black', 'black'),
    ('select button', 'dark green, bold', 'black'),
    ('reset button', 'dark green, bold', 'black'),
    ('quit button', 'dark red, bold', 'black'),
    ('abort button', 'dark red, bold', 'black'),
    ('reversed', 'standout', ''),
    ('buttn', 'white', 'black'),
    ('buttnf', 'white', 'black', 'bold'),
]

version = 'batchren ' + __version__

# create columns for the header for the header
header_cols = urwid.Columns([
    ('weight', 5, urwid.Text(version)),
    ('weight', 7, urwid.Text(u'manual file selection'))
])

header = urwid.Pile([
    urwid.AttrMap(urwid.Padding(header_cols, left=2), 'titlebar'),
    urwid.AttrMap(urwid.Divider(), 'titlebar-divide')
])

menu = urwid.Text([
    ('select button', u'(a)'), u':select all  ',
    ('reset button', u'(r)'), u':unselect all  ',
    ('quit button', u'(q)'), u':save and quit  ',
    ('abort button', u'(c)'), u':abort batchren  ',
])


def create_checkbox(text):
    box = urwid.Padding(urwid.CheckBox(text), left=2)
    return urwid.AttrMap(box, 'buttn', 'buttnf')


def main(files):
    def handle_input(key):
        if key == 'R' or key == 'r':
            # send a signal to unselect files
            wdgt = app.widget.body
            for n in wdgt.body:
                n.base_widget.set_state(False)
            wdgt.focus_position = 0
        elif key == 'A' or key == 'a':
            # send a signal to select all files
            wdgt = app.widget.body
            for n in wdgt.body:
                n.base_widget.set_state(True)
            wdgt.focus_position = 0
        elif key == 'C' or key == 'c':
            # send a signal to abort batchren
            app.abort = True
            raise urwid.ExitMainLoop()
        elif key == 'Q' or key == 'q':
            # send a signal to return contents of body
            raise urwid.ExitMainLoop()

    body = urwid.ListBox([create_checkbox(f) for f in files])
    layout = urwid.Frame(header=header, body=body, footer=menu)
    app = urwid.MainLoop(layout, stylesheet, unhandled_input=handle_input)
    app.abort = False
    app.run()

    if app.abort:
        print('Batch rename was aborted')
        return None
    else:
        wdgt = app.widget.body
        return [n.base_widget.label for n in wdgt.body if n.base_widget.state]
