#!/usr/bin/env python3

import os
import requests

from json import dumps

DIRECTORY = os.path.dirname(__file__)


def main():
    data = requests.get('http://schemastore.org/api/json/catalog.json').json()

    # Pick only required properties
    schema_list = [
        {'fileMatch': schema['fileMatch'], 'url': schema['url']}
        for schema in data['schemas'] if 'fileMatch' in schema
    ]

    with open(os.path.join(DIRECTORY, '..', 'schemas.json'), 'w') as f:
        f.write(dumps(schema_list, indent=2))


if __name__ == '__main__':
    main()
