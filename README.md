# LSP-json

JSON support for Sublime's LSP plugin.

Uses [VSCode JSON Language Server](https://github.com/Microsoft/vscode/tree/master/extensions/json-language-features/server) to provide validation, formatting and other features for JSON files. See linked repository for more information.

* Install [LSP](https://packagecontrol.io/packages/LSP) and `LSP-json` from Package Control.
* Restart Sublime.

### Configuration

Open configuration file using command palette with `Preferences: LSP-json Settings` command or opening it from the Sublime menu (`Preferences > Package Settings > LSP > Servers > LSP-json`).

### Custom schemas

To load manually created schemas, add those to `userSchemas` configuration in the settings file. See more information in the comments there.

### Schemas contributed by Packages

Sublime Text packages can provide schemas for its own settings, or contribute to global ST settings or other configuration files (for example `*.sublime-project` files).

This is accomplished by including a `sublime-package-types.json` file in the package (location doesn't matter) and defining schemas within it.

Here is a an example of how this could look:

```js
{
  "contributions": {
    "settings": [
      {
        // Schema for MyPackage configuration.
        "file_patterns": ["/MyPackage.sublime-settings"],
        "schema": {
          "properties": {
            "my_cool_setting": {
              "type": "string",
              "default": "yes",
              "enum": ["yes", "no"],
              "markdownDescription": "Decides whether something is `on` or `off`."
            }
          },
          "additionalProperties": false,
        }
      },
      {
        // Schema to extend global ST Preferences.
        "file_patterns": ["/Preferences.sublime-settings"],
        "schema": {
          "properties": {
            "my_cool_setting": {
              "type": "string",
              "default": "no",
              "enum": ["yes", "no"],
              "markdownDescription": "Decides whether something is `on` or `off`."
            }
          },
        }
      }
    ]
  }
}
```
