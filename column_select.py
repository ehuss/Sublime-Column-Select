import sublime, sublime_plugin

view_directions = {}


class ColumnSelect(sublime_plugin.TextCommand):

    def all_selections_at_begin_end(self, sel):
        """Determines if all selections are at the beginning or end of lines.

        :Returns: 'BEGIN' if all selections are at the beginning of a line.
        'END' if they are all at the end.  None otherwise.
        """
        at_begin_end = None
        for i, s in enumerate(sel):
            # Don't bother looking at more than a thousand lines.
            if i > 1000:
                break

            if at_begin_end == 'BEGIN':
                if s.begin() == self.view.line(s.begin()).begin():
                    pass
                elif s.end() == self.view.line(s.end()).end():
                    at_begin_end = 'END'
                else:
                    return None

            elif at_begin_end == 'END':
                if s.end() == self.view.line(s.end()).end():
                    pass
                else:
                    return None

            else:
                # None
                if s.begin() == self.view.line(s.begin()).begin():
                    at_begin_end = 'BEGIN'
                elif s.end() == self.view.line(s.end()).end():
                    at_begin_end = 'END'
                else:
                    break
        return at_begin_end

    def should_undo(self, sel, forward):
        """Determines if it should undo the last motion.

        :Returns: True if it should shrink the selection.
        """
        # This mostly works, since it is relatively safe to assume the motion
        # starts from a single region.  This might not always work as
        # expected, for example after a "find all".
        last_motion = view_directions.get(self.view.id())
        if ((last_motion == 'UP' and forward) or
            (last_motion == 'DOWN' and not forward)
           ):
            if len(sel) > 1:
                return True
        return False

    def run_(self, *args):
        if len(args) == 1:
            # Sublime 2
            kwargs = args[0]
            edit = self.view.begin_edit(self.name(), kwargs)
        else:
            # Sublime 3
            edit_token, kwargs = args
            edit = self.view.begin_edit(edit_token, self.name(), kwargs)

        if 'event' in kwargs:
            event = kwargs['event']
            del kwargs['event']
        else:
            event = None

        try:
            self.run(edit=edit, event=event, **kwargs)
        finally:
            self.view.end_edit(edit)

    def run(self, edit=None, by='lines', forward=True, event=None):
        all_sel = self.view.sel()
        if len(all_sel) == 1 and self.view.id() in view_directions:
            # Reset when first starting.
            del view_directions[self.view.id()]

        # Whether or not to ignore lines that are too short in the line count.
        # I particularly want PgUp/PgDn to always be 1 screenfull.
        ignore_too_short = by in ('lines', 'all')

        # Yes, this is a little messy.
        # How far to go?  This computes num_lines.
        # Mouse movement may change `all_sel` and `forward`.
        if by == 'lines':
            num_lines = 1
        elif by == 'pages':
            # Is there a better way?
            vr = self.view.visible_region()
            lines = self.view.lines(vr)
            num_lines = len(lines)
        elif by == 'all':
            num_lines = 2147483647
        elif by == 'mouse':
            orig_sel = [s for s in all_sel]
            # Determine where the mouse click was.
            self.view.run_command('drag_select', {'event': event})
            all_sel = self.view.sel()
            click_point = all_sel[0].a
            # Delay restoring the selection.  I'm running into a weird bug.
            # After calling rowcol(), if you do not change the length of the
            # selection, sublime gets into a wonky state.

            # `relative` is the point from which the selection should grow.
            if click_point < orig_sel[0].begin():
                forward = False
                relative = orig_sel[0].begin()
                # Prevent undo.
                view_directions.pop(self.view.id(), None)
            elif click_point > orig_sel[-1].end():
                forward = True
                relative = orig_sel[-1].end()
                # Prevent undo.
                view_directions.pop(self.view.id(), None)
            else:
                # Clicked within a line of the existing regions.
                last_motion = view_directions.get(self.view.id())
                # Allow undo if possible.
                if last_motion == 'UP':
                    forward = True
                    relative = orig_sel[0].begin()
                elif last_motion == 'DOWN':
                    forward = False
                    relative = orig_sel[-1].end()
                else:
                    # No last motion, abort.
                    return
            crow, ccol = self.view.rowcol(click_point)
            rrow, rcol = self.view.rowcol(relative)

            if forward:
                num_lines = crow - rrow
            else:
                num_lines = rrow - crow

            if num_lines == 0:
                # Clicked on the same line as the current selection.
                # Unfortunately due to an issue in sublime, I can't seem to
                # get it to work properly if I restore the original selection
                # (as long as the length of the selection doesn't change, it
                # gets confused).
                return

            # Restore selection after running drag_select.
            all_sel.clear()
            for r in orig_sel:
                all_sel.add(r)
        else:
            sublime.error_message('Invalid "by" argument.')
            return

        if self.should_undo(all_sel, forward):
            # Remove the appropriate regions from the selection.
            sels = [s for s in all_sel]
            num_to_remove = min(num_lines, len(all_sel)-1)
            if forward:
                sels = sels[:num_to_remove]
            else:
                sels = sels[-num_to_remove:]
            for s in sels:
                all_sel.subtract(s)
            if forward:
                self.view.show(all_sel[0])
            else:
                self.view.show(all_sel[-1])
            # Importantly, this does not update view_directions.
            return

        all_begin_end = self.all_selections_at_begin_end(all_sel)

        if forward:
            sp = all_sel[len(all_sel)-1].end()
        else:
            sp = all_sel[0].begin()
        current_line = self.view.line(sp)
        sp_column = self._column_from_pt(sp)
        # Count of selections made.
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
            if all_begin_end == 'BEGIN':
                sel_pos = next_line.begin()
            elif all_begin_end == 'END':
                sel_pos = next_line.end()
            else:
                if self._line_size(next_line) >= sp_column:
                    # A good line.
                    sel_pos = self._pt_from_column(sp_column, next_line.begin())
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

        if forward:
            view_directions[self.view.id()] = 'DOWN'
        else:
            view_directions[self.view.id()] = 'UP'

    def _column_from_pt(self, pt):
        # From indentation.py.
        tab_size = self._tab_size()
        col = 0
        ln = self.view.line(pt)
        for lpt in range(ln.begin(), pt):
            ch = self.view.substr(lpt)
            if ch == '\t':
                col += tab_size - (col % tab_size)
            else:
                col += 1
        return col

    def _pt_from_column(self, desired_col, line_pt):
        tab_size = self._tab_size()
        col = 0
        ln = self.view.line(line_pt)
        for lpt in range(ln.begin(), ln.end()):
            if col >= desired_col:
                break
            ch = self.view.substr(lpt)
            if ch == '\t':
                col += tab_size - (col % tab_size)
            else:
                col += 1
        else:
            return lpt+1
        return lpt

    def _line_size(self, line):
        return self._column_from_pt(line.end())

    def _tab_size(self):
        return int(self.view.settings().get('tab_size', 8))
