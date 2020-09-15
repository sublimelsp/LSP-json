from abc import ABCMeta, abstractmethod
from LSP.plugin.core.typing import Any, Dict, List, Optional
from lsp_utils import ApiWrapperInterface
from lsp_utils import NpmClientHandler
from os import path
from sublime_lib import ResourcePath
from urllib.parse import quote
from weakref import WeakSet
import sublime


def plugin_loaded():
    LspJSONPlugin.setup()


def plugin_unloaded():
    LspJSONPlugin.cleanup()


class StoreListener(metaclass=ABCMeta):

    @abstractmethod
    def on_store_changed(self, schemas: List[Dict]) -> None:
        pass


class SchemaStore:
    def __init__(self) -> None:
        self._listeners = WeakSet()  # type: WeakSet[StoreListener]
        self._schema_list = []  # type: List[Dict]
        self._schema_uri_to_content = {}  # type: Dict[str, str]
        self._schemas_loaded = False
        self._watched_settings = []  # type: List[sublime.Settings]

    def add_listener(self, listener: StoreListener) -> None:
        self._listeners.add(listener)
        if self._schemas_loaded:
            sublime.set_timeout_async(lambda: listener.on_store_changed(self._schema_list))

    def get_schema_for_uri(self, uri: str) -> Optional[str]:
        if uri in self._schema_uri_to_content:
            return self._schema_uri_to_content[uri]
        if uri.startswith('sublime://'):
            schema_path = uri.replace('sublime://', '')
            schema_components = schema_path.split('/')
            domain = schema_components[0]
            if domain == 'schemas':
                # Internal schema - 1:1 schema path to file path mapping.
                schema_path = 'Packages/{}/{}.json'.format(LspJSONPlugin.package_name, schema_path)
                return ResourcePath(schema_path).read_text()
        print('LSP-json: Unknown schema URI "{}"'.format(uri))
        return None

    def cleanup(self) -> None:
        for settings in self._watched_settings:
            settings.clear_on_change(LspJSONPlugin.package_name)

    def load_schemas(self) -> None:
        if self._schemas_loaded:
            return
        settings = sublime.load_settings('sublime-package.json')
        settings.add_on_change(LspJSONPlugin.package_name,
                               lambda: sublime.set_timeout_async(self._collect_schemas_async))
        self._watched_settings.append(settings)
        sublime.set_timeout_async(self._collect_schemas_async)
        self._schemas_loaded = True

    def _collect_schemas_async(self) -> None:
        self._schema_list = []
        self._schema_uri_to_content = {}
        self._load_bundled_schemas()
        global_preferences_schemas = self._load_package_schemas()
        self._generate_project_settings_schemas(global_preferences_schemas)
        self._load_syntax_schemas(global_preferences_schemas)
        sublime.set_timeout_async(self._on_schemas_changed)

    def _load_bundled_schemas(self) -> None:
        for schema in ['lsp-json-schemas_extra.json', 'lsp-json-schemas.json']:
            path = 'Packages/{}/{}'.format(LspJSONPlugin.package_name, schema)
            schema_list = self._parse_schema(ResourcePath(path))
            if schema_list:
                self._register_schemas(schema_list)

    def _load_package_schemas(self) -> List[Any]:
        global_preferences_schemas = []
        resources = ResourcePath.glob_resources('sublime-package.json')
        for resource in resources:
            schema = self._parse_schema(resource)
            if not schema:
                continue
            settings = schema.get('contributions').get('settings')
            for s in settings:
                i = len(self._schema_uri_to_content)
                file_patterns = s.get('file_patterns')
                schema_content = s.get('schema')
                uri = schema_content.get('$id') or 'sublime://settings/{}'.format(i)
                self._schema_uri_to_content[uri] = sublime.encode_value(schema_content)
                self._register_schemas([{'fileMatch': file_patterns, 'uri': uri}])
                if file_patterns:
                    for pattern in file_patterns:
                        if pattern == '/Preferences.sublime-settings':
                            global_preferences_schemas.append(schema_content)
        return global_preferences_schemas

    def _generate_project_settings_schemas(self, global_preferences_schemas: List[Any]):
        """
        Injects schemas mapped to /Preferences.json into the "settings" object in *.sublime.project schemas.
        """
        for i, schema in enumerate(global_preferences_schemas):
            schema_uri = 'sublime://auto-generated/sublime-project/{}'.format(i)
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
            self._schema_uri_to_content[schema_uri] = sublime.encode_value(schema_content)
            self._register_schemas([{'fileMatch': ['/*.sublime-project'], 'uri': schema_uri}])

    def _load_syntax_schemas(self, global_preferences_schemas: List[Any]) -> None:
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
                schema_uri = 'sublime://auto-generated/syntax.sublime-settings/{}'.format(i)
                schema_content = {
                    '$schema': 'http://json-schema.org/draft-07/schema#',
                    '$id': schema_uri,
                    'allowComments': True,
                    'allowTrailingCommas': True,
                    'type': 'object',
                }
                schema_content.update(schema)
                self._schema_uri_to_content[schema_uri] = sublime.encode_value(schema_content)
                self._register_schemas([{'fileMatch': file_patterns, 'uri': schema_uri}])

    def _parse_schema(self, resource: ResourcePath) -> Any:
        try:
            return sublime.decode_value(resource.read_text())
        except Exception:
            print('Failed parsing schema "{}"'.format(resource.file_path()))
            return None

    def _register_schemas(self, schemas: List[Any]) -> None:
        for schema in schemas:
            file_matches = schema.get('fileMatch')
            if file_matches:
                schema['fileMatch'] = [quote(fm, safe="/*") for fm in file_matches]
            self._schema_list.append(schema)

    def _on_schemas_changed(self) -> None:
        for listener in self._listeners:
            listener.on_store_changed(self._schema_list)


class LspJSONPlugin(NpmClientHandler, StoreListener):
    package_name = __package__
    server_directory = 'language-server'
    server_binary_path = path.join(server_directory, 'out', 'node', 'jsonServerMain.js')
    _user_schemas = []  # type: List[Dict]
    _schema_store = SchemaStore()

    @classmethod
    def cleanup(cls) -> None:
        cls._schema_store.cleanup()
        super().cleanup()

    @classmethod
    def on_settings_read(cls, settings: sublime.Settings):
        cls._user_schemas = settings.get('userSchemas', [])
        # Nothing has changed so don't force saving.
        return False

    def __init__(self, *args, **kwargs) -> None:
        self._api = None  # type: Optional[ApiWrapperInterface]
        super().__init__(*args, **kwargs)

    def on_ready(self, api: ApiWrapperInterface) -> None:
        self._api = api
        self._schema_store.add_listener(self)
        self._schema_store.load_schemas()
        self._api.on_request('vscode/content', self.handle_vscode_content)

    def handle_vscode_content(self, uri, respond):
        respond(self._schema_store.get_schema_for_uri(uri))

    def on_store_changed(self, schemas: List[Dict]) -> None:
        self._api.send_notification('json/schemaAssociations', schemas + self._user_schemas)
