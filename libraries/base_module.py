import traceback
class Module():
    def __init__(self):
        self.bind = {}
    
    async def run_command(self, server, msg, client):
        cmd = msg["command"].split(".")[1]
        if cmd not in self.bind:
            await client.system_message(f"Command {cmd} not found")
            return
        try:
            await self.bind[cmd](msg, client)
        except Exception as ex:
            server.log(traceback.format_exc())
            await client.system_message(f"Command {ex} got error")
