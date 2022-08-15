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
        if file_match:
            file_match = list(map(to_absolute_pattern, file_match))
            file_match = fix_edge_cases(file_match)
            schema_list.append({'fileMatch': file_match, 'uri': url})

    with open(os.path.join(DIRECTORY, '..', 'lsp-json-schemas.json'), 'w') as f:
        f.write(dumps(schema_list, indent=2))

def fix_edge_cases(file_match):
    if "/messages.json" in file_match:
        return ["!/Packages/**/messages.json", *file_match]
    return file_match


if __name__ == '__main__':
    main()
