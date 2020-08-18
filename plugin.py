import os
import sublime
from LSP.plugin.core.typing import Any, Dict, List, Optional
from lsp_utils import ApiWrapperInterface
from lsp_utils import NpmClientHandler
from sublime_lib import ResourcePath


def plugin_loaded():
    LspJSONPlugin.setup()


def plugin_unloaded():
    LspJSONPlugin.cleanup()


def parse_schema(resource: ResourcePath) -> Optional[Any]:
    try:
        return sublime.decode_value(resource.read_text())
    except Exception:
        print('Failed parsing schema "{}"'.format(resource.file_path()))
        return None


class LspJSONPlugin(NpmClientHandler):
    package_name = __package__
    server_directory = 'language-server'
    server_binary_path = os.path.join(server_directory, 'out', 'node', 'jsonServerMain.js')
    _default_schemas = []  # type: List[Dict]
    _user_schemas = []  # type: List[Dict]
    _package_schemas = {'settings': []}  # type: Dict[str, List[str]]

    @classmethod
    def on_settings_read(cls, settings: sublime.Settings):
        cls._user_schemas = settings.get('userSchemas', [])
        # Nothing has changed so don't force saving.
        return False

    def on_ready(self, api: ApiWrapperInterface) -> None:
        if not LspJSONPlugin._default_schemas:
            sublime.set_timeout_async(lambda: self.collect_schemas_async(api))
        else:
            sublime.set_timeout_async(lambda: self.notify_schemas_async(api))
        api.on_request('vscode/content', self.handle_vscode_content)

    def collect_schemas_async(self, api: ApiWrapperInterface) -> None:
        self.load_bundled_schemas()
        self.load_package_schemas(api)
        self.notify_schemas_async(api)

    def load_bundled_schemas(self) -> None:
        for schema in ['lsp-json-schemas_extra.json', 'lsp-json-schemas.json']:
            path = 'Packages/{}/{}'.format(LspJSONPlugin.package_name, schema)
            schema_json = parse_schema(ResourcePath(path))
            if schema_json:
                LspJSONPlugin._default_schemas.extend(schema_json)

    def load_package_schemas(self, api: ApiWrapperInterface) -> None:
        resources = ResourcePath.glob_resources('sublime-package-types.json')
        for resource in resources:
            schema = parse_schema(resource)
            if schema:
                settings = schema.get('contributions').get('settings')
                for s in settings:
                    i = len(LspJSONPlugin._package_schemas['settings'])
                    schema_id = 'sublime://settings/{}'.format(i)
                    LspJSONPlugin._default_schemas.append({'fileMatch': s.get('file_patterns'), 'uri': schema_id})
                    schema_content = s.get('schema')
                    schema_content['type'] = 'object'
                    LspJSONPlugin._package_schemas['settings'].append(sublime.encode_value(schema_content))

    def notify_schemas_async(self, api: ApiWrapperInterface) -> None:
        api.send_notification(
            'json/schemaAssociations', self._default_schemas + self._user_schemas)

    def handle_vscode_content(self, uri, respond):
        if uri.startswith('sublime://'):
            schema_path = uri.replace('sublime://', '')
            schema_components = schema_path.split('/')
            if schema_components[0] == 'schemas':
                # Internal schema - 1:1 schema path to file path mapping.
                schema_path = 'Packages/{}/{}.json'.format(self.package_name, schema_path)
                respond(ResourcePath(schema_path).read_text())
                return
            if schema_components[0] == 'settings':
                schema_index = int(schema_components[1])
                respond(self._package_schemas['settings'][schema_index])
                return
        print('LSP-json: Unknown schema URI "{}"'.format(uri))
        respond(None)
