'''
LICENSING
-------------------------------------------------

Smartyparse: A python library for smart dynamic binary de/encoding.
    Copyright (C) 2016 Muterra, Inc.
    
    Contributors
    ------------
    Nick Badger 
        badg@muterra.io | badg@nickbadger.com | nickbadger.com

    This library is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) any later version.

    This library is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this library; if not, write to the 
    Free Software Foundation, Inc.,
    51 Franklin Street, 
    Fifth Floor, 
    Boston, MA  02110-1301 USA

------------------------------------------------------

'''

# Global dependencies
import struct
import abc
import collections

# ###############################################
# Parsers
# ###############################################


class ParserBase(metaclass=abc.ABCMeta):
    LENGTH = None
    
    @staticmethod
    @abc.abstractmethod
    def load(data):
        ''' Loads raw bytes into python objects.
        '''
        pass
        
    @staticmethod
    @abc.abstractmethod
    def dump(obj):
        ''' Dumps python objects into raw bytes.
        '''
        # Note that the super() implementation here makes it possible for
        # children to support callables when parsing.
        # If a child parser wants to customize handling a callable, don't
        # call super(). Take extra care with callable classes.
        if callable(obj):
            return obj()
        else:
            return obj
        

class _ParseNeat(ParserBase):
    ''' Class for no parsing necessary. Creates a bytes object from a 
    memoryview, and a memoryview from bytes.
    '''    
    @staticmethod
    def load(data):
        return bytes(data)
        
    @classmethod
    def dump(cls, obj):
        obj = super().dump(obj)
        # This might be a good place for some type checking to fail quickly
        # if it's not bytes-like
        return memoryview(obj)
        

class _ParseINT8US(ParserBase):
    ''' Parse an 8-bit unsigned integer.
    '''
    PACKER = struct.Struct('>B')
    LENGTH = PACKER.size
    
    @classmethod
    def load(cls, data):
        return cls.PACKER.unpack(data)[0]
        
    @classmethod
    def dump(cls, obj):
        obj = super().dump(obj)
        return cls.PACKER.pack(obj)
        

class _ParseINT16US(ParserBase):
    ''' Parse a 16-bit unsigned integer.
    '''
    PACKER = struct.Struct('>H')
    LENGTH = PACKER.size
    
    @classmethod
    def load(cls, data):
        return cls.PACKER.unpack(data)[0]
        
    @classmethod
    def dump(cls, obj):
        obj = super().dump(obj)
        return cls.PACKER.pack(obj)
        

class _ParseINT32US(ParserBase):
    ''' Parse a 32-bit unsigned integer.
    '''
    PACKER = struct.Struct('>I')
    LENGTH = PACKER.size
    
    @classmethod
    def load(cls, data):
        return cls.PACKER.unpack(data)[0]
        
    @classmethod
    def dump(cls, obj):
        obj = super().dump(obj)
        return cls.PACKER.pack(obj)
        

class _ParseINT64US(ParserBase):
    ''' Parse a 64-bit unsigned integer.
    '''
    PACKER = struct.Struct('>Q')
    LENGTH = PACKER.size
    
    @classmethod
    def load(cls, data):
        return cls.PACKER.unpack(data)[0]
        
    @classmethod
    def dump(cls, obj):
        obj = super().dump(obj)
        return cls.PACKER.pack(obj)
    

class _ParseNone(ParserBase):
    ''' Parses nothing. Load returns None, dump returns b''
    '''
    LENGTH = 0
    
    @classmethod
    def load(cls, data):
        return None
        
    @classmethod
    def dump(cls, obj):
        obj = super().dump(obj)
        return b''