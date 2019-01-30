import urwid

from batchren._version import __version__


stylesheet = [
    ('titlebar', 'black', 'white'),
    ('titlebar-divide', 'black', 'black'),
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
    ('reset button', u'(r)'), u':reset  ',
    ('quit button', u'(q)'), u':save and quit  ',
    ('abort button', u'(c)'), u':abort batchren  ',
])


def create_checkbox(text):
    box = urwid.Padding(urwid.CheckBox(text), left=2)
    return urwid.AttrMap(box, 'buttn', 'buttnf')


def main(files):
    def handle_input(key):
        if key == 'R' or key == 'r':
            # send a signal to reset files
            wdgt = app.widget.body
            for n in wdgt.body:
                n.base_widget.set_state(False)
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
        print('batchren operation was aborted')
        return None
    else:
        ret = []
        wdgt = app.widget.body
        for n in wdgt.body:
            if n.base_widget.state:
                ret.append(n.base_widget.label)
        return ret