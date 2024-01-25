# LSP-json

JSON support for Sublime's LSP plugin.

Uses [VSCode JSON Language Server](https://github.com/Microsoft/vscode/tree/master/extensions/json-language-features/server) to provide validation, formatting and other features for JSON files. See linked repository for more information.

### Installation

* Install [LSP](https://packagecontrol.io/packages/LSP) and `LSP-json` from Package Control.
* Restart Sublime.

### Configuration

Open configuration file using command palette with `Preferences: LSP-json Settings` command or opening it from the Sublime menu (`Preferences > Package Settings > LSP > Servers > LSP-json`).

### For users of PackageDev

The [PackageDev](https://packagecontrol.io/packages/PackageDev) package implements features that provide completions and tooltips when editing the Sublime settings files, which overlaps and conflicts with functionality provided by this package. To take advantage of the strict schemas that this package provides, disable corresponding functionality in `PackageDev` by opening `Preferences: PackageDev Settings` from the Command Palette and set the following settings on the right side:

```json
{
  "settings.auto_complete": false,
  "settings.tooltip": false
}
```

### Color Provider

The JSON-Language-Server implements a color provider that adds color decorators next to values representing colors in JSON files. If you are using a color plugin like [ColorHelper](https://packagecontrol.io/packages/ColorHelper) or [Color Highlight](https://packagecontrol.io/packages/Color%20Highlight) you may wish to disable this feature. To disable it open the LSP-json Settings as described above and add the following settings on the right side:

```json
{
  "disabled_capabilities": {
    "colorProvider": true
  }
}
```

### Custom schemas

To load manually created schemas, add those to `userSchemas` configuration in the settings file. See more information in the comments there.

The custom schema entry needs to look like:

```json
{
  "fileMatch": [
    "/my-file.json"
  ],
  "uri": "./my-file-schema.json",
}
```

The `fileMatch` is an array of file patterns to match against when resolving JSON files to schemas. `*` and `**` can be used as a wildcard. Exclusion patterns can also be defined and start with `!`. A file matches when there is at least one matching pattern and the last matching pattern is not an exclusion pattern.

The `uri` is a URI or a file path to a schema. Can be a relative path (starting with `./`) when defined in a project settings and in that case will be resolved relative to the first project folder.

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
