#coding: utf-8
#!/path/to/Python_3.12.10

_debug = True

"""
[requirements]
python -V
Python 3.12.10

pip show discord
#Version: 1.7.3
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
from datetime import datetime, timedelta, timezone
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

import discord
from discord.ext import commands
import rapidfuzz

TOKEN = None


if _debug:
    token_file = "canary_token.txt"
    from bot_settings import canary_bot_target_channel_id as target_channel_id
    from bot_settings import canary_bot_server_id as guild_id
else:
    token_file = "token.txt"
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

def now():
    return datetime.now(timezone.utc)

lock = asyncio.Lock()
on_ready_complete = asyncio.Event()
quit = asyncio.Event()

intents = discord.Intents.default()
intents.messages = True
allowed_mentions = discord.AllowedMentions(users=True)
bot = commands.Bot(command_prefix="!", intents=intents)

bot_commands = [
    "--yyk", "--call", "--create", "--reserve", "--heybros",
    "--bakuha", "--del", "--cancel", "--destroy", "--hakai", "--explosion",
    "--no", "--in", "--join",
    "--nuke", "--out", "--leave", "--dismiss",
    "--rooms",
    "--force-bakuha-tekumakumayakonn-tekumakumayakonn",
    "--help", "--help-en",
    ] + secret_commands
room_number_pool = list(range(1, 100))
room_number_pool_file = ".bot4wz.room_number_pool.pickle"
rooms = []
rooms_file = ".bot4wz.rooms.pickle"
temp_message_ids = []
temp_message_ids_file = ".bot4wz.temp_message_ids.pickle"
last_process_message_timestamp = now()


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
        room = Room(author=owner, name=self.name, capacity=self.capacity)
        room.number = self.number
        room.members = members
        room.garbage_queue = self.garbage_queue
        room.last_notice_timestamp = self.last_notice_timestamp
        return room


class Room(object):

    def __init__(self, author , name, capacity):
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


async def save():
    rooms_picklable = [RoomPicklable(room) for room in rooms]
    with open(rooms_file, "wb") as f:
        pickle.dump(rooms_picklable, f)
    with open(room_number_pool_file, "wb") as f:
        pickle.dump(room_number_pool, f)
    with open(temp_message_ids_file, "wb") as f:
        pickle.dump(temp_message_ids, f)

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

async def process_message(message):
    async with lock:
        reply = "初期値。問題が起きているのでrakouに連絡"
        room_to_clean = None
        temp_message = False

        for command in ["--yyk", "--call", "--create", "--reserve", "--heybros"]:
            if message.content.startswith(command):
                capacity = 8
                name = message.content.split(command)[1]
                if name:
                    if name[0] in ["1", "2", "3", "4", "5", "6", "１", "２", "３", "４", "５", "６"]:
                        capacity = to_int(name[0]) + 1
                        name = name.replace(name[0], "")
                name = "無制限" if not name else name.strip()
                try:
                    room = Room(author=message.author, name=name, capacity=capacity)
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
                                room.members.append(message.author)
                                room.last_notice_timestamp = now()
                                reply = f"[{room.number}] {room.name} ＠{room.capacity - len(room.members)}\n" + ", ".join(f"`{get_name(member)}`" for member in room.members) + f"\n[IN] `{get_name(message.author)}`"
                                room_to_clean = room
                            else:
                                reply = "もう入ってるよ"
                                temp_message = True
                if room is not None:
                    if len(room.members) == room.capacity:
                        reply = f"[IN] `{get_name(message.author)}`\n" + f"埋まり: [{room.number}] {room.name} ＠{room.capacity - len(room.members)}\n" + " ".join(f"{member.mention}" for member in room.members)
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
    if quit.is_set():
        return
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
                await save()
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
    loop = asyncio.get_event_loop()
    tasks = []
    tasks.append(loop.create_task(temp_message_cleaner()))
    tasks.append(loop.create_task(close_bot()))
    tasks.append(loop.create_task(notice_rooms()))
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
