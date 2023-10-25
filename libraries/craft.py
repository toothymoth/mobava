from libraries.base_module import Module

class_name = "Craft"


class Craft(Module):
    prefix = "crt"
    
    def __init__(self, server):
        super().__init__()
        self.server = server
        self.bind = {"prd": self.product}
    
    async def product(self, msg, client):
        item = msg["data"]["itId"]
        count = msg["data"]["itCnt"]
        if item in self.server.clothes[await self.server.getGender(client.uid)]:
            await self.server.lib["a"].bind["clths"]({"data": {"tpid": item}, "command": "a.clths.buy"}, client)
        elif item in self.server.frn:
            inv = self.server.inv[client.uid]
            await inv.add_item(item, "frn", count)
            await client.update_inv()
        await client.send(msg)
