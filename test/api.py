#!/usr/bin/env python3

import requests as req
import random


BASE_URL = 'http://localhost:5000/api'


names = ['Foo', 'Bar', 'Baz', 'Qux', 'Quux']
sessions = {}


# Create a game
names_stack = list(names)
owner = names_stack.pop()
r = req.post(f'{BASE_URL}/create/', data = {'name': owner})
assert r.status_code == 201
game_code = r.json()['code']
sessions[owner] = r.cookies['session']

# Add other users to it
while len(names_stack) > 0:
    n = names_stack.pop()
    r = req.post(f'{BASE_URL}/join/{game_code}/', data = {'name': n})
    assert r.status_code == 200
    sessions[n] = r.cookies['session']

del names_stack

# Start the game
r = req.post(f'{BASE_URL}/start/{game_code}/', cookies={'session': sessions[owner]})
assert r.status_code == 200

# Get the current activity (and check it's the same for all clients)
# Also check the game actually started
# Also check if all players are added
r = req.get(f'{BASE_URL}/info/{game_code}/', cookies={'session': sessions[owner]})
j = r.json()
assert r.status_code == 200
for n in names:
    r = req.get(f'{BASE_URL}/info/{game_code}/', cookies={'session': sessions[n]})
    assert r.status_code == 200
    assert r.json()['activity'] == j['activity']
    assert r.json()['activity'] != 'waiting'
    assert set(r.json()['players']) == set(names)

activity = j['activity']

# Find out who the wolves are
assert activity == 'wolves'
wolves = []
for n in names:
    r = req.get(f'{BASE_URL}/info/{game_code}/', cookies={'session': sessions[n]})
    assert r.status_code == 200
    j = r.json()
    if len(j['state']) > 0:
        wolves.append(n)
        assert set(j['state']['options']) == set(names)

assert len(wolves) > 0


if len(wolves) == 1:
    wolf = wolves[0]

    # Make the wolf kill any player except himself
    dead = None
    for n in names:
        if n != wolf:
            r = req.post(f'{BASE_URL}/action/{game_code}/', cookies={'session': sessions[wolf]},
                    data = {'player': n})
            dead = n
            assert r.status_code == 200
            break
    alive = [u for u in names if u != dead]

    # Check if the current activity is voting
    for n in names:
        r = req.get(f'{BASE_URL}/info/{game_code}/', cookies={'session': sessions[n]})
        assert r.status_code == 200
        assert r.json()['activity'] == 'vote'

    # Simulate a voting tie
    shuffled = alive[:]
    random.shuffle(shuffled)
    for n, m in zip(alive, shuffled):
        r = req.post(f'{BASE_URL}/action/{game_code}/', cookies={'session': sessions[n]},
                data = {'player': m})
        assert r.status_code == 200

    # Check if the current activity is still voting
    for n in names:
        r = req.get(f'{BASE_URL}/info/{game_code}/', cookies={'session': sessions[n]})
        assert r.status_code == 200
        assert r.json()['activity'] == 'vote'

    # Check if the votes are cast correctly:
    for n, m in zip(alive, shuffled):
        r = req.get(f'{BASE_URL}/info/{game_code}/', cookies={'session': sessions[n]})
        assert r.status_code == 200
        assert r.json()['state']['vote'] == m
        assert r.json()['state']['vote_count'] == {u: 1 for u in alive}
        assert r.json()['state']['options'] == [] if n == dead else alive

    # Make any player except the wolf vote for the wolf
    # Also check the player didn't already vote for the wolf
    for n, m in zip(alive, shuffled):
        if n != wolf and m != wolf:
            r = req.post(f'{BASE_URL}/action/{game_code}/', cookies={'session': sessions[n]},
                    data = {'player': wolf})
            assert r.status_code == 200
            break

    # Check if the game has finished
    for n in alive:
        r = req.get(f'{BASE_URL}/info/{game_code}/', cookies={'session': sessions[n]})
        assert r.json()['activity'] == 'finished'
        assert r.status_code == 200
 
else:

    # TODO
    assert False

    # Make the wolves vote for themselves to simulate a tie
    for n in wolves:
        r = req.post(f'{BASE_URL}/action/{game_code}/', cookies={'session': sessions[n]},
                data = {'player': n})
        assert r.status_code == 200

    # Make sure the votes are cast correctly
    assert activity == 'wolves'
    for n in wolves:
        r = req.get(f'{BASE_URL}/info/{game_code}/', cookies={'session': sessions[n]})
        assert r.status_code == 200
        j = r.json()
        assert len(j) > 0
        assert j['vote'] == n
        assert j['vote_count'] == {u: 1 for u in wolves}

    # Make any two wolves vote for any non-wolf
#    for n in names:
#        i = 0
#        for w in wolves:
