#!/usr/bin/env python3

import sys
sys.path.append("..")
from game import Game


game = Game()
serialized = game.serialize()
game_loaded = Game(serialized)
assert serialized == game_loaded.serialize()
assert game.serialize() == game_loaded.serialize()
assert serialized == game.serialize()
