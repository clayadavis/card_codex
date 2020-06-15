import gzip
import json
import os
# import requests
import sys


DIR_NAME = 'library'

def _get(d, fields):
    return {k:d[k] for k in fields if k in d}

if __name__ == '__main__':

    # url = 'https://mtgjson.com/json/AllCards.json.gz'
    # resp = requests.get(url)
    # cards = json.loads(gzip.decompress(resp.content).decode('utf8'))
    cards = json.load(gzip.open('AllCards.json.gz'))

    library = {}
    CARD_FIELDS = ['name', 'scryfallId', 'printings',
                   'text', 'manaCost', 'colorIdentity',
                   'type', 'types', 'supertypes', 'subtypes',
                   'power', 'toughness', 'loyalty']
    SKIP_TYPES = {'Vanguard', 'Scheme', 'Conspiracy'}

    for name, card in cards.items():
        card_types = set(card.get('types', ''))
        if not card_types.intersection(SKIP_TYPES):
            library[name] = _get(card, CARD_FIELDS)

    if not os.path.isdir(DIR_NAME):
        os.mkdir(DIR_NAME)

    fname = 'card_codex_library.json.gz'
    fpath = os.path.join(DIR_NAME, fname)
    json.dump(list(library.values()), gzip.open(fpath, 'wt'))

    fname = 'card_codex_cardlist.txt'
    fpath = os.path.join(DIR_NAME, fname)
    with open(fpath, 'wt') as f:
        f.write('\n'.join(sorted(library.keys())))
