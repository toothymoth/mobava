from libraries.base_module import Module
from libraries.location import join_room, Location

class_name = "Out"


class Out(Module):
    prefix = "o"
    
    def __init__(self, server):
        super().__init__()
        self.server = server
        self.bind = {"gr": self.get_room, "r": self.room}
    
    async def get_room(self, msg, client):
        room_id = msg['data']['lid'] + "_" + msg['data']['gid'] + "_1"
        await join_room(self.server, room_id, client)
        await client.send({"data": {"rid": room_id}, "command": "o.gr"})
        
    async def room(self, msg, client):
        await Location(self.server).room(msg, client)
        