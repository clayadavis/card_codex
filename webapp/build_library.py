import gzip
import json

import requests

def _get(d, fields):
    return {k:d[k] for k in fields if k in d}

if __name__ == '__main__':
    url = 'https://mtgjson.com/json/AllSetsArray.json.gz'
    resp = requests.get(url)
    sets = json.loads(gzip.decompress(resp.content).decode('utf8'))

    cards = {}
    SERIE_FIELDS = ['name', 'code']
    CARD_FIELDS = ['name', 'names', 'manaCost', 'type', 'text',
                   'supertypes', 'types', 'subtypes', 'colorIdentity']

    for serie in sets:
        serie_info = _get(serie, SERIE_FIELDS)
        for card in serie['cards']:
            card_info = _get(card, CARD_FIELDS)
            card_info['set'] = serie_info
            cards[card['name']] = card_info

    fname = 'card_commander_library.json.gz'
    json.dump(list(cards.values()), gzip.open(fname, 'wt'))

    fname = 'card_commander_cardlist.txt'
    with open(fname, 'wt') as f:
        f.write('\n'.join(sorted(cards.keys())))
