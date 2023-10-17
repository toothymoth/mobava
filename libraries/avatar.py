from libraries.base_module import Module

class_name = "Avatar"


class Avatar(Module):
    prefix = "a"
    
    def __init__(self, server):
        self.server = server
        self.bind = {"apprnc": self.appearance, "clths": self.clothes}
    
    async def appearance(self, msg, client):
        subcmd = msg["command"].split(".")[-1];
        r = self.server.redis;
        if (subcmd == "chn"):
            name = msg["data"]["unm"];
            if (2 < len(name) < 20):
                if (await client.get_appearance()):
                    await r.lset(f"mob:{client.uid}:appearance", 0, name);
                await client.send({'data': {'unm': name}, 'command': 'a.apprnc.rnn'});
        elif (subcmd == "save"):
            oldavatar = await client.get_appearance()
            await self.update_appearance(msg["data"]["apprnc"], client.uid);
            if not oldavatar:
                await self.server.create_account(client.uid, msg["data"]["apprnc"]["g"])
            await client.send({'data': {
                'apprnc': await client.get_appearance()},
                'command': 'a.apprnc.save'});
            
    async def update_appearance(self, apprnc, uid):
        r = self.server.redis;
        if (len(apprnc["n"]) > 20 or len(apprnc["n"]) <= 2):
            return
        await r.delete(f"mob:{uid}:appearance");
        await r.rpush(f"mob:{uid}:appearance", apprnc["n"],
                      apprnc["g"], apprnc["hc"], apprnc["ec"],
                      apprnc["bc"], apprnc["sc"], apprnc["bt"],
                      apprnc["rg"], apprnc["et"], apprnc["brc"],
                      apprnc["ht"], apprnc["sh"], apprnc["ss"],
                      apprnc["mc"], apprnc["brt"], apprnc["rc"],
                      apprnc["shc"], apprnc["mt"]);
        
    async def clothes(self, msg, client):
        subcmd = msg["command"].split(".")[-1]
        if subcmd == "buy":
            inv = self.server.inv[client.uid]
            await inv.add_item(msg["data"]["tpid"], "cls")
            await inv.change_wearing(msg["data"]["tpid"], True)
            clths = await self.server.get_clothes(client.uid, type_=2)
            ccltn = await self.server.get_clothes(client.uid, type_=3)
            rating = await self.update_rating(client, msg["data"]["tpid"])
            await client.send({
                'data': {'inv': inv.get(), 'clths': clths, 'ccltn': ccltn, 'crt': rating},
                'command': msg["command"]})
        elif subcmd == "wear":
            inv = self.server.inv[client.uid]
            clths = await self.server.get_clothes(client.uid, type_=2)
            for clth in clths["clths"]:
                await inv.change_wearing(clth["tpid"], False)
            for clth in msg["data"]["clths"]:
                await inv.change_wearing(clth["tpid"], True)
            
    async def update_rating(self, client, item):
        apprnc = await client.get_appearance()
        gender = "boy" if apprnc["g"] == 1 else "girl"
        rating = int(self.server.clothes[gender][item]["rating"])
        return await self.server.redis.incrby(f"mob:{client.uid}:crt", rating)
