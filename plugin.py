from __future__ import annotations

from .schema_store import SchemaEntry
from .schema_store import SchemaStore
from .schema_store import StoreListener
from copy import deepcopy
from LSP.plugin import ClientNotification
from LSP.plugin import command_handler
from LSP.plugin import filename_to_uri
from LSP.plugin import LspPlugin
from LSP.plugin import Notification
from LSP.plugin import OnPreStartContext
from LSP.plugin import Promise
from LSP.plugin import request_handler
from lsp_utils import NodeManager
from pathlib import Path
from sublime_lib import ResourcePath
from typing import Any
from typing import final
from typing_extensions import override
import re


@final
class LspJSONPlugin(LspPlugin, StoreListener):
    schema_store = SchemaStore()

    @classmethod
    @override
    def on_pre_start_async(cls, context: OnPreStartContext) -> None:
        package_name = cls.plugin_storage_path.name
        NodeManager.on_pre_start_async(
            context,
            cls.plugin_storage_path,
            ResourcePath('Packages', package_name, 'language-server'),
            Path('out', 'node', 'jsonServerMain.js'),
            '>=18',
        )

    @override
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._jsonc_patterns: list[re.Pattern[str]] = []

    @override
    def on_initialize_async(self) -> None:
        self.schema_store.add_listener(self)
        self.schema_store.initialize()

    @override
    def on_pre_send_notification_async(self, notification: ClientNotification) -> None:
        if notification['method'] == 'textDocument/didOpen':
            text_document = notification['params']['textDocument']
            if any(pattern.search(text_document['uri']) for pattern in self._jsonc_patterns):
                text_document['languageId'] = 'jsonc'
            return
        if notification['method'] == 'workspace/didChangeConfiguration' and (session := self.weaksession()):
            jsonc_patterns: list[str] = session.config.settings.get('jsonc.patterns') or []
            new_patterns = list(map(self._create_pattern_regexp, jsonc_patterns))
            if self._jsonc_patterns != new_patterns:
                self._jsonc_patterns = new_patterns
                self.schema_store.reload_schemas()
            return

    def _create_pattern_regexp(self, pattern: str) -> re.Pattern[str]:
        # This matches handling of patterns in vscode-json-languageservice.
        escaped = re.sub(r'[\-\\\{\}\+\?\|\^\$\.\,\[\]\(\)\#\s]', r'\\\g<0>', pattern)
        escaped = re.sub(r'[\*]', r'.*', escaped)
        return re.compile(escaped + '$')

    @request_handler('vscode/content')
    def handle_vscode_content(self, params: tuple[str]) -> Promise[str | None]:
        return Promise.resolve(self.schema_store.get_schema_for_uri(params[0]))

    @command_handler('json.sort')
    def on_json_sort(self, _: list[None] | None) -> Promise[None]:
        if (session := self.weaksession()) and (view := session.window.active_view()):
            view.run_command('lsp_json_sort_document')
        return Promise.resolve(None)

    # --- StoreListener ------------------------------------------------------------------------------------------------

    @override
    def on_store_changed_async(self, schemas: list[SchemaEntry]) -> None:
        if session := self.weaksession():
            user_schemas: list[SchemaEntry] = deepcopy(session.config.settings.get('userSchemas') or [])
            if folders := session.get_workspace_folders():
                for schema in schemas:
                    # Filesystem paths are resolved relative to the first workspace folder.
                    if schema['uri'].startswith(('.', '/')):
                        absolute_path = Path(folders[0].path, schema['uri'])
                        schema['uri'] = filename_to_uri(str(absolute_path))
            session.send_notification(Notification('json/schemaAssociations', [schemas + user_schemas]))


def plugin_loaded() -> None:
    LspJSONPlugin.register()


def plugin_unloaded() -> None:
    LspJSONPlugin.unregister()
