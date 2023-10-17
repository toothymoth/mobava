class Decoder:
    def __init__(self, data):
        self.pos = 0
        self.data = data

    def read(self, amount):
        if self.pos + amount > len(self.data):
            raise Exception("Data is None")
        old_pos = self.pos
        self.pos = self.pos + amount
        return self.data[old_pos:self.pos]

    def decodeByte(self, byte):
        type, cnt = (">b", 1) if byte == "i8" else \
                    (">B", 1) if byte == "u8" else \
                    (">i", 4) if byte == "i32" else \
                    (">I", 4) if byte == "u32" else \
                    (">q", 8) if byte == "i64" else \
                    (">d", 8)
        return struct.unpack(type, self.read(cnt))[0]

    def processFrame(self):
        self.read(9)
        return {
            'type': self.decodeByte('i8'),
            'msg': self.decodeObject()
        }

    def decodeValue(self):
        dataType = self.decodeByte('i8')
        if dataType == 0: return None
        elif dataType == 1:
            return True if self.decodeByte('i8') else False
        elif dataType == 2: return self.decodeByte('i32')
        elif dataType == 3: return self.decodeByte('i64')
        elif dataType == 4: return self.decodeByte('f64')
        elif dataType == 5: return self.decodeString()
        elif dataType == 6: return self.decodeDictionary()
        elif dataType == 7: return self.decodeArray()
        else: raise ValueError(f"Invalid data type signature = {dataType}")

    def decodeArray(self, element=0):
        array=[]
        elements = self.decodeByte('i32')
        while element < elements:
            array.append(self.decodeValue()); element += 1
        return array

    def decodeObject(self, element=0):
        object={}
        elements = self.decodeByte('i32')
        while element < elements:
            key = self.decodeString()
            object[key] = self.decodeValue(); element += 1
        return object

    def decodeDictionary(self, element=0):
        object={}
        elements = self.decodeByte('i32')
        while element < elements:
            key = self.decodeString()
            object[key] = self.decodeValue(); element += 1
        return object

    def decodeString(self):
        length = 1
        replaceBytes = self.read(2)
        while not isinstance(length, str):
            letter = self.getNextValue(length)
            if letter:
                length += 1
                continue
            break
        return self.read(length-1).decode('utf-8', 'ignore')

    def getNextValue(self, element):
        if not self.data[self.pos+(element-1):self.pos+(element-1)+1]:
            return None
        elements = struct.unpack(">b", self.data[self.pos+(element-1):self.pos+(element-1)+1])[0]
        if elements > 8 or elements < 0:
            return self.data[self.pos:self.pos+element]
        return None


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
            length = len(data.encode().hex())//2
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
            raise ValueError("Не могу энкодить "+str(type(data)))
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
