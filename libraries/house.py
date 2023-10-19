import time

from libraries.base_module import Module
from libraries.location import join_room, gen_plr
from libraries.location import Location

class_name = "House"


class House(Module):
    prefix = "h"
    
    def __init__(self, server):
        super().__init__()
        self.server = server
        self.bind = {"minfo": self.my_info, "gr": self.get_room, "r": self.room}
        
    async def my_info(self, msg, client):
        if not await client.get_appearance():
            return await client.send({
                'data': {'has.avtr': False},
                'command': 'h.minfo'})
        if "onl" in msg["data"]:
            if msg["data"]["onl"]:
               return await client.send({'data': {'scs': True, 'politic': 'default'}, 'command': 'h.minfo'})
        plr = await gen_plr(self.server, client.uid)
        inv = self.server.inv[client.uid].get()
        wear = await self.server.get_clothes(client.uid, type_=1)
        rooms = {'r': await self.server.get_room_all(client.uid), 'lt': 0}
        clths = await self.server.get_clothes(client.uid, type_=2)
        await self.server.lib["tr"].bind["dr"]({}, client)
        return await client.send({
            'data': {'bklst': {'uids': []},
                     'politic': 'default',
                     'plr': {'locinfo': plr['locinfo'],
                             'res': plr['res'], 'apprnc': await client.get_appearance(),
                             'ci': plr['ci'], 'hs': rooms,
                             'onl': True, 'achc': {'ac': {}}, 'cs': wear,
                             'inv': inv, 'uid': client.uid, 'qc': {'q': []}, 'wi': {'wss': []},
                             'clths': clths, 'usrinf': plr['usrinf']}, 'tm': int(time.time())},
            'command': 'h.minfo'})
    
    async def get_room(self, msg, client):
        room_id = "_".join([msg["data"]["lid"], msg["data"]["gid"], msg["data"]["rid"]])
        await client.send({'data': {'rid': room_id}, 'command': 'h.gr'})
        if msg["data"]["gid"] == client.uid:
            await client.send({'data': {'ath': True}, 'command': 'h.oah'})
        await join_room(self.server, room_id, client)
        
    async def room(self, msg, client):
        await Location(self.server).room(msg, client)
    
        
