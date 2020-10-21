#!/usr/bin/env python3

import random
import sys
from flask import Flask, redirect, url_for, render_template, request, session, Blueprint
from game import Game
import gamedb


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


api = Blueprint('api', __name__)


@api.errorhandler(405)
def handle_405(**kwargs):
    return {'message': 'Method not allowed'}, 405


@api.route('/')
def index():
    return {}


@api.route('/create/', methods=['POST'])
def create_game():
    name = request.form.get('name')
    if name is None:
        return {'message': f'Name field is not found or empty'}, 400
    code = None
    while code is None or gamedb.load_game(code) is not None:
        code = ''.join((random.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(6)))
    with gamedb.lock:
        gamedb.create_game(code)
        game = gamedb.load_game(code)
        game.add_player(name)
        gamedb.save_game(code, game)
    session[code] = name
    return {'code': code}, 201


@api.route('/info/<string:code>/')
def get_game_info(code: str):
    game = gamedb.load_game(code)
    if game is None:
        return {'message': f'Game {code} not found'}, 404
    d = {
            'activity': game.activity,
            'players': list(game.player_roles),
        }
    name = session.get(code)
    if name is not None or game.activity == 'finished':
        d['state'] = game.get_info(name)
    return d


@api.route('/action/<string:code>/', methods=['POST'])
def perform_action(code: str):
    with gamedb.lock:
        game = gamedb.load_game(code)
        if game is None:
            return {'message': f'Game {code} not found'}, 404
        name = session.get(code)
        if name is None:
            return {'message': f'Name is not set'}, 404
        game.perform_action(name, request.form)
        gamedb.save_game(code, game)
    return {}, 200


@api.route('/join/<string:code>/', methods=['POST'])
def join_game(code: str):
    name = request.form.get('name')
    if name is None:
        return {'message': f'Name field is not found or empty'}, 400
    with gamedb.lock:
        game = gamedb.load_game(code)
        if game is None:
            return {'message': f'Game {code} not found'}, 404
        if name in game.player_roles:
            if code in session:
                return {'message': f'Already joined game {code}'}, 400
            else:
                return {'message': f'Name {name} already taken'}, 403
        if game.activity != 'waiting':
            return {'message': f'Game {code} has already started'}, 404
        if code in session:
            eprint(f'Player {name} has code {code} set but has not joined the game')
        game.add_player(name)
        game = gamedb.save_game(code, game)
    session[code] = name
    return {}, 200


@api.route('/start/<string:code>/', methods=['POST'])
def start_game(code: str):
    with gamedb.lock:
        game = gamedb.load_game(code)
        if game is None:
            return {'message': f'Game {code} not found'}, 404
        if game.activity != 'waiting':
            return {'message': f'Game {code} has already started'}, 404
        game.start()
        gamedb.save_game(code, game)
    return {}, 200
