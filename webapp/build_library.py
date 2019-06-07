import gzip
import json
import os
import requests


DIR_NAME = 'library'

def _get(d, fields):
    return {k:d[k] for k in fields if k in d}

if __name__ == '__main__':
    try:
        os.chdir(DIR_NAME)
    except FileNotFoundError:
        os.mkdir(DIR_NAME)
        os.chdir(DIR_NAME)

    url = 'https://mtgjson.com/json/AllCards.json.gz'
    resp = requests.get(url)
    cards = json.loads(gzip.decompress(resp.content).decode('utf8'))

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

    fname = 'card_codex_library.json.gz'
    json.dump(list(library.values()), gzip.open(fname, 'wt'))

    fname = 'card_codex_cardlist.txt'
    with open(fname, 'wt') as f:
        f.write('\n'.join(sorted(library.keys())))
