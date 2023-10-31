import asyncio
import time
from libraries.base_module import Module

class_name = "EVENT"

BACKGROUND_TIME = 60


class EVENT(Module):
    prefix = 'ev'
    
    def __init__(self, server):
        super().__init__()
        self.server = server
        self.events = {}
        self.bind = {"crt": self.create, "cse": self.close, "get": self.get, "gse": self.my_event}
    
    async def create(self, msg, client):
        event = msg["data"]["ev"]
        event["uid"] = client.uid
        apprnc = await client.get_appearance()
        nick = apprnc["n"]
        event["unm"] = nick
        event["id"] = int(client.uid)
        event["st"] = int(time.time())
        event["ft"] = int(time.time()) + (event["lg"] * 60)
        self.events[client.uid] = event
        await client.send(msg)
        
    async def close(self, msg, client):
        if client.uid not in self.events:
            return
        del self.events[client.uid]
        await client.send(msg)
        
    async def get(self, msg, client):
        cat = msg["data"]["c"]
        events = [ev for ev in self.events.values() if (ev["c"] == cat or cat == -1)]
        msg["data"]["evlst"] = events
        await client.send(msg)
        
    async def my_event(self, msg, client):
        if client.uid in self.events:
            msg["data"]["ev"] = self.events[client.uid]
            await client.send(msg)
    
    async def _background(self):
        while True:
            for ev in self.events:
                if self.events[ev]["ft"] - int(time.time()) <= 0:
                    del self.events[ev]
            await asyncio.sleep(BACKGROUND_TIME)
