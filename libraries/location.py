class Location:
    def __init__(self, server):
        self.server = server
        self.actions = ["ks", "hg", "gf",
                        "k", "sl", "lks",
                        "hs", "aks", "pd"]
    
    async def room(self, msg, client):
        subcmd = msg["command"].split(".")[-1]
        if subcmd == "info":
            isHouse = "h" == get_pref_loc(msg["roomId"])
            plrs = []
            if msg["roomId"] in self.server.room:
                for uid in self.server.room[msg["roomId"]]:
                    plrs.append(await gen_plr(self.server, uid))
            cmd = {"data": {"rmmb": plrs}, "command": f"{get_pref_loc(msg['roomId'])}.r.info"}
            if isHouse:
                house_room = msg["roomId"]
                owner = house_room.split("_")[1]
                room = house_room.split("_")[2]
                name_room = await self.server.redis.get(f"rooms:{owner}:{room}:name")
                cmd["data"]["rm"] = {"f": await self.server.get_room(msg["roomId"]), "w": 13,
                                     "id": msg["roomId"].split("_")[2], "l": 13, "lev": 1, "nm": name_room}
            await client.send(cmd)
        elif subcmd in self.actions + ['m', 'u', 'ca', 'sa']:
            if subcmd == "u":
                client.position = (msg["data"]["x"], msg["data"]["y"])
                client.act = "stand"
            if subcmd == "ca":
                msg["data"]["uid"] = client.uid
            if subcmd in self.actions:
                rl = self.server.lib["rl"]
                uid = msg["data"]["tmid"]
                link = await rl.get_link(client.uid, uid)
                if link:
                    await rl.add_progress({"ks": "kiss", "hg": "hug", "gf": "giveFive",
                                           "k": "kickAss", "sl": "slap", "lks": "longKiss",
                                           "hs": "handShake", "aks": "airKiss", "pd": "pairDance"}[subcmd], link)
            if "at" in msg["data"]:
                if msg["data"]["at"]:
                    client.act = msg["data"]["at"]
            await self.server.send_everybody(client.room, msg)
        elif subcmd == "ra":
            await refresh_avatar(self.server, client)
        elif subcmd == "rfr":
            room_items = await self.server.get_room(client.room, 2)
            await self.server.send_everybody(client.room, {
                'data': {'rm': room_items},
                'command': 'h.r.rfr'
            })


async def join_room(server, new_room, client):
    await leave_room(server, client)
    pref = get_pref_loc(new_room)
    if new_room not in server.room:
        server.room[new_room] = []
    server.room[new_room].append(client.uid)
    client.room = new_room
    await server.send_everybody(new_room,
                                {"data": {"plr": await gen_plr(server, client.uid)}, "command": f"{pref}.r.jn"})


async def refresh_avatar(server, client):
    room = client.room
    pref = get_pref_loc(room)
    await server.send_everybody(room, {'command': f'{pref}.r.ra', 'data': {"plr": await gen_plr(server, client.uid)}})


async def gen_plr(server, uid):
    r = server.redis
    plr = {}
    plr["uid"] = uid
    plr["apprnc"] = await server.get_appearance(uid)
    loc = None
    action = ""
    pos = (-1.0, -1.0)
    if uid in server.online:
        action = server.online[uid].act
        pos = server.online[uid].pos
        loc = server.online[uid].room
    plr["locinfo"] = {'st': 0, 'at': action, 'd': 4, 'x': pos[0], 'y': pos[1], 'l': loc}
    plr["usrinf"] = {'sid': int(uid), 'rl': 4, 'lng': '', 'lcl': 'RU', 'al': 99}
    plr["ci"] = await city_info(server, uid)
    plr["onl"] = uid in server.online
    plr["clths"] = await server.get_clothes(uid, 2)
    plr['res'] = {
        'slvr': await r.get(f"mob:{uid}:slvr"),
        'gld': await r.get(f"mob:{uid}:gld"),
        'enrg': await r.get(f"mob:{uid}:enrg"),
        'emd': await r.get(f"mob:{uid}:emd")
    }
    return plr


def get_lvl(exp):
    expSum = 0
    lvl = 0
    while expSum <= exp:
        lvl += 1
        expSum += lvl * 50
    return lvl


async def city_info(server, uid):
    r = server.redis
    ci = {}
    ci["exp"] = await r.incrby(f"mob:{uid}:exp", 0)
    ci["crt"] = await r.incrby(f"mob:{uid}:crt", 0)
    ci["hrt"] = await r.incrby(f"mob:{uid}:hrt", 0)
    ci["lvt"] = await r.incrby(f"mob:{uid}:lvt", 0)
    ci["dr"] = bool(await r.incrby(f"mob:{uid}:dr", 0))
    ci["vexp"] = str(await r.incrby(f"mob:{uid}:vip", 0))
    ci["vip"] = False if ci["vexp"] == "0" else True
    ci["ceid"] = 0
    ci["cmid"] = 0
    ci["nl"] = 0
    ci["lv"] = get_lvl(ci["exp"])
    return ci


def get_pref_loc(room):
    if "house" in room:
        return "h"
    elif "work" in room:
        return "w"
    return "o"


async def leave_room(server, client):
    old_room = client.room
    if not old_room:
        return
    pref = get_pref_loc(old_room)
    await server.send_everybody(old_room, {"data": {"uid": client.uid}, "command": f"{pref}.r.lv"})
    server.room[old_room].remove(client.uid)
    if not server.room[old_room]:
        del server.room[old_room]
    client.room = None
