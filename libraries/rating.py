import asyncio
import operator
from libraries.base_module import Module

class_name = "Rating"

BACKGROUND_TIME = 300


class Rating(Module):
    prefix = 'ur'
    
    def __init__(self, server):
        super().__init__()
        self.server = server
        self.rating = []
        self.bind = {}
    
    async def get_rating(self):
        r = self.server.redis
        players = {}
        for uid in range(1, await r.incrby(f"mob:uids", 0) + 1):
            rtg = int(await r.get(f"mob:{uid}:crt") or 0)
            if not rtg:
                continue
            players[uid] = rtg
        await self.slice_top(players)
    
    async def slice_top(self, uids: dict, count: int = 3):
        rating = sorted(uids.items(), key=operator.itemgetter(1),
                        reverse=True)
        best_top = []
        i = 1
        for user in rating:
            best_top.append(str(user[0]))
            if i == count:
                break
            i += 1
        self.rating = best_top
    
    async def _background(self):
        while True:
            await self.get_rating()
            await asyncio.sleep(BACKGROUND_TIME)
