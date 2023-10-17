
class Inventory():
    def __init__(self, server, uid):
        self.server = server
        self.uid = uid
        self.expire = 0

    def get(self):
        return self.inv

    async def add_item(self, name, type_, amount=1):
        if "_" in name:
            tid, iid = name.split("_")
        else:
            tid = name
            iid = ""
        redis = self.server.redis
        item = await redis.lrange(f"mob:{self.uid}:items:{name}", 0, -1)
        if item:
            if type_ == "cls":
                return
            await redis.lset(f"mob:{self.uid}:items:{name}", 1,
                             int(item[1])+amount)
            for tmp in self.inv["c"][type_]["it"]:
                if tmp["tid"] == tid and tmp["iid"] == iid:
                    tmp["c"] = int(item[1])+amount
                    break
        else:
            await redis.sadd(f"mob:{self.uid}:items", name)
            await redis.rpush(f"mob:{self.uid}:items:{name}", type_, amount)
            type_items = self.inv["c"][type_]["it"]
            type_items.append({"c": amount, "tid": tid, "iid": iid})

    async def take_item(self, item, amount=1):
        redis = self.server.redis
        items = await redis.smembers(f"mob:{self.uid}:items")
        if item not in items:
            return False
        tmp = await redis.lrange(f"mob:{self.uid}:items:{item}", 0, -1)
        if not tmp:
            await redis.srem(f"mob:{self.uid}:items", item)
            return False
        type_ = tmp[0]
        have = int(tmp[1])
        del tmp
        if have < amount:
            return False
        type_items = self.inv["c"][type_]["it"]
        if have > amount:
            await redis.lset(f"mob:{self.uid}:items:{item}", 1, have - amount)
            for tmp in type_items:
                if tmp["tid"] == item:
                    tmp["c"] = have - amount
                    break
        else:
            await redis.delete(f"mob:{self.uid}:items:{item}")
            await redis.srem(f"mob:{self.uid}:items", item)
            for tmp in type_items:
                if tmp["tid"] == item:
                    type_items.remove(tmp)
                    break
        return True

    async def get_item(self, item):
        redis = self.server.redis
        items = await redis.smembers(f"mob:{self.uid}:items")
        if item not in items:
            return 0
        have = int(await redis.lindex(f"mob:{self.uid}:items:{item}", 1))
        return have

    async def change_wearing(self, cloth, wearing):
        redis = self.server.redis
        if not await redis.lindex(f"mob:{self.uid}:items:{cloth}", 0):
            not_found = True
        else:
            not_found = False
        if "_" in cloth:
            tid, iid = cloth.split("_")
        else:
            tid = cloth
            iid = ""
        type_items = self.inv["c"]["cls"]["it"]
        ctp = await redis.get(f"mob:{self.uid}:wearing")
        await self.setclothes(tid)
        if wearing:
            if not_found:
                self.server.log(f"Cloth {cloth} not found for {self.uid}")
                return
            for item in type_items:
                if item["tid"] == tid and item["iid"] == iid:
                    type_items.remove(item)
                    break
            await redis.sadd(f"mob:{self.uid}:{ctp}", cloth)
        else:
            weared = await redis.smembers(f"mob:{self.uid}:{ctp}")
            if cloth not in weared:
                self.server.log(f"Cloth {cloth} not weared for {self.uid}")
                return
            if not not_found:
                type_items.append({"c": 1, "iid": iid, "tid": tid})
            await redis.srem(f"mob:{self.uid}:{ctp}", cloth)
            
    async def setclothes(self, newcloth):
        redis = self.server.redis
        clothes = self.server.clothes
        ignore = ["boyUnderdress1"] + ["girlUnderdress1", "girlUnderdress2"]
        gender = await self.server.getGender(self.uid)
        ctp = await redis.get(f"mob:{self.uid}:wearing")
        type_items = self.inv["c"]["cls"]["it"]
        for cloth in await redis.smembers(f"mob:{self.uid}:{ctp}"):
            if cloth in ignore:
                continue
            if clothes[gender][cloth]["category"] == clothes[gender][newcloth]["category"]:
                await redis.srem(f"mob:{self.uid}:{ctp}", cloth)
                if "_" in cloth:
                    iid = cloth.split("_")[1]
                    tid = cloth.split("_")[0]
                else:
                    iid = ""
                    tid = cloth
                type_items.append({"c": 1, "iid": iid, "tid": tid})

    def __get_expire(self):
        return self.__expire

    def __set_expire(self, value):
        self.__expire = value

    expire = property(__get_expire, __set_expire)

    async def _get_inventory(self):
        self.inv = {"c": {"frn": {"id": "frn", "it": []},
                          "act": {"id": "act", "it": []},
                          "gm": {"id": "gm", "it": []},
                          "lt": {"id": "lt", "it": []},
                          "cls": {"id": "cls", "it": []}}}
        ctp = await self.server.redis.get(f"mob:{self.uid}:wearing")
        wearing = await self.server.redis.smembers(f"mob:{self.uid}:{ctp}")
        keys = []
        pipe = self.server.redis.pipeline()
        for item in await self.server.redis.smembers(f"mob:{self.uid}:items"):
            if item in wearing:
                continue
            pipe.lrange(f"mob:{self.uid}:items:{item}", 0, -1)
            keys.append(item)
        items = await pipe.execute()
        for i in range(len(keys)):
            name = keys[i]
            item = items[i]
            if not item:
                continue
            if "_" in name:
                self.inv["c"][item[0]]["it"].append({"c": int(item[1]),
                                                     "iid": name.split("_")[1],
                                                     "tid": name.split("_")[0]}
                                                    )
            else:
                try:
                    self.inv["c"][item[0]]["it"].append({"c": int(item[1]),
                                                         "iid": "",
                                                         "tid": name})
                except IndexError:
                    r = self.server.redis
                    await r.srem(f"mob:{self.uid}:items", name)
                    await r.delete(f"mob:{self.uid}:items:{name}")
