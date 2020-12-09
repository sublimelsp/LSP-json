# LSP-json

JSON support for Sublime's LSP plugin.

Uses [VSCode JSON Language Server](https://github.com/Microsoft/vscode/tree/master/extensions/json-language-features/server) to provide validation, formatting and other features for JSON files. See linked repository for more information.

* Make sure you have Node.js installed and `node` is in your `$PATH`. The language server subprocess is a Node.js app.
* Install [LSP](https://packagecontrol.io/packages/LSP) and `LSP-json` from Package Control.
* Restart Sublime.

### Configuration

Open configuration file using command palette with `Preferences: LSP-json Settings` command or opening it from the Sublime menu (`Preferences > Package Settings > LSP > Servers > LSP-json`).

### Custom schemas

To load manually created schemas, add those to `userSchemas` configuration in the settings file. See more information in the comments there.

### Schemas contributed by Packages

Sublime Text packages can provide schemas for its own settings, or contribute to global ST settings or other configuration files (for example `*.sublime-project` files).

This is accomplished by including a `sublime-package.json` file in the package (location doesn't matter) and defining schemas within it. Any changes made to the schemas are automatically applied to matching files so there is no need to restart the server or ST.

Here is a an example of three different schemas defined in one `sublime-package.json` file:

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
              // Reuses definition from the pattern-less schema defined below.
              "$ref": "sublime://settings/foo/base#/definitions/ReuseMe"
            }
          },
        }
      },
      {
        // Pattern-less schema (note that "file_patterns" is missing).
        // Can be added for the purpose of referencing it (or its definitions) from another schema.
        // Pattern-less schema must define an "$id" to be able to refer to it from other schemas.
        // It's recommended to assign URIs like "sublime://settings/foo/base" for "$id".
        "schema": {
          "$id": "sublime://settings/foo/base"
          "definitions": {
            "ReuseMe": {
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
