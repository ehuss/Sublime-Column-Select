import sys
import sublime, sublime_plugin

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

    def run(self, edit, by, forward):
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

