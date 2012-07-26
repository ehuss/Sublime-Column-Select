import sys
import sublime, sublime_plugin

# Notes:
# - Would prefer that after going down, pressing up would undo the last down,
#   not extend the selection from the top.  However, there's no simple way
#   that I can think of to determine which direction the last move was.

class ColumnSelect(sublime_plugin.TextCommand):

    def all_selections_at_end(self, sel):
        at_end = True
        for i, s in enumerate(sel):
            # Don't bother looking at more than a thousand lines.
            if i > 1000:
                break
            if s.end() != self.view.line(s.end()).end():
                at_end = False
                break
        return at_end

    def run_(self, args):
        if 'event' in args:
            event = args['event']
            del args['event']
        else:
            event = None
        edit = self.view.begin_edit(self.name(), args)
        try:
            self.run(edit=edit, event=event, **args)
        finally:
            self.view.end_edit(edit)

    def run(self, edit=None, by='lines', forward=True, event=None):
        all_sel = self.view.sel()

        # Whether or not to ignore lines that are too short in the line count.
        ignore_too_short = True
        # How far to go?
        if by == 'lines':
            num_lines = 1
        elif by == 'pages':
            # Is there a better way?
            vr = self.view.visible_region()
            lines = self.view.lines(vr)
            num_lines = len(lines)
            ignore_too_short = False
        elif by == 'all':
            num_lines = sys.maxint
        elif by == 'mouse':
            orig_sel = [s for s in all_sel]
            self.view.run_command('drag_select', {'event': event})
            all_sel = self.view.sel()
            click_point = all_sel[0].a
            all_sel.clear()
            map(all_sel.add, orig_sel)

            if click_point < all_sel[0].begin():
                forward = False
                relative = all_sel[0].begin()
            else:
                forward = True
                relative = all_sel[-1].end()
            crow, ccol = self.view.rowcol(click_point)
            rrow, rcol = self.view.rowcol(relative)

            if forward:
                if crow <= rrow: return
                num_lines = crow - rrow
            else:
                if crow >= rrow: return
                num_lines = rrow - crow
            ignore_too_short = False
        else:
            sublime.error_message('Invalid "by" argument.')
            return

        all_at_end = self.all_selections_at_end(all_sel)

        if forward:
            sp = all_sel[-1].end()
        else:
            sp = all_sel[0].begin()
        current_line = self.view.line(sp)
        sp_column = sp - current_line.begin()
        # Cound of selections made.
        sel_count = 0
        # Count of lines traversed.  Lines too short are not counted unless
        # ignore_too_short is False.
        line_count = 0
        # Keep track of the last selection made to scroll the viewport.
        last_sel = None
        while 1:
            if line_count >= num_lines:
                # Force it to select at least one line.
                if sel_count > 0:
                    break
            if forward:
                if current_line.end() == self.view.size():
                    # End of view.
                    break
                next_line = self.view.line(current_line.end()+1)
            else:
                if current_line.begin() == 0:
                    # Beginning of view.
                    break
                next_line = self.view.line(current_line.begin()-1)
            if all_at_end:
                sel_pos = next_line.end()
            else:
                if next_line.size() >= sp_column:
                    # A good line.
                    sel_pos = next_line.begin()+sp_column
                else:
                    # Line too short.
                    sel_pos = None
            if sel_pos == None:
                if not ignore_too_short:
                    line_count += 1
            else:
                r = sublime.Region(sel_pos, sel_pos)
                last_sel = r
                all_sel.add(r)
                line_count += 1
                sel_count += 1
            current_line = next_line

        if last_sel != None:
            self.view.show(last_sel)

