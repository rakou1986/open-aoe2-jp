#coding: utf-8

import os
import pickle

from fastapi import FastAPI, Response

from bot4wz import (
    Player,
    Game,
    players_file_name,
    games_file_name,
    )
from rating_statistics import (
    find_initial_rate,
    visualize_player_rate,
    )

players = []
games = []

def load():
    global players
    if os.path.exists(players_file_name):
        with open(players_file_name, "rb") as f:
            try:
                players = pickle.load(f)
            except Exception as e:
                pass
    global games
    if os.path.exists(games_file_name):
        with open(games_file_name, "rb") as f:
            try:
                games = pickle.load(f)
            except Exception as e:
                pass

load()
app = FastAPI()

@app.get("/")
async def hello():
    return {"message": "Hello everyone from rakou's phone"}

@app.get("/histogram/initial_rate/{ladder}")
async def show_initial_rate_histogram(ladder: str):
    print(len(players))
    if players:
        print(players[0].name)
    initial_rate, method, image_bytes = find_initial_rate(players, ladder, visualize=True)
    return Response(content=image_bytes, media_type="image/png")

@app.get("/histogram/player/{player_id}/{ladder}")
async def show_player_histogram(player_id: int, ladder: str):
    image_bytes = visualize_player_rate(players, ladder, player_id)
    return Response(content=image_bytes, media_type="image/png")

@app.get("/reload")
async def reload():
    load()
    return "reloaded."
