from libraries.base_module import Module

class_name = "HS"


class HS(Module):
    prefix = 'hs'
    
    def __init__(self, server):
        super().__init__()
        self.server = server
        self.bind = {"ac": self.action}
    
    async def action(self, msg, client):
        act = msg["data"]["act"]
        room = client.room.split("_")
        owner = room[1]
        oid = int(msg["data"]["oid"])
        if not owner.isdigit():
            return
        r = self.server.redis
        items = f"rooms:{owner}:{room[2]}:items"
        furn = None
        for item in await r.smembers(items):
            if int(item.split("_")[-1]) == oid:
                furn = item
        if not furn:
            return
        furnModel = f"rooms:{owner}:{room[2]}:items:{furn}:"
        if act == "broke":
            await r.sadd(furnModel+"options", "bid")
            await r.set(furnModel + "bid", client.uid)
        elif act == "chgCh":
            channel = msg["data"]["tid"]["cnl"]
            if 'tvpch' in channel:
                await r.sadd(furnModel+"options", "ch")
                await r.set(furnModel+"ch", channel)
            elif "mch" in channel:
                await r.sadd(furnModel+"options", "tr")
                await r.set(furnModel + "tr", channel)
            await r.sadd(furnModel+"options", "st")
            await r.set(furnModel + "st", 1)
        elif act == "turnOn":
            await r.sadd(furnModel+"options", "st")
            await r.set(furnModel + "st", 1)
        elif act == "turnOff":
            await r.srem(furnModel+"options", "st")
            await r.delete(furnModel + "st")
            await r.srem(furnModel + "options", "tr")
            await r.delete(furnModel + "tr")
        await self.server.send_everybody(client.room, msg)
        await self.update_room(client.room)
        
    async def update_room(self, room):
        room_items = await self.server.get_room(room, 2)
        await self.server.send_everybody(room, {
            'data': {'rm': room_items},
            'command': 'h.r.rfr'
        })
