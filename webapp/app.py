import json
import gzip
import random

from flask import Flask, render_template, redirect, request, Response
app = Flask(__name__)

from gensim import corpora, models, similarities

from build_models import Similaritron
sim = Similaritron()
## Routes

@app.route('/')
def home():
    context = {}
    card_name = request.args.get('card')
    if card_name:
        N = 10
        context['target_card_name'] = card_name
        context['target_card'] = sim.get_card_by_name(card_name)

        try:
            page = int(request.args.get('page'))
        except (TypeError, ValueError):
            page = 1
        context['page'] = page

        offset = N * (page - 1)
        context['similar_cards'] = sim.get_similar_cards(card_name, N, offset)
    return render_template('home.html', **context)

@app.route('/random')
def random_card():
    card = random.choice(sim.cards)
    return redirect("/?card=%s" % card['name'])

if __name__ == '__main__':
    app.run(debug=True)
