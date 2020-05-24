import json
import os
import sublime
from LSP.plugin.core.typing import Any, Dict, List
from lsp_utils import NpmClientHandler
from sublime_lib import ResourcePath


def plugin_loaded():
    LspJSONPlugin.setup()


def plugin_unloaded():
    LspJSONPlugin.cleanup()


class LspJSONPlugin(NpmClientHandler):
    package_name = __package__
    server_directory = 'vscode-json-languageserver'
    server_binary_path = os.path.join(
        server_directory, 'node_modules', 'vscode-json-languageserver', 'bin', 'vscode-json-languageserver'
    )
    _default_schemas = []  # type: List[Dict]

    @classmethod
    def configuration(cls) -> sublime.Settings:
        config = super().configuration()
        settings = config.get('settings')
        cls._setup_schemas(settings)
        config.set('settings', settings)
        return config

    @classmethod
    def on_client_configuration_ready(cls, configuration: Dict):
        cls._setup_schemas(configuration['settings'])

    @classmethod
    def _setup_schemas(cls, d: Dict[str, Any]) -> None:
        if not cls._default_schemas:
            schemas = ['schemas_extra.json', 'schemas.json']
            for schema in schemas:
                path = 'Packages/{}/{}'.format(cls.package_name, schema)
                cls._default_schemas.extend(json.loads(ResourcePath(path).read_text()))
        d.setdefault('json', {})['schemas'] = cls._default_schemas

    def on_ready(self, api) -> None:
        api.on_request('vscode/content', self.handle_vscode_content)

    def handle_vscode_content(self, uri, respond):
        name = uri.split('/')[-1]
        schema_resource = ResourcePath('Packages', self.package_name, 'schemas', '{}.json'.format(name))
        respond(schema_resource.read_text())
