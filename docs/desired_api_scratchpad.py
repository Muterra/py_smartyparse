''' How I want smartyparse to work...

This document itself is a WIP. I'm still not entirely decided on how I
want this whole thing to work.
    
Question: how to handle repeated/streaming parsers, like ghidlists?
Should that use, for example, a field.repeat = True or something?

Note: tracking order of field definition is included as an example in
the metaclass docs:
https://docs.python.org/3.6/reference/datamodel.html#metaclass-example
'''

from smartyparse import Field
from smartyparse import Parser
from smartyparse import parsed

from smartyparse.parsers import Literal
from smartyparse.parsers import Int
from smartyparse.parsers import Length
from smartyparse.parsers import Typed


class CustomField(Field):
    ''' Create a custom parser field.
    '''
    
    async def load(self, data):
        ''' Load that obj shit from binary data.
        '''
        return 'hello world'
        
    async def dump(self, obj):
        ''' Dump that obj shit into binary data.
        '''
        return b'hello world'


class Checksum(Int):
    ''' Create a custom, fixed-length parser field.
    '''
    
    def __init__(self, *args, **kwargs):
        super().__init__(bits=32, signed=False, endian='big', *args, **kwargs)
    
    async def load(self, data):
        ''' Load that obj shit from binary data.
        '''
        return (await super().load(data))
        
    async def dump(self, obj):
        ''' Dump that obj shit into binary data.
        '''
        return (await super().dump(obj))


class ParserDemo(metaclass=Parser):
    ''' Example parser declaration.
    
    Note: should also be able to set this up such that everything within
    the class itself is just declarative -- so all of the actual parsers
    are spelled out elsewhere.
    
    Parsers can be nested -- ParserDemo could be used as a field in a
    parent parser.
    
    Parser classes, once defined, have two methods:
        obj = await Parser.parse()
        data = await obj.serialize()
        
    All of the various fields are accessible via attributes on the
    objects themselves.
    '''
    
    magic = parsed(Literal(b'1234'))
    magic.preload_callback = 'update_checksum'
    magic.postdump_callback = 'update_checksum'
    
    version = parsed(Int(bits=32, signed=False, endian='big'))
    version.preload_callback = 'update_checksum'
    version.postdump_callback = 'update_checksum'
    
    varint = parsed(Typed({
        b'+': Int(bits=32, signed=False, endian='big'),
        b'-': Int(bits=32, signed=True, endian='big')
    }))
    varint.preload_callback = 'update_checksum'
    varint.postdump_callback = 'update_checksum'
    
    # Note explicit fixed-length declaration here, which is maybe silly.
    custom = parsed(CustomField(bits=88))
    custom.preload_callback = 'update_checksum'
    custom.postdump_callback = 'update_checksum'
    
    body_length = parsed(
        Length(bits=32, signed=False, endian='big', field='body')
    )
    body_length.preload_callback = 'update_checksum'
    body_length.postdump_callback = 'update_checksum'
    
    body = parsed(Field(bits=None))
    body.preload_callback = 'update_checksum'
    body.postdump_callback = 'update_checksum'
    
    checksum = parsed(Checksum())
    checksum.postload_callback = 'verify_checksum'
    checksum.predump_callback = 'finalize_checksum'
        
    async def update_checksum(self, data):
        ''' Example callback for binary data.
        '''
        self._checksum.update(data)
        
    async def finalize_checksum(self, obj):
        ''' Example callback for python objects.
        '''
        self.checksum = self._checksum.finalize()
        
    async def verify_checksum(self, obj):
        ''' Example callback for post-load.
        '''
        verifier = self._checksum.finalize()
        if self.checksum != verifier:
            raise ValueError('Checksum verification failed.')
