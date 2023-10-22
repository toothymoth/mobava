from libraries.base_module import Module
from libraries.location import city_info

class_name = "Furn"


class Furn(Module):
    prefix = "frn"
    
    def __init__(self, server):
        super().__init__()
        self.server = server
        self.bind = {"buy": self.buy, "save": self.save_room}
        
    async def buy(self, msg, client):
        item = msg["data"]["tpid"]
        type_ = "frn" if item in self.server.frn else "gm"
        await self.server.inv[client.uid].add_item(item, type_)
        await client.update_inv()
        await client.send(msg)
        
    def getOwner(self, room, uid):
        return room.split("_")[1] == str(uid)
    
    async def add_furn(self, item, client):
        redis = self.server.redis
        uid = client.uid
        room = client.room.split("_")[2]
        item['oid'] = item["lid"]
        await redis.sadd(f"rooms:{uid}:{room}:items",
                         f"{item['tpid']}_{item['oid']}")
        if "rid" in item:
            await redis.sadd(f"rooms:{uid}:{room}:items:"
                             f"{item['tpid']}_{item['oid']}:options", "rid")
            if item["rid"]:
                await redis.set(f"rooms:{uid}:{room}:items:"
                                f"{item['tpid']}_{item['oid']}:rid",
                                item["rid"])
        await redis.rpush(f"rooms:{uid}:{room}:items:"
                          f"{item['tpid']}_{item['oid']}", item["x"],
                          item["y"], item["z"], item["d"])

    async def del_furn(self, name, client):
        redis = self.server.redis
        uid = client.uid
        room = client.room.split("_")[2]
        items = await redis.smembers(f"rooms:{uid}:{room}:items")
        try:
            item = f"{name['tpid']}_{name['lid']}"
        except KeyError:
            item = f"{name['tpid']}_{name['oid']}"
        except TypeError:
            return
        if item not in items:
            return
        options = await redis.smembers(f"rooms:{uid}:{room}:items:{item}"
                                       ":options")
        for op in options:
            await redis.delete(f"rooms:{uid}:{room}:items:{item}:{op}")
        await redis.delete(f"rooms:{uid}:{room}:items:{item}:options")
        await redis.srem(f"rooms:{uid}:{room}:items", item)
        await redis.delete(f"rooms:{uid}:{room}:items:{item}")

    async def type_add(self, item, client):
        room = client.room.split("_")
        redis = self.server.redis
        uid = client.uid
        inv = self.server.inv[uid]
        await inv.take_item(item["tpid"])
        items = await redis.smembers(f"rooms:{uid}:{room[2]}:items")
        if any(ext in item["tpid"].lower() for ext in ["wll", "wall"]):
            walls = []
            for wall in ["wall", "wll"]:
                for room_item in items:
                    if wall in room_item.lower():
                        furn = await self.server.getFurn(room_item, client)
                        await self.del_furn(furn, client)
                        if room_item not in walls:
                            walls.append(room_item)
                        if len(walls) == 1:
                            await inv.add_item("_".join(room_item.split("_")[:-1]), "frn")
                            add_comfort = self.server.frn["_".join(room_item.split("_")[:-1])]["rating"]
                            await self.server.redis.decrby(f"mob:{client.uid}:hrt", int(add_comfort or 0))
            if 'oid' in item:
                item['lid'] = item['oid']
                del item['oid']
            item["x"] = 0.0
            item["y"] = 0.0
            item["z"] = 0.0
            item["d"] = 3
            await self.add_furn(item, client)
            item["x"] = 13.0
            item["d"] = 5
            if 'lid' in item:
                item["lid"] += 1
            await self.add_furn(item, client)
            add_comfort = self.server.frn[item["tpid"]]["rating"]
            await self.server.redis.incrby(f"mob:{client.uid}:hrt", int(add_comfort or 0))
        elif any(ext in item["tpid"].lower() for ext in ["flr", "floor"]):
            for floor in ["flr", "floor"]:
                for room_item in items:
                    if floor in room_item.lower():
                        furn = await self.server.getFurn(room_item,client)
                        await self.del_furn(furn, client)
                        await inv.add_item("_".join(room_item.split("_")[:-1]), "frn")
                        add_comfort = self.server.frn["_".join(room_item.split("_")[:-1])]["rating"]
                        await self.server.redis.decrby(f"mob:{client.uid}:hrt", int(add_comfort or 0))
            item["x"] = 0.0
            item["y"] = 0.0
            item["z"] = 0.0
            item["d"] = 5
            if 'oid' in item:
                item['lid'] = item['oid']
                del item['oid']
            await self.add_furn(item, client)
            add_comfort = self.server.frn[item["tpid"]]["rating"]
            await self.server.redis.incrby(f"mob:{client.uid}:hrt", int(add_comfort or 0))

    async def replace_door(self, item, client):
        uid = client.uid
        room = client.room.split("_")
        redis = self.server.redis
        inv = self.server.inv[uid]
        items = await redis.smembers(f"rooms:{uid}:{room[2]}:items")
        found = None
        for tmp in items:
            oid = int(tmp.split("_")[-1])
            if oid == item["oid"]:
                found = tmp
                break
        if not found:
            return
        await inv.take_item(item["tpid"])
        data = await redis.lrange(f"rooms:{uid}:{room[2]}:items:{found}",
                                  0, -1)
        options = await redis.smembers(f"rooms:{uid}:{room[2]}:items:{found}:"
                                       "options")
        if "rid" in options:
            rid = await redis.get(f"rooms:{uid}:{room[2]}:items:{found}:rid")
        else:
            return
        furn = await self.server.getFurn(found, client)
        await self.del_furn(furn, client)
        await inv.add_item("_".join(found.split("_")[:-1]), "frn")
        if "oid" in item:
            item['lid'] = item['oid']
            del item['oid']
        item.update({"x": float(data[0]), "y": float(data[1]),
                     "z": float(data[2]), "d": int(data[3]),
                     "rid": rid})
        await self.add_furn(item, client)
        
    async def save_room(self, msg, client):
        if not self.getOwner(client.room, client.uid):
            return
        new_room = msg["data"]["f"]
        for furn in new_room:
            type_ = furn["t"]
            if type_ == 0:
                await self.type_add(furn, client)
            elif type_ == 1:
                isNew = True
                for olditem in await self.server.get_room(client.room):
                    if olditem["tpid"] + str(olditem["lid"]) == furn["tpid"] + str(furn["oid"]):
                        isNew = False
                        break
                if not await self.server.inv[client.uid].take_item(furn["tpid"]) and isNew:
                    return
                if not isNew:
                    await self.del_furn(furn, client)
                else:
                    add_comfort = self.server.frn[furn["tpid"]]["rating"]
                    await self.server.redis.incrby(f"mob:{client.uid}:hrt", int(add_comfort or 0))
                await self.add_furn(furn, client)
            elif type_ == 2:
                add_comfort = self.server.frn[furn["tpid"]]["rating"]
                await self.server.redis.decrby(f"mob:{client.uid}:hrt", int(add_comfort or 0))
                await self.server.inv[client.uid].add_item(furn["tpid"], "frn")
                await self.del_furn(furn, client)
            elif type_ == 3:
                await self.replace_door(furn, client)
        room_items = {'r': await self.server.get_room(client.room), 'lt': 0}
        cityInfo = await city_info(self.server, client.uid)
        await client.update_inv()
        return await client.send({
            'data': {'ci': cityInfo, 'hs': room_items},
            'command': 'frn.save'
        })
