#coding: utf-8
#!/path/to/Python_3.12.10

_debug = True

"""
[requirements]
python -V
Python 3.12.10

pip show discord
Version: 2.3.2

[discord developer setting]
Bot:
  MESSAGE CONTENT INTENT: enable
  TOKEN: Press "Reset Token". Token appear once. Copy token and paste to token.txt

OAuth2:
  SCOPES:
    bot
  BOT PERMISIOONS:
    Send Messages
    Manage Messages
    Read Message History
    Mention Everyone

  Copy and paste to warzone "GENERATED URL" at "OAuth2"

[run]
$ python bot4wz.py

[quit]
Ctrl + C
"""

import asyncio
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
import json
import os
import io
import matplotlib.pyplot as plt
import numpy as np
import pickle
import psutil
import random
import re
from scipy.signal import find_peaks
import socket
import statistics
import sys
import time
import urllib

import discord
from discord.ext import commands
import rapidfuzz

TOKEN = None


if _debug:
    token_file_name = "canary_token.txt"
    from bot_settings import canary_bot_target_channel_id as target_channel_id
    from bot_settings import canary_bot_server_id as guild_id
else:
    token_file_name = "token.txt"
    from bot_settings import available_bot_target_channel_id as target_channel_id
    from bot_settings import available_bot_server_id as guild_id
import usage

try:
    from secret import secret_commands
    from secret import process_secret_commands
    print("隠しコマンドが有効です。")
except ImportError:
    secret_commands = []
    process_secret_commands = None

if os.path.exists(token_file_name):
    with open(token_file_name) as f:
        TOKEN = f.read().strip()
        print(f"{token_file_name}を読み取りました。")

if TOKEN is None:
    print(usage.no_token)
    input("Enterを押して終了: ")
    sys.exit(0)

def now():
    return datetime.now()

lock = asyncio.Lock()
on_ready_complete = asyncio.Event()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
allowed_mentions = discord.AllowedMentions(users=True)
bot = commands.Bot(command_prefix="!", intents=intents)

bot_commands = [
    "--yyk", "--call", "--create", "--reserve", "--heybros",
    "--ln",
    "--michi",
    "--bakuha", "--del", "--cancel", "--destroy", "--hakai", "--explosion",
    "--no", "--in", "--join",
    "--nuke", "--out", "--leave", "--dismiss",
    "--rooms",
    "--force-bakuha-tekumakumayakonn-tekumakumayakonn",
    "--help", "--help-en",
    ] + secret_commands
room_number_pool = list(range(1, 100))
room_number_pool_file_name = ".bot4wz.room_number_pool.pickle"
rooms = []
rooms_file_name = ".bot4wz.rooms.pickle"
temp_message_ids = []
temp_message_ids_file_name = ".bot4wz.temp_message_ids.pickle"
last_process_message_timestamp = now()
players = []
players_file_name = ".bot4wz.players.pickle"
games = []
games_file_name = ".bot4wz.games.pickle"
ladder_dict = {
    "Arabia": "アラビア系",
    "LN": "遊牧系",
    "Michi": "みち",
}


class RoomNumberExhaust(BaseException):
    def __init__(self):
        pass


class RoomPicklable(object):

    def __init__(self, room):
        self.number = room.number
        self.name = room.name
        self.owner_id = room.owner.id
        self.member_ids = [user.id for user in room.members]
        self.capacity = room.capacity
        self.garbage_queue = room.garbage_queue
        self.last_notice_timestamp = room.last_notice_timestamp
        self.ladder = room.ladder
        self.team1 = room.team1
        self.team2 = room.team2
        self.fighting = room.fighting
        self.win_team = room.win_team

    async def to_room(self, bot):
        guild = bot.get_guild(guild_id)
        if not guild:
            raise ValueError("Guild not found")

        try:
            owner = await guild.fetch_member(self.owner_id)
        except discord.NotFound:
            owner = None

        members = []
        for user_id in self.member_ids:
            try:
                member = await guild.fetch_member(user_id)
                members.append(member)
            except discord.NotFound:
                continue
        room = Room(author=owner, name=self.name, capacity=self.capacity, ladder=self.ladder)
        room.number = self.number
        room.members = members
        room.garbage_queue = self.garbage_queue
        room.last_notice_timestamp = self.last_notice_timestamp
        room.team1 = self.team1
        room.team2 = self.team2
        room.fighting = self.fighting
        room.win_team = self.win_team
        return room


class Room(object):

    def __init__(self, author , name, capacity, ladder):
        try:
            self.number = room_number_pool.pop(0)
        except IndexError:
            raise RoomNumberExhaust
        self.name = name
        self.owner = author
        self.members = [author]
        self.capacity = capacity
        self.garbage_queue = []
        self.last_notice_timestamp = now()
        self.ladder = ladder
        # team1, team2にはself.membersの中にあるDiscord.UserではなくPlayerを入れる。
        # message.author.idでPlayerが見つからなければ作って入れる
        self.team1 = []
        self.team2 = []
        self.fighting = False
        self.win_team = None


class Player(object):

    def __init__(self, user, ladder_to_rate={ladder: find_initial_rate(players, ladder)[0] for ladder in ladder_dict.keys()}, rating_booster=30):
        self.id = user.id
        self.name = user.name
        self.rate_history = {}
        self.rating_booster = rating_booster # 最大値30。新規は30、久しぶりは15加算。何回久しぶりになっても30まで。
        for ladder in ladder_dict.keys():
            self.rate_history.update({
                ladder: [{
                    "rate": ladder_to_rate[ladder],
                    "timestamp": now(),
                }]
            })

    def latest_winrate(go_back, ladder):
        rates = [record["rate"] for record in self.rate_history[ladder][-go_back -1:]]
        win = 0
        lose = 0
        prev = rates.pop(0)
        if not rates:
            return 0
        for next_ in rate:
            if prev < next_:
                win += 1
            else:
                lost += 1
            prev = next_
        return win / (win + lose)

    def streak(ladder):
        idx = -1
        streak = 0
        rates = [record["rate"] for record in self.rate_history[ladder]]
        next_ = rates[idx]
        for i in range(len(rates) - 1):
            idx -= 1
            prev = rates[idx]
            if prev < next_:
                if 0 <= streak:
                    streak += 1
                else:
                    break
            else:
                if streak <= 0:
                    streak -= 1
                else:
                    break
            next_ = prev
        return streak

    def latest_rate(ladder):
        return self.rate_history[ladder][-1]["rate"]

    def latest_timestamp(ladder):
        return self.rate_history[ladder][-1]["timestamp"]


class Game(object):
    def __init__(self, id, host_id, ladder, team1_deltas, team2_deltas, win_team):
        self.id = id
        self.host_id = host_id
        self.ladder = ladder
        self.team1_deltas = team1
        self.team2_deltas = team2
        self.timestamp = now()
        self.win_team = win_team

def split(players):
    half = len(players) // 2
    delta_min = float("infinity")

def process_umari(room):
    pass

def make_rate_histogram(players, ladder, bin_width=20):
    histogram = defaultdict(int)
    for player in players:
        latest_rate = player.latest_rate(ladder)
        bucket = bin_width * (latest_rate // bin_width)
        histogram[bucket] += 1
    return dict(sorted(histogram.items()))

def pick_peak_or_median(histogram, players, ladder):
    keys = list(histogram.keys())
    values = list(histogram.values())
    smooth = np.convolve(values, [1, 1, 1], mode="same")
    peaks, properties = find_peaks(smooth)
    if len(peaks) == 1:
        max_idx = int(np.argmax(smooth))
        return keys[max_idx], "peak"
    else:
        all_rates = [player.latest_rate(ladder) for player in players]
        return int(statistics.median(all_rates)), "median"

def draw_histogram_png(histogram, value, ladder, method):
    fig, ax = plt.subplots()
    bins = list(histogram.keys())
    values = list(histogram.values())
    ax.bar(bins, values, width=18, align="center", edgecolor="black")
    ax.axvline(x=value, color="red", linestyle="--")
    ax.annotate(f"Initial rate ({method}): {value}",
            xy=(value, max(values) * 0.9),
            xytext=(value + 100, max(values) * 0.9),
            arrowprops=dict(facecolor='red', shrink=0.05),
            fontsize=10)
    ax.set_xlabel("Rating")
    ax.set_ylabel("Players")
    ax.set_title(f"'{ladder}' Rating Histogram")
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return buf.read()

def find_initial_rate(players, ladder, visualize=False):
    image_bytes = None
    histogram = make_rate_histogram(players, ladder)
    value, method = pick_peak_or_median(histogram, players, ladder)
    if visualize:
        image_bytes = draw_histogram_png(histogram, value, ladder, method)
    initial_rate = value
    return initial_rate, image_bytes

async def customized_elo_rating(room):
    """
    スマーフ対策済み、適正値に早く近づくメンテフリーなELOレーティング
    """
    ladder = room.ladder
    players = room.team1 + room.team2

    Ra = sum(player.latest_rate(ladder) for player in room.team1)
    Rb = sum(player.latest_rate(ladder) for player in room.team2)
    team1_winrate_avg = sum(player.latest_winrate(30) for player in room.team1) / len(room.team1)
    team2_winrate_avg = sum(player.latest_winrate(30) for player in room.team2) / len(room.team2)

    deltas = {}
    for player in players:
        player_team = 1 if player in room.team1 else 2
        win = room.win_team == player_team

        team_rate = Ra if player_team == 1 else Rb
        opponent_rate = Rb if player_team == 1 else Ra

        # イロレーティングはチェス(1v1)なので、チームレート差のスケールを合わせたほうがよい。例えば4v4なら1/4、3v3なら1/3。
        Ea = 1.0 / (1 + 10 ** ( ((opponent_rate - team_rate) / len(players) / 2) / 400.0))
        Sa = 1 if win else 0
        K = customized_k_factor(player, room, win, player_team, team1_winrate_avg, team2_winrate_avg)
        delta = K * (Sa - Ea)
        delta = int(Decimal(delta).quantize(Decimal("0"), ROUND_HALF_UP))
        delta = max(1, delta)

        player.rate_history[ladder].append({
            "rate": player.latest_rate(ladder) + delta,
            "timestamp": now()
        })
        deltas.append({"name": player.name, "delta": delta})

    team1_deltas = [(player.name, deltas[player.name]) for player in room.team1]
    team2_deltas = [(player.name, deltas[player.name]) for player in room.team2]
    games.append(
        Game(id=len(games)+1, host_id=room.owner.id, ladder=ladder,
        team1_deltas=team1_deltas, team2_deltas=team2_deltas, win_team=room.win_team)
    )

    await save_rating_system()
    return result


def customized_k_factor(player, room, win, player_team, team1_winrate_avg, team2_winrate_avg):
    base_K = 26 # たまひよが約26
    ladder = room.ladder

    # 復帰者に補正をつける
    if timedelta(days=90) < now() - player.latest_timestamp:
        player.rating_booster = min(30, player.rating_booster + 15)
    # player.rating_boosterの初期値30、最大30。
    boost_ratio = 1.0 + 14 * player.rating_booster / 30
    winrate_ratio = 1.0
    streak_ratio = 1.0
    strength_ratio = 1.0
    streak = player.streak(ladder)

    if 0 < player.rating_booster:
        # スマーフ対策
        # 新規登録から間もないほど補正を強く。復帰から間もないほど補正を強く。
        matches = min(30, len(player.rate_history[ladder]) - 1)
        # 連敗が続くほど補正を減らす
        # 試合数が増えるにつれて補正の減らし方を穏やかにする
        weight = 1 + (30 / (matches + 1))
        if streak < -1:
            boost_ratio *= 0.90 ** (abs(streak) * weight)
        # 連敗ではなかろうが勝率でも負けすぎは補正を減らす
        if 4 < matches:
            winrate = player.latest_winrate(30, ladder)
            if winrate < 0.5:
                boost_ratio *= 0.988 ** ((0.5 - winrate) * 100 * weight)
        player.rating_booster -= 1
    else:
        # いつもやってる人（ブーストなし）は最近30戦で1％勝ち越す/負け越すごとに5％補正
        winrate = player.latest_winrate(30, ladder)
        winrate_ratio = 1 + 0.05 * abs(0.5 - winrate) * 100
        # 連勝・連敗補正
        if 1 < abs(streak):
            streak_ratio = 1.0 + 0.08 * abs(streak)

    # チーム平均勝率による補正
    if not team1_winrate_avg == team2_winrate_avg:
        winrate_delta = abs(team1_winrate_avg - team2_winrate_avg)
        if player_team == 1:
            lesser = team1_winrate_avg < team2_winrate_avg
        else:
            lesser = team2_winrate_avg < team1_winrate_avg
        lose = False if win else True
        greater = False if lesser else True
        if win and lesser: # 劣勢なのに勝った（レア）
            strength_ratio = 1 + 0.08 * winrate_delta * 100
        if win and greater: # 優勢で勝った（コモン）
            strength_ratio = 1 - 0.08 * winrate_delta * 100
        if lose and lesser: # 劣勢で負けた（コモン）
            strength_ratio = 1 - 0.08 * winrate_delta * 100
        if lose and greater: # 優勢なのに負けた（レア）
            strength_ratio = 1 + 0.08* winrate_delta * 100

    return base_K * boost_ratio * winrate_ratio * streak_ratio * strength_ratio


async def save_rating_system(backup=False):
    with open(players_file_name, "wb") as f:
        pickle.dump(players, f)
    with open(games_file_name, "wb") as f:
        pickle.dump(games, f)
    if backup:
        players_backup = os.path.join("./backup", now().strftime("%Y-%m-%d") + players_file_name)
        if not os.path.exists(players_backup):
            with open(players_backup, "wb") as f:
                pickle.dump(players, f)
        games_backup = os.path.join("./backup", now().strftime("%Y-%m-%d") + games_file_name)
        if not os.path.exists(games_backup):
            with open(games_backup, "wb") as f:
                pickle.dump(games, f)

async def save_bot_state():
    rooms_picklable = [RoomPicklable(room) for room in rooms]
    with open(rooms_file_name, "wb") as f:
        pickle.dump(rooms_picklable, f)
    with open(room_number_pool_file_name, "wb") as f:
        pickle.dump(room_number_pool, f)
    with open(temp_message_ids_file_name, "wb") as f:
        pickle.dump(temp_message_ids, f)

async def load(bot):
    global rooms
    if os.path.exists(rooms_file_name):
        with open(rooms_file_name, "rb") as f:
            try:
                rooms_picklable = pickle.load(f)
                rooms = await asyncio.gather(*(picklable.to_room(bot) for picklable in rooms_picklable))
            except Exception as e:
                pass
    global room_number_pool
    if os.path.exists(room_number_pool_file_name):
        with open(room_number_pool_file_name, "rb") as f:
            try:
                room_number_pool = pickle.load(f)
            except Exception as e:
                pass
    global temp_message_ids
    if os.path.exists(temp_message_ids_file_name):
        with open(temp_message_ids_file_name, "rb") as f:
            try:
                temp_message_ids = pickle.load(f)
            except Exception as e:
                pass
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

def to_int(string):
    try:
        return int(string)
    except ValueError:
        return None

def get_name(member):
    """サーバーニックネーム、表示名、ユーザー名（グローバル）の順に名前を探す"""
    if hasattr(member, "nick") and member.nick:
        return member.nick
    if hasattr(member, "global_name") and member.global_name:
        return member.global_name  # 実はglobal_nameがGUI上の「表示名」らしい。display_nameではない
    return member.name # これがglobal_nameのような気がするが…

def delete_room(room):
    rooms.pop(rooms.index(room))
    room_number_pool.append(room.number)
    room_number_pool.sort()

async def process_message(message):
    async with lock:
        reply = "初期値。問題が起きているのでrakouに連絡"
        room_to_clean = None
        temp_message = False

        for command in ["--yyk", "--call", "--create", "--reserve", "--heybros", "--ln", "--michi"]:
            if message.content.startswith(command):
                capacity = 8
                name = message.content.split(command)[1]
                if name:
                    if name[0] in ["1", "2", "3", "4", "5", "6", "１", "２", "３", "４", "５", "６"]:
                        capacity = to_int(name[0]) + 1
                        name = name.replace(name[0], "")
                name = "無制限" if not name else name.strip()
                if command == "--ln":
                    ladder = "LN"
                elif command == "--michi":
                    ladder = "Michi"
                else:
                    ladder = "Arabia"
                try:
                    room = Room(author=message.author, name=name, capacity=capacity, ladder=ladder)
                    rooms.append(room)
                    reply = f"[{room.number}] {room.name} ＠{room.capacity - len(room.members)} レーティング：{ladder_dict[ladder]}\n" + ", ".join(f"`{get_name(member)}`" for member in room.members)
                    room_to_clean = room
                    rooms.sort(key=lambda room: room.number)
                except RoomNumberExhaust:
                    reply = "部屋は同時に100個しか建てれません"
                    temp_message = True

        for command in ["--bakuha", "--del", "--cancel", "--destroy", "--hakai", "--explosion"]:
            if message.content.startswith(command):
                room_number = message.content.split(command)[1]
                if room_number == "":
                    owned_rooms = []
                    for room in rooms:
                        if message.author.id == room.owner.id:
                            owned_rooms.append(room)
                    if len(owned_rooms) == 1:
                        room = owned_rooms[0]
                        delete_room(room)
                        reply = f"爆破: [{room.number}] {room.name} ＠{room.capacity - len(room.members)}\n" + " ".join(f"{member.mention}" for member in room.members)
                        room_to_clean = room
                    elif len(owned_rooms) == 0:
                        reply = "現在、部屋はありません"
                        temp_message = True
                    else:
                        reply = "複数の部屋を建てたときは部屋番号を指定してね"
                        temp_message = True
                else:
                    room_number = to_int(room_number)
                    if room_number is None:
                        reply = "部屋番号をアラビア数字で指定してね"
                        temp_message = True
                    else:
                        room = None
                        for room_ in rooms:
                            if room_number == room_.number:
                                if message.author.id == room_.owner.id:
                                    room = room_
                                    break
                        if room is None:
                            reply = "その番号の部屋がないか、ホストではないため爆破できません"
                            temp_message = True
                        else:
                            delete_room(room)
                            reply = f"爆破: [{room.number}] {room.name} ＠{room.capacity - len(room.members)}\n" + " ".join(f"{member.mention}" for member in room.members)
                            room_to_clean = room

        for command in ["--no", "--in", "--join"]:
            if message.content.startswith(command):
                room_number = message.content.split(command)[1]
                room = None
                if room_number == "":
                    if len(rooms) == 1:
                        room = rooms[0]
                        if not message.author in room.members:
                            if room.fighting:
                                reply = "対戦中の部屋には入れません"
                                temp_message = True
                            else:
                                room.members.append(message.author)
                                room.last_notice_timestamp = now()
                                reply = f"[{room.number}] {room.name} ＠{room.capacity - len(room.members)}\n" + ", ".join(f"`{get_name(member)}`" for member in room.members) + f"\n[IN] `{get_name(message.author)}`"
                                room_to_clean = room
                        else:
                            reply = "もう入ってるよ"
                            temp_message = True
                    elif len(rooms) == 0:
                        reply = "現在、部屋はありません"
                        temp_message = True
                    else:
                        reply = "複数の部屋があるときは部屋番号を指定してね"
                        temp_message = True
                else:
                    room_number = to_int(room_number)
                    if room_number is None:
                        reply = "部屋番号をアラビア数字で指定してね"
                        temp_message = True
                    else:
                        room = None
                        for room_ in rooms:
                            if room_number == room_.number:
                                room = room_
                                break
                        if room is None:
                            reply = "その番号の部屋はありません"
                            temp_message = True
                        else:
                            if not message.author in room.members:
                                if room.fighting:
                                    reply - "対戦中の部屋には入れません"
                                    temp_message = True
                                else:
                                    room.members.append(message.author)
                                    room.last_notice_timestamp = now()
                                    reply = f"[{room.number}] {room.name} ＠{room.capacity - len(room.members)}\n" + ", ".join(f"`{get_name(member)}`" for member in room.members) + f"\n[IN] `{get_name(message.author)}`"
                                    room_to_clean = room
                            else:
                                reply = "もう入ってるよ"
                                temp_message = True
                if room is not None:
                    if len(room.members) == room.capacity and not room.fighting:
                        process_umari(room)
                        reply = "".join([f"[IN] `{get_name(message.author)}`\n",
                            f"埋まり: [{room.number}] {room.name} ＠{room.capacity - len(room.members)}\n",
                            " ".join(f"{member.mention}" for member in room.members) + "\n",
                            f"チーム1:【{sum(player.latest_rate(room.ladder) for player in room.team1)}】\n",
                            " ".join(f"{player.name}({player.latest_rate(room.ladder)})" for player in room.team1) + "\n",
                            f"チーム2:【{sum(player.latest_rate(room.ladder) for player in room.team2)}】\n",
                            " ".join(f"{player.name}({player.latest_rate(room.ladder)})" for player in room.team2) + "\n",
                            ])
                        # delete_room(room) # --won, --lost コマンド実行時にgames.append(Game(...))をしてから消す。
                        # --won, --lost 実行までは対戦中の部屋として表示されて、爆破でキャンセル
                        room_to_clean = room

        for command in ["--nuke", "--out", "--leave", "--dismiss"]:
            if message.content.startswith(command):
                room_number = message.content.split(command)[1]
                if room_number == "":
                    entered_rooms = []
                    for room in rooms:
                        for member in room.members:
                            if message.author.id == member.id:
                                entered_rooms.append(room)
                                break
                    if len(entered_rooms) == 1:
                        room = entered_rooms[0]
                        if room.owner == message.author:
                            reply = "ホストが抜けるときは--bakuhaを使ってね"
                            temp_message = True
                        else:
                            room.members.pop(room.members.index(message.author))
                            room.last_notice_timestamp = now()
                            reply = f"[{room.number}] {room.name} ＠{room.capacity - len(room.members)}\n" + ", ".join(f"`{get_name(member)}`" for member in room.members) + f"\n[OUT] `{get_name(message.author)}`"
                            room_to_clean = room
                    elif len(entered_rooms) == 0:
                        reply = "どこにも入ってないよ"
                        temp_message = True
                    else:
                        reply = "複数の部屋に入っているときは部屋番号を指定してね"
                        temp_message = True
                else:
                    room_number = to_int(room_number)
                    if room_number is None:
                        reply = "部屋番号をアラビア数字で指定してね"
                        temp_message = True
                    else:
                        room = None
                        for room_ in rooms:
                            if room_number == room_.number:
                                for member in room_.members:
                                    if message.author.id == member.id:
                                        room = room_
                                        break
                                break
                        if room is None:
                            reply = "その番号の部屋がないか、入っていないので抜けれません"
                            temp_message = True
                        else:
                            if room.owner == message.author:
                                reply = "ホストが抜けるときは--bakuhaを使ってね"
                                temp_message = True
                            else:
                                room.members.pop(room.members.index(message.author))
                                room.last_notice_timestamp = now()
                                reply = f"[{room.number}] {room.name} ＠{room.capacity - len(room.members)}\n" + ", ".join(f"`{get_name(member)}`" for member in room.members) + f"\n[OUT] `{get_name(message.author)}`"
                                room_to_clean = room

        if message.content.startswith("--rooms"):
            lines = []
            for room in rooms:
                lines.append(f"[{room.number}] {room.name} ＠{room.capacity - len(room.members)}\n" + ", ".join(f"`{get_name(member)}`" for member in room.members) + "\n")
            if lines:
                reply = "\n".join(lines)
            else:
                reply = "現在、部屋はありません"
            temp_message = True

        if message.content.startswith("--force-bakuha-tekumakumayakonn-tekumakumayakonn"):
            room_number = to_int(message.content.split("--force-bakuha-tekumakumayakonn-tekumakumayakonn")[1])
            if room_number is None:
                reply = "部屋番号をアラビア数字で指定してね"
                temp_message = True
            else:
                room = None
                for room_ in rooms:
                    if room_number == room_.number:
                        room = room_
                        break
                if room is None:
                    reply = "その番号の部屋はありません"
                    temp_message = True
                else:
                    delete_room(room)
                    reply = f"爆破: [{room.number}] {room.name} ＠{room.capacity - len(room.members)}\n" + ", ".join(f"`{get_name(member)}`" for member in room.members)
                    room_to_clean = room

        if message.content.startswith("--help"):
            reply = usage.jp
            temp_message = True

        if message.content.startswith("--help-en"):
            reply = usage.en
            temp_message = True

        if secret_commands and process_secret_commands:
            for command in secret_commands:
                if message.content.startswith(command):
                    reply = process_secret_commands(message)
                    temp_message = True
                    break

        global last_process_message_timestamp
        last_process_message_timestamp = now()

        return reply, room_to_clean, temp_message

async def room_cleaner(room, received_message, sent_message):
    room.garbage_queue.append(sent_message.id)
    while True:
        if 1 < len(room.garbage_queue):
            message_id = room.garbage_queue.pop(0)
            try:
                msg = await received_message.channel.fetch_message(message_id)
                await msg.delete()
            except discord.NotFound:
                pass
        else:
            break

async def notice_rooms():
    while True:
        if on_ready_complete.is_set():
            break
        await asyncio.sleep(1)
    channel = bot.get_channel(target_channel_id)
    if not channel:
        return
    while True:
        await asyncio.sleep(3)
        for room in rooms:
            if timedelta(minutes=8) <= now() - room.last_notice_timestamp:
                line = f"[{room.number}] {room.name} ＠{room.capacity - len(room.members)}\n" + ", ".join(f"`{get_name(member)}`" for member in room.members)
                sent_message = await channel.send(line, allowed_mentions=allowed_mentions)
                room.garbage_queue.append(sent_message.id)
                room.last_notice_timestamp = now()
                while True:
                    if 1 < len(room.garbage_queue):
                        message_id = room.garbage_queue.pop(0)
                        try:
                            msg = await channel.fetch_message(message_id)
                            await msg.delete()
                        except discord.NotFound:
                            pass
                    else:
                        break
                await save_bot_state()

async def temp_message_cleaner():
    global last_process_message_timestamp
    while True:
        if on_ready_complete.is_set():
            break
        await asyncio.sleep(1)
    while True:
        await asyncio.sleep(3)
        if timedelta(minutes=2) <= now() - last_process_message_timestamp:
            for channel_id, message_id in temp_message_ids:
                channel = bot.get_channel(channel_id)
                if channel:
                    try:
                        msg = await channel.fetch_message(message_id)
                        await msg.delete()
                    except discord.NotFound:
                        pass
            temp_message_ids.clear()

async def daily_backup():
    while True:
        if on_ready_complete.is_set():
            break
        await asyncio.sleep(1)
    while True:
        await save_rating_system(backup=True)
        tommorow_6 = (now() + timedelta(days=1)).replace(hour=6, minute=0, second=0, microsecond=0)
        await asyncio.sleep( (tommorow_6 - now()).total_seconds() )

@bot.event
async def on_ready():
    print("前回の状態を読み取り中。")
    await load(bot)
    print("読み取り完了。botを実行します。")
    print(f"{bot.user}でDicordにログインしました。")
    print(usage.at_launch)
    on_ready_complete.set()

@bot.event
async def on_message(message):
    if not on_ready_complete.is_set():
        await on_ready_complete.wait()
    # bot自身の発言を拾わない
    if message.author.bot:
        return
    if message.channel.id == target_channel_id:
        for command in bot_commands:
            if message.content.startswith(command):
                jst = now() + timedelta(hours=9)
                print(f"INPUT:\n{message.content}\n{jst}\n")
                reply, room_to_clean, temp_message = await process_message(message)
                sent_message = await message.channel.send(reply, allowed_mentions=allowed_mentions)
                if room_to_clean:
                    await room_cleaner(room_to_clean, message, sent_message)
                if temp_message:
                    temp_message_ids.append( (message.channel.id, sent_message.id) )
                jst = now() + timedelta(hours=9)
                print(f"OUTPUT:\n{reply}\n{jst}\n")
                await save_bot_state()
                break
    await bot.process_commands(message)

def already_running():
    # うっかりbotを重複起動しちゃうのを防止
    current_pid = os.getpid()
    for proc in psutil.process_iter(attrs=["pid", "cmdline"]):
        try:
            if proc.info["pid"] == current_pid:
                continue
            cmdline = proc.info["cmdline"]
            str_ = "".join(cmdline)
            if str_ and "bot4wz.py" in str_ and "python" in str_:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    tasks = []
    tasks.append(loop.create_task(temp_message_cleaner()))
    tasks.append(loop.create_task(notice_rooms()))
    tasks.append(loop.create_task(daily_backup()))
    asyncio.gather(*tasks, return_exceptions=True) # ssl.SSLErrorの出所を探るため、例外がタスクから来た場合に Ctrl+C を押すまで保留する
    try:
        loop.run_until_complete(bot.start(TOKEN))
    except KeyboardInterrupt:
        print("終了命令Ctrl+Cを受け付けました。非同期タスクの終了を待っています…")
    except discord.errors.LoginFailure:
        print("botがDiscordにログインできませんでした。有効なトークンをtoken.txtに保存してください。")
        print("トークンが有効ならば、Discordに問題が起きているかもしれません。")
    finally:
        for task in tasks:
            task.cancel()
            try:
                loop.run_until_complete(task)
            except asyncio.CancelledError:
                pass
        if not bot.is_closed():
            loop.run_until_complete(bot.close())
        loop.close()
        print("bye")
        sys.exit(0)

if __name__ == "__main__":
    if already_running():
        print("すでに実行中のbot4wz.pyがあるのでbotを開始せずに終了します")
        sys.exit(0)
    main()
