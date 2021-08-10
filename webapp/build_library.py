import argparse
import gzip
import json
import os
# import requests
import sys


DIR_NAME = 'library'

def _get(d, fields):
    return {k:d[k] for k in fields if k in d}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('json')
    args = parser.parse_args()

    cards = json.load(gzip.open(args.json, 'rt'))
    cards = cards['data']

    library = {}
    CARD_FIELDS = ['name', 'scryfallId', 'printings',
                   'text', 'manaCost', 'colorIdentity',
                   'type', 'types', 'supertypes', 'subtypes',
                   'power', 'toughness', 'loyalty']
    SKIP_TYPES = {'Vanguard', 'Scheme', 'Conspiracy'}

    for card_name, faces in cards.items():
        for face in faces:
            card_types = set(face.get('types', ''))
            if 'faceName' in face:
                face['name'] = face.pop('faceName')
            if not card_types.intersection(SKIP_TYPES):
                library[face['name']] = _get(face, CARD_FIELDS)

    if not os.path.isdir(DIR_NAME):
        os.mkdir(DIR_NAME)

    fname = 'card_codex_library.json.gz'
    fpath = os.path.join(DIR_NAME, fname)
    json.dump(list(library.values()), gzip.open(fpath, 'wt'))

    fname = 'card_codex_cardlist.txt'
    fpath = os.path.join(DIR_NAME, fname)
    with open(fpath, 'wt') as f:
        f.write('\n'.join(sorted(library.keys())))
