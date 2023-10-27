from libraries.base_module import Module
from libraries.location import gen_plr

class_name = "Player"


class Player(Module):
    prefix = "pl"
    
    def __init__(self, server):
        self.server = server
        self.bind = {"flw": self.follow}
    
    async def follow(self, msg, client):
        uid = msg["data"]["uid"]
        info = await gen_plr(self.server, uid)
        online = "userOffline"
        if str(uid) in self.server.online:
            online = "success"
        await client.send({"command": "pl.flw", "data": {"locinfo": info["locinfo"], "scs": online}})
