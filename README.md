Sublime Column Select
=====================

This plugin provides an alternate behavior for Sublime keyboard column selection.  I often found it challenging to select columns with lines that were shorter than the rest.

Downloading
-----------
The best way to download and install Sublime Column Select is to use the Package Control plugin.  If you do not already have it installed, it's really the best way to manage your packages.

XXX TBD

Configuring
-----------
No need to configure anything.  By default it uses the default keystroke for column selection, plus a few extras.  These keystrokes will select the same column in the next or previous line, page, or until the beginning/end of the document.

Windows:

- Ctrl-Alt-Up / Ctrl-Alt-Down: Up/down one line.
- Ctrl-Alt-PageUp / Ctrl-Alt-PageDown: Up/down one page.
- Ctrl-Alt-Home: Up until the beginning of the document.
- Ctrl-Alt-End: Down until the end of the document.

Linux:

- Alt-Shift-Up / Ctrl-Alt-Down: Up/down one line.
- Alt-Shift-PageUp / Ctrl-Alt-PageDown: Up/down one page.
- Alt-Shift-Home: Up until the beginning of the document.
- Alt-Shift-End: Down until the end of the document.

OS X:

- Ctrl-Shift-Up / Ctrl-Alt-Down: Up/down one line.
- Ctrl-Shift-PageUp / Ctrl-Alt-PageDown: Up/down one page.
- Ctrl-Shift-Home: Up until the beginning of the document.
- Ctrl-Shift-End: Down until the end of the document.

If you want to use a different keystroke, go to "Preferences" then "Key Bindings - User", and add an entry like this:

	{ "keys": ["ctrl+alt+up"], "command": "column_select", "args": {"by": "lines", "forward": false}},
	{ "keys": ["ctrl+alt+down"], "command": "column_select", "args": {"by": "lines", "forward": true}},
	{ "keys": ["ctrl+alt+pageup"], "command": "column_select", "args": {"by": "pages", "forward": false}},
	{ "keys": ["ctrl+alt+pagedown"], "command": "column_select", "args": {"by": "pages", "forward": true}},
	{ "keys": ["ctrl+alt+home"], "command": "column_select", "args": {"by": "all", "forward": false}},
	{ "keys": ["ctrl+alt+end"], "command": "column_select", "args": {"by": "all", "forward": true}},

Do not include the trailing comma if it is the last entry.

Using
-----
You should be able to place the character on any position on the line, and then use the keystrokes to add additional carets (cursors) to the next/previous lines.  It will skip over lines that are too short.

It will behave differently if the cursor is at the end of the line.  In this case, it will select the end of every line.

Contact
-------
If you find a bug, or have suggestions, head over to the github page:
https://github.com/ehuss/Sublime-Column-Select
