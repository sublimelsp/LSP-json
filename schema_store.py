from __future__ import annotations

from abc import ABCMeta
from abc import abstractmethod
from os import path
from sublime_lib import ResourcePath
from typing import Any
from typing import cast
from typing import Dict
from typing import TypedDict
from typing_extensions import NotRequired
from typing_extensions import TypeAlias
from urllib.parse import quote
from weakref import WeakSet
import sublime

package_name = str(__package__)


Schema: TypeAlias = Dict[str, Any]


class SchemaEntry(TypedDict):
    fileMatch: NotRequired[list[str]]
    schema: Schema
    uri: str


class StoreListener(metaclass=ABCMeta):

    @abstractmethod
    def on_store_changed_async(self, schemas: list[SchemaEntry]) -> None:
        pass


class SchemaStore:
    def __init__(self) -> None:
        self._listeners: WeakSet[StoreListener] = WeakSet()
        self._schema_list: list[SchemaEntry] = []
        self._schema_uri_to_content: dict[str, str] = {}
        self._schemas_loaded: bool = False
        self._watched_settings: list[sublime.Settings] = []

    def add_listener(self, listener: StoreListener) -> None:
        self._listeners.add(listener)
        if self._schemas_loaded:
            sublime.set_timeout_async(lambda: listener.on_store_changed_async(self._schema_list))

    def get_schema_for_uri(self, uri: str) -> str | None:
        if uri in self._schema_uri_to_content:
            return self._schema_uri_to_content[uri]
        if uri.startswith('sublime://'):
            schema_path = uri.replace('sublime://', '')
            schema_components = schema_path.split('/')
            domain = schema_components[0]
            if domain == 'schemas':
                # Internal schema - 1:1 schema path to file path mapping.
                schema_path = f'Packages/{package_name}/{schema_path}.json'
                return sublime.encode_value(sublime.decode_value(ResourcePath(schema_path).read_text()), pretty=False)
        print(f'{package_name}: Unknown schema URI "{uri}"')
        return None

    def cleanup(self) -> None:
        for settings in self._watched_settings:
            settings.clear_on_change(package_name)

    def load_schemas_async(self) -> None:
        if self._schemas_loaded:
            return
        settings = sublime.load_settings('sublime-package.json')
        settings.add_on_change(package_name, lambda: sublime.set_timeout_async(self._collect_schemas_async))
        self._watched_settings.append(settings)
        self._schemas_loaded = True
        self._collect_schemas_async()

    def _collect_schemas_async(self) -> None:
        self._schema_list = []
        self._schema_uri_to_content = {}
        self._load_bundled_schemas()
        global_preferences_schemas = self._load_package_schemas()
        self._generate_project_settings_schemas(global_preferences_schemas)
        self._load_syntax_schemas(global_preferences_schemas)
        self._on_schemas_changed()

    def _load_bundled_schemas(self) -> None:
        for schema in ['lsp-json-schemas_extra.json', 'lsp-json-schemas.json']:
            path = f'Packages/{package_name}/{schema}'
            schema_list = self._parse_schema(ResourcePath(path))
            if schema_list:
                self._register_schemas(schema_list)

    def _load_package_schemas(self) -> list[Schema]:
        global_preferences_schemas: list[Schema] = []
        resources = ResourcePath.glob_resources('sublime-package.json')
        for resource in resources:
            schema = self._parse_schema(resource)
            if not schema:
                continue
            settings: list[dict[str, Any]] = schema.get('contributions', {}).get('settings', [])
            for s in settings:
                i = len(self._schema_uri_to_content)
                file_patterns: list[str] | None = s.get('file_patterns')
                schema_content: Schema | None = s.get('schema')
                if not schema_content:
                    continue
                uri = schema_content.get('$id') or f'sublime://settings/{i}'
                self._schema_uri_to_content[uri] = sublime.encode_value(schema_content, pretty=False)
                self._register_schemas([{'fileMatch': file_patterns, 'uri': uri}])
                if file_patterns:
                    for pattern in file_patterns:
                        if pattern == '/Preferences.sublime-settings':
                            global_preferences_schemas.append(schema_content)
        return global_preferences_schemas

    def _generate_project_settings_schemas(self, global_preferences_schemas: list[Schema]) -> None:
        """
        Injects schemas mapped to /Preferences.json into the "settings" object in *.sublime.project schemas.
        """
        for i, schema in enumerate(global_preferences_schemas):
            schema_uri = f'sublime://auto-generated/sublime-project/{i}'
            schema_content = {
                '$schema': 'http://json-schema.org/draft-07/schema#',
                '$id': schema_uri,
                'allowComments': True,
                'allowTrailingCommas': True,
                'type': 'object',
                'properties': {
                    'settings': schema,
                },
            }
            self._schema_uri_to_content[schema_uri] = sublime.encode_value(schema_content, pretty=False)
            self._register_schemas([{'fileMatch': ['/*.sublime-project'], 'uri': schema_uri}])

    def _load_syntax_schemas(self, global_preferences_schemas: list[Schema]) -> None:
        """
        Discovers all available syntaxes and maps their file names to schema.
        """
        syntaxes = []
        try:
            syntaxes = sublime.list_syntaxes()
        except AttributeError:
            pass
        file_patterns = ['/{}.sublime-settings'.format(path.splitext(path.basename(s.path))[0]) for s in syntaxes]
        if file_patterns:
            self._register_schemas([{'fileMatch': file_patterns, 'uri': 'sublime://schemas/syntax.sublime-settings'}])
        if global_preferences_schemas:
            for i, schema in enumerate(global_preferences_schemas):
                schema_uri = f'sublime://auto-generated/syntax.sublime-settings/{i}'
                schema_content: Schema = {
                    '$schema': 'http://json-schema.org/draft-07/schema#',
                    '$id': schema_uri,
                    'allowComments': True,
                    'allowTrailingCommas': True,
                    'type': 'object',
                }
                schema_content.update(schema)
                self._schema_uri_to_content[schema_uri] = sublime.encode_value(schema_content, pretty=False)
                self._register_schemas([{'fileMatch': file_patterns, 'uri': schema_uri}])

    def _parse_schema(self, resource: ResourcePath) -> list[SchemaEntry] | None:
        try:
            return cast(list[SchemaEntry], sublime.decode_value(resource.read_text()))
        except Exception:
            print(f'Failed parsing schema "{resource.file_path()}"')
            return None

    def _register_schemas(self, schemas: list[SchemaEntry]) -> None:
        for schema in schemas:
            file_matches = schema.get('fileMatch')
            if file_matches:
                schema['fileMatch'] = [quote(fm, safe="/*!") for fm in file_matches]
            self._schema_list.append(schema)

    def _on_schemas_changed(self) -> None:
        for listener in self._listeners:
            listener.on_store_changed_async(self._schema_list)
