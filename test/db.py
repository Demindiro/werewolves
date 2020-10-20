#!/usr/bin/env python3

import sys
sys.path.append("..")
from game import Game
import gamedb


gamedb.create_game('abcdef')

game = gamedb.load_game('abcdef', True)
assert game.serialize() == Game().serialize()

game = gamedb.load_game('abcdef', False)
assert game.serialize() == Game().serialize()
game = gamedb.save_game('abcdef', game, True)
