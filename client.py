import asyncio
import binascii
import inventory
import struct
from libraries.location import leave_room

from net import protocol


class Client:
    def __init__(self, server):
        self.address = ""
        self.room = ""
        self.uid = "0"
        self.act = "stand"
        self.server = server
        self.pos = (-1, -1)
    
    async def process(self, reader, writer):
        self.writer, self.reader = writer, reader
        self.address = writer.get_extra_info('peername')[0]
        self.server.log(f"{self.address} is connected")
        buffer = b""
        while True:
            await asyncio.sleep(0.2)
            try:
                data = await self.reader.read(2048)
            except OSError:
                break
            if not data:
                break
            try:
                final_data = protocol.Decoder(buffer + data).processFrame()
                if final_data:
                    self.server.log(f"CLIENT: {self.address}|{final_data}\n")
                    await self.server.process_data(final_data, self)
            except Exception as e:
                self.server.log(f"{self.address}|{self.uid} got error: {e}")
                continue
        await self._close_connection()
    
    async def send(self, data, type_=34):
        self.server.log(f"SERVER: {self.address}|{data}\n")
        final_data = struct.pack(">b", type_)
        final_data += protocol.Encoder(data).processFrame()
        final_data = self._make_header(final_data) + final_data
        try:
            self.writer.write(final_data)
            await self.writer.drain()
        except (BrokenPipeError, ConnectionResetError, AssertionError,
                TimeoutError, OSError, AttributeError):
            self.writer.close()
            
    async def system_message(self, text):
        await self.send({"text": text}, type_=36)
        
    async def get_appearance(self):
        return await self.server.get_appearance(self.uid)
    
    async def update_inv(self):
        if self.uid not in self.server.inv:
            self.server.inv[self.uid] = inventory.Inventory(self.server, self.uid)
            await self.server.inv[self.uid]._get_inventory()
        inv = self.server.inv[self.uid].get()
        await self.send({'data': {'inv': inv}, 'command': 'ntf.inv'})
        
    async def update_res(self):
        r = self.server.redis
        res = {
            'slvr': await r.get(f"mob:{self.uid}:slvr"),
            'gld': await r.get(f"mob:{self.uid}:gld"),
            'enrg': await r.get(f"mob:{self.uid}:enrg"),
            'emd': await r.get(f"mob:{self.uid}:emd")
        }
        await self.send({'data': {'res': res}, 'command': 'ntf.res'})
    
    def _make_header(self, msg):
        buf = struct.pack(">i", len(msg) + 5)
        buf += struct.pack(">B", (1 << 3))
        buf += struct.pack(">I", binascii.crc32(msg))
        return buf
    
    async def _close_connection(self):
        del self.server.inv[self.uid]
        if self.room and self.uid != "0":
            await leave_room(self.server, self)
        if self.uid in self.server.online:
            del self.server.online[self.uid]
        self.writer.close()
        del self
