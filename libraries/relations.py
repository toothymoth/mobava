import time
from libraries.base_module import Module
from libraries.location import refresh_avatar

class_name = "Relations"


class Relations(Module):
    prefix = "rl"
    
    def __init__(self, server):
        self.server = server
        self.bind = {"get": self.get_relations,
                         "rmv": self.remove_relation,
                         "crs": self.change_relation_status,
                         "urp": self.add_progress}
        self.statuses = self.server.parser.parse_relations()
        self.progresses = self.server.parser.parse_relation_progresses()
    
    async def get_relations(self, msg, client):
        data = {"command": "rl.get", "data": {"uid": client.uid, "rlts": {}}}
        relations = await self.server.redis.smembers(f"rl:{client.uid}")
        for rl in relations:
            relation = await self._get_relation(client.uid, rl)
            data["data"]["rlts"][relation["uid"]] = relation["rlt"]
        await client.send(data)
    
    async def remove_relation(self, msg, client):
        uid = msg["data"]["uid"]
        if uid == client.uid:
            return
        link = None
        for rl in await self.server.redis.smembers(f"rl:{client.uid}"):
            if uid in rl:
                link = rl
                break
        if not link:
            return
        await self._remove_relation(link)
    
    async def change_relation_status(self, msg, client):
        relation = msg["data"]
        link = await self.get_link(client.uid, relation["uid"])
        if not link:
            confirms = self.server.lib["cf"].confirms
            if client.uid in confirms and \
                    not confirms[client.uid]["completed"] and int(relation["s"]) != 0:
                return
            await self._create_relation(f"{client.uid}:{relation['uid']}",
                                        relation)
            if client.uid in confirms:
                del confirms[client.uid]
        else:
            await self._update_relation(link, relation)
    
    async def _create_relation(self, link, relation):
        pipe = self.server.redis.pipeline()
        for uid in link.split(":"):
            pipe.sadd(f"rl:{uid}", link)
        pipe.set(f"rl:{link}:p", 0)
        pipe.set(f"rl:{link}:st", int(time.time()))
        pipe.set(f"rl:{link}:ut", int(time.time()))
        pipe.set(f"rl:{link}:s", relation["s"])
        await pipe.execute()
        for uid in link.split(":"):
            rl = await self._get_relation(uid, link)
            if uid in self.server.online:
                tmp = self.server.online[uid]
                await refresh_avatar(self.server, tmp)
                await tmp.send({"command": "rl.new", "data": rl})
    
    async def _update_relation(self, link, relation):
        pipe = self.server.redis.pipeline()
        pipe.set(f"rl:{link}:p", 0)
        pipe.set(f"rl:{link}:st", int(time.time()))
        pipe.set(f"rl:{link}:ut", int(time.time()))
        pipe.set(f"rl:{link}:s", relation["s"])
        await pipe.execute()
        for uid in link.split(":"):
            rl = await self._get_relation(uid, link)
            if uid in self.server.online:
                tmp = self.server.online[uid]
                await refresh_avatar(self.server, tmp)
                await tmp.send({"command": "rl.crs", "data": rl})
    
    async def _remove_relation(self, link):
        pipe = self.server.redis.pipeline()
        pipe.delete(f"rl:{link}:p")
        pipe.delete(f"rl:{link}:st")
        pipe.delete(f"rl:{link}:ut")
        pipe.delete(f"rl:{link}:s")
        pipe.delete(f"rl:{link}:t")
        for uid in link.split(":"):
            pipe.srem(f"rl:{uid}", link)
        await pipe.execute()
        for uid in link.split(":"):
            if link.split(":")[0] == uid:
                second_uid = link.split(":")[1]
            else:
                second_uid = link.split(":")[0]
            if uid in self.server.online:
                tmp = self.server.online[uid]
                await refresh_avatar(self.server, tmp)
                await tmp.send({"command": "rl.rmv","data": {"uid": second_uid}})
    
    async def add_progress(self, action, link):
        value = self.progresses[action]
        s = int(await self.server.redis.get(f"rl:{link}:s"))
        p = int(await self.server.redis.get(f"rl:{link}:p"))
        if s == 50:
            return
        if 100 in self.statuses[s]["progress"]:
            max_value = 100
        else:
            max_value = 0
        if -100 in self.statuses[s]["progress"]:
            min_value = -100
        else:
            min_value = 0
        total = p + value
        if total >= max_value:
            total = 100
        elif min_value < min_value:
            total = -100
        if total in self.statuses[s]["progress"]:
            await self.server.redis.set(f"rl:{link}:p", 0)
            await self.server.redis.set(f"rl:{link}:s",
                                        self.statuses[s]["progress"][total])
            command = "rl.crs"
        else:
            await self.server.redis.set(f"rl:{link}:p", total)
            command = "rl.urp"
        for uid in link.split(":"):
            rl = await self._get_relation(uid, link)
            rl["chprr"] = action
            if uid in self.server.online:
                tmp = self.server.online[uid]
                if command == "rl.crs":
                    await refresh_avatar(self.server, tmp)
                await tmp.send({"command": command, "data": rl})
    
    async def get_link(self, uid1, uid2):
        rlts = await self.server.redis.smembers(f"rl:{uid1}")
        if f"{uid1}:{uid2}" in rlts:
            return f"{uid1}:{uid2}"
        elif f"{uid2}:{uid1}" in rlts:
            return f"{uid2}:{uid1}"
        else:
            return None
    
    async def _get_relation(self, uid, link):
        if link.split(":")[0] == uid:
            second_uid = link.split(":")[1]
        else:
            second_uid = link.split(":")[0]
        pipe = self.server.redis.pipeline()
        for item in ["p", "st", "ut", "s"]:
            pipe.get(f"rl:{link}:{item}")
        result = await pipe.execute()
        try:
            rl = {"uid": second_uid, "rlt": {"p": int(result[0]),
                                             "st": int(result[1]),
                                             "ut": int(result[2]),
                                             "s": int(result[3]),
                                             "t": None}}
        except TypeError:
            await self.server.redis.srem(f"rl:{uid}", link)
            return
        return rl
