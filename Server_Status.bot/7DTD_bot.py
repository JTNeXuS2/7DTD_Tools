#Python 3.8 or higher is required.
#py -3 -m pip install -U disnake
#pip install aiofiles
#pip install psutil

import disnake
from disnake.ext import commands, tasks
from disnake import Intents
import json
import datetime
import requests
import configparser
import re
import unicodedata
from requests.auth import HTTPBasicAuth
from concurrent.futures import ThreadPoolExecutor

import urllib.parse
import http.client
import aiohttp
import asyncio
import time
import os
import glob
import subprocess
import random
import aiofiles
import psutil

import telnetlib
import chat_handler  # Импорт функций из chat_handler.py

#Buffer Limits
from collections import deque
MAX_MESSAGES = 14
TIME_WINDOW = 60
BUFFER_LIMIT = MAX_MESSAGES // 2  # Половина лимита
message_buffer = deque()
send_interval = 0
shard_count = 1

#cant used
prefix = '/'

#Nothing change more

def read_cfg():
    config = configparser.ConfigParser(interpolation=None)
    try:
        with open('config.ini', 'r', encoding='utf-8') as file:
            config.read_file(file)
    except FileNotFoundError:
        print("Error: Config.ini not found.")
        return None
    return config
async def write_cfg(section, key, value):
    config = read_cfg()
    if f'{section}' not in config:
        config[f'{section}'] = {}
    config[f'{section}'][f'{key}'] = str(f'{value}')

    with open('config.ini', 'w', encoding='utf-8') as configfile:
        config.write(configfile)
def update_settings():
    global token, channel_id, crosschat_id, message_id, update_time, bot_name, bot_ava, address, user_role_ids, command_prefex, username, password, log_dir, chatlog_dir, webhook_url, add_string, players_message_id

    config = read_cfg()
    if config:
        try:
            token = config['botconfig'].get('token', None)
            channel_id = config['botconfig'].get('channel_id', None)
            crosschat_id = config['botconfig'].get('crosschat_id', None)
            message_id = config['botconfig'].get('message_id', None)
            players_message_id = config['botconfig'].get('players_message_id', None)
            bot_name = config['botconfig'].get('bot_name', None)
            bot_ava = config['botconfig'].get('bot_ava', None)
            username = config['botconfig'].get('username', None)
            password = config['botconfig'].get('password', None)
            update_time = config['botconfig'].get('update_time', None)
            command_prefex = config['botconfig'].get('command_prefex', None) and config['botconfig'].get('command_prefex').lower()
            address = (config['botconfig'].get('ip', None), int(config['botconfig'].get('query_port', 0)), int(config['botconfig'].get('restapi_port', 0)), config['botconfig'].get('telnet_port', 0))
            log_dir = config['botconfig'].get('log_dir', None)
            chatlog_dir = config['botconfig'].get('chatlog_dir', None)
            webhook_url = config['botconfig'].get('webhook_url', None)
            add_string = config['botconfig'].get('add_string', "")

            user_role_ids = config['botconfig'].get('user_role_ids', None)
            if user_role_ids is not None:
                user_role_ids = [int(role_id.strip()) for role_id in user_role_ids.split(',')]

        except ValueError as e:
            print(f"Error: wrong value in config file {e}")
        except Exception as e:
            print(f"Error: {e}")

token = None
channel_id = None
crosschat_id = None
message_id = None
players_message_id = None
bot_name = None
bot_ava = None
username = None
password = None
update_time = 10
address = None
command_prefex = None
webhook_url = None

log_dir = None
current_file = None
file_position = 0

conn = None
access_token = None
refresh_token = None
add_string = ""
user_role_ids = []

chatlog_dir = None
current_file2 = None
file2_position = 0
webhook_url2 = "https://discord.com/api/webhooks/1350263539427835914/DXbJhJsJEHPrlKkpBrtalZKMNXzwlbjYr2mNFg6HDBFK62mMbUfLAx5HtNbAmUZoMKjM"
find_error = "NullReferenceException: Object reference not set to an instance of an object"

count = 0
max_errors = 100 
useonce = None
day7 = None
update_settings()


#bot idents
intents = disnake.Intents.default()
intents.messages = True
intents = disnake.Intents().all()
client = commands.Bot(command_prefix=prefix, intents=intents, case_insensitive=True)
#bot = commands.Bot(command_prefix=prefix, intents=intents, case_insensitive=True)
bot = commands.AutoShardedBot(command_prefix=prefix, intents=intents, shard_count=shard_count ,case_insensitive=True)

def find_latest_file(logs_dir):
    latest_file = None
    try:
        list_of_files = glob.glob(f'{logs_dir}*')
        latest_file = max(list_of_files, key=os.path.getctime)
    except Exception as e:
        return None
        print(f"Error find_latest_file: {e}")
    return latest_file

async def watch_log_file(chatlog_dir):
    global current_file, file_position
    old_line = ""
    while True:
        new_file = find_latest_file(chatlog_dir)
        if new_file != current_file:
            current_file = new_file
            print(f"watch log start at {current_file}")
            file_position = 0
        async with aiofiles.open(current_file, 'r', encoding='utf-8') as file:
            await file.seek(file_position)
            lines = await file.readlines()
            file_position = await file.tell()
        for line in lines:
            if line != old_line:
                await process_line(line)
                old_line = line
        await asyncio.sleep(1)

async def watch_log_file2(log_dir):
    global current_file2, file2_position, count
    old_line = ""
    start_time = time.time()
    count = 0

    while True:
        new_file = find_latest_file(log_dir)
        if new_file != current_file2:
            current_file2 = new_file
            print(f"watch log start at {current_file2}")
            file2_position = 0

        async with aiofiles.open(current_file2, 'r', encoding='utf-8') as file:
            await file.seek(file2_position)
            lines = await file.readlines()
            file2_position = await file.tell()

        for line in lines:
            if line != old_line:
                if find_error in line:
                    count += 1
                    #print(f"{count}")
                old_line = line

        if time.time() - start_time >= 3:
            if count > max_errors:
                print("Auto FIX_IT")
                await send_api_command(f"ty-rax")

                data = {"content": f"**AutoFIX**\n trying auto fix server:\n errors >{count}"}
                response = requests.post(webhook_url2, json=data)
                if response.status_code != 204:
                    print(f"Error sending message to Discord: {response.status_code} - {response.text}")
                await asyncio.sleep(5)

            start_time = time.time()
            count = 0
        await asyncio.sleep(1)

async def process_line(line):
    # Parse log string
    chat_pattern = r"(\d{2}[./]\d{2}[./]\d{4}|[^\s]+) (\d{2}:\d{2}:\d{2}) (\w+) (.+?): (.+)"
    # Parse Chat
    chat_match = re.match(chat_pattern, line)
    if chat_match:

        timestamp = chat_match.group(2)
        channel = chat_match.group(3)
        nick = chat_match.group(4)
        message = chat_match.group(5)

        # send to webhook
        send_to_discord(f"[{channel}] **{nick}**", message)

    # END PARSE
    return None

def send_to_discord(nick, message):
    message_buffer.append((nick, message))

async def send_from_buffer_to_discord(nick, message):
    def escape_markdown(text):
        markdown_chars = ['\\', '*', '_', '~', '`', '>', '|']
        for char in markdown_chars:
            text = text.replace(char, '\\' + char)
        return text
    def truncate_message(text, max_length=2000):
        return text if len(text) <= max_length else text[:max_length-3] + '...'
    nick = escape_markdown(nick)
    message = escape_markdown(message)
    # Recovery BOLD **
    nick = nick.replace(r'\*\*', '**')
    message = message.replace(r'\*\*', '**')
    message = message.replace(r'\`\`\`', '```')
    nick = nick.replace(r'\>', '>')
    message = message.replace(r'\>', '>')
    message = truncate_message(message)
    message = f"{nick}: {message}"
    data = {"content": message}
    response = requests.post(webhook_url, json=data)
    if response.status_code != 204:
        print(f"Error sending message to Discord: {response.status_code} - {response.text}")

async def auth(address):
    global conn, access_token, refresh_token
    try:
        conn = http.client.HTTPConnection(address[0], address[2])
    except Exception as e:
        print(f"Ошибка подключения: {e}")
    payload = f'grant_type=password&username={username}&password={password}'
    #headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    headers = {'Content-Type': 'application/json'}
    try:
        conn.request("POST", "/api/oauth/token", payload, headers)
        res = conn.getresponse()
        data = res.read()
        response_data = data.decode("utf-8")
        if res.status == 200:
            access_token = json.loads(response_data).get("access_token")
            refresh_token = json.loads(response_data).get("refresh_token")
    except Exception as e:
        print(f"Ошибка аутентификации: {e}\n", res.status, response_data)
        conn.close()
        conn = None
        access_token = None
        refresh_token = None

def normalize_string(string):
    return unicodedata.normalize('NFKD', string).encode('utf-8', 'ignore').decode("utf-8")

retry_attempted = False
async def send_annonce(author, message):
    global conn, access_token, refresh_token, retry_attempted
    
    author = normalize_string(author)
    message = normalize_string(message)

    await auth(address)
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
        }
    payload = json.dumps({
       "message": f"{message}",
       "senderName": f"{author}"
    })

    try:
        conn.request("POST", "/api/Server/SendGlobalMessage", payload, headers)
        res = conn.getresponse()
        response_data = res.read().decode("utf-8")
        if res.status == 200:
            # print(response_data)
            retry_attempted = False
        else:
            print("Ошибка send_annonce. Ответ соединения:", res.status)
            if not retry_attempted:
                await asyncio.sleep(2)
                if conn:
                    conn.close()
                    conn = None
                access_token = None
                refresh_token = None
                retry_attempted = True
                await send_annonce(author, message)
            else:
                print("Ошибка send_annonce. Повторная отправка не удалась. Ответ соединения:", res.status, response_data)
                
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")
        if conn:
            conn.close()
            conn = None
        access_token = None
        refresh_token = None
        retry_attempted = False

async def update_avatar_if_needed(bot, bot_name, bot_ava):
    # Проверяем, совпадает ли ссылка на аватар
    current_avatar_url = bot.user.avatar.url if bot.user.avatar else None
    if current_avatar_url != bot_ava:
        try:
            response = requests.get(bot_ava)
            response.raise_for_status()  # Проверка на ошибки HTTP
            data = response.content
            print("Avatar data retrieved successfully.")
            await bot.user.edit(avatar=data)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching avatar: {e}")
            
async def get_players():
    global conn, access_token, refresh_token
    try:
        data = None
        await auth(address)
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        conn.request("GET", "/api/OnlinePlayers", headers=headers)
        res = conn.getresponse()
        if res is not None:
            data = res.read().decode("utf-8")
        else:
            print(f"WARN get_players: res is None ")
            return None, None
        if res.status == 200:
            #print("Список онлайн игроков:\n", json.dumps(json.loads(data), indent=4, ensure_ascii=False))
            if data:
                players_data = json.loads(data)
            index = "#"
            name = "Name"
            level = "LvL"
            platformId = "ID"
            ping = "Ping"

            playerKills = "pKill"
            zombieKills = "zKill"
            deaths = "Die"
            totalTimePlayed = "Play"

            #table_header = f"|{index:<2}|{name:<12}|{level:<3}|{platformId:<18}|{ping:<4}|{playerKills:<4}|{zombieKills:<4}|{deaths:<3}|{totalTimePlayed:<4}|\n"
            table_header = f"|{index:<2}|{name:<18}|{level:<3}|{ping:<4}|{playerKills:<5}|{zombieKills:<5}|{deaths:<3}\n"
            table_rows = ""
            players_info = []
            if not players_data:
                table_rows = f"|{'':<17}No Online Players{'':<18}|"
            else:
                for player in players_data:
                    name = player["playerName"]
                    level = player["playerDetails"]["level"]
                    platformId = player["platformId"].replace("Steam_", "")
                    ping = player["ping"]
                    playerKills = player["playerDetails"]["playerKills"]
                    zombieKills = player["playerDetails"]["zombieKills"]
                    deaths = player["playerDetails"]["deaths"]
                    
                    totalTimePlayed = player["playerDetails"]["totalTimePlayed"]
                    days = int(totalTimePlayed // (24 * 3600))
                    hours = int((totalTimePlayed % (24 * 3600)) // 3600)
                    minutes = int((totalTimePlayed % 3600) // 60)
                    totalTimePlayed = f"{hours:02}:{minutes:02}"

                    # Добавляем информацию о игроке в список
                    players_info.append({
                        "name": name,
                        "level": level,
                        "ping": ping,
                        "playerKills": playerKills,
                        "zombieKills": zombieKills,
                        "deaths": deaths,
                        "totalTimePlayed": totalTimePlayed,
                        "effectiveZombieKills": zombieKills - (deaths * 50)  # Эффективные убийства зомби
                    })

                # Сортируем список по эффективным zombieKills от большего к меньшему
                players_info.sort(key=lambda x: x["effectiveZombieKills"], reverse=True)

                # Формируем строку table_rows из отсортированных данных
                for index, player in enumerate(players_info, start=1):
                    #table_rows += f"|{index:<2}|{normalize_string(player['name']):<18}|{player['level']:<3}|{player['ping']:<4}|{player['playerKills']:<5}|{player['zombieKills']:<5}|{player['deaths']:<3}|{player['totalTimePlayed']:<5}|\n"
                    table_rows += f"|{index:<2}|{normalize_string(player['name']):<18}|{player['level']:<3}|{player['ping']:<4}|{player['playerKills']:<5}|{player['zombieKills']:<5}|{player['deaths']:<3}|\n"
                    
            return table_header, table_rows
        else:
            return None, None

    except Exception as e:
        print(f"Ошибка get_players: {e}")
        return None, None

async def send_long_message(ctx, content, ephemeral=True, max_length=1900):
    messages = []
    current_message = ""
    ephemeral = False
    for line in content.splitlines():
        if len(current_message) + len(line) + 1 > max_length:
            messages.append(current_message)
            current_message = line
        else:
            if current_message:
                current_message += "\n"
            current_message += line
    if current_message:
        messages.append(current_message)
    await ctx.followup.send(content=messages[0], ephemeral=ephemeral)
    for message in messages[1:]:
        await ctx.followup.send(content=message, ephemeral=ephemeral)

async def send_api_command(text):

    global conn, access_token, refresh_token
    res = None
    await auth(address)
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    encoded_text = urllib.parse.quote(text)
    #print(f"{encoded_text}")
    url = f"/api/Server/ExecuteConsoleCommand?command={encoded_text}&inMainThread=True"
    #url = f"/api/Server/ExecuteConsoleCommand?command={text}&inMainThread=True"
    conn.request("POST", url, None, headers)
    res = conn.getresponse()
    #data = res.read().decode("utf-8")
    return res

@tasks.loop(seconds=0.1)
async def message_sender():
    global send_interval
    try:
        #print(f"\rCurrent Buffer Limit: {len(message_buffer)}", end='')
        await asyncio.sleep(send_interval)
        if message_buffer:
            message = message_buffer.popleft()
            await send_from_buffer_to_discord(*message)
            if len(message_buffer) > BUFFER_LIMIT:
                send_interval += 1  # Увеличиваем интервал
            else:
                send_interval = max(0, send_interval - 0.1)  # Уменьшаем интервал, не ниже 0.1 секунды
    except Exception as e:
        print(f'\nmessage buffer ERROR >>: {e}')

@tasks.loop(seconds=2)
async def watch_chatlog():
    global current_file, file_position
    current_file = find_latest_file(chatlog_dir)

    if not current_file:
        return
    try:
        if current_file:
            file_position = os.path.getsize(current_file)
            print(f"watch chat_log start at {current_file}")
            await watch_log_file(chatlog_dir)
    except Exception as e:
        print(f'watch log ERROR >>: {e}')

@tasks.loop(seconds=1)
async def watch_logs():
    global current_file2, file2_position
    try:
        current_file2 = find_latest_file(log_dir)
        if current_file2:
            file2_position = os.path.getsize(current_file2)
            print(f"watch log start at {current_file2}")
            await watch_log_file2(log_dir)
    except Exception as e:
        print(f'watch log ERROR >>: {e}')

@tasks.loop(seconds=int(update_time))
async def update_status():
    global conn, access_token, refresh_token, day7
    data_list = None
    data_list2 = None

    if bot.user.name != bot_name:
        await bot.user.edit(username=bot_name)

    try:
        await auth(address)
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        try:
            conn.request("GET", "/api/Server/Stats", headers=headers)
            res = conn.getresponse()
            data = res.read().decode("utf-8")
        except Exception as e:
            print(f"/api/Server/Stats: {e}")
        try:
            payload = ''
            conn.request("GET", "/api/Server/GameInfo", payload, headers)
            res2 = conn.getresponse()
            data2 = res2.read().decode("utf-8")
            #print(json.dumps(json.loads(data2), indent=4, ensure_ascii=False))
            if res2.status == 200:
                try:
                    data_list2 = json.loads(data2)
                except Exception as e:
                    pass
        except Exception as e:
            print(f"/api/Server/GameInfo: {e}")

        if res is not None and res.status == 200:
            try:
                data_list = json.loads(data)  # Декодируем JSON в список
            except Exception as e:
                data_list = None
                activity = disnake.Game(name=f"Offline")
                await bot.change_presence(status=disnake.Status.online, activity=activity)
            if data_list:

                online_players = data_list.get("onlinePlayers", 0)
                max_players = data_list.get("maxOnlinePlayers", 0)

                activity = disnake.Game(name=f"Online: {online_players}/{max_players}")
                await bot.change_presence(status=disnake.Status.online, activity=activity)

        async def upd_msg():
            global day7
            update_settings()
            if data_list:
                uptime_seconds = int(data_list.get("uptime", 0))
                hours = f"{uptime_seconds // 3600:02}"
                minutes = f"{(uptime_seconds % 3600) // 60:02}"
                
                game_days = data_list["gameTime"].get("days", 0)
                game_hours = data_list["gameTime"].get("hours", 0)
                game_minutes = data_list["gameTime"].get("minutes", 0)


            try:
                moon_now = data_list.get('isBloodMoon', 0)
                cycle_length = data_list2.get('BloodMoonFrequency', {'value': 0})['value']
                next_blood_moon = ((game_days // cycle_length) + 1) * cycle_length
                days_until = '0' if (next_blood_moon - game_days >= cycle_length) else f'{next_blood_moon - game_days}'
            except:
                days_until = f"∞"
            try:
                day7 = f"{'NOW :red_circle:' if moon_now else f'{days_until} Day :full_moon:'}"
                add_code_string = eval(f'f"""{add_string}"""')
                message = (
                    f":green_circle: Online:                        **{online_players}/{max_players}**\n"
                    f":link:Direct Link:                            **```{data_list2.get('IP', {'value': 0})['value']}:{data_list.get("serverPort", 0)}```**\n"
                    f":earth_americas: World:                       **{data_list.get("gameWorld", 0)}**\n"
                    f":film_frames: FPS:                            **{int(data_list.get("fps", 0))}**\n"
                    f":timer: UpTime:                               **{hours}:{minutes}**\n"
                    f":newspaper: Ver:                              **{data_list.get("serverVersion", 0)}**\n"
                    f"{f'{add_code_string}\n' if add_string else ''}"
                    f"============ Server Settings ============\n"
                    f":date: Game Time:                             **{game_days}d :timer: {game_hours:02}h:{game_minutes:02}m**\n"
                    f":waxing_crescent_moon: Moon Cycle:            **{cycle_length}**\n"
                    f":first_quarter_moon: Blood Moon:              **{day7}**\n"
                    f":traffic_light: Difficulty:                   **{data_list.get("gameDifficulty", 0)}**\n"
                )
            except Exception as e:
                message = f"Error forming message {e}"

            title_value = data_list.get("serverName", 0) if data_list is not None else "Unknown Server"
            addition_embed = disnake.Embed(
                title=f"**{title_value}**",
                colour=disnake.Colour.green(),
                description=f"{message}",
            )
            try:
                channel = await bot.fetch_channel(channel_id)
                message = await channel.fetch_message(message_id)

                if message:
                    await message.edit(content=f'Last update: {datetime.datetime.now().strftime("%H:%M")}', embed=addition_embed)
            except Exception as e:
                print(f'Failed to fetch channel, message or server data. Maybe try /{command_prefex}_sendhere\n {e}')
        await upd_msg()
    except Exception as e:
        print(f'Cant connect to server, check ip and query/rest_api port ERROR >>: {e}')
        embed = disnake.Embed(
            title=f"**{address[0]}:{address[2]}**",
            colour=disnake.Colour.red(),
            description=f"offline or cannot answer",
        )
        channel = await bot.fetch_channel(channel_id)
        message = await channel.fetch_message(message_id)
        if message:
            await message.edit(content=f'Last update: {datetime.datetime.now().strftime("%H:%M")}', embed=embed)
    #update player banner
    try:
        table_header, table_rows = await get_players()
        full_table = f"```ps\n{table_header}{table_rows}```"

        # Проверка длины full_table
        if len(full_table) > 4096:
            full_table = full_table[:4090] + '...'  # Обрезаем и добавляем многоточие, чтобы не превышать лимит

        embed = disnake.Embed(
            title=f"",
            colour=disnake.Colour(int("FF00FF", 16)),
            description=f"{full_table}",
        )
        embed.set_image(url=f"http://65.109.113.61:26980/footbar.png?timestamp={int(time.time())}")
        #embed.set_footer(text="banner", icon_url=f"http://65.109.113.61:26980/footbar.png?timestamp={int(time.time())}")
        channel = await bot.fetch_channel(channel_id)
        message = await channel.fetch_message(players_message_id)
        if message:
            await message.edit(content=f'', embed=embed)
    except Exception as e:
        print(f"{players_message_id} Error: {e}")
        embed = disnake.Embed(
            title=f"**{address[0]}:{address[2]}**",
            colour=disnake.Colour.red(),
            description=f"offline or cannot answer",
        )
        channel = await bot.fetch_channel(channel_id)
        message = await channel.fetch_message(players_message_id)
        if message:
            await message.edit(content=f'', embed=embed)

@tasks.loop(seconds=10)
async def start_plink():
    chat_line = re.compile(
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2} \d+\.\d+ INF Chat "
        r"\(from '([^']+)', entity id '([^']+)', to '([^']+)'\): '([^']+)': (.+)$"
    )
    nonplayer_line = re.compile(
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2} \d+\.\d+ INF Chat "
        r"\(from '([^']+)', entity id '([^']+)', to '([^']+)'\): (.+)$"
    )
    adminplayer_line = re.compile(
        r"from '([^']*)', entity id '([^']*)', to '([^']*)'\): (.+?): (.+)$"
    )
    def clear_string(text):
        text = re.sub(r'\[[0-9A-Fa-f]{6}\]', '', text)
        text = text.replace('[-]', '')
        return text

    # Запускаем telnet-соединение и читаем в фоне, если не запущено
    if not hasattr(start_plink, "task") or start_plink.task.done():
        print("Watch Chat via telnet started")
        async def telnet_reader():
            try:
                tn = telnetlib.Telnet(address[0], int(address[3]), timeout=10)
                tn.write((password + "\n").encode('utf-8'))
                # Очистка буфера (как в оригинале)
                start = time.time()
                while time.time() - start < 1:
                    try:
                        tn.read_very_eager()
                    except:
                        break

                while True:
                    line_bytes = await asyncio.to_thread(tn.read_until, b"\n", 1)
                    if not line_bytes:
                        await asyncio.sleep(0.1)
                        continue
                    line = line_bytes.decode('utf-8').rstrip()

                    # Вызов функции из chat_handler.py (чат команды)
                    if "INF Chat (" in line:
                        await chat_handler.handle_chat_line(tn, line)

                    # Вызов функции из chat_handler.py (чат команды)
                    if "INF Client" in line:
                        command_pattern = re.compile(r"Client\s+(\S+?)/(\S+?)\s+executing client side command:\s+(.*)$")
                        match = command_pattern.search(line)
                        if match:
                            id_ = match.group(1)
                            nick = match.group(2)
                            command = match.group(3)
                            print(f"id: {id_}, nick: {nick}, command: {command}")

                            send_to_discord(f"**WARN**\n[Console] **{nick}**", command)

                    content = {}
                    match = chat_line.match(line)
                    if match:
                        content = {
                            "from": match.group(1),
                            "entityId": match.group(2),
                            "to": match.group(3),
                            "name": match.group(4),
                            "text": match.group(5)
                        }
                        channel = content["to"]
                        nick = content["name"]
                        message = content["text"]
                        if content.get("to", "").lower() == "global":
                            send_to_discord(f"[{channel}] **{nick}**", message)

                    elif (match := adminplayer_line.match(line)):
                        content = {
                            "from": match.group(1),
                            "entityId": match.group(2),
                            "to": match.group(3),
                            "name": match.group(4),
                            "text": match.group(5),
                        }
                        channel = content["to"]
                        nick = clear_string(content["name"])
                        message = clear_string(content["text"])
                        if content.get("to", "").lower() == "global":
                            send_to_discord(f"[{channel}] **{nick}**", message)

                    elif (match := nonplayer_line.match(line)):
                        content = {
                            "from": match.group(1),
                            "entityId": match.group(2),
                            "to": match.group(3),
                            "name": None,
                            "text": match.group(4)
                        }
                        nick = clear_string(content["from"])
                        message = clear_string(content["text"])
                        #print(f"Debug:{nick}> {message}")
                        if nick.lower() == "-non-player-" and content.get("to", "").lower() == "global":
                            parts = message.split(":", 1)
                            if len(parts) == 2:
                                send_to_discord(f"[{content["to"]}] **{parts[0].strip()}**", parts[1].strip())
                            else:
                                send_to_discord(f"[{content['to']}] **[Server]**", f"{message.strip()}")

            except Exception as e:
                #print(f"Telnet connection error: {e}")
                pass

        # start parralel telnet_reader
        start_plink.task = asyncio.create_task(telnet_reader())

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}\nBot Shards: {bot.shard_count}')
    print('Invite bot link to discord (open in browser):\nhttps://discord.com/api/oauth2/authorize?client_id='+ str(bot.user.id) +'&permissions=8&scope=bot\n')

    try:
        await update_avatar_if_needed(bot, bot_name, bot_ava)
    except Exception as e:
        print(f'update_avatar ERROR >>: {e}')
    update_status.start()
    #watch_chatlog.start()
    watch_logs.start()
    start_plink.start()
    message_sender.start()

@bot.event
async def on_message(message):
    if message.author == client.user:		#отсеим свои сообщения
        return;
    if message.author.bot:
        return;
    if str(message.channel.id) != crosschat_id:
        return
    if message.content.startswith(''):
        text = ''
        #print(f"global_name: {message.author.global_name} text: {text}")
        role_color = f"[{str(message.author.color).lstrip('#')}]" if message.author.color else ""
        try:
            await send_annonce(f"{role_color}[Discord] {message.author.global_name}[-]", message.content)
            await message.add_reaction('✅')
        except Exception as e:
            print(f'ERROR send_annonce>>: {e}')

#template admin commands
'''
@bot.slash_command(description="Add SteamID to Whitelist")
async def admin_cmd(ctx: disnake.ApplicationCommandInteraction, steamid: str):
    if ctx.author.guild_permissions.administrator:
        print(f'it admin command')
        try:
            await ctx.send(f'admin command try', ephemeral=True)
        except Exception as e:
            await ctx.send(f'ERROR Adding SteamID', ephemeral=True)
    else:
        await ctx.response.send_message("❌ You do not have permission to run this command.", ephemeral=True)
'''
#template users command
'''
@bot.slash_command(description="Show commands list")
async def help(ctx):
    await ctx.send('**==Support commands==**\n'
    f' Show commands list```{prefix}help```'
    f' Show server status```{prefix}moestatus```'
    f'\n **Need admin rights**\n'
    f' Auto send server status here```{prefix}sendhere```'
    f' Add server to listing```{prefix}serveradd adress:port name```',
    ephemeral=True
    )
'''

@bot.slash_command(name=f'{command_prefex}_sendhere', description="Set this channel to status")
async def sendhere(ctx: disnake.ApplicationCommandInteraction):
    if ctx.author.guild_permissions.administrator:
        try:
            guild = ctx.guild
            print(f'New channel id - {ctx.channel.id}')
            await write_cfg('botconfig', 'channel_id', str(ctx.channel.id))
            channel = await guild.fetch_channel(ctx.channel.id)
            
            await ctx.response.send_message(content=f'This message for auto updated the status', ephemeral=False)
            last_message = await ctx.channel.fetch_message(ctx.channel.last_message_id)
            print(f'New message id - {last_message.id}')
            await write_cfg('botconfig', 'message_id', str(last_message.id))

            await ctx.followup.send(content=f'This message for auto updated the status players', ephemeral=False)
            last_message = await ctx.channel.fetch_message(ctx.channel.last_message_id)
            print(f'New players message id - {last_message.id}')
            await write_cfg('botconfig', 'players_message_id', str(last_message.id))

            update_settings()

        except Exception as e:
            await ctx.response.send_message(content='❌ An error occurred. Please try again later.', ephemeral=True)
            print(f'Error occurred during file write: {e}')
    else:
        await ctx.response.send_message(content='❌ You do not have permission to run this command.', ephemeral=True)

@bot.slash_command(name=f'{command_prefex}_lookhere', description="Look this channel to crosschat")
async def lookhere(ctx: disnake.ApplicationCommandInteraction):
    if ctx.author.guild_permissions.administrator:
        try:
            guild = ctx.guild
            print(f'New crosschat channel id - {ctx.channel.id}')
            await write_cfg('botconfig', 'crosschat_id', str(ctx.channel.id))
            channel = await guild.fetch_channel(ctx.channel.id)
            await ctx.response.send_message(content=f'This channel id [**{channel}**] for crosschat', ephemeral=False)
            update_settings()

        except Exception as e:
            await ctx.response.send_message(content='❌ An error occurred. Please try again later.', ephemeral=True)
            print(f'Error occurred during file write: {e}')
    else:
        await ctx.response.send_message(content='❌ You do not have permission to run this command.', ephemeral=True)

'''
@bot.slash_command(name=f'{command_prefex}_status', description="Request Servers status")
async def status(ctx: disnake.ApplicationCommandInteraction, ip: str = None, query: int = None):
    if ip is None:
        ip = address[0]
    try:
        if ip is not None and query is not None:
            info, players, rules = await get_info((f"{ip}", int(query)))
        else:
            info, players, rules = await get_info(address)
        message = (
            f":earth_africa: Direct Link: **{ip}:{info.port}**\n"
            f":link: Invite: **{rules.get('SU_s', 'N/A')}**\n"
            f":map: Map: **{info.map_name}**\n"
            f":green_circle: Online: **{info.player_count}/{info.max_players}**\n"
            f":asterisk: Pass: **{info.password_protected}**\n"
            f":newspaper: Ver: **{rules.get('NO_s', 'N/A')}**\n"
        )
        addition_embed = disnake.Embed(
            title=f"**{info.server_name}**",
            colour=disnake.Colour.green()
        )
        addition_embed.add_field(name="", value=message, inline=False)

        try:
            await ctx.response.send_message(embed=addition_embed, ephemeral=True)
        except Exception as e:
            await ctx.response.send_message(f'❌ Failed to send the status message. \nError:\n{e}', ephemeral=True)
            print(f'Error occurred during sending message: {e}')

    except Exception as e:
        await ctx.response.send_message(content='❌ An error occurred. Please try again later.', ephemeral=True)
        print(f'Error occurred during fetching server info: {e}')
'''

@bot.slash_command(name=f'{command_prefex}_players', description="Request Players status")
async def players(ctx: disnake.ApplicationCommandInteraction):
    global conn, access_token, refresh_token
    try:
        table_header, table_rows = await get_players()
        if table_header and table_rows:
            # Формируем сообщение с таблицей
            full_table = f"```ps\n{table_header}{table_rows}```"

            # Разделяем сообщение на части по 1500 символов
            max_length = 1700
            current_message = "```ps\n" + table_header  # Начинаем с заголовка

            for row in table_rows.splitlines(keepends=True):  # Сохраняем переносы строк
                if len(current_message) + len(row) > max_length:
                    # Если добавление строки превышает лимит, отправляем текущее сообщение
                    current_message += "```"  # Закрываем кодовый блок
                    await ctx.send(current_message, ephemeral=True)
                    current_message = "```ps\n" + table_header + row  # Начинаем новый блок с заголовком
                else:
                    current_message += row  # Добавляем строку в текущее сообщение

            # Отправляем оставшийся текст, если он есть
            if current_message.strip() != "```ps\n" + table_header:
                current_message += "```"  # Закрываем кодовый блок
                await ctx.send(current_message, ephemeral=True)
        else:
            print("Ошибка получения списка игроков:", res.status, data)
            await ctx.response.send_message(content=f'❌ Ошибка получения списка игроков:" res.status:{res.status}\nData:{data}', ephemeral=True)

    except Exception as e:
        await ctx.response.send_message(content='❌ An error occurred. Please try again later.', ephemeral=True)
        print(f'Error occurred during fetching server info: {e}')
    finally:
        conn.close()
        conn = None

@bot.slash_command(name=f'{command_prefex}_players_info', description="Request Players info")
async def players_info(ctx: disnake.ApplicationCommandInteraction):
    global conn, access_token, refresh_token
    if ctx.author.guild_permissions.administrator:
        try:
            await auth(address)
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            conn.request("GET", "/api/OnlinePlayers", headers=headers)
            res = conn.getresponse()
            data = res.read().decode("utf-8")
            if res.status == 200:
                #print("Список онлайн игроков:\n", json.dumps(json.loads(data), indent=4, ensure_ascii=False))
                players_data = json.loads(data)

                index = "#"
                name = "Name"
                level = "LvL"
                platformId = "ID"
                ping = "Png"

                ip = "IP"
                zombieKills = "zKill"
                deaths = "Die"
                totalTimePlayed = "PlayTime"

                table_header = f"|{name:<14}|{ping:<3}|{ip:<16}|{platformId:<17}|\n"
                table_rows = ""

                for index, player in enumerate(players_data, start=1):
                    name = player["playerName"]
                    level = player["playerDetails"]["level"]
                    platformId = player["platformId"].replace("Steam_", "")
                    ping = player["ping"]
                    ip = player["ip"]
                    zombieKills = player["playerDetails"]["zombieKills"]
                    deaths = player["playerDetails"]["deaths"]
                    
                    totalTimePlayed = player["playerDetails"]["totalTimePlayed"]
                    days = int(totalTimePlayed // (24 * 3600))
                    hours = int((totalTimePlayed % (24 * 3600)) // 3600)
                    minutes = int((totalTimePlayed % 3600) // 60)
                    totalTimePlayed = f"{days:02}:{hours:02}:{minutes:02}"

                    table_rows += f"|{name:<14}|{ping:<3}|{ip:<16}|{platformId:<17}|\n"

                # Формируем сообщение с таблицей
                full_table = f"```ps\n{table_header}{table_rows}```"

                # Разделяем сообщение на части по 1500 символов
                max_length = 1700
                current_message = "```ps\n" + table_header  # Начинаем с заголовка

                for row in table_rows.splitlines(keepends=True):  # Сохраняем переносы строк
                    if len(current_message) + len(row) > max_length:
                        # Если добавление строки превышает лимит, отправляем текущее сообщение
                        current_message += "```"  # Закрываем кодовый блок
                        await ctx.send(current_message, ephemeral=True)
                        current_message = "```ps\n" + table_header + row  # Начинаем новый блок с заголовком
                    else:
                        current_message += row  # Добавляем строку в текущее сообщение

                # Отправляем оставшийся текст, если он есть
                if current_message.strip() != "```ps\n" + table_header:
                    current_message += "```"  # Закрываем кодовый блок
                    await ctx.send(current_message, ephemeral=True)
            else:
                print("Ошибка получения списка игроков:", res.status, data)
                await ctx.response.send_message(content=f'❌ Ошибка получения списка игроков:" res.status:{res.status}\nData:{data}', ephemeral=True)
        except Exception as e:
            await ctx.response.send_message(content='❌ An error occurred. Please try again later.', ephemeral=True)
            print(f'Error occurred during fetching server info: {e}')
        finally:
            conn.close()
            conn = None
    else:
        await ctx.response.send_message(content='❌ You do not have permission to run this command.', ephemeral=True)

@bot.slash_command(name=f'{command_prefex}_command', description="Execute console command")
async def command(ctx: disnake.ApplicationCommandInteraction, text: str):
    global conn, access_token, refresh_token, user_role_ids
    
    #if ctx.author.guild_permissions.administrator:
    if ctx.author.guild_permissions.administrator or \
       any(role.id in user_role_ids for role in ctx.author.roles) or \
       ctx.author.id in user_role_ids:
        await ctx.response.defer()
        if text.lower() == "server kill":
            print(f"call Kill server!!!")
            bat_file_path = r"C:\7DTD\Server\server_killer.bat"
            try:
                #subprocess.run(bat_file_path, check=True)
                subprocess.Popen(["cmd.exe", "/c", bat_file_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                #send = f"cmd.exe /c echo {command}|plink.exe -telnet 127.0.0.1 -P {port} -raw -batch"
                #process = subprocess.Popen(send, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                #output, error = process.communicate()
                
                await send_long_message(ctx, "принудительное завершения сервера")
            except subprocess.CalledProcessError as e:
                print(f"Ошибка при выполнении {bat_file_path}: {e}")
            return

        try:
            await auth(address)
            res = await send_api_command(text)
            data = res.read().decode("utf-8")

            if res.status == 200:
                #print("Результат:\n", json.dumps(json.loads(data), indent=4, ensure_ascii=False))
                #data = json.loads(data)
                #print(f"data:\n{data}")

                formatted_text = "\n".join(item.replace("\r\n", "\n") for item in json.loads(data))
                #print(f"{formatted_text}")

                #await ctx.response.send_message(content=f'{formatted_text}', ephemeral=True)
                await send_long_message(ctx, formatted_text)

            else:
                #print(f"res.status: {res.status}\ndata:\n{data}")
                #await ctx.response.send_message(content=f'❌ERROR\nres.status: {res.status}\ndata:\n{data}', ephemeral=False)
                await ctx.followup.send(content=f'❌ERROR\nres.status: {res.status}\ndata:\n{data}', ephemeral=True)

        except Exception as e:
            await ctx.followup.send(content='❌ An error occurred. Please try again later.', ephemeral=True)
            print(f'Error occurred during fetching server info: {e}')

        finally:
            if conn:
                conn.close()
                conn = None
    else:
        await ctx.followup.send(content='❌ You do not have permission to run this command.', ephemeral=True)

try:
    bot.run(token)
except disnake.errors.LoginFailure:
    print(' Improper token has been passed.\n Get valid app token https://discord.com/developers/applications/ \nscreenshot https://junger.zzux.com/webhook/guide/4.png')
except disnake.HTTPException:
    print(' HTTPException Discord API')
except disnake.ConnectionClosed:
    print(' ConnectionClosed Discord API')
except disnake.errors.PrivilegedIntentsRequired:
    print(' Privileged Intents Required\n See Privileged Gateway Intents https://discord.com/developers/applications/ \nscreenshot http://junger.zzux.com/webhook/guide/3.png')
except KeyboardInterrupt:
    print(' Stoping...')
