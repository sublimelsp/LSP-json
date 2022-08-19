#!/usr/bin/env python3

import os
import re
import requests

from json import dumps

DIRECTORY = os.path.dirname(__file__)
RE_YAML = re.compile(r'\.ya?ml$')


def to_absolute_pattern(pattern: str) -> str:
    if pattern.startswith('/'):
        return pattern
    return '/{}'.format(pattern)


def main():
    schemas = requests.get('http://schemastore.org/api/json/catalog.json').json()['schemas']
    schema_list = []
    for schema in schemas:
        file_match = schema.get('fileMatch')
        url = schema['url']
        if not file_match:
            schema_list.append({'uri': url})
        if file_match:
            file_match = list(filter(lambda pattern: not RE_YAML.search(pattern), schema['fileMatch']))
            file_match = list(filter(lambda match: not is_ignored(match), file_match))
        if file_match:
            file_match = list(map(to_absolute_pattern, file_match))
            schema_list.append({'fileMatch': file_match, 'uri': url})

    with open(os.path.join(DIRECTORY, '..', 'lsp-json-schemas.json'), 'w') as f:
        f.write(dumps(schema_list, indent=2))


def is_ignored(file_match: str):
    ignored_schemas = [
        "messages.json"  # fixes: https://github.com/sublimelsp/LSP-json/issues/109
    ]
    return file_match in ignored_schemas


if __name__ == '__main__':
    main()
