from fastapi import FastAPI, Response

from bot4wz import (
    find_initial_rate,
    players_file,
    games_file,
    )

app = FastAPI()

@app.get("/")
async def hello():
    return {"message": "Hello everyone from rakou's phone"}

@app.get("/histogram/{ladder}")
def show_ladder_histogram(ladder: str):
    initial_rate, img = find_initial_rate(players, ladder, visualize=True)
    return Response(content=img, media_type="image/png")
