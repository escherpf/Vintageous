import sublime
import sublime_plugin

from Vintageous.vi.constants import regions_transformer
from Vintageous.vi.constants import MODE_VISUAL, MODE_NORMAL, _MODE_INTERNAL_NORMAL
from Vintageous.state import VintageState


class ViMoveToHardBol(sublime_plugin.TextCommand):
    def run(self, edit, extend=False):
        sels = list(self.view.sel())
        self.view.sel().clear()

        new_sels = []
        for s in sels:
            hard_bol = self.view.line(s.b).begin()
            if s.a < s.b and (self.view.line(s.a) != self.view.line(s.b)) and self.view.full_line(hard_bol - 1).b == hard_bol:
                hard_bol += 1
            a, b = (hard_bol, hard_bol) if not extend else (s.a, hard_bol)
            # Avoid ending up with a en empty selection while on visual mode.

            if extend and s.a == hard_bol:
                b = b + 1
            new_sels.append(sublime.Region(a, b))

        for s in new_sels:
            self.view.sel().add(s)

# FIXME: Only find exact char counts. Vim ignores the command when the count is larger than the
# number of instances of the sought character.
class ViFindInLineInclusive(sublime_plugin.TextCommand):
    def run(self, edit, extend=False, character=None, mode=None, count=1):
        def f(view, s):
            offset = s.b + 1 - view.line(s.b).a
            a, eol = s.b + 1, view.line(s.b).b
            final_offset = -1

            try:
                for i in range(count):
                    line_text = view.substr(sublime.Region(a, eol))
                    match_in_line = line_text.index(character)

                    final_offset = offset + match_in_line

                    a = view.line(s.a).a + final_offset + 1
                    offset += match_in_line + 1
            except ValueError:
                pass

            if final_offset > -1:
                pt = view.line(s.b).a + final_offset

                state = VintageState(view)
                if state.mode == MODE_VISUAL or mode == _MODE_INTERNAL_NORMAL:
                    return sublime.Region(s.a, pt + 1)

                return sublime.Region(pt, pt)

            return s

        regions_transformer(self.view, f)


# FIXME: Only find exact char counts. Vim ignores the command when the count is larger than the
# number of instances of the sought character.
class ViReverseFindInLineInclusive(sublime_plugin.TextCommand):
    def run(self, edit, extend=False, character=None, mode=None, count=1):
        def f(view, s):
            line_text = view.substr(sublime.Region(view.line(s.b).a, s.b))
            offset = 0
            a, b = view.line(s.b).a, s.b
            final_offset = -1

            try:
                for i in range(count):
                    line_text = view.substr(sublime.Region(a, b))
                    match_in_line = line_text.rindex(character)

                    final_offset = match_in_line

                    b = view.line(s.a).a + final_offset
            except ValueError:
                pass

            if final_offset > -1:
                pt = view.line(s.b).a + final_offset

                state = VintageState(view)
                if state.mode == MODE_VISUAL or mode == _MODE_INTERNAL_NORMAL:
                    return sublime.Region(s.a, pt)

                return sublime.Region(pt, pt)

            return s

        regions_transformer(self.view, f)


class ViFindInLineExclusive(sublime_plugin.TextCommand):
    """Contrary to *f*, *t* does not look past the caret's position, so if ``character`` is under
       the caret, nothing happens.
    """
    def run(self, edit, extend=False, character=None, mode=None, count=1):
        def f(view, s):
            offset = s.b + 1 - view.line(s.b).a
            a, eol = s.b + 1, view.line(s.b).b
            final_offset = -1

            try:
                for i in range(count):
                    line_text = view.substr(sublime.Region(a, eol))
                    match_in_line = line_text.index(character)

                    final_offset = offset + match_in_line

                    a = view.line(s.a).a + final_offset + 1
                    offset += match_in_line + 1
            except ValueError:
                pass

            if final_offset > -1:
                pt = view.line(s.b).a + final_offset

                state = VintageState(view)
                if state.mode == MODE_VISUAL or mode == _MODE_INTERNAL_NORMAL:
                    return sublime.Region(s.a, pt)

                return sublime.Region(pt - 1, pt - 1)

            return s

        regions_transformer(self.view, f)


class ViReverseFindInLineExclusive(sublime_plugin.TextCommand):
    """Contrary to *F*, *T* does not look past the caret's position, so if ``character`` is right
       before the caret, nothing happens.
    """
    def run(self, edit, extend=False, character=None, mode=None, count=1):
        def f(view, s):
            line_text = view.substr(sublime.Region(view.line(s.b).a, s.b))
            a, b = view.line(s.b).a, s.b
            final_offset = -1

            try:
                for i in range(count):
                    line_text = view.substr(sublime.Region(a, b))
                    match_in_line = line_text.rindex(character)

                    final_offset = match_in_line

                    b = view.line(s.a).a + final_offset
            except ValueError:
                pass

            if final_offset > -1:
                pt = view.line(s.b).a + final_offset

                state = VintageState(view)
                if state.mode == MODE_VISUAL or mode == _MODE_INTERNAL_NORMAL:
                    return sublime.Region(s.a, pt + 1)

                return sublime.Region(pt + 1, pt + 1)

            return s

        regions_transformer(self.view, f)


class ViGoToLine(sublime_plugin.TextCommand):
    def run(self, edit, extend=False, line=None):
        line = line if line > 0 else 1
        dest = self.view.text_point(line - 1, 0)

        def f(view, s):
            if not extend:
                return sublime.Region(dest, dest)
            else:
                return sublime.Region(s.a, dest)

        regions_transformer(self.view, f)

        # FIXME: Bringing the selections into view will be undesirable in many cases. Maybe we
        # should have an optional .scroll_selections_into_view() step during command execution.
        self.view.show(self.view.sel()[0])


class ViPercent(sublime_plugin.TextCommand):
    def run(self, edit, extend=False, percent=None):
        if percent == None:
            return

        row = self.view.rowcol(self.view.size())[0] * (percent / 100)

        def f(view, s):
            pt = view.text_point(row, 0)
            return sublime.Region(pt, pt)

        regions_transformer(self.view, f)

        # FIXME: Bringing the selections into view will be undesirable in many cases. Maybe we
        # should have an optional .scroll_selections_into_view() step during command execution.
        self.view.show(self.view.sel()[0])


class ViBigH(sublime_plugin.TextCommand):
    def run(self, edit, extend=False, count=0):
        r = self.view.visible_region()
        row, _ = self.view.rowcol(r.a)
        row += count + 1

        target = self.view.text_point(row, 0)

        self.view.sel().clear()
        self.view.sel().add(sublime.Region(target, target))
        self.view.show(target)


class ViBigL(sublime_plugin.TextCommand):
    def run(self, edit, extend=False, count=0):
        r = self.view.visible_region()
        row, _ = self.view.rowcol(r.b)
        row -= count + 1

        target = self.view.text_point(row, 0)

        self.view.sel().clear()
        self.view.sel().add(sublime.Region(target, target))
        self.view.show(target)


class ViBigM(sublime_plugin.TextCommand):
    def run(self, edit, extend=False):
        r = self.view.visible_region()
        row_a, _ = self.view.rowcol(r.a)
        row_b, _ = self.view.rowcol(r.b)
        row = ((row_a + row_b) / 2)

        target = self.view.text_point(row, 0)

        self.view.sel().clear()
        self.view.sel().add(sublime.Region(target, target))
        self.view.show(target)


class ViStar(sublime_plugin.TextCommand):
    def run(self, edit, mode=None, count=1, extend=False):
        state = VintageState(self.view)
        def f(view, s):
            # TODO: make sure we swallow any leading white space.
            query = view.substr(view.word(s.end()))
            
            if mode == _MODE_INTERNAL_NORMAL:
                match = view.find(query, view.word(s.end()).end(), sublime.LITERAL)
            else:
                match = view.find(query, view.word(s).end(), sublime.LITERAL)

            if match:
                if mode == _MODE_INTERNAL_NORMAL:
                    return sublime.Region(s.a, match.begin())
                elif state.mode == MODE_VISUAL:
                    return sublime.Region(s.a, match.begin())
                elif state.mode == MODE_NORMAL:
                    return sublime.Region(match.begin(), match.begin())
            return s

        regions_transformer(self.view, f)


class ViOctothorp(sublime_plugin.TextCommand):
    def run(self, edit, mode=None, count=1, extend=False):
        state = VintageState(self.view)
        def f(view, s):
            return s

        regions_transformer(self.view, f)