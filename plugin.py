import shutil
import os
import sublime
import threading
import subprocess
import json

from LSP.plugin.core.handlers import LanguageHandler
from LSP.plugin.core.settings import ClientConfig, LanguageConfig, read_client_config
from .schemas import schemas

package_path = os.path.dirname(__file__)
server_path = os.path.join(package_path, 'node_modules', 'vscode-json-languageserver', 'bin', 'vscode-json-languageserver')


def get_plugin_schemas():
    plugin_schemas = []
    added_schemas = []

    for schema in sublime.find_resources("*.schema.json"):
        schema_content = sublime.load_resource(schema)
        schema_file_name = os.path.basename(schema)

        # Associate a `LSP-json.schema.json` file to `LSP-json.sublime-settings`
        settings_file_name = schema_file_name.replace(".schema.json", ".sublime-settings")
        try:
            if schema_file_name in added_schemas:
                continue

            added_schemas.append(schema_file_name)
            plugin_schemas.append({
                "name": schema_file_name,
                "fileMatch": [
                    settings_file_name
                ],
                "schema": json.loads(schema_content)
            })
        except Exception as e:
            pass

    return plugin_schemas


def plugin_loaded():
    get_plugin_schemas()
    is_server_installed = os.path.isfile(server_path)
    print('LSP-json: Server {}.'.format('installed' if is_server_installed else 'is not installed' ))

    # install the node_modules if not installed
    if not is_server_installed:
        # this will be called only when the plugin gets:
        # - installed for the first time,
        # - or when updated on package control
        logAndShowMessage('LSP-json: Installing server.')

        runCommand(
            onCommandDone,
            ["npm", "install", "--verbose", "--prefix", package_path, package_path]
        )


def onCommandDone():
    logAndShowMessage('LSP-json: Server installed.')


def runCommand(onExit, popenArgs):
    """
    Runs the given args in a subprocess.Popen, and then calls the function
    onExit when the subprocess completes.
    onExit is a callable object, and popenArgs is a list/tuple of args that
    would give to subprocess.Popen.
    """
    def runInThread(onExit, popenArgs):
        try:
            if sublime.platform() == 'windows':
                subprocess.check_call(popenArgs, shell=True)
            else:
                subprocess.check_call(popenArgs)
            onExit()
        except subprocess.CalledProcessError as error:
            logAndShowMessage('LSP-json: Error while installing the server.', error)
        return
    thread = threading.Thread(target=runInThread, args=(onExit, popenArgs))
    thread.start()
    # returns immediately after the thread starts
    return thread


def is_node_installed():
    return shutil.which('node') is not None


def logAndShowMessage(msg, additional_logs=None):
    print(msg, '\n', additional_logs) if additional_logs else print(msg)
    sublime.active_window().status_message(msg)


class LspJSONPlugin(LanguageHandler):
    @property
    def name(self) -> str:
        return 'lsp-json'

    @property
    def config(self) -> ClientConfig:
        settings = sublime.load_settings("LSP-json.sublime-settings")
        client_configuration = settings.get('client')

        all_schemas = []
        plugin_schemas = get_plugin_schemas()
        all_schemas.extend(plugin_schemas)
        all_schemas.extend(schemas)

        default_configuration = {
            "command": [
                'node',
                server_path,
                '--stdio'
            ],
            "languages": [
                {
                    "languageId": "json",
                    "scopes": ["source.json"],
                    "syntaxes": [
                        "Packages/JavaScript/JSON.sublime-syntax",
                        "Packages/JSON/JSON.sublime-syntax"
                    ]
                },
                {
                    "languageId": "jsonc",
                    "scopes": ["source.jsonc"],
                    "syntaxes": [
                        "Packages/LSP-json/syntax/JSONC.sublime-syntax"
                    ]
                }
            ]
        }
        default_configuration.update(client_configuration)
        default_configuration['settings']['json']['schemas'] = all_schemas
        return read_client_config('lsp-json', default_configuration)

    def on_start(self, window) -> bool:
        if not is_node_installed():
            sublime.status_message('Please install Node.js for the JSON server to work.')
            return False
        return True

    def on_initialized(self, client) -> None:
        pass