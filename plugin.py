import json
import os
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

    def __init__(self) -> None:
        super().__init__()
        self._default_schemas = []  # type: List[Dict]

    def on_client_configuration_ready(self, configuration: Dict):
        if not self._default_schemas:
            schemas = ['schemas_extra.json', 'schemas.json']
            for schema in schemas:
                path = 'Packages/{}/{}'.format(self.package_name, schema)
                self._default_schemas.extend(json.loads(ResourcePath(path).read_text()))

        configuration['settings'].setdefault('json', {})['schemas'] = self._default_schemas

    def on_ready(self, api) -> None:
        api.on_request(
            'vscode/content',
            lambda params, request_id: self.handle_vscode_content(params, request_id))

    def handle_vscode_content(self, uri, respond):
        name = uri.split('/')[-1]
        schema_resource = ResourcePath('Packages', self.package_name, 'schemas', '{}.json'.format(name))
        respond(schema_resource.read_text())
