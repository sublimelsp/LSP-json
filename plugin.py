from __future__ import annotations

from .schema_store import SchemaEntry
from .schema_store import SchemaStore
from .schema_store import StoreListener
from LSP.plugin import DottedDict
from LSP.plugin import filename_to_uri
from LSP.plugin import Notification
from LSP.plugin import Promise
from LSP.plugin import request_handler
from lsp_utils import ApiWrapperInterface
from lsp_utils import NpmClientHandler
from pathlib import Path
from typing import Any
from typing import cast
from typing import final
from typing import TYPE_CHECKING
from typing_extensions import override
import re
import sublime
import sublime_plugin

if TYPE_CHECKING:
    from collections.abc import Callable
    from LSP.protocol import ExecuteCommandParams


def plugin_loaded():
    LspJSONPlugin.setup()


def plugin_unloaded():
    LspJSONPlugin.cleanup()


@final
class LspJSONPlugin(NpmClientHandler, StoreListener):
    package_name = str(__package__)
    server_directory = 'language-server'
    server_binary_path = str(Path(server_directory, 'out', 'node', 'jsonServerMain.js'))
    _schema_store = SchemaStore()

    @classmethod
    @override
    def required_node_version(cls) -> str:
        return '>=18'

    @classmethod
    @override
    def cleanup(cls) -> None:
        cls._schema_store.cleanup()
        super().cleanup()

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._api: ApiWrapperInterface | None = None
        self._user_schemas: list[SchemaEntry] = []
        self._jsonc_patterns: list[re.Pattern[str]] = []
        super().__init__(*args, **kwargs)

    @override
    def on_settings_changed(self, settings: DottedDict) -> None:
        self._user_schemas = self._resolve_file_paths(cast('list[SchemaEntry]', settings.get('userSchemas')) or [])
        self._jsonc_patterns = list(map(self._create_pattern_regexp, settings.get('jsonc.patterns') or []))
        self._schema_store.load_schemas_async()

    def _resolve_file_paths(self, schemas: list[SchemaEntry]) -> list[SchemaEntry]:
        if (session := self.weaksession()) and (folders := session.get_workspace_folders()):
            for schema in schemas:
                # Filesystem paths are resolved relative to the first workspace folder.
                if schema['uri'].startswith(('.', '/')):
                    absolute_path = Path(folders[0].path, schema['uri'])
                    schema['uri'] = filename_to_uri(str(absolute_path))
        return schemas

    def _create_pattern_regexp(self, pattern: str) -> re.Pattern[str]:
        # This matches handling of patterns in vscode-json-languageservice.
        escaped = re.sub(r'[\-\\\{\}\+\?\|\^\$\.\,\[\]\(\)\#\s]', r'\\\g<0>', pattern)
        escaped = re.sub(r'[\*]', r'.*', escaped)
        return re.compile(escaped + '$')

    @override
    def on_ready(self, api: ApiWrapperInterface) -> None:
        self._api = api
        self._schema_store.add_listener(self)

    @request_handler('vscode/content')
    def handle_vscode_content(self, params: tuple[str]) -> Promise[str | None]:
        return Promise.resolve(self._schema_store.get_schema_for_uri(params[0]))

    @override
    def on_pre_send_notification_async(self, notification: Notification[Any]) -> None:
        if notification.method == 'textDocument/didOpen':
            params = cast('dict[str, Any]', notification.params)
            text_document = params['textDocument']
            if any(pattern.search(text_document['uri']) for pattern in self._jsonc_patterns):
                text_document['languageId'] = 'jsonc'

    @override
    def on_pre_server_command(self, command: ExecuteCommandParams, done_callback: Callable[[], None]) -> bool:
        if command['command'] == 'json.sort':
            if (session := self.weaksession()) and (view := session.window.active_view()):
                view.run_command('lsp_json_sort_document')
            done_callback()
            return True
        return False

    # --- StoreListener ------------------------------------------------------------------------------------------------

    @override
    def on_store_changed_async(self, schemas: list[SchemaEntry]) -> None:
        if self._api:
            self._api.send_notification('json/schemaAssociations', [schemas + self._user_schemas])


class LspJsonAutoCompleteCommand(sublime_plugin.TextCommand):

    @override
    def run(self, _: sublime.Edit) -> None:
        self.view.run_command("insert_snippet", {"contents": '"$0"'})
        # Do auto-complete one tick later, otherwise LSP is not up-to-date with
        # the incremental text sync.
        sublime.set_timeout(lambda: self.view.run_command("auto_complete"))
