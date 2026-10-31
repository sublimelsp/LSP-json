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
from LSP.plugin import request_handler
from LSP.plugin import uri_handler
from lsp_utils import NodeManager
from pathlib import Path
from sublime_lib import ResourcePath
from typing import Any
from typing import final
from typing import TYPE_CHECKING
from typing_extensions import override
from urllib.parse import quote
import re

if TYPE_CHECKING:
    from LSP.protocol import DocumentUri
    import sublime


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
            node_version_requirement='>=18',
        )

    @override
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._jsonc_patterns: list[re.Pattern[str]] = []

    @override
    async def on_initialized(self) -> None:
        self.schema_store.add_listener(self)
        await self.schema_store.initialize()

    @override
    async def on_pre_send_notification(self, notification: ClientNotification) -> None:
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
                await self.schema_store.reload_schemas()
            return

    def _create_pattern_regexp(self, pattern: str) -> re.Pattern[str]:
        # This matches handling of patterns in vscode-json-languageservice.
        escaped = re.sub(r'[\-\\\{\}\+\?\|\^\$\.\,\[\]\(\)\#\s]', r'\\\g<0>', pattern)
        escaped = re.sub(r'[\*]', r'.*', escaped)
        return re.compile(escaped + '$')

    @request_handler('vscode/content')
    async def handle_vscode_content(self, params: tuple[str]) -> str | None:
        return self.schema_store.get_schema_for_uri(params[0])

    @command_handler('json.sort')
    async def on_json_sort(self, _: list[None] | None) -> None:
        if (session := self.weaksession()) and (view := session.window.active_view()):
            view.run_command('lsp_json_sort_document')

    @uri_handler('json-schema')
    async def handle_json_schema_uri(self, uri: DocumentUri, _flags: sublime.NewFileFlags) -> sublime.Sheet | None:
        print(f'LSP-json: Unhandled URI: {uri}')  # ruff: ignore[print]
        return None

    # --- StoreListener ------------------------------------------------------------------------------------------------

    @override
    async def on_store_changed(self, schemas: list[SchemaEntry]) -> None:
        if session := self.weaksession():
            user_schemas: list[SchemaEntry] = deepcopy(session.config.settings.get('userSchemas') or [])
            # The server combines all matching schemas, so a user pattern must remove the same bundled pattern
            # for the user schema to replace the bundled one. Bundled patterns are URL-quoted by the store.
            user_patterns = {quote(fm, safe='/*!') for s in user_schemas for fm in s.get('fileMatch', [])}
            store_schemas = deepcopy(schemas)
            if user_patterns:
                for schema in store_schemas:
                    if file_match := schema.get('fileMatch'):
                        schema['fileMatch'] = [fm for fm in file_match if fm not in user_patterns]
            all_schemas = store_schemas + user_schemas
            if folders := session.get_workspace_folders():
                for schema in all_schemas:
                    # Filesystem paths are resolved relative to the first workspace folder.
                    if schema['uri'].startswith(('.', '/')):
                        absolute_path = Path(folders[0].path, schema['uri'])
                        schema['uri'] = filename_to_uri(str(absolute_path))
            await session.notify(Notification('json/schemaAssociations', [all_schemas]))


def plugin_loaded() -> None:
    LspJSONPlugin.register()


def plugin_unloaded() -> None:
    LspJSONPlugin.unregister()
