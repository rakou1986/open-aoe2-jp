#coding: utf-8
#!/path/to/Python_3.6.3

_debug = False

"""
[requirements]

python -V
Python 3.6.3 :: Anaconda, Inc.

pip show discord
Version: 1.7.3

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

import aiohttp
import ast
import asyncio
from datetime import datetime, timedelta
import json
import os
import pickle
import psutil
import random
import re
import socket
import sys
import time
import urllib
import win32gui
import win32con

import discord
from discord.ext import commands
import rapidfuzz

TOKEN = None

status_channel_id = 0

if _debug:
    token_file = "canary_token.txt"
    from bot_settings import canary_bot_status_channel_id as status_channel_id
    from bot_settings import canary_bot_target_channel_id as target_channel_id
    from bot_settings import canary_bot_server_id as guild_id
else:
    token_file = "token.txt"
    from bot_settings import available_bot_status_channel_id as status_channel_id
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

if os.path.exists(token_file):
    with open(token_file) as f:
        TOKEN = f.read().strip()
        print(f"{token_file}を読み取りました。")

if TOKEN is None:
    print(usage.no_token)
    input("Enterを押して終了: ")
    sys.exit(0)

lock = asyncio.Lock()
on_ready_complete = asyncio.Event()
quit = asyncio.Event()

intents = discord.Intents.default()
intents.messages = True
allowed_mentions = discord.AllowedMentions(users=True)
bot = commands.Bot(command_prefix="!", intents=intents)

bot_commands = [
    "--yyk", "--call", "--create", "--reserve", "--heybros", "--lzyyk",
    "--bakuha", "--del", "--cancel", "--destroy", "--hakai", "--explosion",
    "--no", "--in", "--join",
    "--nuke", "--out", "--leave", "--dismiss",
    "--rooms",
    "--force-bakuha-tekumakumayakonn-tekumakumayakonn",
    "--help", "--help-en", "--help-warzone-url", "--help-lazuaoe-url",
    ] + secret_commands
room_number_pool = list(range(1, 100))
room_number_pool_file = ".bot4wz.room_number_pool.pickle"
rooms = []
rooms_file = ".bot4wz.rooms.pickle"
temp_message_ids = []
temp_message_ids_file = ".bot4wz.temp_message_ids.pickle"
last_process_message_timestamp = datetime.utcnow()
last_running = None
warzone_players = []
warzone_players_file = ".bot4wz.warzone_players.pickle"
warzone_players_url = "http://warzone.php.xdomain.jp/?action=Rate"
lazuaoe_players = []
lazuaoe_players_file = ".bot4wz.lazuaoe_players.pickle"
lazuaoe_players_url = "http://lazuaoe.php.xdomain.jp/rate/?act=ply"

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
        self.rating_system = room.rating_system

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
        room = Room(author=owner, name=self.name, capacity=self.capacity, rating_system=self.rating_system)
        room.number = self.number
        room.members = members
        room.garbage_queue = self.garbage_queue
        room.last_notice_timestamp = self.last_notice_timestamp
        return room


class Room(object):

    def __init__(self, author , name, capacity, rating_system):
        try:
            self.number = room_number_pool.pop(0)
        except IndexError:
            raise RoomNumberExhaust
        self.name = name
        self.owner = author
        self.members = [author]
        self.capacity = capacity
        self.garbage_queue = []
        self.last_notice_timestamp = datetime.utcnow()
        self.rating_system = rating_system


async def save():
    rooms_picklable = [RoomPicklable(room) for room in rooms]
    with open(rooms_file, "wb") as f:
        pickle.dump(rooms_picklable, f)
    with open(room_number_pool_file, "wb") as f:
        pickle.dump(room_number_pool, f)
    with open(temp_message_ids_file, "wb") as f:
        pickle.dump(temp_message_ids, f)
    with open(warzone_players_file, "wb") as f:
        pickle.dump(warzone_players, f)
    with open(lazuaoe_players_file, "wb") as f:
        pickle.dump(lazuaoe_players, f)

async def load(bot):
    global rooms
    if os.path.exists(rooms_file):
        with open(rooms_file, "rb") as f:
            try:
                rooms_picklable = pickle.load(f)
                rooms = await asyncio.gather(*(picklable.to_room(bot) for picklable in rooms_picklable))
            except Exception as e:
                pass
    global room_number_pool
    if os.path.exists(room_number_pool_file):
        with open(room_number_pool_file, "rb") as f:
            try:
                room_number_pool = pickle.load(f)
            except Exception as e:
                pass
    global temp_message_ids
    if os.path.exists(temp_message_ids_file):
        with open(temp_message_ids_file, "rb") as f:
            try:
                temp_message_ids = pickle.load(f)
            except Exception as e:
                pass
    global warzone_players
    if os.path.exists(warzone_players_file):
        with open(warzone_players_file, "rb") as f:
            try:
                warzone_players = pickle.load(f)
            except Exception as e:
                pass
    global lazuaoe_players
    if os.path.exists(lazuaoe_players_file):
        with open(lazuaoe_players_file, "rb") as f:
            try:
                lazuaoe_players = pickle.load(f)
            except Exception as e:
                pass

def to_int(string):
    try:
        return int(string)
    except ValueError:
        return None

def get_name(user):
    # サーバーニックネーム、表示名、ユーザー名（グローバル）の順に名前を探す
    for name in [user.nick, user.display_name, user.name]:
        if name is not None:
            return name
    return "名前を取得できませんでした"

def delete_room(room):
    rooms.pop(rooms.index(room))
    room_number_pool.append(room.number)
    room_number_pool.sort()

def create_customized_url(room):
    members = []
    # room.rating_system in ["warzone", "lazuaoe"] = True が保障されている
    if room.rating_system == "warzone":
        url_base = "http://warzone.php.xdomain.jp/?action=NewGame&rakou_bot_param_members="
        players = warzone_players
    if room.rating_system == "lazuaoe":
        url_base = "http://lazuaoe.php.xdomain.jp/rate/?act=mkt&rakou_bot_param_members="
        players = lazuaoe_players
    for user in room.members:
        name = get_name(user)
        match, similarity_score, idx = rapidfuzz.process.extractOne(name, players)
        if 55 < similarity_score:
            name = match
        else:
            name = "**" + name
        members.append(name)
    url = "".join([url_base, urllib.parse.quote(json.dumps(members, ensure_ascii=False))])
    discord_compatible_url = f"<{url}>"
    return discord_compatible_url

async def process_message(message):
    async with lock:
        reply = "初期値。問題が起きているのでrakouに連絡"
        room_to_clean = None
        temp_message = False

        for command in ["--yyk", "--call", "--create", "--reserve", "--heybros", "--lzyyk"]:
            if message.content.startswith(command):
                capacity = 8
                name = message.content.split(command)[1]
                if name:
                    if name[0] in ["1", "2", "3", "4", "5", "6", "１", "２", "３", "４", "５", "６"]:
                        capacity = to_int(name[0]) + 1
                        name = name.replace(name[0], "")
                if not name:
                    if command == "--lzyyk":
                        name = "LN"
                    else:
                        name = "無制限"
                else:
                    name = name.strip()
                rating_system = "lazuaoe" if command == "--lzyyk" else "warzone"
                try:
                    room = Room(author=message.author, name=name, capacity=capacity, rating_system=rating_system)
                    rooms.append(room)
                    reply = f"[{room.number}] {room.name} ＠{room.capacity - len(room.members)}\n" + ", ".join(f"`{get_name(member)}`" for member in room.members)
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
                            room.members.append(message.author)
                            room.last_notice_timestamp = datetime.utcnow()
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
                                room.members.append(message.author)
                                room.last_notice_timestamp = datetime.utcnow()
                                reply = f"[{room.number}] {room.name} ＠{room.capacity - len(room.members)}\n" + ", ".join(f"`{get_name(member)}`" for member in room.members) + f"\n[IN] `{get_name(message.author)}`"
                                room_to_clean = room
                            else:
                                reply = "もう入ってるよ"
                                temp_message = True
                if room is not None:
                    if len(room.members) == room.capacity:
                        reply = f"[IN] `{get_name(message.author)}`\n" + f"埋まり: [{room.number}] {room.name} ＠{room.capacity - len(room.members)}\n" + " ".join(f"{member.mention}" for member in room.members) + ("\n" + create_customized_url(room) if room.capacity in [6, 8] else "")
                        delete_room(room)
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
                            room.last_notice_timestamp = datetime.utcnow()
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
                                room.last_notice_timestamp = datetime.utcnow()
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

        if message.content.startswith("--help-warzone-url"):
            reply = usage.warzone_url
            temp_message = True

        if message.content.startswith("--help-lazuaoe-url"):
            reply = usage.lazuaoe_url
            temp_message = True

        if secret_commands and process_secret_commands:
            for command in secret_commands:
                if message.content.startswith(command):
                    reply = process_secret_commands(message)
                    temp_message = True
                    break

        global last_process_message_timestamp
        last_process_message_timestamp = datetime.utcnow()

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
    if quit.is_set():
        return
    channel = bot.get_channel(target_channel_id)
    if not channel:
        return
    while True:
        await asyncio.sleep(3)
        for room in rooms:
            if timedelta(minutes=8) <= datetime.utcnow() - room.last_notice_timestamp:
                line = f"[{room.number}] {room.name} ＠{room.capacity - len(room.members)}\n" + ", ".join(f"`{get_name(member)}`" for member in room.members)
                sent_message = await channel.send(line, allowed_mentions=allowed_mentions)
                room.garbage_queue.append(sent_message.id)
                room.last_notice_timestamp = datetime.utcnow()
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
                await save()

async def temp_message_cleaner():
    global last_process_message_timestamp
    while True:
        if on_ready_complete.is_set():
            break
        await asyncio.sleep(1)
    if quit.is_set():
        return
    while True:
        await asyncio.sleep(3)
        if timedelta(minutes=2) <= datetime.utcnow() - last_process_message_timestamp:
            for channel_id, message_id in temp_message_ids:
                channel = bot.get_channel(channel_id)
                if channel:
                    try:
                        msg = await channel.fetch_message(message_id)
                        await msg.delete()
                    except discord.NotFound:
                        pass
            temp_message_ids.clear()

async def report_survive():
    global last_running
    while True:
        if on_ready_complete.is_set():
            break
        await asyncio.sleep(1)
    if quit.is_set():
        return
    channel = bot.get_channel(status_channel_id)
    hostname = socket.gethostname()
    if channel:
        await channel.send(f"{bot.user.id} launch on {hostname}")
    while True:
        if channel:
            sent_message = await channel.send(f"{bot.user.id} running on {hostname}")
            if last_running is not None:
                await last_running.delete()
            last_running = sent_message
        await asyncio.sleep(300)

async def close_bot():
    while True:
        if quit.is_set():
            break
        if on_ready_complete.is_set():
            return
        await asyncio.sleep(1)
    await asyncio.sleep(1)
    await bot.wait_until_ready()
    await bot.close()

async def list_warzone_players():
    global warzone_players
    while True:
        if on_ready_complete.is_set():
            break
        await asyncio.sleep(1)
    if quit.is_set():
        return
    retry = False
    while True:
        if retry:
            await asyncio.sleep(60)
        timeout = aiohttp.ClientTimeout(total=15)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(warzone_players_url) as response:
                    html = await response.text()
                    html = html.replace("\r", "")
            match = re.search(r"var\s+UserData\s*=\s*(\[\s*(?:\[.*?\],?\s*)+\]);", html, re.DOTALL)
            if match:
                array_text = match.group(1)
                array_text = array_text.replace("null", "None").replace("true", "True").replace("false", "False")
                user_data = ast.literal_eval(array_text)
                warzone_players = [row[1] for row in user_data]
                retry = False
                await asyncio.sleep(3600)
            else:
                # htmlに問題がありvar UserDataが見つからない
                retry = True
                continue
        except asyncio.TimeoutError:
            retry = True
            continue
        except asyncio.CancelledError:
            break
        except Exception as e:
            # 通信エラーなどで正しいHTMLが得られずにvar UserDataを扱っているときに問題が起きた
            retry = True
            continue

async def list_lazuaoe_players():
    global lazuaoe_players
    while True:
        if on_ready_complete.is_set():
            break
        await asyncio.sleep(1)
    if quit.is_set():
        return
    retry = False
    while True:
        if retry:
            await asyncio.sleep(300)
        timeout = aiohttp.ClientTimeout(total=15)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(lazuaoe_players_url) as response:
                    html = await response.text()
            lines = html.split("\n")
            idx = lines.index("var PlayerList = [")
            array_text = "".join(lines[idx:idx+3]).replace("var PlayerList = ", "")[:-1]
            player_list = ast.literal_eval(array_text)
            lazuaoe_players = [player[0] for player in player_list]
            retry = False
            await asyncio.sleep(43200) # 12時間
        except asyncio.TimeoutError:
            retry = True
            continue
        except asyncio.CancelledError:
            break
        except Exception as e:
            # 通信エラーなどで正しいHTMLが得られずにvar PlayerListを扱っているときに問題が起きた
            retry = True
            continue

@bot.event
async def on_ready():
    # already_running()がPC上での重複起動を防ぐのに対して、botの生存実績を見て、他の人がbotを実行中に重複実行を防ぐ
    channel = bot.get_channel(status_channel_id)
    if channel:
        messages = await channel.history(limit=1).flatten()
        if messages:
            message = messages[0]
            if message.content.startswith(f"{bot.user.id} running"):
                delta = datetime.utcnow() - message.created_at.replace(tzinfo=None)
                if delta.total_seconds() < 900:
                    print("botが実行中であることをbot自身がステータスチャンネル # bot_status に報告してから間もないため他のPCでbotが実行されている可能性があります。多重実行を防ぐためbotを実行せずに終了します。")
                    await asyncio.sleep(10)
                    quit.set()
                    return

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
                jst = datetime.utcnow() + timedelta(hours=9)
                print(f"INPUT:\n{message.content}\n{jst}\n")
                reply, room_to_clean, temp_message = await process_message(message)
                sent_message = await message.channel.send(reply, allowed_mentions=allowed_mentions)
                if room_to_clean:
                    await room_cleaner(room_to_clean, message, sent_message)
                if temp_message:
                    temp_message_ids.append( (message.channel.id, sent_message.id) )
                jst = datetime.utcnow() + timedelta(hours=9)
                print(f"OUTPUT:\n{reply}\n{jst}\n")
                await save()
                break
    await bot.process_commands(message)

def disable_close_button():
    # うっかり閉じるボタンで終了しないように、閉じるボタンを無効化する
    hwnd = win32gui.GetForegroundWindow()
    if hwnd:
        menu = win32gui.GetSystemMenu(hwnd, False)
        try:
            win32gui.RemoveMenu(menu, win32con.SC_CLOSE, win32con.MF_BYCOMMAND)
        except Exception:
            # シェルで2回目に実行するとボタンがないので例外が出る
            pass
        win32gui.DrawMenuBar(hwnd)

def already_running():
    # うっかりbotを重複起動しちゃうのを防止
    current = psutil.Process()
    current_pid = current.pid
    parent_pid = current.ppid()
    for proc in psutil.process_iter(attrs=["pid", "cmdline"]):
        try:
            cmdline = " ".join(proc.info["cmdline"])
            if "bot4wz.py" in cmdline and proc.info["pid"] != current_pid and not "cmd" in proc.info["cmdline"]:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        except TypeError:
            pass
    for proc in psutil.process_iter(attrs=["pid", "exe"]):
        try:
            if proc.pid in (current_pid, parent_pid):
                continue
            proc_exe = proc.info["exe"]
            if not proc_exe:
                continue
            if "bot4wz.exe" == os.path.basename(proc_exe):
                return True
            if "bot4wz.exe" == proc.name().lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

def main():
    disable_close_button()
    loop = asyncio.get_event_loop()
    tasks = []
    tasks.append(loop.create_task(temp_message_cleaner()))
    tasks.append(loop.create_task(report_survive()))
    tasks.append(loop.create_task(close_bot()))
    tasks.append(loop.create_task(notice_rooms()))
    tasks.append(loop.create_task(list_warzone_players()))
    tasks.append(loop.create_task(list_lazuaoe_players()))
    asyncio.gather(*tasks, return_exceptions=True) # ssl.SSLErrorの出所を探るため、例外がタスクから来た場合に Ctrl+C を押すまで保留する
    try:
        loop.run_until_complete(bot.start(TOKEN))
    except KeyboardInterrupt:
        print("終了命令Ctrl+Cを受け付けました。非同期タスクの終了を待っています…")
    except discord.errors.LoginFailure:
        print("botがDiscordにログインできませんでした。有効なトークンをtoken.txtに保存してください。")
        print("トークンが有効ならば、Discordに問題が起きているかもしれません。")
        time.sleep(10)
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
        print("10秒後に終了します。")
        time.sleep(10)

if __name__ == "__main__":
    if already_running():
        print("すでに実行中のbot4wz.pyまたはbot4wz.exeがあるのでbotを開始せず10秒後に終了します")
        time.sleep(10)
        sys.exit(0)
    main()
