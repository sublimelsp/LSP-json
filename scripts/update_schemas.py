#!/usr/bin/env python3

from __future__ import annotations

from json import dumps
from pathlib import Path
from typing import TypedDict
from typing_extensions import NotRequired
import re
import requests

DIRECTORY = Path(__file__).parent
RE_EXCLUDED_EXT = re.compile(r'\.(?:ya?ml|toml)$')


class Schema(TypedDict):
    name: str
    url: str
    description: str
    fileMatch: NotRequired[list[str]]


def main() -> None:
    schemas: list[Schema] = requests.get('https://schemastore.org/api/json/catalog.json', timeout=10).json()['schemas']
    schema_list = []
    for schema in schemas:
        file_match = schema.get('fileMatch')
        url = schema['url']
        if not file_match:
            schema_list.append({'uri': url})
        if file_match:
            file_match = list(filter(lambda pattern: not RE_EXCLUDED_EXT.search(pattern), file_match))
            file_match = list(filter(lambda match: not is_ignored(match), file_match))
        if file_match:
            file_match = list(map(to_absolute_pattern, file_match))
            schema_list.append({'fileMatch': file_match, 'uri': url})
    Path(DIRECTORY.parent, 'lsp-json-schemas.json').write_text(dumps(schema_list, indent=2), encoding='utf-8')


def is_ignored(file_match: str) -> bool:
    ignored_schemas = [
        'messages.json',  # fixes: https://github.com/sublimelsp/LSP-json/issues/109
    ]
    return file_match in ignored_schemas


def to_absolute_pattern(pattern: str) -> str:
    return pattern if pattern.startswith('/') else f'/{pattern}'


if __name__ == '__main__':
    main()
