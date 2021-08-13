import json
import gzip
import logging
import random
import re
import os

from flask import Flask, render_template, redirect, request, Response, abort
app = Flask(__name__)

from gensim import corpora, models, similarities

from build_models import Similaritron, tokenize
sim = Similaritron()


@app.url_defaults
def hashed_url_for_static_file(endpoint, values):
    if 'static' == endpoint or endpoint.endswith('.static'):
        filename = values.get('filename')
        if filename:
            if '.' in endpoint:  # has higher priority
                blueprint = endpoint.rsplit('.', 1)[0]
            else:
                blueprint = request.blueprint  # can be None too

            if blueprint:
                static_folder = app.blueprints[blueprint].static_folder
            else:
                static_folder = app.static_folder

            param_name = 'h'
            while param_name in values:
                param_name = '_' + param_name
            values[param_name] = static_file_hash(
                os.path.join(static_folder, filename))


def static_file_hash(filename):
    return int(os.stat(filename).st_mtime)

# Routes


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


def request_context(request):
    """Extract context from request args."""
    context = {}
    N = 10

    try:
        page = int(request.args.get('page'))
    except (TypeError, ValueError):
        page = 1
    context['page'] = page
    offset = N * (page - 1)

    filters = {}
    if request.args.get('ci'):
        filters['ci'] = request.args.getlist('ci')
    if filters:
        context['filters'] = filters

    card_name = request.args.get('card')
    card_text = request.args.get('text')
    if card_name:
        try:
            context['search_type'] = 'card'
            target_card = sim.get_card_by_name(card_name)
            context['target_card'] = target_card
            app.logger.debug('%s: %s' % (card_name, tokenize(target_card)))
            context['similar_cards'] = sim.get_similar_cards(
                card_name, N, offset, filters)
        except Exception as e:
            if app.debug:
                raise e
            msg = 'Card name not found. Please try again.'
            return render_template('home.html',  error=msg), 404

    elif card_text:
        context['search_type'] = 'text'
        try:
            context['target_card'] = {'name': card_text}
            context['similar_cards'] = sim.text_search_similar_cards(
                card_text, N, offset, filters)
        except Exception as e:
            if app.debug:
                raise e
            msg = ('Unable to search related cards.'
                   ' Try rephrasing or expanding your query.')
            return render_template('home.html',  error=msg), 404
    return context


@app.route('/')
def home():

    try:
        return render_template('home.html', **request_context(request))
    except KeyError:
        msg = 'Card name not found. Please try again.'
        return render_template('home.html', error=msg), 404
    except Exception as e:
        if app.debug:
            raise e
        msg = ('Unable to search related cards.'
               ' Try rephrasing or expanding your query.')
        return render_template('home.html', error=msg), 404

    context = {}
    N = 10

    try:
        page = int(request.args.get('page'))
    except (TypeError, ValueError):
        page = 1
    context['page'] = page
    offset = N * (page - 1)

    filters = {}
    if request.args.get('ci'):
        filters['ci'] = request.args.getlist('ci')
    if filters:
        context['filters'] = filters

    card_name = request.args.get('card')
    card_text = request.args.get('text')
    if card_name:
        try:
            context['search_type'] = 'card'
            target_card = sim.get_card_by_name(card_name)
            context['target_card'] = target_card
            app.logger.debug('%s: %s' % (card_name, tokenize(target_card)))
            context['similar_cards'] = sim.get_similar_cards(
                card_name, N, offset, filters)
        except Exception as e:
            if app.debug:
                raise e
            msg = 'Card name not found. Please try again.'
            return render_template('home.html',  error=msg), 404

    elif card_text:
        context['search_type'] = 'text'
        try:
            context['target_card'] = {'name': card_text}
            context['similar_cards'] = sim.text_search_similar_cards(
                card_text, N, offset, filters)
        except Exception as e:
            if app.debug:
                raise e
            msg = ('Unable to search related cards.'
                   ' Try rephrasing or expanding your query.')
            return render_template('home.html',  error=msg), 404

    return render_template('home.html', **context)


@app.route("/api/")
def api_search():
    try:

        return json.dumps(request_context(request))
    except KeyError:
        abort(404)


@app.route('/random')
def random_card():
    card = random.choice(sim.cards)
    return redirect("/?card=%s" % card['name'])

if __name__ == '__main__':
    app.run(debug=True)
