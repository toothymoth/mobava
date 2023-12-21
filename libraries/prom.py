from libraries.base_module import Module

class_name = "Prom"


class Prom(Module):
    prefix = "pc"
    
    def __init__(self, server):
        super().__init__()
        self.server = server
        self.proms = {"test": {'promo_hellrabbit': 1, 'oct23_Loot_Coin': 666,
                               'hlwn19_balloons': 1, 'GraffitiVampire': 5}}
        self.bind = {"ac": self.accept}
    
    async def accept(self, msg, client):
        pcid = msg["data"]["pc.id"]
        if pcid not in self.proms:
            return await client.send({"data": {"err": 0}, "command": "pc.er"})
        if await self.server.redis.get(f"mob:{client.uid}:prm:{pcid}"):
            return await client.send({"data": {"err": 3}, "command": "pc.er"})
        items = self.proms[pcid]
        inv = self.server.inv[client.uid]
        await self.server.redis.set(f"mob:{client.uid}:prm:{pcid}", 1)
        for item in items:
            count = int(items[item] or 1)
            for cat in self.server.game_items:
                if item in self.server.game_items[cat]:
                    type_ = "gm"
                    break
            if item in self.server.frn:
                type_ = "frn"
            elif item in self.server.clothes[await self.server.getGender(client.uid)]:
                type_ = "cls"
            else:
                type_ = "lt"
            await inv.add_item(item, type_, count)
        await client.update_inv()
        await client.send({'data': {"items": items},
                          'command': 'pc.ac'})
