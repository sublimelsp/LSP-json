import shutil
import os
import sublime

from LSP.plugin.core.handlers import LanguageHandler
from LSP.plugin.core.settings import ClientConfig, LanguageConfig
from .schemas import schemas


package_path = os.path.dirname(__file__)
server_path = os.path.join(package_path, 'node_modules', 'vscode-json-languageserver-bin', 'jsonServerMain.js')


def plugin_loaded():
    print('LSP-json: Server {}.'.format('installed' if os.path.isfile(server_path) else 'is not installed' ))

    if not os.path.isdir(os.path.join(package_path, 'node_modules')):
        # install server if no node_modules
        print('LSP-json: Installing server.')
        sublime.active_window().run_command(
            "exec", {
                "cmd": [
                    "npm",
                    "install",
                    "--verbose",
                    "--prefix",
                    package_path
                ]
            }
        )


def is_node_installed():
    return shutil.which('node') is not None


class LspJSONPlugin(LanguageHandler):
    @property
    def name(self) -> str:
        return 'lsp-json'

    @property
    def config(self) -> ClientConfig:
        return ClientConfig(
            name='lsp-json',
            binary_args=[
                'node',
                server_path,
                '--stdio'
            ],
            tcp_port=None,
            enabled=True,
            init_options=dict(),
            settings={
                "json": {
                    "format": {
                        "enable": True
                    },
                    "schemas": schemas
                }
            },
            env=dict(),
            languages=[
                LanguageConfig(
                    'json',
                    ['source.json', 'source.json.sublime.settings'],
                    [
                        'Packages/JavaScript/JSON.sublime-syntax',
                        'Packages/PackageDev/Package/Sublime Text Settings/Sublime Text Settings.sublime-syntax'
                    ]
                )
            ]
        )

    def on_start(self, window) -> bool:
        if not is_node_installed():
            sublime.status_message('Please install Node.js for the JSON server to work.')
            return False
        return True

    def on_initialized(self, client) -> None:
        pass