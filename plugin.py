import os
import sublime
from LSP.plugin.core.typing import Any, Dict, List, Optional
from abc import ABCMeta, abstractmethod
from lsp_utils import ApiWrapperInterface
from lsp_utils import NpmClientHandler
from sublime_lib import ResourcePath
from weakref import WeakSet


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
        self._schemas = []  # type: List[Dict]
        self._schemas_loaded = False
        self._package_schemas = {'settings': []}  # type: Dict[str, List[str]]
        self._watched_settings = []  # type: List[sublime.Settings]

    def add_listener(self, listener: StoreListener) -> None:
        self._listeners.add(listener)

    def get_schema_for_uri(self, uri: str) -> Optional[str]:
        if not uri.startswith('sublime://'):
            print('LSP-json: Unknown schema URI "{}"'.format(uri))
            return None
        schema_path = uri.replace('sublime://', '')
        schema_components = schema_path.split('/')
        domain = schema_components[0]
        if domain == 'schemas':
            # Internal schema - 1:1 schema path to file path mapping.
            schema_path = 'Packages/{}/{}.json'.format(LspJSONPlugin.package_name, schema_path)
            return ResourcePath(schema_path).read_text()
        if domain == 'settings':
            schema_index = int(schema_components[1])
            return self._package_schemas[domain][schema_index]

    def cleanup(self) -> None:
        for settings in self._watched_settings:
            settings.clear_on_change(LspJSONPlugin.package_name)

    def load_schemas(self) -> None:
        if self._schemas_loaded:
            sublime.set_timeout_async(self._notify_listeners)
            return
        settings = sublime.load_settings('sublime-package.json')
        settings.add_on_change(LspJSONPlugin.package_name,
                               lambda: sublime.set_timeout_async(self._collect_schemas_async))
        self._watched_settings.append(settings)
        sublime.set_timeout_async(self._collect_schemas_async)

    def _collect_schemas_async(self) -> None:
        self._schemas = []
        self._package_schemas = {'settings': []}
        self._load_bundled_schemas()
        self._load_package_schemas()
        sublime.set_timeout_async(self._notify_listeners)
        self._schemas_loaded = True

    def _load_bundled_schemas(self) -> None:
        for schema in ['lsp-json-schemas_extra.json', 'lsp-json-schemas.json']:
            path = 'Packages/{}/{}'.format(LspJSONPlugin.package_name, schema)
            schema_json = self._parse_schema(ResourcePath(path))
            if schema_json:
                self._schemas.extend(schema_json)

    def _load_package_schemas(self) -> None:
        resources = ResourcePath.glob_resources('sublime-package.json')
        for resource in resources:
            schema = self._parse_schema(resource)
            if schema:
                settings = schema.get('contributions').get('settings')
                for s in settings:
                    i = len(self._package_schemas['settings'])
                    schema_id = 'sublime://settings/{}'.format(i)
                    self._schemas.append({'fileMatch': s.get('file_patterns'), 'uri': schema_id})
                    schema_content = s.get('schema')
                    schema_content['type'] = 'object'
                    self._package_schemas['settings'].append(sublime.encode_value(schema_content))

    def _parse_schema(self, resource: ResourcePath) -> Any:
        try:
            return sublime.decode_value(resource.read_text())
        except Exception:
            print('Failed parsing schema "{}"'.format(resource.file_path()))
            return None

    def _notify_listeners(self) -> None:
        for listener in self._listeners:
            listener.on_store_changed(self._schemas)


class LspJSONPlugin(NpmClientHandler, StoreListener):
    package_name = __package__
    server_directory = 'language-server'
    server_binary_path = os.path.join(server_directory, 'out', 'node', 'jsonServerMain.js')
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
