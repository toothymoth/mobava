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
        if daily[day]["type"] == "rs":
            await r.incrby(f"mob:{client.uid}:{_removeVowels(daily[day]['item'])}", daily[day]['count'])
        elif daily[day]["type"] == "gm":
            await inv.add_item(daily[day]['item'], "gm", daily[day]['count'])
        else:
            return
        await client.update_inv()
        await client.update_res()
        await client.send({
            'data': {'day': day},
            'command': 'tr.dr'
        })


def _removeVowels(string):
    vowels = ["e", "y", "u", "i", "o", "a"]
    new_string = string
    for i in vowels:
        new_string = new_string.lower().replace(i, "")
    return new_string
