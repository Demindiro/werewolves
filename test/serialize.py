#!/usr/bin/env python3

import sys
import json
sys.path.append("..")
from game import Game


game = Game()
serialized = game.serialize()
game_loaded = Game(serialized)
assert serialized == game_loaded.serialize()
assert game.serialize() == game_loaded.serialize()
assert serialized == game.serialize()


game = Game()
game.add_player('foo')
serialized = game.serialize()
game_loaded = Game(serialized)
assert len(json.loads(serialized)['players']) == 1
assert serialized == game_loaded.serialize()
assert game.serialize() == game_loaded.serialize()
assert serialized == game.serialize()
