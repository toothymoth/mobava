import io


class Decoder:
    def __init__(self, bytes_):
        self.bytes = bytes_
    
    def decodeByte(self, byte):
        type_, cnt = (">b", 1)
        if byte == "u8":
            type_, cnt = (">B", 1)
        elif byte == "i16":
            type_, cnt = (">h", 2)
        elif byte == "u16":
            type_, cnt = (">H", 2)
        elif byte == "i32":
            type_, cnt = (">i", 4)
        elif byte == "u32":
            type_, cnt = (">I", 4)
        elif byte == "i64":
            type_, cnt = (">q", 8)
        elif byte == "f64":
            type_, cnt = (">d", 8)
        return struct.unpack(type_, self.bytes.read(cnt))[0]
    
    def processFrame(self):
        self.bytes: io.BytesIO = io.BytesIO(self.bytes)
        self.bytes.read(9)
        return {
            'type': self.decodeByte("i8"),
            'msg': self.decodeObject()
        }
    
    def decodeValue(self):
        dataType = self.decodeByte("i8")
        if dataType == 0:
            return None
        elif dataType == 1:
            return bool(self.decodeByte('i8'))
        elif dataType == 2:
            return self.decodeByte('i32')
        elif dataType == 3:
            return self.decodeByte('i64')
        elif dataType == 4:
            return self.decodeByte('f64')
        elif dataType == 5:
            return self.decodeString()
        elif dataType == 6:
            return self.decodeObject()
        elif dataType == 7:
            return self.decodeArray()
        else:
            raise ValueError(f"Invalid data type signature = {dataType}")
    
    def decodeArray(self, element=0):
        array = []
        elements = self.decodeByte('i32')
        while element < elements:
            array.append(self.decodeValue())
            element += 1
        return array
    
    def decodeObject(self):
        object = {}
        elements = self.decodeByte('i32')
        # print(elements)
        for _ in range(elements):
            key = self.decodeString()
            object[key] = self.decodeValue()
            # print(key, object[key])
        return object
    
    def decodeString(self):
        leng: int = self.decodeByte("i16")
        data = self.bytes.read(leng)
        return data.decode()


import struct
from datetime import datetime


class Encoder:
    def __init__(self, data):
        self.data = data
    
    def processFrame(self):
        if isinstance(self.data, dict):
            return self.encodeObject()
        return print(f"Не могу енкодить: {type(self.data)}")
    
    def encodeValue(self, data, forDict=False):
        final_data = b""
        if data is None:
            final_data += struct.pack(">b", 0)
        elif isinstance(data, bool):
            final_data += struct.pack(">b", 1)
            final_data += struct.pack(">b", int(data))
        elif isinstance(data, int):
            if data > 2147483647:
                final_data += struct.pack(">b", 3)
                final_data += struct.pack(">q", data)
            else:
                final_data += struct.pack(">b", 2)
                final_data += struct.pack(">i", data)
        elif isinstance(data, float):
            final_data += struct.pack(">b", 4)
            final_data += struct.pack(">d", data)
        elif isinstance(data, str):
            if not forDict:
                final_data += struct.pack(">b", 5)
            length = len(data.encode().hex()) // 2
            if len(data) >= 1000:
                final_data += struct.pack(">b", 4)
            while (length & 4294967168) != 0:
                final_data += struct.pack(">B", length & 127 | 128)
                length = length >> 7
            if len(data) < 1000:
                final_data += struct.pack(">h", length & 127)
            final_data += data.encode()
        elif isinstance(data, dict):
            final_data += struct.pack(">b", 6)
            final_data += self.encodeDict(data)
        elif isinstance(data, list):
            final_data += struct.pack(">b", 7)
            final_data += self.encodeArray(data)
        elif isinstance(data, datetime):
            final_data += struct.pack(">b", 8)
            final_data += struct.pack(">q", int(data.timestamp() * 1000))
        else:
            raise ValueError("Не могу энкодить " + str(type(data)))
        return final_data
    
    def encodeObject(self):
        final_data = struct.pack(">I", len(self.data))
        for item in self.data.keys():
            final_data += self.encodeValue(item, forDict=True)
            final_data += self.encodeValue(self.data[item])
        return final_data
    
    def encodeDict(self, data):
        final_data = struct.pack(">I", len(data))
        for item in data.keys():
            final_data += self.encodeValue(item, forDict=True)
            final_data += self.encodeValue(data[item])
        return final_data
    
    def encodeArray(self, data):
        final_data = struct.pack(">i", len(data))
        for item in data:
            final_data += self.encodeValue(item)
        return final_data
