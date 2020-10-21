import random
import json


class GameException(Exception):
    pass


class Game:

    def __init__(self, serialized_data: dict = None):
        self._activity_order = (
            'wolves',
            'vote',
        )
        self._activity_actions = {
            'vote': self._action_vote,
            'wolves': self._action_wolves,
        }
        self._activity_info = {
            'waiting': lambda _: {},
            'finished': self._info_finished,
            'vote': self._info_vote,
            'wolves': self._info_wolves,
        }
        if serialized_data is None:
            self.player_roles = {}
            self.dead_players = set()
            self.activity = 'waiting'
            self._activity_state = {}
        else:
            data = json.loads(serialized_data)
            self.player_roles = data['players']
            self.dead_players = set(data['dead'])
            self.activity = data['activity']
            self._activity_state = data['state']


    def add_player(self, name: str):
        name = name.strip()
        if name in self.player_roles:
            raise GameException(f'Name {name} has already been taken')
        self.player_roles[name] = 'citizen'


    def start(self):
        if len(self.player_roles) < 4:
            raise GameException('You need at least 4 players to start a game')
        wolf = random.choice(list(self.player_roles))
        self.player_roles[wolf] = 'wolf'
        self.activity = self._activity_order[0]


    def perform_action(self, player: str, action: dict):
        self._check_not_finished()
        if self.activity == 'waiting':
            return GameError('Game has not started yet')
        return self._activity_actions[self.activity](player, action)


    def get_info(self, player: str):
        return self._activity_info[self.activity](player)


    def serialize(self):
        return json.dumps({
                'players': self.player_roles,
                'dead': list(self.dead_players),
                'activity': self.activity,
                'state': self._activity_state,
            })


    def _next_activity(self):
        self._activity_state = {}

        if self.activity == 'vote':
            if self._is_finished():
                self.activity = 'finished'
                return

        assert self.activity != 'waiting'
        assert self.activity != 'finished'

        index = self._activity_order.index(self.activity)
        index += 1
        index %= len(self._activity_order)
        self.activity = self._activity_order[index]

        if self.activity == 'vote':
            if self._is_finished():
                self.activity = 'finished'


    def _action_vote(self, player: str, action: dict):
        self._check_activity('vote')
        self._check_alive(player)
        user = Game._get_action_value(action, 'player', str)
        self._check_exists(user)
        self._check_alive(user)

        state = self._activity_state
        voted_for = state.setdefault('voted_for', {}).get(player)
        if voted_for is not None:
            state['votes'][voted_for] -= 1
        state['voted_for'][player] = user
        state.setdefault('votes', {}).setdefault(user, 0)
        state['votes'][user] += 1

        if len(state['voted_for']) == len(self.player_roles) - len(self.dead_players):
            max_votes = max(state['votes'].values())
            players = [p for p in state['votes'] if state['votes'][p] == max_votes]
            if len(players) == 1:
                self.dead_players.add(players[0])
                self._next_activity()


    def _action_wolves(self, player: str, action: dict):
        self._check_activity('wolves')
        self._check_alive(player)
        if self.player_roles[player] != 'wolf':
            raise GameException(f'Player {player} is not a wolf')
        user = Game._get_action_value(action, 'player', str)
        self._check_exists(user)
        self._check_alive(user)

        state = self._activity_state
        voted_for = state.setdefault('voted_for', {}).get(player)
        if voted_for is not None:
            state['votes'][voted_for] -= 1
        state['voted_for'][player] = user
        state.setdefault('votes', {}).setdefault(user, 0)
        state['votes'][user] += 1

        wolf_count = len([p for p in self.player_roles if p not in self.dead_players and self.player_roles[p] == 'wolf'])
        if len(state['voted_for']) == wolf_count:
            players = [p for p, v in state['votes'].items() if v > 0]
            if len(players) == 1:
                self.dead_players.add(players[0])
                self._next_activity()


    def _info_vote(self, player: str):
        self._check_activity('vote')
        state = self._activity_state
        return {
                'vote': state.get('voted_for', {}).get(player),
                'vote_count': state.get('votes', {}),
                'options': [] if player in self.dead_players else
                        [p for p in self.player_roles if p not in self.dead_players]
            }


    def _info_wolves(self, player: str):
        self._check_activity('wolves')
        state = self._activity_state
        if self.player_roles[player] == 'wolf':
            return {
                    'vote': state.get('voted_for', {}).get(player),
                    'vote_count': state.get('votes', {}),
                    'options': [] if player in self.dead_players else
                            [p for p in self.player_roles if p not in self.dead_players]
                }
        return {}


    def _info_finished(self, player: str):
        self._check_activity('finished')
        return {
                'winners': self._activity_state['winners']
            }


    def _is_finished(self):
        wolf_count = 0
        citizen_count = 0
        for player in (p for p in self.player_roles if p not in self.dead_players):
            if self.player_roles[player] == 'wolf':
                wolf_count += 1
            else:
                citizen_count += 1
        if wolf_count == 0:
            self._activity_state['winners'] = 'citizens'
            return True
        elif wolf_count >= citizen_count:
            self._activity_state['winners'] = 'wolves'
            return True
        return False


    def _check_activity(self, name: str):
        if self.activity != name:
            raise GameException(f'Current activity is {self.activity}, not {name}')


    def _check_alive(self, name: str):
        if name in self.dead_players:
            raise GameException(f'Player {name} is dead')


    def _check_exists(self, name: str):
        if name not in self.player_roles:
            raise GameException(f'Player {name} does not exist')


    def _check_not_finished(self):
        if self.activity == 'finished':
            raise GameException('The game has finished')


    def _get_action_value(action: dict, key: str, p_type: type):
        value = action.get(key)
        if value is None:
            raise GameException(f'Expected {key} field in action')
        if type(value) != p_type:
            raise GameException(f'{key} value is not a {p_type}')
        return value
