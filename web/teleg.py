import asyncio
import functools
import nest_asyncio
nest_asyncio.apply()
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.dispatcher.filters import Command
import redis

TOKEN = "6663087665:AAHSrLFl-9543xbBt6pUYUVr6LqkYLZkmPM"
API = Bot(token=TOKEN)
dr = Dispatcher(API)
r = redis.Redis(decode_responses=True)


async def get_online(serv, msg: types.Message):
    reg = r.get(f"mob:uids")
    online = len(serv.online)
    await API.send_message(msg.from_user.id, f"ONLINE: {online}; REG: {reg}")
    import const
    if const.CLOSED_SERVER:
        await API.send_message(msg.from_user.id, f"SERVER CLOSED: {const.DESCRIPTION_CLOSED}")


async def best(serv, msg: types.Message):
    if "ur" not in serv.lib:
        return
    top = serv.lib["ur"].rating
    if not top:
        return
    text = ""
    award = ["🥇", "🥈", "🥉"]
    for uid in top:
        nick = r.lrange(f"mob:{uid}:appearance", 0, 0)[0]
        rtg = r.get(f"mob:{uid}:crt")
        text += f"{award[top.index(uid)]} - {nick} [UID: {uid}] Rating: ({rtg})\n"
    await API.send_message(msg.from_user.id, f"Best players:\n {text}")


async def Init(s):
    global serv
    serv = s
    dr.register_message_handler(functools.partial(get_online, serv), Command("online"))
    dr.register_message_handler(functools.partial(best, serv), Command("best"))
    executor.start_polling(dr)
