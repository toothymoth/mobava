import time

from libraries.base_module import Module

class_name = "Inv"


class Inv(Module):
    prefix = "tr"
    
    def __init__(self, server):
        super().__init__()
        self.server = server
        self.bind = {"dr": self.dailyGift}
    
    async def dailyGift(self, msg, client):
        r = self.server.redis
        dailyModel = f"mob:{client.uid}:daily:"
        daily = self.server.daily
        oldGiving = int(await r.get(dailyModel + "now") or 0)
        day = int(await r.get(dailyModel + "day") or 1)
        if not oldGiving:
            await r.set(dailyModel + "day", 1)
            await r.set(dailyModel + "now", int(time.time()))
        else:
            if int(time.time()) - oldGiving >= 12 * 60 * 60:
                if day+1 == 30:
                    await r.set(dailyModel + "day", 1)
                else:
                    await r.incrby(dailyModel + "day", 1)
                await r.set(dailyModel + "now", int(time.time()))
            else:
                return
        inv = self.server.inv[client.uid]
        type_ = daily[day]["type"]
        count = daily[day]['count']
        item = daily[day]["item"]
        if type_ == "currency":
            typeCurr = item
            if typeCurr == "gold":
                typeCurr = "gld"
            elif typeCurr == "silver":
                typeCurr = "slvr"
            await r.incrby(f"mob:{client.uid}:{typeCurr}", count)
        elif type_ in ["graffity", "joke"]:
            await inv.add_item(item, "gm", count)
        elif type_ == "energyItem":
            await inv.add_item(item, "act", count)
        elif type_ == "furinture":
            await inv.add_item(item, "frn", count)
        elif type_ == "clothes":
            gender = await self.server.getGender(client.uid)
            if item in self.server.clothes[gender]:
                await inv.add_item(item, "cls", count)
        else:
            return
        await client.update_inv()
        await client.update_res()
        await client.send({
            'data': {'day': day},
            'command': 'tr.dr'
        })
