#
# This file is part of upyHome
# Copyright (c) 2020 ng-galien
#
# Licensed under the MIT license:
#   http://www.opensource.org/licenses/mit-license.php
#
# Project home:
#   https://github.com/upyhome/upyhome
#
from micropython import const
from machine import lightsleep
import ustruct as struct
from usocket import socket, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR, IPPROTO_IP, IP_ADD_MEMBERSHIP
import gc

RECORDS = [
    '_upyhome', '_tcp', 'local.'
]

_TTL_DEFAULT = const(4500)

_TYPE_TXT = const(16)
_TYPE_PTR = const(12)
_TYPE_SRV = const(33)
_TYPE_A = const(1)
_CLASS_IN = const(1)
_CLASS_UNIQUE = const(32768)

_MDNS_ADDR = '224.0.0.251'
_MDNS_PORT = const(5353)

def dotted_ip_to_bytes(ip):
    l = [int(i) for i in ip.split('.')]
    if len(l) != 4 or any(i<0 or i>255 for i in l):
        raise ValueError
    return bytes(l)

class DNService():
    def __init__(self, name, server, props={}, port=8266, ttl=120):
        self._buffer = []
        self._socket = socket(AF_INET, SOCK_DGRAM)
        self._pointers = {}
        self._props = props
        self._name = name
        self._server = server
        self._port = port 
        self._address = None
        self._ttl = ttl
        self._size = 12

    def init_socket(self, address):
        self._address = address
        self._socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        member_info = bytes(tuple(map(int, _MDNS_ADDR.split("."))) + tuple(map(int, address.split("."))))
        self._socket.setsockopt(IPPROTO_IP, IP_ADD_MEMBERSHIP, member_info)
        self._socket.setblocking(False)
        #self._socket.bind((address, _MDNS_PORT))

    def _reset(self):
        self._buffer = []
        self._size = 12
        self._pointers = {}

    def _pack(self, _format, _value):
        self._buffer.append(struct.pack(_format, _value))
        self._size += struct.calcsize(_format)

    def _write_byte(self, _value):
        """Writes a single byte to the packet"""
        self._buffer.append(struct.pack('>B', _value))
        self._size += 1

    def _insert_short(self, _index, _value):
        """Inserts an unsigned short in a certain position in the packet"""
        self._buffer.insert(_index, struct.pack(b'!H', _value))
        self._size += 2

    def _write_short(self, _value):
        """Writes an unsigned short to the packet"""
        self._pack(b'!H', _value)

    def _write_int(self, _value):
        """Writes an unsigned integer to the packet"""
        self._pack(b'!I', int(_value))

    def _write_string(self, _value):
        """Writes a string to the packet"""
        self._buffer.append(_value)
        self._size += len(_value)

    def _write_utf(self, s: str):
        """Writes a UTF-8 string of a given length to the packet"""
        utfstr = s.encode('utf-8')
        length = len(utfstr)
        self._write_byte(length)
        self._write_string(utfstr)

    def _to_byte(self, val):
        return str(val).encode()

    def _write_name(self, _name):
        parts = _name.split('.')
        if not parts[-1]:
            parts.pop()
        name_suffices = ['.'.join(parts[i:]) for i in range(len(parts))]
        for count, sub_name in enumerate(name_suffices):
            if sub_name in self._pointers:
                break
        else:
            count = len(name_suffices)

        # note the new names we are saving into the packet
        name_length = len(_name.encode('utf-8'))
        for suffix in name_suffices[:count]:
            self._pointers[suffix] = self._size + name_length - len(suffix.encode('utf-8')) - 1

        # write the new names out.
        for part in parts[:count]:
            self._write_utf(part)

        # if we wrote part of the name, create a pointer to the rest
        if count != len(name_suffices):
            # Found substring in packet, create pointer
            index = self._pointers[name_suffices[count]]
            self._write_byte((index >> 8) | 0xC0)
            self._write_byte(index & 0xFF)
        else:
            # this is the end of a name
            self._write_byte(0)

    def _write_record(self, records, _type, _class, _ttl = 4500, _self_write = None):
        
            
        start_data_length = len(self._buffer)
        start_size = self._size
        self._write_name(records)
        self._write_short(_type)
        self._write_short(_class)#class
        self._write_int(_ttl)#ttl
        index = len(self._buffer)
        self._size += 2
        if _self_write is None:
            self._write_name(self._name+'.'+records)
        else:
            _self_write()
        self._size -= 2
        length = sum((len(d) for d in self._buffer[index:]))
        # Here is the short we adjusted for
        self._insert_short(index, length)

    def _self_write_srv(self):
        self._write_short(0)
        self._write_short(0)
        self._write_short(self._port)
        self._write_name(self._server+'.local.')

    def _self_write_data(self):
        temp = []
        for key, value in self._props.items():
            temp.append(key + '=' +value)
        text = '\n' + '\x0b'.join(temp)
        text = text.encode()
        self._write_string(text)

    def _self_write_adress(self):
        addr = dotted_ip_to_bytes(self._address)
        self._write_string(addr)

    def _self_write_pointer(self):
        pointer = self._name + '.'.join(RECORDS)
        self._write_string(pointer)

    def _broadcat_message(self):
        self._reset()
        records = '.'.join(RECORDS)
        self._write_record(records, _TYPE_PTR, _CLASS_IN)
        records = self._name+'.'+records
        _class = _CLASS_IN | _CLASS_UNIQUE
        self._write_record(records, _TYPE_SRV, _class , self._ttl, self._self_write_srv)
        self._write_record(records, _TYPE_TXT, _class, _TTL_DEFAULT, self._self_write_data)
        records = self._server+'.local.'
        self._write_record(records, _TYPE_A, _class, self._ttl, self._self_write_adress)
        vals = [0,0,4,0,33792,0]
        for val in vals:
            self._insert_short(0, val)
        return b''.join(self._buffer)

    def _check_message(self):
        records = '.'.join(RECORDS)
        self._write_name(records)
        self._write_short(_TYPE_PTR)
        self._write_short(_CLASS_IN)
        self._write_record(records, _TYPE_PTR, _CLASS_IN)
        vals = [0,1,0,1,1024,0]
        for val in vals:
            self._insert_short(0, val)
        return b''.join(self._buffer)

    def check(self):
        msg = self._check_message()
        print(msg)
        self._reset()
        for i in range(3):
            self._socket.sendto(msg, (_MDNS_ADDR, _MDNS_PORT))
            gc.collect()
            lightsleep(100)
        

    def broadcast(self):
        msg = self._broadcat_message()
        print(msg)
        self._reset()
        for i in range(3):
            self._socket.sendto(msg, (_MDNS_ADDR, _MDNS_PORT))
            gc.collect()
            lightsleep(100)
        