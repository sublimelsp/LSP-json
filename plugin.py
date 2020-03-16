import json
import os
import shutil
import sublime

from LSP.plugin.core.handlers import LanguageHandler
from LSP.plugin.core.protocol import Response
from LSP.plugin.core.settings import ClientConfig, read_client_config
from LSP.plugin.core.typing import Dict, List
from lsp_utils import ServerNpmResource
from sublime_lib import ResourcePath

PACKAGE_NAME = 'LSP-json'
SETTINGS_FILENAME = 'LSP-json.sublime-settings'
SERVER_DIRECTORY = 'vscode-json-languageserver'
SERVER_BINARY_PATH = os.path.join(SERVER_DIRECTORY, 'node_modules', 'vscode-json-languageserver',
                                  'bin', 'vscode-json-languageserver')

server = ServerNpmResource(PACKAGE_NAME, SERVER_DIRECTORY, SERVER_BINARY_PATH)


def plugin_loaded():
    server.setup()


def plugin_unloaded():
    server.cleanup()


def is_node_installed():
    return shutil.which('node') is not None


class LspJSONPlugin(LanguageHandler):
    def __init__(self) -> None:
        self._default_schemas = []  # type: List[Dict]

    @property
    def name(self) -> str:
        return PACKAGE_NAME.lower()

    @property
    def config(self) -> ClientConfig:
        # Calling setup() also here as this might run before `plugin_loaded`.
        # Will be a no-op if already ran.
        # See https://github.com/sublimelsp/LSP/issues/899
        server.setup()

        configuration = self.migrate_and_read_configuration()

        default_configuration = {
            'enabled': True,
            'command': ['node', server.binary_path, '--stdio'],
        }

        default_configuration.update(configuration)

        if not self._default_schemas:
            schemas = ['schemas_extra.json', 'schemas.json']
            for schema in schemas:
                path = 'Packages/{}/{}'.format(PACKAGE_NAME, schema)
                self._default_schemas.extend(json.loads(ResourcePath(path).read_text()))

        default_configuration['settings'].setdefault('json', {})['schemas'] = self._default_schemas

        return read_client_config(self.name, default_configuration)

    def migrate_and_read_configuration(self) -> dict:
        settings = {}
        loaded_settings = sublime.load_settings(SETTINGS_FILENAME)

        if loaded_settings:
            if loaded_settings.has('client'):
                client = loaded_settings.get('client')
                loaded_settings.erase('client')
                # Migrate old keys
                for key in client:
                    loaded_settings.set(key, client[key])
                sublime.save_settings(SETTINGS_FILENAME)

            # Read configuration keys
            for key in ['languages', 'initializationOptions', 'settings']:
                settings[key] = loaded_settings.get(key)

        return settings

    def on_start(self, window) -> bool:
        if not is_node_installed():
            sublime.status_message('Please install Node.js for the JSON server to work.')
            return False
        return True

    def on_initialized(self, client) -> None:
        client.on_request(
            'vscode/content',
            lambda params, request_id: self.handle_vscode_content(client, params, request_id))

    def handle_vscode_content(self, client, uri, request_id):
        name = uri.split('/')[-1]
        schema_resource = ResourcePath('Packages', PACKAGE_NAME, 'schemas', '{}.json'.format(name))
        client.send_response(Response(request_id, schema_resource.read_text()))
