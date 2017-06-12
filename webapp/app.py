import json
import gzip
import logging
import random
import re

from flask import Flask, render_template, redirect, request, Response
app = Flask(__name__)

from gensim import corpora, models, similarities

from build_models import Similaritron, tokenize
sim = Similaritron()

## Routes

@app.template_filter('mana')
def manafy(s):
    return re.sub('[{}\s]+', '', s or '')

@app.template_filter('params')
def params(d):
    def vals():
        for param in d:
            for val in d[param]:
                yield '%s=%s' % (param, val)
    s = '&'.join(vals())
    return '&' + s if s else ''


@app.route('/')
def home():
    context = {}
    card_name = request.args.get('card')
    if card_name:
        N = 10
        context['target_card_name'] = card_name
        try:
            target_card = sim.get_card_by_name(card_name)
            context['target_card'] = target_card
            app.logger.debug('%s: %s' % (card_name, tokenize(target_card)))
        except:
            msg = 'Card name not found. Please try again.'
            return render_template('home.html',  error=msg), 404

        try:
            page = int(request.args.get('page'))
        except (TypeError, ValueError):
            page = 1
        context['page'] = page

        offset = N * (page - 1)
        filters = {}
        if request.args.get('ci'):
            filters['ci'] = request.args.getlist('ci')
        context['filters'] = filters
        context['similar_cards'] = sim.get_similar_cards(card_name, N, offset, filters)
    return render_template('home.html', **context)

@app.route('/random')
def random_card():
    card = random.choice(sim.cards)
    return redirect("/?card=%s" % card['name'])

if __name__ == '__main__':
    app.run(debug=True)
    app.logger.setLevel(logging.DEBUG)
