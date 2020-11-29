import types
import json
FILE_NAME = 'schemas/sublime-theme.json'


def enum(*enums):
    result = {
        "enum": [],
        "markdownEnumDescriptions": []
     }

    for enum, description in enums:
        result["enum"].append(enum),
        result["markdownEnumDescriptions"].append(description)

    return result


def create_negation(*attrs):
    result = []
    for attr, description in attrs:
        result.append((attr, description))
        result.append((f"!{attr}", f"Opposite of `{attr}`"))  # create opposite
    return result


def iff(className, all_of):
    return {
        "if": { "properties": {"class": {"const": className} } },
        "then": {
            "allOf": all_of,
            "unevaluatedProperties": False
        }
    }


def leave_only_attributes(when_rule):
    name = when_rule.get("if", {}).get("properties", {}).get("class", {}).get("const")
    attributes = when_rule.get("then", {}).get("properties", {}).get("attributes", None)
    if not attributes:
        return None
    return {
        "if": { "properties": {"class": {"const": name} } },
        "then": {
            "properties": {
                "attributes": attributes
            }
        }
    }


def layers():
    layers = {}
    for layer in [0,1,2,3]:
        name = f"layer{layer}"
        layers[f"{name}.opacity"] = {
            "markdownDescription": "a float value from `0.0` to `1.0` that controls the master opacity of the layer.",
            "type": "number", "minimum": 0, "maximum": 1
        }
        layers[f"{name}.tint"] = { "$ref": "#/definitions/COLOR" }
        layers[f"{name}.texture"] = {
            "markdownDescription": "a string of the file path to a PNG image, relative to the `Packages/` folder",
            "type": "string"
        }
        layers[f"{name}.inner_margin"] = { "$ref": "#/definitions/SPACING" }
        layers[f"{name}.draw_center"] = {
            "markdownDescription": "a boolean that controls if the center rectangle of the 9-grid created via `layer#.inner_margin` should be drawn. This is an optimization that allows skipping an unused section of texture.",
            "type": "boolean",
        }
        layers[f"{name}.repeat"] = {
            "markdownDescription": "a boolean that controls if the texture should be repeated instead of stretched. ",
            "type": "boolean",
        }
    return layers

LAYERS = layers()


CLASS_NAMES = {
    "type": "string",
    **enum(
        # Windows
        ("title_bar", "Only supported on OS X 10.10+."),
        ("window", "This element can not be styled directly, however it can be used in a parents specifier. The luminosity attributes are set based on the global color scheme."),
        ("edit_window", "This element contains the main editor window, and is intended for use in a parents specifier."),
        ("switch_project_window", "This element contains the Switch Project window, and is intended for use in a parents specifier."),

        # Side Bar
        ("sidebar_container", "The primary sidebar container that handles scrolling"),
        ("sidebar_tree", "A tree control containing multiple `tree_row`s"),
        ("tree_row", "A row may contain a header, open file, folder or file"),
        ("sidebar_heading", "One of the \"Open Files\", \"Group #\" or \"Folders\" headings in the sidebar"),
        ("file_system_entry", "The container holding information about a file or folder in the sidebar. Contains different controls based on which section of the sidebar it is within.\n\nWithin the _Open Files_ section, this control will contain a `sidebar_label` with the file name, plus possibly a `vcs_status_badge`.\n\nWithin the _Folders_ section, this control will contain a folder or file icon (either `icon_folder`, `icon_folder_loading`, `icon_folder_dup` or `icon_file_type`), a `sidebar_label` with the file or folder name, plus possibly a `vcs_status_badge`."),
        ("sidebar_label", "Names of open files, folder names and filenames"),
        ("close_button", "A button to the left of each file in the _Open Files_ section"),
        ("disclosure_button_control", "An expand/collapse icon present in all `tree_rows` that can be expanded"),
        ("icon_folder", "Used for a folder once the contents have been fully enumerated"),
        ("icon_folder_loading", "Used for a folder while the contents are being enumerated"),
        ("icon_folder_dup", "Used for a folder that has been scanned previously in the sidebar. _This is necessary to prevent a possibly infinite list of files due to recursive symlinks_."),
        ("icon_file_type", "The icon for a file. The `layer0.texture` should not be set since it is determined dynamically based on the `icon` setting provided by _.tmPreferences_ files."),
        ("vcs_status_badge", "An icon contained within `file_system_entry` that is used to display the status of a file or folder with regards to a Git repository it is contained in. This icon will only be shown if the setting `show_git_status` is `true`, the file is contained within a Git repository, and the file has some sort of special state within the repository. _A file that is not shown via git status and is not ignored via a .gitignore rule will have no icon_."),

        # Tabs
        ("tabset_control", ""),
        ("tab_control", ""),
        ("tab_label", ""),
        ("tab_close_button", ""),
        ("scroll_tabs_left_button", ""),
        ("scroll_tabs_right_button", ""),
        ("show_tabs_dropdown_button", ""),

        # Quick Panel
        ("overlay_control", "The container for the quick panel, including the input and data table"),
        ("overlay_control goto_file", "The Goto File quick panel"),
        ("overlay_control goto_symbol", "The Goto Symbol quick panel"),
        ("overlay_control goto_symbol_in_project", "The Goto Symbol in Project quick panel"),
        ("overlay_control goto_line", "The Goto Line quick panel"),
        ("overlay_control goto_word", "The Goto Line quick panel"),
        ("overlay_control goto_line", "The Goto Anything quick panel, filtering by word"),
        ("overlay_control command_palette", "The Command Palette"),
        ("quick_panel", "The data table displayed below the input. Normally the height is dynamic so the layers will not be visible, however the Switch Project window will use layers for the blank space below the filtered options."),
        ("mini_quick_panel_row", "A non-file row in `quick_panel`. Contains one `quick_panel_label` for each line of text in the row."),
        ("quick_panel_row", "A Goto Anything file row in `quick_panel`. Also used in the Switch Project window.\n\n Contains `quick_panel_label` with the filename, and `quick_panel_path_label` for the file path."),
        ("kind_container", "A container shown to the left of the symbols in the Goto Symbol and Goto Symbol in Project quick panels. It contains the `kind_label` and is used to indicate the kind of the symbol.\n\n_This element is also used in `auto_complete` to show the kind of the item being inserted. A \"parents\" key should be used to distinguish the two uses._"),
        ("kind_container kind_ambiguous", "When the kind of the item is unknown"),
        ("kind_container kind_keyword", "When the item is a keyword "),
        ("kind_container kind_type", "When the item is a data type, class, struct, interface, enum, trait, etc"),
        ("kind_container kind_function", "When the item is a function, method, constructor or subroutine"),
        ("kind_container kind_namespace", "When the item is a namespace or module"),
        ("kind_container kind_navigation", "When the item is a definition, label or section"),
        ("kind_container kind_markup", "When the item is a markup component, including HTML tags and CSS selectors"),
        ("kind_container kind_variable", "When the item is a variable, member, attribute, constant or parameter"),
        ("kind_container kind_snippet", "When the item is a snippet"),
        ("kind_label", "A label showing a single unicode character, contained within the `kind_container`\n\n_This element is also used in `auto_complete` to show the kind of the item being inserted. A \"parents\" key should be used to distinguish the two uses._"),
        ("symbol_container", "A container around the `quick_panel_label` when showing the Goto Symbol or Goto Symbol in Project symbol lists"),
        ("quick_panel_label", "Filenames in `quick_panel_row` and all text in `mini_quick_panel_row`"),
        ("quick_panel_path_label", "File paths in `quick_panel_row`"),

        # Views
        ("text_area_control", "This element can not be styled directly since that is controlled by the color scheme, however it can be used in a parents specifier."),
        ("grid_layout_control", "The borders displayed between views when multiple groups are visible"),
        ("minimap_control", "Control over the display of the viewport projection on the minimap"),
        ("fold_button_control", "Code folding buttons in the gutter"),

        # Auto Complete
        ("popup_control auto_complete_popup", "The primary container for the auto complete popup"),
        ("popup_control html_popup", "The primary container for the HTML popups used by _Show Definitions_ and third-party packages. The tint of the scroll bar will be set to the background color of the HTML document."),
        ("auto_complete", "The data table for completion data. The tint is set based on the background color of the color scheme applied to the view the popup is displayed in."),
        ("table_row", "A row in `auto_complete`"),
        ("trigger_container", "A container around the auto_complete_label"),
        ("auto_complete_label", "Text in a `table_row`"),
        ("auto_complete_label auto_complete_hint", "The \"annotation\" hint displayed at the right-hand-side of a `table_row`"),
        ("auto_complete_detail_pane", "A detail pane displayed below the list of auto complete items, containing the `auto_complete_info` spacer, with `auto_complete_kind_name_label` and `auto_complete_details` inside"),
        ("auto_complete_info", "Provides spacing between `auto_complete_kind_name_label` and `auto_complete_details`"),
        ("auto_complete_kind_name_label", "A label used to display the name of the auto complete kind"),
        ("auto_complete_details", "A single-line HTML control used to display the details of the auto complete item"),

        # Panels
        ("panel_control find_panel", "The container for the Find and Incremental Find panels."),
        ("panel_control replace_panel", "The container for the Replace panel."),
        ("panel_control find_in_files_panel", "The container for the Find in Files panel."),
        ("panel_control input_panel", "The container for the input panel, which is available via the API and used for things like file renaming."),
        ("panel_control console_panel", "The container for the Console."),
        ("panel_control output_panel", "The container for the output panel, which is available via the API and used for build results."),
        ("panel_control switch_project_panel", "The container for the input in the Switch Project window."),
        ("panel_grid_control", "The layout grid used to position inputs on the various panels."),
        ("panel_close_button", "The button to close the open panel"),

        # Status Bar
        ("status_bar", ""),
        ("panel_button_control", "The panel switcher button on the left side of the status bar"),
        ("sidebar_button_control", "The sidebar/panel switcher button on the left side of the status bar"),
        ("status_container", "The area that contains the current status message"),
        ("status_button", "The status buttons that display, and allow changing, the indentation, syntax, encoding and line endings"),
        ("vcs_status", "The container holding the `vcs_branch_icon`, `label_control` with the current branch name, and `vcs_changes_annotation` control"),
        ("vcs_branch_icon", "An icon shown to the left of the current branch name"),
        ("vcs_changes_annotation", "Displays the number of files that have been added, modified or deleted"),

        # Dialogs
        ("dialog", "The Indexer Status and Update windows both use this class for the window background"),
        ("progress_bar_control", "The progress bar container. The progress bar is displayed in the Update window used for updates on OS X and Windows."),
        ("progress_gauge_control", "The bar representing the progress completed so far"),

        # Scroll Bars
        ("scroll_area_control", "The scroll area contains the element being scrolled, along with the bar, track and puck."),
        ("scroll_bar_control", "The scroll bar contains the scroll track. The tint is set based on the background color of the element being scrolled."),
        ("scroll_track_control", "The track that the puck runs along. The tint is set based on the background color of the element being scrolled."),
        ("scroll_corner_control", "The dead space in the bottom right of a scroll_area_control when both the vertical and horizontal scroll bars are being shown."),
        ("puck_control", "The scroll puck, or handle. The tint is set based on the background color of the element being scrolled."),

        # Inputs
        ("text_line_control", "The text input used by the Quick Panel, Find, Replace, Find in Files and Input panels."),
        ("dropdown_button_control", "The button to close the open panel"),

        # Buttons
        ("button_control", "Text buttons"),
        ("icon_button_group", "A grid controlling the spacing of related icon buttons"),
        ("icon_button_control", "Small icon-based buttons in the Find, Find in Files, and Replace panels"),
        ("icon_regex", "The button to enable regex mode in the Find, Find in Files and Replace panels"),
        ("icon_case", "The button to enable case-sensitive mode in the Find, Find in Files and Replace panels"),
        ("icon_whole_word", "The button to enable whole-word mode in the Find, Find in Files and Replace panels"),
        ("icon_wrap", "The button to enable search wrapping when using the Find and Replace panels"),
        ("icon_in_selection", "The button to only search in the selection when using the Find and Replace panels"),
        ("icon_highlight", "The button to enable highlighting all matches in the Find and Replace panels"),
        ("icon_preserve_case", "The button to enable preserve-case mode when using the Replace panel"),
        ("icon_context", "The button to show context around matches when using the Find in Files panel"),
        ("icon_use_buffer", "The button to display results in a buffer, instead of an output panel, when using the Find in Files panel"),

        # Labels
        ("label_control", "Labels are shown in the Find, Replace, Find in File and Input panels. Additionally, labels are used in the Update window, on textual buttons and for the text in the status_container.\n\n_ Targeting specific labels can be accomplished by using the `parents` key._"),
        ("title_label_control", "The title label is used in the About window."),

        # Tool Tips
        ("tool_tip_control", "Tool tips shown when hovering over tabs and buttons"),
        ("tool_tip_label_control", "Text shown in a tool tip"),

        # undocumented
        ("quick_panel_entry", ""),
        ("quick_panel_detail_label", ""),
        ("quick_panel_label hint", ""),
        ("quick_panel_label key_binding", ""),
        ("popup_shadow", ""),
        ("auto_complete_hint", ""),
        ("icon_use_gitignore", ""),
        ("annotation_close_button", ""),
        ("popup_control", ""),
        ("panel_control", ""),
        ("overlay_control kind_info", "")

    )
}

def attributes(*attrs):
    return {
        "type": "array",
        "items": {
            "type": "string", **enum(*create_negation(*attrs)),
        }
    }

def less_strict_attributes(*attrs):
    return {
        "type": "array",
        "items": {
            "anyOf": [
                {"type": "string", **enum(*create_negation(*attrs))},
                {"type": "string"}
            ]
        }
    }


PLATFORMS = {
    "type": "array",
    "items": {
        "type": "string",
        "enum": ["osx", "windows", "linux"]
    }
}

SETTINGS = less_strict_attributes(
        ("overlay_scroll_bars", "this should affect the style of the scroll bars – generally they should be semi-transparent and the `overlay` property of the `scroll_area_control` should be set to `true`"),
        ("always_show_minimap_viewport", "if the current viewport area should be highlighted on the minimap even when the user is not hovering over the minimap."),
        ("bold_folder_labels", "if folder names in the side bar should have the `font.bold` property set to `true`."),
        ("mouse_wheel_switches_tabs", "this is used to control mouse wheel behavior of tabs on Linux. It should be combined with checking for `!enable_tab_scrolling` to change the `mouse_wheel_switch` key of the `tabset_control` to `false`. "),
        ("highlight_modified_tabs", "if the tabs of modified files should be highlighted. This setting should be checked in addition to the `dirty` attribute."),
        ("show_tab_close_buttons", "if tabs should have close buttons")
)

LUMINOSITY = [
    ("file_light", "`V` from `0.60-1.00`"),
    ("file_medium", "`V` from `0.30-0.59`"),
    ("file_medium_dark", "`V` from `0.10-0.29`"),
    ("file_dark", "`V` from `0.00-0.09`")
]

SPECIFIC_CLASS_PROPERTIES = [
    # Windows
    iff("title_bar", [
        {
        "properties": {
                "attributes": attributes(*LUMINOSITY, ("hover", "")),
                "fg": { "$ref": "#/definitions/COLOR" },
                "bg": { "$ref": "#/definitions/COLOR" },
                "style": {
                    "markdownDescription": "The OS style to use for the title bar",
                    "type": "string",
                    "default": "system",
                    **enum(
                        ("system", "default"),
                        ("dark", "Mac/Linux only"),
                        ("light", "Mac only")
                    )
                }
            }
        }
    ]),
    iff("window", [
        {
            "properties": {
                "attributes": attributes(*LUMINOSITY)
            }
        }
    ]),

    # Side bar
    iff("sidebar_container", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("sidebar_tree", [
        {
            "properties": { "$ref": "#/definitions/DATA_TABLE_PROPERTIES" },
        },
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "indent": { "type": "integer", "markdownDescription": "an integer amount to indent each level of the tree structure" },
                "indent_offset": { "type": "integer", "markdownDescription": "an additional indent applied to every row, for the sake of positioning `disclosure_button_control` and `close_button`" },
                "indent_top_level": {"type": "boolean", "markdownDescription": "a boolean if top-level rows in the tree should be indented"},
                "spacer_rows": {"type": "boolean", "markdownDescription": "a boolean controlling if a blank row should be added between the _Open Files_ and _Folders_ sections of the sidebar, when both are visible."}
            }
        }
    ]),
    iff("tree_row", [
        {
            "properties": {
                "attributes": attributes(
                    ("hover", ""),
                    ("selectable", "when a row is selectable"),
                    ("selected", "when an selectable row is selected"),
                    ("expandable", "when a row is expandable"),
                    ("expanded", "when an expandable row is expanded"),
                )
            }
        }
    ]),
    iff("sidebar_heading", [
        {
            "properties": { "$ref": "#/definitions/SHADOW_PROPERTIES" }
        },
        {
            "properties": { "$ref": "#/definitions/FONT_PROPERTIES" }
        },
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "fg": { "$ref": "#/definitions/COLOR" },
                "case": {
                    "type": "string",
                    "default": "upper",
                    "enum": ["upper", "lower", "title"]
                }
            }
        }
    ]),
    iff("file_system_entry", [
        {
            "properties": {
                "attributes": attributes(
                    ("hover", ""),
                    ("ignored", "**Files**: when a file is ignored\n\n**Folders**: when the entire folder is ignored"),
                    ("untracked", "**Files**: when a file is new or not recognized\n\n**Folders**: when a folder contains one or more untracked files"),
                    ("modified", "**Files**: when a file has been changed on disk\n\n**Folders**: when a folder contains one or more modified files"),
                    ("missing", "**Folders**: when one or more of a folder‘s files is no longer on disk"),
                    ("added", "**Files**: when a new file has been newly added to the index\n\n**Folders**: when a folder contains one or more added files"),
                    ("staged", "**Files**: when a modified file has been added to the index\n\n**Folders**: when a folder contains one or more staged files"),
                    ("deleted", "**Folders**: when one or more of a folder‘s files has been added to the index for removal"),
                    ("unmerged", "**Files**: when a file is in a conflict state and needs to be resolved\n\n**Folders**: when a folder contains one or more unmerged files"),
                ),
                "content_margin": { "$ref": "#/definitions/SPACING" },
                "spacing": {"type": "integer", "markdownDescription": "an integer number of pixels between each contained control"}
            }
        }
    ]),
    iff("sidebar_label", [
        {
            "properties": { "$ref": "#/definitions/SHADOW_PROPERTIES" }
        },
        {
            "properties": { "$ref": "#/definitions/FONT_PROPERTIES" }
        },
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "fg": { "$ref": "#/definitions/COLOR" }
            }
        }
    ]),
    iff("close_button", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("disclosure_button_control", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("icon_folder", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("icon_folder_loading", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("icon_folder_dup", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("icon_file_type", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("vcs_status_badge", [
        {
            "properties": {
                "attributes": attributes(
                    ("hover", ""),
                    ("ignored", "**Files**: when a file is ignored\n\n**Folders**: when the entire folder is ignored"),
                    ("untracked", "**Files**: when a file is new or not recognized\n\n**Folders**: when a folder contains one or more untracked files"),
                    ("modified", "**Files**: when a file has been changed on disk\n\n**Folders**: when a folder contains one or more modified files"),
                    ("missing", "**Folders**: when one or more of a folder‘s files is no longer on disk"),
                    ("added", "**Files**: when a new file has been newly added to the index\n\n**Folders**: when a folder contains one or more added files"),
                    ("staged", "**Files**: when a modified file has been added to the index\n\n**Folders**: when a folder contains one or more staged files"),
                    ("deleted", "**Folders**: when one or more of a folder‘s files has been added to the index for removal"),
                    ("unmerged", "**Files**: when a file is in a conflict state and needs to be resolved\n\n**Folders**: when a folder contains one or more unmerged files"),
                ),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),

    # Tabs
    iff("tabset_control", [
        {
            "properties": {
                "attributes": attributes(*LUMINOSITY, ("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
                "tab_overlap": {"type": "integer", "markdownDescription": "how many DIPs the tabs should overlap"},
                "tab_width": {"type": "integer", "markdownDescription": "default tab width when space is available"},
                "tab_min_width": {"type": "integer", "markdownDescription": "the minimum tab width before tab scrolling occurs"},
                "tab_height": {"type": "integer", "markdownDescription": "the height of the tabs in DIPs"},
                "mouse_wheel_switch": {"type": "boolean", "markdownDescription": "if the mouse wheel should switch tabs – this should only be set to `true` if the setting `enable_tab_scrolling` is `false`"},
            }
        }
    ]),
    iff("tab_control", [
        {
            "properties": {
                "attributes": attributes(
                    *LUMINOSITY,
                    ("hover", ""),
                    ("dirty", "when the associated view has unsaved changed"),
                    ("selected", "when the associated view is the active view in its group"),
                    ("transient", "when the associate view is a preview and not fully opened")
                ),
                "content_margin": { "$ref": "#/definitions/SPACING" },
                "max_margin_trim": {"markdownDescription": "how much of the left and right `content_margin` may be removed when tab space is extremely limited"},
                "accent_tint_index": {"type": "integer", "minimum": 0, "maximum": 3, "markdownDescription": "Controls which layer the accent tint is applied to. Must be an integer from `0` to `3`. The accent color is specified by the color scheme."},
                "accent_tint_modifier": {"type": "array", "items": [{"type": "integer", "minimum": 0, "maximum": 255}, {"type": "integer", "minimum": 0, "maximum": 255}, {"type": "integer", "minimum": 0, "maximum": 255}, {"type": "integer", "minimum": 0, "maximum": 255}], "markdownDescription": "An array of four integers in the range `0` to `255`. The first three are blended into the RGB values from the accent tint color with the fourth value specifying how much of these RGB modifier values to apply."},
            }
        }
    ]),
    iff("tab_label", [
        {
            "properties": { "$ref": "#/definitions/SHADOW_PROPERTIES" }
        },
        {
            "properties": { "$ref": "#/definitions/FONT_PROPERTIES" }
        },
        {
            "properties": {
                "attributes": attributes(
                    ("hover", ""),
                    ("transient", "when the associate view is a preview and not fully opened")
                ),
                "fg": { "$ref": "#/definitions/COLOR" },
            }
        }
    ]),
    iff("tab_close_button", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
                "accent_tint_index": {"type": "integer", "minimum": 0, "maximum": 3, "markdownDescription": "Controls which layer the accent tint is applied to. Must be an integer from `0` to `3`. The accent color is specified by the color scheme."},
                "accent_tint_modifier": {"type": "array", "items": [{"type": "integer", "minimum": 0, "maximum": 255}, {"type": "integer", "minimum": 0, "maximum": 255}, {"type": "integer", "minimum": 0, "maximum": 255}, {"type": "integer", "minimum": 0, "maximum": 255}], "markdownDescription": "An array of four integers in the range `0` to `255`. The first three are blended into the RGB values from the accent tint color with the fourth value specifying how much of these RGB modifier values to apply."},
            }
        }
    ]),
    iff("scroll_tabs_left_button", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("scroll_tabs_right_button", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("show_tabs_dropdown_button", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),

    # Quick Panel
    iff("overlay_control", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("overlay_control goto_file", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("overlay_control goto_symbol", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("overlay_control goto_symbol_in_project", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("overlay_control goto_line", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("overlay_control goto_word", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("overlay_control command_palette", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("quick_panel", [
        {
            "properties": { "$ref": "#/definitions/DATA_TABLE_PROPERTIES" }
        },
        {
            "properties": {
                "attributes": attributes(("hover", "")),
            }
        }
    ]),
    iff("mini_quick_panel_row", [
        {
            "properties": {
                "attributes": attributes(
                    ("hover", ""),
                    ("selected", "when the row is selected"),
                ),
            }
        }
    ]),
    iff("quick_panel_row", [
        {
            "properties": {
                "attributes": attributes(
                    ("hover", ""),
                    ("selected", "when the row is selected"),
                )
            }
        }
    ]),
    iff("kind_container", [
        {
            "properties": {
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("kind_container kind_ambiguous", [
        {
            "properties": {
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("kind_container kind_keyword", [
        {
            "properties": {
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("kind_container kind_type", [
        {
            "properties": {
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("kind_container kind_function", [
        {
            "properties": {
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),

    iff("kind_container kind_namespace", [
        {
            "properties": {
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("kind_container kind_navigation", [
        {
            "properties": {
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("kind_container kind_markup", [
        {
            "properties": {
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("kind_container kind_variable", [
        {
            "properties": {
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("kind_container kind_snippet", [
        {
            "properties": {
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("kind_label", [
        {
            "properties": { "$ref": "#/definitions/FONT_PROPERTIES" }
        }
    ]),
    iff("symbol_container", [
        {
            "properties": {
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("quick_panel_label", [
        {
            "properties": { "$ref": "#/definitions/FILTER_LABEL_PROPERTIES" }
        },
        {
            "properties": {
                "attributes": attributes(("hover", "")),
            }
        }
    ]),
    iff("quick_panel_path_label", [
        {
            "properties": { "$ref": "#/definitions/FILTER_LABEL_PROPERTIES" }
        },
        {
            "properties": {
                "attributes": attributes(("hover", "")),
            }
        }
    ]),

    # Views
    iff("text_area_control", [
        {
            "properties": {
                "attributes": attributes(("hover", ""), *LUMINOSITY),
            }
        }
    ]),
    iff("grid_layout_control", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "border_color": { "$ref": "#/definitions/COLOR"},
                "border_size": { "type": "integer", "markdownDescription": "an integer of the border size in DIPs"}
            }
        }
    ]),
    iff("minimap_control", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "viewport_color": { "$ref": "#/definitions/COLOR"},
                "viewport_opacity": { "type": "number", "minimum": 0, "maximum": 1, "markdownDescription": "a float from 0.0 to 1.0 specifying the opacity of the viewport projection"}
            }
        }
    ]),
    iff("fold_button_control", [
        {
            "properties": {
                "attributes": attributes(
                    ("hover", ""),
                    ("expanded", "when a section of code is unfolded ")
                ),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("auto_complete", [
        {
            "properties": { "$ref": "#/definitions/DATA_TABLE_PROPERTIES" }
        },
        {
            "properties": { "$ref": "#/definitions/TEXTURE_TINTING_PROPERTIES" }
        },
        {
            "properties": {
                "attributes": attributes(("hover", "")),
            }
        }
    ]),
    iff("table_row", [
        {
            "properties": {
                "attributes": attributes(
                    ("hover", ""),
                    ("selected", "when the user has highlighted a completion")
                )
            }
        }
    ]),
    iff("trigger_container", [
        {
            "properties": {
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("auto_complete_label", [
        {
            "properties": { "$ref": "#/definitions/FILTER_LABEL_PROPERTIES" }
        },
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "fg_blend": {"type": "boolean", "markdownDescription": "a boolean controlling if the `fg`, `match_fg`, `selected_fg`, and `selected_match_fg` values should be blended onto the foreground color from the color scheme of the current view"}
            }
        }
    ]),
    iff("auto_complete_label auto_complete_hint", [
        {
            "properties": { "$ref": "#/definitions/FONT_PROPERTIES" }
        },
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "fg_blend": {"type": "boolean", "markdownDescription": "a boolean controlling if the `fg`, `match_fg`, `selected_fg`, and `selected_match_fg` values should be blended onto the foreground color from the color scheme of the current view"}
            }
        }
    ]),
    iff("auto_complete_detail_pane", [
        {
            "properties": {
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("auto_complete_info", [
        {
            "properties": {
                "spacing": { "type": "integer", "markdownDescription": "an integer number of pixels between each contained control" },
            }
        }
    ]),
    iff("auto_complete_label auto_complete_hint", [
        {
            "properties": { "$ref": "#/definitions/FONT_PROPERTIES" }
        },
        {
            "properties": { "$ref": "#/definitions/STYLED_LABEL_PROPERTIES" }
        },
    ]),
    iff("auto_complete_details", [
        {
            "properties": {
                "font.face": { "type": "string", "markdownDescription": "the name of the font face" },
                "font.size": { "type": "integer", "markdownDescription": "an integer point size"},
                "color": { "$ref": "#/definitions/COLOR"},
                "link_color": { "$ref": "#/definitions/COLOR"},
                "monospace_color": { "$ref": "#/definitions/COLOR"},
                "monospace_background_color": { "$ref": "#/definitions/COLOR"},
            }
        }
    ]),

    # Panels
    iff("panel_control find_panel", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("panel_control replace_panel", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("panel_control find_in_files_panel", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("panel_control input_panel", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("panel_control console_panel", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("panel_control output_panel", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("panel_control switch_project_panel", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("panel_grid_control", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "inside_spacing": { "type": "integer", "markdownDescription": "an integer padding to place between each cell of the grid" },
                "outside_vspacing": { "type": "integer", "markdownDescription": "an integer padding to place above and below the grid" },
                "outside_hspacing": { "type": "integer", "markdownDescription": "an integer padding to place to the left and right of the grid" },
            }
        }
    ]),
    iff("panel_close_button", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    # Status Bar
    iff("status_bar", [
        {
            "properties": {
                "attributes": attributes(
                    ("hover", ""),
                    ("panel_visible", "when a panel is displayed above the status bar")
                ),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("panel_button_control", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("sidebar_button_control", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("status_container", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("status_button", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
                "min_size": {"type": "array", "items": [{"type": "integer"}, {"type": "integer"}], "markdownDescription": "an array of two integers specifying the minimum width and height of a button, in DIPs"}
            }
        }
    ]),
    iff("vcs_status", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
                "spacing": {"type": "integer", "markdownDescription": "an integer number of pixels between each contained control"}
            }
        }
    ]),
    iff("vcs_branch_icon", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("vcs_changes_annotation", [
        {
            "properties": { "$ref": "#/definitions/SHADOW_PROPERTIES" }
        },
        {
            "properties": { "$ref": "#/definitions/FONT_PROPERTIES" }
        },
        {
            "properties": { "$ref": "#/definitions/STYLED_LABEL_PROPERTIES" }
        },
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),

    # Dialogs
    iff("dialog", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("progress_gauge_control", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),

    # Scroll Bars
    iff("scroll_area_control", [
        {
            "properties": {
                "attributes": attributes(
                    ("hover", ""),
                    ("scrollable", "when the control can be scrolled vertically"),
                    ("hscrollable", "when the control can be scrolled horizontally")
                ),
                "content_margin": { "$ref": "#/definitions/SPACING" },
                "overlay": {"type": "boolean", "markdownDescription": "sets the scroll bars to be rendered on top of the content"},
                "left_shadow": { "$ref": "#/definitions/COLOR"},
                "left_shadow_size": {"type": "integer", "markdownDescription": "in integer of the width of the shadow to draw when the area can be scrolled to the left"},
                "top_shadow": { "$ref": "#/definitions/COLOR"},
                "top_shadow_size": {"type": "integer", "markdownDescription": "in integer of the height of the shadow to draw when the area can be scrolled to the top"},
                "right_shadow": { "$ref": "#/definitions/COLOR"},
                "right_shadow_size": {"type": "integer", "markdownDescription": "in integer of the width of the shadow to draw when the area can be scrolled to the right"},
                "bottom_shadow": { "$ref": "#/definitions/COLOR"},
                "bottom_shadow_size": {"type": "integer", "markdownDescription": "in integer of the height of the shadow to draw when the area can be scrolled to the bottom"},
            }
        }
    ]),
    iff("scroll_bar_control", [
        {
            "properties": { "$ref": "#/definitions/TEXTURE_TINTING_PROPERTIES" }
        },
        {
            "properties": {
                "attributes": attributes(
                    ("hover", ""),
                    ("dark", "when the scroll area content is dark, necessitating a light scroll bar"),
                    ("horizontal", "when the scroll bar should be horizontal instead of vertical")
                ),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("scroll_track_control", [
        {
            "properties": { "$ref": "#/definitions/TEXTURE_TINTING_PROPERTIES" }
        },
        {
            "properties": {
                "attributes": attributes(
                    ("hover", ""),
                    ("dark", "when the scroll area content is dark, necessitating a light scroll bar"),
                    ("horizontal", "when the scroll bar should be horizontal instead of vertical")
                ),
            },
        }
    ]),
    iff("scroll_corner_control", [
        {
            "properties": { "$ref": "#/definitions/TEXTURE_TINTING_PROPERTIES" }
        },
        {
            "properties": {
                "attributes": attributes(
                    ("hover", ""),
                    ("dark", "when the scroll area content is dark, necessitating a light scroll bar"),
                ),
            }
        }
    ]),
    iff("puck_control", [
        {
            "properties": { "$ref": "#/definitions/TEXTURE_TINTING_PROPERTIES" }
        },
        {
            "properties": {
                "attributes": attributes(
                    ("hover", ""),
                    ("dark", "when the scroll area content is dark, necessitating a light scroll bar"),
                    ("horizontal", "when the scroll bar should be horizontal instead of vertical")
                ),
            }
        }
    ]),

    # Inputs
    iff("text_line_control", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
                "color_scheme_tint": { "$ref": "#/definitions/COLOR" },
                "color_scheme_tint_2": { "$ref": "#/definitions/COLOR" },
            }
        }
    ]),
    iff("dropdown_button_control", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),

    # Buttons
    iff("button_control", [
        {
            "properties": {
                "attributes": attributes(
                    ("hover", ""),
                    ("pressed", "set when a button is pressed down"),
                ),
                "content_margin": { "$ref": "#/definitions/SPACING" },
                "min_size": {"type": "array", "items": [{"type": "integer"}, {"type": "integer"}], "markdownDescription": "an array of two integers specifying the minimum width and height of a button, in DIPs"}
            }
        }
    ]),
    iff("icon_button_group", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "spacing": {"type": "integer", "markdownDescription": "an integer number of pixels between each button in the group"}
            }
        }
    ]),
    iff("icon_button_control", [
        {
            "properties": {
                "attributes": attributes(
                    ("hover", ""),
                    ("selected", "when an icon button is toggled on"),
                    ("left", "when the button is the left-most button in a group"),
                    ("right", "when the button is the right-most button in a group"),
                ),
            }
        }
    ]),
    iff("icon_regex", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("icon_case", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("icon_whole_word", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("icon_wrap", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("icon_in_selection", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("icon_highlight", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("icon_preserve_case", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("icon_context", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("icon_use_buffer", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),

    # Labels
    iff("label_control", [
        {
            "properties": { "$ref": "#/definitions/SHADOW_PROPERTIES" }
        },
        {
            "properties": { "$ref": "#/definitions/FONT_PROPERTIES" }
        },
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "color": { "$ref": "#/definitions/COLOR" },
            }
        }
    ]),
    iff("title_label_control", [
        {
            "properties": { "$ref": "#/definitions/SHADOW_PROPERTIES" }
        },
        {
            "properties": { "$ref": "#/definitions/FONT_PROPERTIES" }
        },
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "color": { "$ref": "#/definitions/COLOR" },
            }
        }
    ]),

    # Tool Tips
    iff("tool_tip_control", [
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "content_margin": { "$ref": "#/definitions/SPACING" },
            }
        }
    ]),
    iff("tool_tip_label_control", [
        {
            "properties": { "$ref": "#/definitions/SHADOW_PROPERTIES" }
        },
        {
            "properties": { "$ref": "#/definitions/FONT_PROPERTIES" }
        },
        {
            "properties": {
                "attributes": attributes(("hover", "")),
                "color": { "$ref": "#/definitions/COLOR" },
            }
        }
    ]),
]

PARENTS = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "class": { "$ref": "#/definitions/CLASS_NAMES" },
            "attributes": { "$ref": "#/definitions/ATTRIBUTES" }
        },
        # "allOf": [leave_only_attributes(d) for d in SPECIFIC_CLASS_PROPERTIES if leave_only_attributes(d)]
    }
}

RULE = {
    "type": "object",
    "properties": {
        "class": { "$ref": "#/definitions/CLASS_NAMES" },
        "attributes": { "$ref": "#/definitions/ATTRIBUTES" },
        "settings": { "$ref": "#/definitions/SETTINGS" },
        "parents": { "$ref": "#/definitions/PARENTS" },
        "platforms": { "$ref": "#/definitions/PLATFORMS" },
        **LAYERS
    },
    "allOf": SPECIFIC_CLASS_PROPERTIES
}

schema = {
    "$schema": "sublime://schemas/sublime-base",
    "$id": "sublime://schemas/sublime-theme",
    "title": "Sublime Text Theme",
    "allowComments": True,
    "allowTrailingCommas": True,
    "oneOf": [
        {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "extends": {
                    "type": "string",
                    "markdownDescription": "Any variables from the extending theme will override variables with the same name in the base theme. Variable overrides will affect rules both in the base theme and the extending theme.",
                    "default": "Default.sublime-theme"
                },
                    "variables": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "string",
                        "format": "color"
                    }
                },
                "rules": {
                    "type": "array",
                    "items": { "$ref": "#/definitions/RULE" }
                }
            }
        },
        {
            "type": "array",
            "items": { "$ref": "#/definitions/RULE" }
        }
    ],
    "definitions": {
        "RULE": RULE,
        "CLASS_NAMES": CLASS_NAMES,
        "ATTRIBUTES": {"type": "array", "items": {"type": "string" }, "markdownDescription": "Attributes are specified as an array of strings. Each string is an attribute name. To check for the absence of an attribute, prepend a `!` to the name."},
        "PARENTS": PARENTS,
        "PLATFORMS": PLATFORMS,
        "SETTINGS": {**SETTINGS, "markdownDescription": "Certain Sublime Text settings are design to influence the UI. Themes should respect these settings and change elements based on them."},
        "SPACING": {
            "markdownDescription": "Padding and margin may be specified in one of three ways:\n\n - A single integer value – the same value is applied to the left, top, right and bottom\n\n - An array of two integers – the first value is applied to the left and right, while the second value is applied to the top and bottom\n\n - An array of four integers – the values are applied, in order, to the left, top, right and bottom",
            "anyOf": [
                {
                  "type": "number"
                },
                {
                  "type": "array",
                  "items": [{"type": "number"}, {"type": "number"}],
                  "additionalItems": False
                },
                {
                  "type": "array",
                  "items": [{"type": "number"}, {"type": "number"}, {"type": "number"}, {"type": "number"}],
                  "additionalItems": False
                }
            ]
        },
        "COLOR": {
            "anyOf": [
                {
                    "type": "string",
                    "format": "color"
                },
                {
                    "type": "string",
                    "enum": ["var(--background)", "var(--foreground)", "var(--accent)", "var(--redish)", "var(--orangish)", "var(--yellowish)", "var(--greenish)", "var(--cyanish)", "var(--bluish)", "var(--purplish)", "var(--pinkish)"]
                },
                {
                    "type": "array",
                    "items": {
                        "type": ["string", "number"]
                    }
                }
            ]
        },
        "DATA_TABLE_PROPERTIES": {
            "dark_content": {"type": "boolean", "markdownDescription": "if the background is dark – used to set the `dark` attribute for scrollbars"},
            "row_padding": { "$ref": "#/definitions/SPACING" }
        },
        "SHADOW_PROPERTIES": {
            "shadow_color": { "$ref": "#/definitions/COLOR" },
            "shadow_offset": {"type": "array", "items": [{"type": "integer"}, {"type": "integer"}], "markdownDescription": "a 2-element array containing the X and Y offsets of the shadow"},
        },
        "FONT_PROPERTIES": {
            "font.face": {"type": "string", "markdownDescription": "the name of the font face"},
                "font.size": { "type": "integer", "markdownDescription": "an integer point size"},
                "viewport_color": { "$ref": "#/definitions/COLOR"},
            "font.bold": {"type": "boolean", "markdownDescription": "a boolean, if the font should be bold"},
            "font.italic": {"type": "boolean", "markdownDescription": "a boolean, if the font should be italic"},
        },
        "FILTER_LABEL_PROPERTIES": {
            "fg": { "$ref": "#/definitions/COLOR" },
            "match_fg": { "$ref": "#/definitions/COLOR" },
            "bg": { "$ref": "#/definitions/COLOR" },
            "selected_fg": { "$ref": "#/definitions/COLOR" },
            "selected_match_fg": { "$ref": "#/definitions/COLOR" },
            "font.face": { "type": "string", "markdownDescription": "the name of the font face" },
            "font.size": { "type": "integer", "markdownDescription": "an integer point size" },
        },
        "STYLED_LABEL_PROPERTIES": {
            "border_color": { "$ref": "#/definitions/COLOR" },
            "background_color": { "$ref": "#/definitions/COLOR" },
        },
        "TEXTURE_TINTING_PROPERTIES": {
            "tint_index": {"type": "integer", "minimum": 0, "maximum": 3, "markdownDescription": "Controls which layer the tint is applied to. Must be an integer from `0` to `3`."},
            # TODO: bug should be array
            "tint_modifier": {"type": "integer", "minimum": 0, "maximum": 255, "markdownDescription": "An array of four integers in the range `0` to `255`. The first three are blended into the RGB values from the tint color with the fourth value specifying how much of these RGB modifier values to apply."}
        }
    }
}


with open(FILE_NAME, 'w') as outfile:
    json.dump(schema, outfile,  sort_keys=True, indent=4)

#open and read the file after the appending:
f = open(FILE_NAME, "r")
print(f.read())
