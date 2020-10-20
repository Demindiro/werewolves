#!/usr/bin/env python3

from game import Game, GameException


def new_game(player_count):
    # Player names follow the RFC 3092 convention
    player_names = ['Foo', 'Bar', 'Baz', 'Qux', 'Quux', 'Corge', 'Grault',
            'Garply', 'Waldo', 'Fred', 'Plugh', 'Xyzzy', 'Thud']
    game = Game()
    for i in range(player_count):
        game.add_player(player_names[i])
    game.start()
    return game



if True:
    # Test a successfull game with 4 players
    game = new_game(4)

    assert game.current_activity == 'wolves'

    # Kill a random citizen
    wolf = [p for p, r in game.player_roles.items() if r == 'wolf'][0]
    victim = [p for p, r in game.player_roles.items() if r == 'citizen'][0]
    game.perform_action(wolf, 'wolves', {'player': victim})

    assert game.current_activity == 'vote'
    assert game.dead_players == {victim}

    # Vote for self to simulate tie
    for player in (p for p in game.player_roles if p not in game.dead_players):
        game.perform_action(player, 'vote', {'player': player})

    assert game.current_activity == 'vote'
    assert game.get_info(wolf, 'vote') == {
            'vote': wolf,
            'vote_count': {p: 1 for p in game.player_roles if p not in game.dead_players},
            'options': [p for p in game.player_roles if p not in game.dead_players],
        }
    assert game.dead_players == {victim}

    # Make any alive citizen vote for the wolf
    for player in (p for p, r in game.player_roles.items() if r != 'wolf' and
            p not in game.dead_players):
        game.perform_action(player, 'vote', {'player': wolf})
        break

    assert game.finished
    assert game.dead_players == {victim, wolf}
