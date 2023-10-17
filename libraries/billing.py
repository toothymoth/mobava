from libraries.base_module import Module
from libraries.location import gen_plr

class_name = "Bill"


class Bill(Module):
    prefix = "b"
    
    def __init__(self, server):
        super().__init__()
        self.server = server
        self.bind = {"bs": self.buy_silver}
        
    async def buy_silver(self, msg, client):
        plr = await gen_plr(self.server, client.uid)
        if await self.server.redis.decrby(f"mob:{client.uid}:gld", msg['data']['gld']) < 0:
            await self.server.redis.set(f"mob:{client.uid}:gld", 0)
            return
        await self.server.redis.incrby(f"mob:{client.uid}:slvr", msg['data']['gld'] * 100)
        await self.update_res(client)
        return await client.send({'data': {
            'slvr': plr['res']['slvr'] + msg['data']['gld'] * 100,
            'inslv': msg['data']['gld'] * 100
        }, 'command': 'b.inslv'
        })
    
    async def update_res(self, client):
        plr = await gen_plr(self.server, client.uid)
        return await client.send({
            'data': {'res': plr['res']},
            'command': 'ntf.res'
        })