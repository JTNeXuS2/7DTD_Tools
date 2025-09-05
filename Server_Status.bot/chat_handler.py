import os
import json
import re
import time
import sys

db_file = "player_data.json"

def load_data():
    if os.path.exists(db_file):
        with open(db_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def send_to_server(tn, cmd):
    tn.write((cmd + "\n").encode())
    tn.write(b"\n")
    tn.write(b"")
    time.sleep(0.1)

def get_player_location(tn, steam_id):
    send_to_server(tn, "lp")
    start_time = time.time()
    while time.time() - start_time < 5:
        try:
            line = tn.read_until(b"\n", timeout=1).decode(errors="ignore").strip()
            if not line:
                continue

            if f"pltfmid=Steam_{steam_id}" in line and "pos=" in line:
                match = re.search(r"pos=\(([-\d.]+), ([-\d.]+), ([-\d.]+)\)", line)
                if match:
                    x, y, z = match.groups()
                    return {"x": float(x), "y": float(y), "z": float(z)}

        except Exception as e:
            print("⚠️ Error reading lp output:", e)
    return None

def get_vehicle_list(tn, entity_id):
    send_to_server(tn, "vl")
    start_time = time.time()
    vehicles_list = []
    pattern = re.compile(r"\[SERVERTOOLS\] '(.+?)' Id '(\d+)' Owner Id '(\d+)' Owner Name '(.+?)', located at '([^']+)'")
    location_pattern = re.compile(r"x\s*(-?\d+)\s*y\s*(-?\d+)\s*z\s*(-?\d+)")
    while time.time() - start_time < 5:
        try:
            line = tn.read_until(b"\n", timeout=1).decode(errors="ignore").strip()
            if not line:
                continue
            match = pattern.search(line)
            if match:
                vehicle_type, vid, owner_id_str, owner_name, location = match.groups()
                #owner_id = int(owner_id_str)
                if str(owner_id_str) == str(entity_id):
                    type_clean = vehicle_type.replace("vehicle", "", 1)
                    loc_match = location_pattern.search(location)
                    if loc_match:
                        x, y, z = loc_match.groups()
                        located_clean = f"{x} {y} {z}"
                    else:
                        located_clean = location

                    vehicles_list.append({
                        "type": type_clean,
                        "id": int(vid),
                        "pos": located_clean
                    })
        except Exception as e:
            print("⚠️ Error reading output:", e)
    if vehicles_list:
        return vehicles_list
    else:
        return None

async def handle_chat_line(tn, line):

    match = re.search(r"Chat \(from 'Steam_(\d+)', entity id '(\d+)', to 'Global'\): '([^']+)':\s*(/[\w]+)", line)
    if not match:
        return
    #print(f"ChatLine> {line}")

    steam_id = match.group(1)
    entity_id = match.group(2)
    name = match.group(3)
    command = match.group(4).strip().lower()

    data = load_data()
    player = data.get(steam_id, {})
    player["entity_id"] = entity_id
    player["name"] = name
    data[steam_id] = player

    if command == "/loc":
        loc = get_player_location(tn, steam_id)
        if loc:
            player["base"] = loc
            send_to_server(tn, f"pm {entity_id} \"[ADFF2F]Location XYZ: {loc['x']:.1f}, {loc['y']:.1f}, {loc['z']:.1f}\"")
        else:
            send_to_server(tn, f"pm {entity_id} \"[ADFF2F]Failed to get your current location\"")

    elif command == "/help":
        send_to_server(tn, f'pm {entity_id} "[ADFF2F]Commands: /help, /loc, В меню Esc (корзинка) подробности"')

    elif command == "/cc":
        send_to_server(tn, f'getbicycle {entity_id}')
        time.sleep(1)
        send_to_server(tn, f'pm {entity_id} "[ADFF2F]: Command Complete"')
        
    elif command == "/bc":
        send_to_server(tn, f'getbike {entity_id}')
        time.sleep(1)
        send_to_server(tn, f'pm {entity_id} "[ADFF2F]: Command Complete"')
        
    elif command == "/lc":
        send_to_server(tn, f'getblimp {entity_id}')
        time.sleep(1)
        send_to_server(tn, f'pm {entity_id} "[ADFF2F]: Command Complete"')
        
    elif command == "/dc":
        send_to_server(tn, f'getdrone {entity_id}')
        time.sleep(1)
        send_to_server(tn, f'pm {entity_id} "[ADFF2F]: Command Complete"')
        
    elif command == "/gc":
        send_to_server(tn, f'getgyrocopter {entity_id}')
        time.sleep(1)
        send_to_server(tn, f'pm {entity_id} "[ADFF2F]: Command Complete"')
        
    elif command == "/hc":
        send_to_server(tn, f'gethelicopter {entity_id}')
        time.sleep(1)
        send_to_server(tn, f'pm {entity_id} "[ADFF2F]: Command Complete"')
        
    elif command == "/jc":
        send_to_server(tn, f'getjeep {entity_id}')
        time.sleep(1)
        send_to_server(tn, f'pm {entity_id} "[ADFF2F]: Command Complete"')
        
    elif command == "/mc":
        send_to_server(tn, f'getmotorcycle {entity_id}')
        time.sleep(1)
        send_to_server(tn, f'pm {entity_id} "[ADFF2F]: Command Complete"')

    elif command == "/deldrone":
        send_to_server(tn, f'resetdronedata {entity_id}')
        time.sleep(1)
        send_to_server(tn, f'pm {entity_id} "[ADFF2F]: Command Complete"')
        
    elif command == "/delchar":
        send_to_server(tn, f'resetplayerdata {entity_id}')
        time.sleep(1)
        send_to_server(tn, f'pm {entity_id} "[ADFF2F]: Command Complete"')

    elif command == "/7day":
        day7 = re.sub(r':red_circle:|:full_moon:', '', sys.modules['__main__'].__dict__.get('day7', '∞'))
        time.sleep(1)
        send_to_server(tn, f'pm {entity_id} "[ADFF2F]: [FF0000]Blood Moon HORDE -[ADFF2F] {day7}"')

    elif command.startswith("/admin"):
        admin_role_id = "952310002528432178"
        admin_message = command[len("/admin"):].strip()
        send_func = sys.modules['__main__'].__dict__.get('send_from_buffer_to_discord')
        if send_func:
            await send_func(f"Call <@&{admin_role_id}> Player: **{name}**", f"ID: {steam_id}")
        else:
            print("Функция send_from_buffer_to_discord не найдена в главном модуле")
        send_to_server(tn, f'pm {entity_id} "[ADFF2F]: Command Complete"')

    elif command == "/resetstats":
        send_to_server(tn, f'st-spk {entity_id} 0')
        send_to_server(tn, f'st-szk {entity_id} 0')
        send_to_server(tn, f'st-deaths {entity_id} 0')
        time.sleep(1)
        send_to_server(tn, f'pm {entity_id} "[ADFF2F]: Command Complete"')

    elif command == "/vc":
        vehicles_list = get_vehicle_list(tn, entity_id)
        if vehicles_list:
            for v in vehicles_list:
                send_to_server(tn, f'pm {entity_id} "[ADFF2F]: Type:{v['type']}, ID:{v['id']}, Pos:{v['pos']}"')
                time.sleep(0.1)
        else:
            send_to_server(tn, f'pm {entity_id} "[ADFF2F]: Vehicles not found"')

    '''
    if command == "/setbase":
        loc = get_player_location(tn, steam_id)
        if loc:
            player["base"] = loc
            send_to_server(tn, f"say \"Base set at XYZ: {loc['x']:.1f}, {loc['y']:.1f}, {loc['z']:.1f}\"")
        else:
            send_to_server(tn, f"say \"Failed to get your current location to set base.\"")

    elif command == "/base":
        if "base" in player:
            current_loc = get_player_location(tn, steam_id)
            if current_loc:
                player["return"] = current_loc  # Save location before teleporting
                base_loc = player["base"]
                send_to_server(tn, f"say \"Teleporting to base at XYZ: {base_loc['x']:.1f}, {base_loc['y']:.1f}, {base_loc['z']:.1f}\"")
                send_to_server(tn, f"teleportplayer {player['entity_id']} {int(base_loc['x'])} {int(base_loc['y'])} {int(base_loc['z'])}")
            else:
                send_to_server(tn, "say \"Could not retrieve your current location before teleporting.\"")
        else:
            send_to_server(tn, "say \"No base set. Use /setbase first.\"")

    elif command == "/return":
        if "return" in player:
            ret_loc = player.pop("return")  # Remove it after use
            send_to_server(tn, f"say \"Returning to X: {ret_loc['x']:.1f}, Y: {ret_loc['y']:.1f}, Z: {ret_loc['z']:.1f}\"")
            send_to_server(tn, f"teleportplayer {player['entity_id']} {int(ret_loc['x'])} {int(ret_loc['y'])} {int(ret_loc['z'])}")
        else:
            send_to_server(tn, "say \"No return location saved. Use /base first.\"")
    '''

    # Always save data at the end
    data[steam_id] = player
    save_data(data)
