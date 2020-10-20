#!/usr/bin/env python3

import random
import sys
from flask import Flask, redirect, url_for, render_template, request, session
from flask_babel import Babel, gettext
from game import Game


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


app = Flask(__name__)
app.secret_key = open('secret.key').read()
babel = Babel(app)
games = {}
total_games = 0


def json_405(**kwargs):
    return {'message': 'Method not allowed'}, 405


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(['en', 'nl'])


@app.route('/')
def index():
    return render_template('index.html')


app.add_url_rule('/create/', view_func=json_405)
@app.route('/create/', methods=['POST'])
def create_game():
    name = request.form.get('name')
    if name is None:
        return {'message': f'Name field is not found or empty'}, 400
    code = None
    while code is None or code in games:
        code = ''.join((random.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(6)))
    game = Game()
    games[code] = game
    global total_games
    total_games += 1
    game.add_player(name)
    session[code] = name
    return redirect(url_for('show_game', code=code))


@app.route('/status/')
def get_status():
    return render_template('status.html', game_count=len(games),
            total_game_count=total_games)


@app.route('/<string:code>/')
def show_game(code: str):
    return render_template('game.html')


app.add_url_rule('/<string:code>/action/<string:activity>/', view_func=json_405)
@app.route('/<string:code>/action/<string:activity>/', methods=['POST'])
def perform_action(code: str, activity: str):
    game = games.get(code)
    if game is None:
        return {'message': f'Game {code} not found'}, 404
    name = session.get(code)
    if name is None:
        return {'message': f'Name is not set'}, 404
    game.perform_action(name, activity, request.form)
    return {}, 200


app.add_url_rule('/<string:code>/info/', view_func=json_405, methods=['POST'])
@app.route('/<string:code>/info/')
def get_game_info(code: str):
    game = games.get(code)
    if game is None:
        return {'message': f'Game {code} not found'}, 404
    return {
            'started': game.started,
            'finished': game.finished,
            'activity': game.current_activity,
            'players': list(game.player_roles),
        }


app.add_url_rule('/<string:code>/info/<string:activity>/', view_func=json_405, methods=['POST'])
@app.route('/<string:code>/info/<string:activity>/')
def get_game_info_activity(code: str, activity: str):
    game = games.get(code)
    if game is None:
        return {'message': f'Game {code} not found'}, 404
    name = session.get(code)
    if name is None:
        return {'message': f'Name is not set'}, 400
    return game.get_info(name, activity)


app.add_url_rule('/<string:code>/join/', view_func=json_405)
@app.route('/<string:code>/join/', methods=['POST'])
def join_game(code: str):
    name = request.form.get('name')
    if name is None:
        return {'message': f'Name field is not found or empty'}, 400
    game = games.get(code)
    if game is None:
        return {'message': f'Game {code} not found'}, 404
    if name in game.player_roles:
        if code in session:
            return {'message': f'Already joined game {code}'}, 400
        else:
            return {'message': f'Name {name} already taken'}, 403
    if game.started:
        return {'message': f'Game {code} has already started'}, 404
    if __debug__:
        if code in session:
            eprint(f'Player {name} has code {code} set but has not joined the game')
    game.add_player(name)
    session[code] = name
    return {}, 200


app.add_url_rule('/<string:code>/join/', view_func=json_405)
@app.route('/<string:code>/start/', methods=['POST'])
def start_game(code: str):
    game = games.get(code)
    if game is None:
        return {'message': f'Game {code} not found'}, 404
    if game.started:
        return {'message': f'Game {code} has already started'}, 404
    game.start()
    return {}


if __name__ == '__main__':
    app.run(port=5000)
