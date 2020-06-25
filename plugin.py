import os
import sublime
from LSP.plugin.core.typing import Dict, List
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
    def on_client_configuration_ready(cls, configuration: Dict):
        if not cls._default_schemas:
            for schema in ['lsp-json-schemas_extra.json', 'lsp-json-schemas.json']:
                path = 'Packages/{}/{}'.format(cls.package_name, schema)
                cls._default_schemas.extend(sublime.decode_value(ResourcePath(path).read_text()))

        configuration['settings'].setdefault('json', {})['schemas'] = cls._default_schemas

    def on_ready(self, api) -> None:
        api.on_request('vscode/content', self.handle_vscode_content)

    def handle_vscode_content(self, uri, respond):
        name = uri.split('/')[-1]
        schema_resource = ResourcePath('Packages', self.package_name, 'schemas', '{}.json'.format(name))
        respond(schema_resource.read_text())
