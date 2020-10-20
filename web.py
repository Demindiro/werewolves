#!/usr/bin/env python3

import random
import sys
from flask import Flask, redirect, url_for, render_template, request, session
from flask_babel import Babel, gettext
from game import Game
from api import api


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


app = Flask(__name__)
app.secret_key = open('secret.key').read()
app.register_blueprint(api, url_prefix='/api')
babel = Babel(app)
games = {}
total_games = 0


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(['en', 'nl'])


@app.route('/')
@app.route('/<string:code>/')
def index(code: str = None):
    return render_template('index.html')


@app.route('/status/')
def get_status():
    return render_template('status.html', game_count=len(api.games),
            total_game_count=api.total_games)


if __name__ == '__main__':
    app.run(port=5000)
