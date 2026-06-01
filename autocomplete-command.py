from __future__ import annotations

from typing import final
from typing_extensions import override
import sublime
import sublime_plugin

# This command on purpose lives in its own file, with no LSP-specific imports, to make it more resilient
# to breaking on updates and preventing '"' from working in JSON files.


@final
class LspJsonAutoCompleteCommand(sublime_plugin.TextCommand):

    @override
    def run(self, _: sublime.Edit) -> None:
        self.view.run_command("insert_snippet", {"contents": '"$0"'})
        # Do auto-complete one tick later, otherwise LSP is not up-to-date with the incremental text sync.
        sublime.set_timeout(lambda: self.view.run_command("auto_complete"))
