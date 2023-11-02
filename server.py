import asyncio
import time
import aioredis
import const
import inventory
import logging
from libraries.location import refresh_avatar
import parserxml
import importlib
from client import Client

BACKGROUND_TIME = 60

log = logging.getLogger("mobile")
logging.basicConfig(format="%(levelname)-3s [%(asctime)s]  %(message)s", datefmt="%H:%M:%S", level=logging.INFO)


class Server:
    def __init__(self):
        self.online = {}
        self.lib = {}
        self.inv = {}
        self.room = {}
        self.parser = parserxml.Parser()
        self.clothes = parserxml.Parser().parse_clothes()
        self.frn = parserxml.Parser().parse_furniture()
        self.emotes = parserxml.Parser().parse_emotes()
        self.daily = parserxml.Parser().parse_daily_gift()
        self.game_items = parserxml.Parser().parse_game_items()
        for item in const.LIBRARIES:
            library = importlib.import_module(f"libraries.{item}")
            class_ = getattr(library, library.class_name)
            self.lib[class_.prefix] = class_(self)
    
    async def start(self):
        self.redis = await aioredis.create_redis_pool(
            "redis://localhost",
            encoding="utf-8"
        )
        self.server = await asyncio.start_server(
            self.client_on,
            const.HOST, const.PORT
        )
        for lib in self.lib:
            if hasattr(self.lib[lib], "_background"):
                asyncio.create_task(self.lib[lib]._background())
        debug = [self.lib[i].prefix for i in self.lib]
        debug = ",".join(debug)
        self.log(f"[{debug}] ({len(self.lib)}) lib is running...")
        asyncio.create_task(self._background())
        self.log("#Server is started#")
    
    async def client_on(self, reader, writer):
        loop = asyncio.get_event_loop()
        loop.create_task(Client(self).process(reader, writer))
    
    async def process_data(self, msg, client):
        type_ = msg["type"]
        if type_ == 1:
            await self.auth(msg["msg"], client)
        elif type_ == 17 or type_ == 2:
            await client.send({
                'secretKey': None,
                'zoneId': None,
                'user': {'roomIds': [],
                         'name': None,
                         'zoneId': None,
                         'userId': client.uid},
                'userId': client.uid
            }, type_=1)
        elif type_ == 32:
            await self.chat(msg["msg"], client)
        elif type_ == 34:
            prefix = msg["msg"]["command"].split(".")[0]
            if prefix not in self.lib:
                self.log(f"{prefix} library not found")
                return
            return await self.lib[prefix].run_command(self, msg['msg'], client)
    
    async def chat(self, msg, client):
        text = msg["text"]
        if text[0] == "!":
            await self.run_command(text[1:], client)
            return
        apprnc = await client.get_appearance()
        command = {'broadcast': True, 'sender': {'name': f'{apprnc["n"]} ({client.uid})',
                                                 'zoneId': client.room.split("_")[0], 'userId': client.uid},
                   'text': text}
        await self.send_everybody(client.room, command, type_=32)
    
    async def ssm(self, room, text):
        if room in self.room:
            if self.room[room]:
                for uid in self.room[room]:
                    if uid in self.online:
                        await self.online[uid].system_message(text)
    
    async def run_command(self, cmd, client):
        pref = cmd.split()[0]
        r = self.redis
        if pref == "ssm":
            text = cmd.split("ssm")[1]
            await self.ssm(client.room, text)
        elif pref == "lvl":
            level = int(cmd.split()[1])
            if 1 < level < 899:
                await self.update_level(client, level)
    
    async def update_level(self, cli, lvl):
        r = self.redis
        await r.set(f"mob:{cli.uid}:exp", (lvl * (lvl - 1)) * 25)
        await refresh_avatar(self, cli)
        await cli.send({"data": {"lv": lvl}, "command": "q.nwlv"})
    
    async def auth(self, msg, client):
        login = msg["login"]
        uid = await self.redis.get(f"mob:{login}:uid")
        if not uid:
            uid = await self._create_account(login)
        if uid not in self.online:
            await self.redis.set(f"mob:{uid}:lvt", int(time.time()))
            self.online[uid] = client
        if uid not in self.inv:
            self.inv[uid] = inventory.Inventory(self, uid)
            await self.inv[uid]._get_inventory()
        client.uid = uid
        await client.send({'secretKey': login, 'zoneId': msg["zoneId"],
                           'user': {'roomIds': [], 'name': None, 'zoneId': msg["zoneId"], 'userId': uid},
                           'userId': uid}, type_=1)
    
    async def create_account(self, uid, gender):
        redis = self.redis
        await redis.set(f"mob:{uid}:emd", 0)
        await redis.set(f"mob:{uid}:gld", 1000)
        await redis.set(f"mob:{uid}:slvr", 10000)
        await redis.set(f"mob:{uid}:enrg", 100)
        await redis.set(f"mob:{uid}:hrt", 880)
        await redis.set(f"mob:{uid}:exp", 4500)
        await redis.sadd(f"rooms:{uid}", "livingroom")
        await redis.set(f"rooms:{uid}:livingroom:name", "#livingRoom")
        for i in range(1, const.ROOM_COUNT):
            await redis.sadd(f"rooms:{uid}", f"room{i}")
            await redis.set(f"rooms:{uid}:room{i}:name", f"Комната {i}")
        for item in const.room_items:
            await self.add_room_item(item, "livingroom", uid)
            for i in range(1, const.ROOM_COUNT):
                await self.add_room_item(item, f"room{i}", uid)
        await redis.set(f"mob:{uid}:wearing", "casual")
        if gender == 1:
            weared = ["boyShoes8", "boyPants10", "boyShirt14"]
            available = ["boyUnderdress1"]
        else:
            weared = ["girlShoes14", "girlPants9", "girlShirt12"]
            available = ["girlUnderdress1", "girlUnderdress2"]
        available += self.emotes
        inv = self.inv[uid]
        for item in weared + available:
            await inv.add_item(item, "cls")
            if item in weared:
                await inv.change_wearing(item, True)
        await inv.add_item("oct23_Loot_Coin", "lt", 10000)
        await inv.add_item("AvaCoin", "lt", 10000)
    
    async def get_appearance(self, uid):
        apprnc = await self.redis.lrange(f"mob:{uid}:appearance", 0, -1)
        if not apprnc:
            return False
        return {"n": apprnc[0], "g": int(apprnc[1]), "hc": int(apprnc[2]),
                "ec": int(apprnc[3]), "bc": int(apprnc[4]),
                "sc": int(apprnc[5]), "bt": int(apprnc[6]),
                "rg": int(apprnc[7]), "et": int(apprnc[8]),
                "brc": int(apprnc[9]), "ht": int(apprnc[10]),
                "sh": int(apprnc[11]), "ss": int(apprnc[12]),
                "mc": int(apprnc[13]), "brt": int(apprnc[14]),
                "rc": int(apprnc[15]), "shc": int(apprnc[16]),
                "mt": int(apprnc[17])}
    
    async def getGender(self, uid):
        apprnc = await self.get_appearance(uid)
        return "boy" if apprnc["g"] == 1 else "girl"
    
    async def get_room_all(self, uid):
        data = []
        rooms = await self.redis.smembers(f"rooms:{uid}")
        for room in rooms:
            name_room = await self.redis.get(f"rooms:{uid}:{room}:name")
            data.append({"f": await self.get_room_items(uid, room), "w": 13,
                         "id": room, "lev": int(uid), "l": 13, "nm": name_room})
        return data
    
    async def getFurn(self, furn, client):
        for item in await self.get_room(client.room):
            if item["tpid"] + "_" + str(item["lid"]) == furn:
                return item
    
    async def get_room_items(self, uid, room):
        names = []
        pipe = self.redis.pipeline()
        spipe = self.redis.pipeline()
        for name in await self.redis.smembers(f"rooms:{uid}:{room}:items"):
            pipe.lrange(f"rooms:{uid}:{room}:items:{name}", 0, -1)
            spipe.smembers(f"rooms:{uid}:{room}:items:{name}:options")
            names.append(name)
        result = await pipe.execute()
        options = await spipe.execute()
        i = 0
        items = []
        for name in names:
            try:
                name, lid = name.split("_")
            except ValueError:
                lid = name.split("_")[-1]
                name = "_".join(name.split("_")[:-1])
            item = result[i]
            option = options[i]
            try:
                tmp = {"tpid": name, "x": float(item[0]),
                       "y": float(item[1]), "z": float(item[2]),
                       "d": int(item[3]), "lid": int(lid)}
            except IndexError:
                await self.redis.srem(f"rooms:{uid}:{room}:items",
                                      f"{name}_{lid}")
                await self.redis.delete(f"rooms:{uid}:{room}:items:"
                                        f"{name}_{lid}")
                continue
            except ValueError:
                print(name, lid)
            for kek in option:
                item = await self.redis.get(f"rooms:{uid}:{room}:items:"
                                            f"{name}_{lid}:{kek}")
                tmp[kek] = item
            items.append(tmp)
            i += 1
        return items
    
    async def get_room(self, house_room, type_=1):
        if "house" not in house_room:
            return
        owner = house_room.split("_")[1]
        room = house_room.split("_")[2]
        if type_ == 1:
            return await self.get_room_items(owner, room)
        elif type_ == 2:
            uid = owner
            name_room = await self.redis.get(f"rooms:{uid}:{room}:name")
            data = {"f": await self.get_room_items(uid, room), "w": 13,
                    "id": room, "lev": int(uid), "l": 13, "nm": name_room}
            return data
    
    async def add_room_item(self, item, room, uid):
        redis = self.redis
        await redis.sadd(f"rooms:{uid}:{room}:items",
                         f"{item['tpid']}_{item['lid']}")
        if "rid" in item:
            await redis.sadd(f"rooms:{uid}:{room}:items:"
                             f"{item['tpid']}_{item['lid']}:options", "rid")
            if item["rid"]:
                await redis.set(f"rooms:{uid}:{room}:items:"
                                f"{item['tpid']}_{item['lid']}:rid",
                                item["rid"])
        await redis.rpush(f"rooms:{uid}:{room}:items:"
                          f"{item['tpid']}_{item['lid']}", item["x"],
                          item["y"], item["z"], item["d"])
    
    async def get_clothes(self, uid, type_):
        clothes = []
        cur_ctp = await self.redis.get(f"mob:{uid}:wearing")
        for item in await self.redis.smembers(f"mob:{uid}:{cur_ctp}"):
            clothes.append({"id": item, "clid": ""})
        if type_ == 1:
            ctps = ["casual", "club", "official", "swimwear", "underdress"]
            clths = {"cc": cur_ctp, "ccltns": {}}
            clths["ccltns"][cur_ctp] = {"cct": [], "cn": "", "ctp": cur_ctp}
            for item in clothes:
                clths["ccltns"][cur_ctp]["cct"].append(item["id"])
            ctps.remove(cur_ctp)
            for ctp in ctps:
                clths["ccltns"][ctp] = {"cct": [], "cn": "", "ctp": ctp}
                clothes = []
                for item in await self.redis.smembers(f"mob:{uid}:{ctp}"):
                    clothes.append({"id": item, "clid": ""})
                for item in clothes:
                    clths["ccltns"][ctp]["cct"].append(item["id"])
        elif type_ == 2:
            clths = {"clths": []}
            for item in clothes:
                clths["clths"].append({"tpid": item["id"]})
        elif type_ == 3:
            clths = {"cct": [], "cn": "", "ctp": cur_ctp}
            for item in clothes:
                clths["cct"].append(item["id"])
        return clths
    
    async def send_everybody(self, room, msg, type_=34):
        for tmp in self.room[room]:
            await self.online[tmp].send(msg, type_)
    
    async def _create_account(self, login):
        uid = await self.redis.incrby("mob:uids", 1)
        await self.redis.set(f"mob:{login}:uid", uid)
        return str(uid)
    
    def log(self, message):
        log.info(message)
    
    async def _background(self):
        await asyncio.sleep(BACKGROUND_TIME)
    
    async def stop(self):
        return
        self.server.close()
        await self.server.wait_closed()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(Server().start())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.run_until_complete(Server().stop())
    loop.close()
