import collections
import gzip
import itertools
import json
import os
import re
from operator import itemgetter

import nltk.stem, nltk.corpus
import wget
from gensim import corpora, models, similarities


LIBRARY_DIR = 'library'
MODEL_DIR = 'models'

LIBRARY =    os.path.join(LIBRARY_DIR, 'card_codex_library.json.gz')
DICTIONARY = os.path.join(MODEL_DIR,   'card_text_dictionary.dict')
CORPUS =     os.path.join(MODEL_DIR,   'card_text_corpus.mm')
INDEX =      os.path.join(MODEL_DIR,   'card_text_lsi.index')
TFIDF =      os.path.join(MODEL_DIR,   'card_text_tfidf.model')
LSI =        os.path.join(MODEL_DIR,   'card_text_lsi.model')

#try:
#    stopwords = set(nltk.corpus.stopwords.words('english'))
#except LookupError:
#    nltk.download('stopwords')
stopwords = set(nltk.corpus.stopwords.words('english'))
stemmer = nltk.stem.snowball.SnowballStemmer('english')


class Similaritron(object):
    # TODO: num_topics is a magic number?
    def __init__(self):
        print('Loading models...')
        self.dictionary = corpora.Dictionary.load(DICTIONARY)
        # self.corpus = corpora.MmCorpus(CORPUS)
        self.index = similarities.MatrixSimilarity.load(INDEX)
        self.tfidf = models.TfidfModel.load(TFIDF)
        self.lsi = models.LsiModel.load(LSI)

        self.cards = json.load(gzip.open(LIBRARY, 'rt'))
        self._card_index = {self._normalize_card_name(c['name']):idx
                            for idx, c in enumerate(self.cards)}
        print('\t...done.')

    def _normalize_card_name(self, name):
        name = name.lower()
        name = re.sub('[^a-z0-9]','', name)
        return name

    def _similarity(self, card):
        vec_bow = self.dictionary.doc2bow(tokenize(card))
        vec_lsi = self.lsi[self.tfidf[vec_bow]]
        scores = self.index[vec_lsi]
        return sorted(enumerate(scores),
                key=itemgetter(1), reverse=True)

    @staticmethod
    def _match_filters(card, filters=None):
        if filters is not None:
            if filters.get('ci'):
                my_ci = set(card.get('colorIdentity', []))
                selected_ci = set(''.join(filters['ci']))
                if not my_ci.issubset(selected_ci):
                    return False
        return True

    def get_card_by_name(self, name):
        return self.cards[self._card_index[self._normalize_card_name(name)]]

    def get_similar_cards(self, target_card_name, N=10, offset=0, filters=None):
        target_card = self.get_card_by_name(target_card_name)
        similarity_scores = self._similarity(target_card)
        similar_cards = []
        for card_idx, score in similarity_scores:
            this_card = self.cards[card_idx]
            is_same_card = (self._normalize_card_name(this_card['name']) ==
                            self._normalize_card_name(target_card_name))
            # Exclude identical and vanilla cards
            if is_same_card or not this_card.get('text'):
                continue
            # Apply filters
            if not self._match_filters(this_card, filters):
                continue
            # Pass all filters
            similar_cards.append(this_card)
            if len(similar_cards) >= N + offset:
                break
        return similar_cards[offset:]

    def text_search_similar_cards(self, search_text, N=10, offset=0,
                                  filters=None):
        my_card = {'name': 'text search', 'text': search_text}
        similarity_scores = self._similarity(my_card)
        similar_cards = []
        for card_idx, score in similarity_scores:
            this_card = self.cards[card_idx]
            if self._match_filters(this_card, filters):
                similar_cards.append(this_card)
            if len(similar_cards) >= N + offset:
                break
        return similar_cards[offset:]


def make_bigrams(_iter):
    a, b = itertools.tee(_iter)
    try:
        next(b)
    except StopIteration:
        return []
    return [' '.join(pair) for pair in zip(a, b)]


def tokenize(card):
    text = card.get('text', '')

    ## Remove "Enchant X" on auras; it messes with TF/IDF
    text = re.sub(r'Enchant .+\n', ' ', text)
    ## Remove the "Equip" cost of equipment
    text = re.sub(r'Equip\W', ' ', text)
    ## Remove case
    text = text.lower()
    ## Replace card name with ~
    text = text.replace(card['name'].lower(), '~')
    ## remove reminder text (in parentheses)
    text = re.sub(r'\([^)]+\)', '', text)
    ## remove costs
    text = re.sub(r'\{[^}]+\}', '', text)
    ## genericize all p/t (de)buffs
    text = re.sub(r'([+-])[\dX*]/([+-])[\dX*]', r'\1X/\2X', text)
    ## genericize numbers
    text = re.sub(r'\d+', 'N', text)
    ## replace opponent with player
    text = text.replace('opponent', 'player')
    ## split on punctuation and spaces
    tokens = re.split(r'[\s.,;:—()]+', text)

    # stem tokens
    stopwords = set(nltk.corpus.stopwords.words('english'))
    # Some stopwords are useful. We should make a custom list at some point.
    stopwords -= {'has', 'be'}
    stopwords.update(['equipped'])

    tokens = [stemmer.stem(t) for t in tokens if t and t not in stopwords]
    ## Perhaps bigrams shouldn't bridge stopwords?
    ## e.g. "can't be blocked and has shroud" =/=> "blocked has"
    bigrams = make_bigrams(tokens)

    ## Add creature subtypes
    if 'Creature' in card.get('types', ''):
        subtypes = [t.lower() for t in card.get('subtypes', [])]
    else:
        subtypes = []

    return tokens + bigrams + subtypes


if __name__ == '__main__':
    if not os.path.isdir(MODEL_DIR):
        os.mkdir(MODEL_DIR)

    cards = json.load(gzip.open(LIBRARY, 'rt'))

    card_names = [c['name'] for c in cards]

    # nltk.download('stopwords')
    # stopwords = set(nltk.corpus.stopwords.words('english'))
    # stemmer = nltk.stem.snowball.SnowballStemmer('english')

    documents = [tokenize(c) for c in cards]

    dictionary = corpora.Dictionary(documents)
    dictionary.save(DICTIONARY)

    print('Building dictionary containing %i items' % len(dictionary))

    corpus = [dictionary.doc2bow(doc) for doc in documents]
    corpora.MmCorpus.serialize(CORPUS, corpus)

    tfidf = models.TfidfModel(corpus)
    corpus_tfidf = tfidf[corpus]
    tfidf.save(TFIDF)

    lsi = models.LsiModel(corpus, id2word=dictionary, num_topics=100)
    corpus_lsi = lsi[corpus_tfidf]
    lsi.save(LSI)

    index = similarities.MatrixSimilarity(corpus_lsi)
    index.save(INDEX)
