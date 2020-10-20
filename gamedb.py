#!/usr/bin/env python3

import sqlite3
from game import Game
from threading import Lock



class DBLock:

    def __init__(self, cursor):
        self.mutex = Lock()
        self.cursor = cursor


    def __enter__(self):
        self.mutex.acquire()
        self.cursor.execute('BEGIN EXCLUSIVE')


    def __exit__(self, type, value, traceback):
        self.cursor.execute('END')
        self.mutex.release()


    def locked(self):
        return self.mutex.locked()


connection = sqlite3.connect('games.db', check_same_thread=False)
cursor = connection.cursor()
lock = DBLock(cursor)

if __debug__:
    connection.set_trace_callback(print)


def create_game(code: str) -> None:
    state = Game().serialize()
    cursor.execute("INSERT INTO games(code, state) VALUES(?, ?)", (code, state))
    if not lock.locked():
        connection.commit()


def save_game(code: str, game: Game) -> None:
    state = game.serialize()
    cursor.execute("UPDATE games SET state = ? WHERE code = ?", (state, code))
    if not lock.locked():
        connection.commit()


def load_game(code: str) -> Game:
    cursor.execute("SELECT state FROM games WHERE code = ?", (code,))
    row = cursor.fetchone()
    if row is not None:
        return Game(row[0])
    return None


if __name__ == '__main__':
    print(f'Creating table games')
    cursor.execute('''
            CREATE TABLE games (
                    code varchar(6) PRIMARY KEY,
                    state text NOT NULL,
                    date datetime DEFAULT CURRENT_TIMESTAMP
                )''')
    connection.commit()
