from libraries.base_module import Module

class_name = "Pass"


class Pass(Module):
    prefix = "psp"
    
    def __init__(self, server):
        super().__init__()
        self.server = server
        self.bind = {"psp": self.passport}
    
    async def passport(self, msg, client):
        await client.send({
            'data': {'psp': {'uid': msg['data']['uid'],
                             'ach': {'ac': {}}, 'rel': {}}},
            'command': 'psp.psp'
        })
