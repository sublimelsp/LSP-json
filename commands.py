from LSP.plugin import apply_text_edits
from LSP.plugin import LspTextCommand
from LSP.plugin import Request
from LSP.plugin import uri_from_view
from LSP.plugin.core.protocol import DocumentUri
from LSP.plugin.core.protocol import Error
from LSP.plugin.core.protocol import FormattingOptions
from LSP.plugin.core.protocol import TextEdit
from LSP.plugin.core.typing import List, TypedDict, Union
from LSP.plugin.core.views import formatting_options
import sublime


JsonSortDocumentParams = TypedDict('JsonSortDocumentParams', {
    'uri': DocumentUri,
    'options': FormattingOptions,
})


class LspJsonSortDocument(LspTextCommand):

    session_name = __package__

    def run(self, _: sublime.Edit) -> None:
        session = self.session_by_name(self.session_name)
        if session is None:
            return
        view = self.view
        params = {
            'uri': uri_from_view(view),
            'options': formatting_options(view.settings()),
        }  # type: JsonSortDocumentParams
        session.send_request_task(Request('json/sort', params)).then(self._on_result_async)

    def _on_result_async(self, response: Union[List[TextEdit], Error]) -> None:
        if isinstance(response, Error):
            sublime.message_dialog(str(response))
            return
        apply_text_edits(self.view, response)
