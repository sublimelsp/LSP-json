import shutil

import sublime
import sublime_plugin
from LSP.plugin.core.handlers import LanguageHandler
from LSP.plugin.core.settings import ClientConfig, LanguageConfig
from .schemas import schemas

default_name = 'json'
server_package_name = 'vscode-json-languageserver-bin'

default_config = ClientConfig(
    name=default_name,
    binary_args=[
        'json-languageserver',
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

# Dependencies that needs to be installed for the server to work
dependencies = ['node', 'json-languageserver']


def is_installed(dependency):
    return shutil.which(dependency) is not None


class LspJsonSetupCommand(sublime_plugin.WindowCommand):
    def is_visible(self):
        if not is_installed('node') or not is_installed('json-languageserver'):
            return True
        return False

    def run(self):
        if not is_installed('node'):
            sublime.message_dialog(
                "Please install Node.js before running setup."
            )
            return

        if not is_installed('json-languageserver'):
            should_install = sublime.ok_cancel_dialog(
                "json-languageserver was not in the PATH.\nInstall {} globally now?".format(
                    server_package_name)
            )
            if should_install:
                self.window.run_command(
                    "exec", {
                        "cmd": [
                            "npm",
                            "install",
                            "--verbose",
                            "-g",
                            server_package_name
                        ]
                    })
        else:
            sublime.message_dialog(
                "{} is already installed".format(server_package_name)
            )


class LspJSONPlugin(LanguageHandler):
    def __init__(self):
        self._name = default_name
        self._config = default_config

    @property
    def name(self) -> str:
        return self._name

    @property
    def config(self) -> ClientConfig:
        return self._config

    def on_start(self, window) -> bool:
        for dependency in dependencies:
            if not is_installed(dependency):
                sublime.status_message('Run: LSP: Setup JSON server')
                return False
        return True

    def on_initialized(self, client) -> None:
        pass