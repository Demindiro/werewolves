import random


class GameException(Exception):
    pass


class Game:

    player_roles = {}
    dead_players = set()
    current_activity = ''
    started = False
    finished = False
    _activity_order = (
            'wolves',
            'vote',
        )
    _activity_index = 0
    _activity_state = {}


    def __init__(self):
        self._activity_actions = {
            'vote': self._action_vote,
            'wolves': self._action_wolves,
        }
        self._activity_info = {
            'vote': self._info_vote,
            'wolves': self._info_wolves,
        }


    def add_player(self, name: str):
        name = name.strip()
        if name in self.player_roles:
            raise GameException('Name {name} has already been taken')
        self.player_roles[name] = 'citizen'


    def start(self):
        wolf = random.choice(list(self.player_roles))
        self.player_roles[wolf] = 'wolf'
        self.current_activity = self._activity_order[self._activity_index]
        self.started = True


    def perform_action(self, player: str, activity: str, action: dict):
        if self.finished:
            raise GameException('The game has finished')
        if activity not in self._activity_actions:
            raise GameException(f'Activity {activity} does not exist')
        return self._activity_actions[activity](player, action)


    def _next_activity(self):
        self._activity_state = {}

        if self.current_activity == 'vote':
            self.finished = self._is_finished()
            if self.finished:
                return

        assert(not self.finished)

        assert(self._activity_order[self._activity_index] == self.current_activity)
        self._activity_index += 1
        self._activity_index %= len(self._activity_order)
        self.current_activity = self._activity_order[self._activity_index]

        if self.current_activity == 'vote':
            self.finished = self._is_finished()


    def _action_vote(self, player: str, action: dict):
        self._check_activity('vote')
        self._check_alive(player)
        user = Game._get_action_value(action, 'player', str)
        self._check_exists(user)
        self._check_alive(user)

        state = self._activity_state
        state.setdefault('voted_for', {})
        if state['voted_for'].get(player) == user:
            state['votes'][user] -= 1
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
        state.setdefault('voted_for', {})
        if state['voted_for'].get(player) == user:
            state['votes'][user] -= 1
        state['voted_for'][player] = user
        state.setdefault('votes', {}).setdefault(user, 0)
        state['votes'][user] += 1

        wolf_count = len([p for p in self.player_roles if p not in self.dead_players and self.player_roles[p] == 'wolf'])
        if len(state['voted_for']) == wolf_count:
            players = [p for p, v in state['votes'].items() if v > 0]
            if len(players) == 1:
                self.dead_players.add(players[0])
                self._next_activity()


    def _info_vote(self, player: str, action: dict):
        return {
                'vote': state['voted_for'].get(player),
                'vote_count': state.getdefault('votes', {}),
                'options': [] if player in self.dead_players else
                        [p for p in player_roles if p not in self.dead_players]
            }


    def _info_wolves(self, player: str, action: dict):
        if player_roles[player] == 'wolf':
            return {
                    'vote': state['voted_for'].get(player),
                    'vote_count': state.getdefault('votes', {}),
                    'options': [] if player in self.dead_players else
                            [p for p in player_roles if p not in self.dead_players]
                }
        return {}


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
        if self.current_activity != name:
            raise GameException(f'Current activity is {self.current_activity}, not {name}')


    def _check_alive(self, name: str):
        if name in self.dead_players:
            raise GameException(f'Player {name} is dead')


    def _check_exists(self, name: str):
        if name not in self.player_roles:
            raise GameException(f'Player {name} does not exist')


    def _get_action_value(action: dict, key: str, p_type: type):
        value = action.get(key)
        if value is None:
            raise GameException(f'Expected {key} field in action')
        if type(value) != p_type:
            raise GameException(f'{key} value is not a {p_type}')
        return value