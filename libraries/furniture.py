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
        item = f"{name['tpid']}_{name['oid']}"
        if item not in items:
            return
        options = await redis.smembers(f"rooms:{uid}:{room}:items:{item}"
                                       ":options")
        for op in options:
            await redis.delete(f"rooms:{uid}:{room}:items:{item}:{op}")
        await redis.delete(f"rooms:{uid}:{room}:items:{item}:options")
        await redis.srem(f"rooms:{uid}:{room}:items", item)
        await redis.delete(f"rooms:{uid}:{room}:items:{item}")
        
    async def save_room(self, msg, client):
        if not self.getOwner(client.room, client.uid):
            return
        new_room = msg["data"]["f"]
        for furn in new_room:
            type_ = furn["t"]
            if type_ == 0:
                ...
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
        room_items = {'r': await self.server.get_room(client.room), 'lt': 0}
        cityInfo = await city_info(self.server, client.uid)
        await client.update_inv()
        return await client.send({
            'data': {'ci': cityInfo, 'hs': room_items},
            'command': 'frn.save'
        })
