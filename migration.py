#coding: utf-8

import random
import pickle
from datetime import datetime
from bot4wz import Player, players_file_name, ladder_dict

"""
find_initial_rate(...)のテスト用playersを作る。のちのちデータ移行にも使う
"""

players = []

class User(object):
    def __init__(self, id, name):
        self.id = id
        self.name = name

def generate_players(count=1000, center=8000, spread=300):
    global players
    for i in range(count):
        rate = int(random.gauss(center, spread))
        ladder_initial_rate = {}
        for ladder in ladder_dict.keys():
            ladder_initial_rate.update({ladder: rate})
        id_ = len(players) + 1
        user = User(id=i, name=f"TestPlayer_{i}")
        players.append(Player(user, ladder_initial_rate=ladder_initial_rate))


def generate_players_single_peak():
    """山を重ねてmin_peak_distanceの機能を見るための分布"""
    generate_players(count=500, center=8000, spread=100)
    generate_players(count=500, center=8100, spread=100)
    generate_players(count=500, center=7800, spread=100)
    generate_players(count=50, center=7700, spread=100)
    generate_players(count=50, center=7900, spread=100)
    generate_players(count=50, center=8300, spread=100)

def generate_players_multi_peak():
    """山が2つある分布"""
    group1 = generate_players(count=500, center=7200, spread=100)
    group2 = generate_players(count=500, center=8800, spread=100)

if __name__ == "__main__":
    generate_players_single_peak()
    #generate_players_multi_peak()

    with open(players_file_name, "wb") as f:
        pickle.dump(players, f)

    print("保存完了")
