from libraries.base_module import Module

class_name = "Client"


class Client(Module):
    prefix = "cl"
    
    def __init__(self, server):
        super().__init__()
        self.server = server
        self.bind = {"st": self.set, "es": self.etags}
        
    async def set(self, msg, client):
        await client.send({'data': {'cs': {'jr': {}, 'ir': {}, 'cid': msg["data"]["cid"]}}, 'command': 'cl.st'})
        
    async def etags(self, msg, client):
        await client.send({'data': {'c': [], 'clid': msg["data"]["clid"]}, 'command': 'cl.es'})
        await client.send({'data': {'d': []}, 'command': 'cl.hre'})