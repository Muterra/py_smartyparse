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

__all__ = ['ParseHelper', 'SmartyParser', 'ListyParser', 'references']

# Global dependencies
import abc
import collections
import inspect
import functools

# Interpackage dependencies
from . import parsers
from .parsers import ParseError

# ###############################################
# Helper objects
# ###############################################


class _SmartyparseCallback():
    ''' Clever callable class wrapper for callbacks in ParseHelper.
    '''
    NOOP = lambda *args, **kwargs: None
    
    def __init__(self, func, modify=False):
        self.func = func
        self.modify = modify
        
    def __call__(self, arg):
        ''' If modify is true, we'll return a modified version of the
        argument.
        
        If modify is false, we'll return the original argument.
        '''
        if self.modify:
            result = self.func(arg)
        else:
            # Discard the function's return
            self.func(arg)
            result = arg
            
        return result
        
    def __bool__(self):
        # Return false if func is NOOP and modify false
        return not (self._func == self.NOOP and not self.modify)
        
    @property
    def func(self):
        return self._func
        
    @func.setter
    def func(self, func):
        ''' Not a guarantee that the callback will correctly execute,
        just that it is correctly formatted for use as a callback.
        '''
        # Use None as a "DNE"
        if func == None:
            func = self.NOOP
        elif not callable(func):
            raise TypeError('Callbacks must be callable.')
            
        # Okay, should be good to go
        self._func = func
        
    @func.deleter
    def func(self):
        self._func = self.NOOP
        
    def __repr__(self):
        ''' Some limited handling of subclasses is included.
        '''
        if self.func == self.NOOP:
            func = None
        else:
            func = self.func
        
        c = type(self).__name__
        # Note that calling repr instead of str will result in infinite
        # recursion, because the function needs the repr(self) for contextual
        # clues in its repr.
        return c + '(func=' + repr(func) + ', modify=' + repr(self.modify) + ')'
        
    def __str__(self):
        if self.func is self.NOOP:
            func = None
        else:
            func = self.func
            
        s = str(func) + ': modify=' + str(self.modify)
        return s
        

class _SPOMeta(type):
    ''' Metaclass for SmartyParseObjects created through _smartyobject.
    
    Defines the class __repr__ and __str__ to expose the available
    fieldnames there.
    '''
    def __len__(self):
        return len(self.__slots__)
    
    def __repr__(self):
        c = "<class 'SmartyParseObject'>: _smartyobject("
        c += str(self.__slots__)
        c += ')'
        return c
        
    def __str__(self):
        s = 'SmartyParseObject class: {'
        for fieldname in self.__slots__:
            s += "'" + fieldname + "', "
        s = s[:len(s) - 2]
        s += '}'
        return s
        

def _smartyobject(fieldnames):
    ''' Class generator function for SmartyParser objects.
    '''
    # # Handle fieldnames
    # stripped_fieldnames = []
    # for fieldname in fieldnames:
    #     s = str(fieldname)
    #     if not s.isidentifier():
    #         s = '__' + s
    #     stripped_fieldnames.append(s)
    
    class SmartyParseObject(metaclass=_SPOMeta):
        ''' Memory-efficient dict-like unordered object that allows 
        access through both attributes and __getitem__.
        '''
        __slots__ = fieldnames
        
        def __init__(self, **kwargs):
            ''' Note that, as both dict and attributes are unordered,
            this MUST be done as keyword arguments.
            '''
            for key, value in kwargs.items():
                setattr(self, key, value)
                
        def __getitem__(self, key):
            try:
                return getattr(self, key)
            except (AttributeError, TypeError, KeyError):
                raise KeyError('Key not found: ' + str(key))
            
        def __setitem__(self, key, value):
            try:
                setattr(self, key, value)
            except (AttributeError, TypeError, KeyError):
                raise KeyError('SmartyparseObjects do not support dynamic '
                               'expansion.')
            
        def __delitem__(self, key):
            ''' Does this error out because of __slots__? Iunno, but it
            won't really make a difference if it does.
            '''
            try:
                delattr(self, key)
            except (AttributeError, TypeError, KeyError):
                raise KeyError('Key not found: ' + str(key))
            
        def __iter__(self):
            # This is quick and dirty.
            for key in self.__slots__:
                try:
                    getattr(self, key)
                    yield key
                # Catch for anything that hasn't been set yet.
                except AttributeError:
                    pass
            
        def __len__(self):
            return len(self.__slots__)
            
        def __eq__(self, other):
            try:
                for key in self:
                    if self[key] == other[key]:
                        continue
                    else:
                        return False
            except (KeyError, TypeError):
                return False
                
            # Successfully managed entire thing without a bad comparison.
            return True
            
        def clear(self):
            for key in self:
                del self[key]
                
        def keys(self):
            return self.__slots__
            
        def values(self):
            for key in self:
                yield self[key]
                
        def items(self):
            for key in self:
                yield key, self[key]
                
        def get(self, key, default=None):
            try:
                return self[key]
            except AttributeError:
                return default
            
        def __repr__(self):
            c = type(self).__name__
            args = ''
            for key, value in self.items():
                args += key + '=' + repr(value) + ', '
            args = args[:len(args) - 2]
            
            return c + '(' + args + ')'
            
        def __str__(self):
            c = type(self).__name__
            args = []
            for key, value in self.items():
                args.append(key + '=' + repr(value))
            s = c + '(\n'
            for arg in args:
                s += '    ' + arg + ', \n'
            s = s[:len(s) - 3]
            s += '\n)'
            
            return s
            
    return SmartyParseObject


class _ParsableBase(metaclass=abc.ABCMeta):
    ''' Base class for anything parsable. Subclassed by both ParseHelper
    and SmartyParser.
    '''
    def __init__(self, offset=0, callbacks=None):
        ''' NOTE THE ORDER OF CALLBACK EXECUTION!
        preunpack calls on data (bytes)
        postunpack calls on object
        prepack calls on object
        postpack calls on data (bytes)
        
        callbacks should be dict-like, formatted as:
        {
            'preunpack': (function func, bool modify)
        }
        '''
        # self._slice needs to be initialized here
        self._slice = None
        self.offset = offset
        
        # Initialize these manually so that subsequent assigns don't reference
        # ex. self.callback_prepack.modify before assignment
        self._callback_prepack = _SmartyparseCallback(None)
        self._callback_postpack = _SmartyparseCallback(None)
        self._callback_preunpack = _SmartyparseCallback(None)
        self._callback_postunpack = _SmartyparseCallback(None)
        
        callbacks = callbacks or {}
        
        for call_on, func_def in callbacks.items():
            self.register_callback(call_on=call_on, *func_def)
        
    def _infer_length(self, data_length=None):
        ''' Attempts to infer length from the parser, or, barring that,
        from the data itself.
        
        IF PASSING DATA, MAKE SURE IT'S BYTES! Otherwise, expect errors,
        bugs, implosions, etc.
        
        If self._length is defined, will return that instead.
        '''
        self_expectation = self.length
        parser_expectation = self.parser.length
        data_expectation = data_length
            
        # Oo, this is going to be clever.
        # If consistent lengthsc prefer parser -> parsehelper -> data
        if parser_expectation != None:
            inferred = parser_expectation
        elif self_expectation != None:
            inferred = self_expectation
        elif data_expectation != None:
            inferred = data_expectation
        else:
            inferred = None
            
        # Now compare the inferred value to existing ones to establish
        # consistency. Don't need to check parser_expectation -- if defined,
        # it MUST be consistent, as per the control flow above.
        if self_expectation != None and self_expectation != inferred:
            raise ParseError('Incorrect expectations while '
                                'inferring length. Did you try to assign '
                                'a different length to a fixed-length parser?')
        if data_expectation != None and data_expectation != inferred:
            raise ParseError('Expectation/reality misalignment while '
                                'inferring length. Data length does not match '
                                'inferred length.')
            
        # And finally, update our length
        self.length = inferred
        
    @property
    def length(self):
        # __len__ MUST return something interpretable as int. If 
        # self._length is None, this raises an error. Use this property 
        # instead of defining __len__ or returning an ambiguous zero.
        return self._length
        
    @length.setter
    def length(self, length):
        self._length = length
        
    @length.deleter
    def length(self):
        self._length = None
        
    @property
    def offset(self):
        '''
        '''
        return self._offset
        
    @offset.setter
    def offset(self, offset):
        # Will need to be wrapped if used in callback
        self._offset = offset
        
    @offset.deleter
    def offset(self):
        # Call this on the proper setter and we can subclass intelligently
        self.offset = 0
        
    @property
    def slice(self):
        return self._slice
        
    def _build_slice(self, pack_into=None, open_ended=False):
        start = self.offset
        length = self.length
        
        # Catch lengths of none as zero, and if slice will be
        # out-of-bounds on pack_into, slice open-ended
        if open_ended or length == None:
            stop = None
        elif pack_into != None and len(pack_into) < length + start:
            stop = None
        else:
            stop = start + length
            
        self._slice = slice(start, stop)
        
    def register_callback(self, call_on, func, modify=False):
        if call_on == 'preunpack':
            self.callback_preunpack = func
            self.callback_preunpack.modify = modify
        elif call_on == 'postunpack':
            self.callback_postunpack = func
            self.callback_postunpack.modify = modify
        elif call_on == 'prepack':
            self.callback_prepack = func
            self.callback_prepack.modify = modify
        elif call_on == 'postpack':
            self.callback_postpack = func
            self.callback_postpack.modify = modify
        else:
            raise ValueError('call_on must be either "preunpack", "postunpack", '
                             '"prepack", or "postpack".')
            
    @property
    def callbacks(self):
        return {
            'preunpack': self.callback_preunpack,
            'postunpack': self.callback_postunpack,
            'prepack': self.callback_prepack,
            'postpack': self.callback_postpack
        }
        
    @property
    def callback_preunpack(self):
        return self._callback_preunpack
        
    @callback_preunpack.setter
    def callback_preunpack(self, func):
        # Preserve current state of modify
        modify = self._callback_preunpack.modify
        self._callback_preunpack = _SmartyparseCallback(func, modify=modify)
        
    @callback_preunpack.deleter
    def callback_preunpack(self):
        self._callback_preunpack = _SmartyparseCallback(None)
        
    @property
    def callback_postunpack(self):
        return self._callback_postunpack
        
    @callback_postunpack.setter
    def callback_postunpack(self, func):
        # Preserve current state of modify
        modify = self._callback_postunpack.modify
        self._callback_postunpack = _SmartyparseCallback(func, modify=modify)
        
    @callback_postunpack.deleter
    def callback_postunpack(self):
        self._callback_postunpack = _SmartyparseCallback(None)
        
    @property
    def callback_prepack(self):
        return self._callback_prepack
        
    @callback_prepack.setter
    def callback_prepack(self, func):
        # Preserve current state of modify
        modify = self._callback_prepack.modify
        self._callback_prepack = _SmartyparseCallback(func, modify=modify)
        
    @callback_prepack.deleter
    def callback_prepack(self):
        self._callback_prepack = _SmartyparseCallback(None)
        
    @property
    def callback_postpack(self):
        return self._callback_postpack
        
    @callback_postpack.setter
    def callback_postpack(self, func):
        # Preserve current state of modify
        modify = self._callback_postpack.modify
        self._callback_postpack = _SmartyparseCallback(func, modify=modify)
        
    @callback_postpack.deleter
    def callback_postpack(self):
        self._callback_postpack = _SmartyparseCallback(None)
        
    @property
    @abc.abstractmethod
    def parser(self):
        pass
        
    @abc.abstractmethod
    def pack(self, obj):
        pass
        
    @abc.abstractmethod
    def unpack(self, data):
        pass
        
    def _pack_padding(self, pack_into):
        ''' Instead of packing an object, packs in padding.
        '''
        # First, build the slice.
        self._build_slice(pack_into)
        pack_into[self.slice] = bytearray(self.length or 0)
        # And for consistency, return the packed object
        return pack_into


# ###############################################
# Objects exposed in public API
# ###############################################


def references(referent):
    def referent_wrapper(func):
        @functools.wraps(func)
        def injected(*args, **kwargs):
            return func(referent, *args, **kwargs)
        return injected
    return referent_wrapper


class StaticParser():
    ''' A static, deterministic parser. Can be generated from a 
    SmartyParser if (and only if) the SmartyParser is totally static --
    that is to say, StaticParsers cannot mutate themselves during
    the packing/unpacking process. They therefore cannot support, for 
    example, the common (blob_length, blob) combination.
    '''
    def __init__(self):
        self.slices = []
        self.parsers = []
        self.parse_order = []
        
        # Basically, don't forget that delayed calls need to be supported, and
        # callbacks, where possible, should still be incorporated.
        
        # This is going to require a massive rewrite on SmartyParser if it's to
        # be capable of automatic discovery of freeze-capable formats.
        
        # Could implement parse_order as a generator that pulls the parsers and
        # slices; that seems like it would be smart, IF if could be done well.


class ParseHelper(_ParsableBase):
    ''' This is a bit messy re: division of concerns. 
    It's getting cleaner though!
    
    Should get rid of the messy unpack vs unpack_from, pack vs pack_into.
    Replace with very simple slice, callback, parse combo. Will need
    to support an optional slice override argument for packing and, I 
    suppose, unpacking.
    
    THIS SHOULD REALLY BE REFACTORED TO USE A CONTEXT MANAGER for state
    management of offset, slice, etc. THAT would definitely be smart.
    '''
    def __init__(self, parser, offset=0, length=None, callbacks=None):
        super().__init__(offset, callbacks)
        self.parser = parser
        self.length = length
        
    @property
    def parser(self):
        return self._parser
        
    @parser.setter
    def parser(self, parser):
        self._parser = parser
        
    @parser.deleter
    def parser(self):
        self._parser = parsers.Null
        
    @property
    def length(self):
        # __len__ MUST return something interpretable as int. If 
        # self._length is None, this raises an error. Use this property 
        # instead of defining __len__ or returning an ambiguous zero.
        
        # Test self._length first, self.parser.length second
        # Will raise later if mismatch
        return self._length or self.parser.length
        
    @length.setter
    def length(self, length):
        self._length = length
        
    @length.deleter
    def length(self):
        self._length = None
        
    def unpack(self, unpack_from):
        # Check/infer lengths. Awkwardly redundant with unpack_from, but
        # necessary to ensure data length always matches parser length
        # DON'T PASS unpack_from, because it won't do any good. Known
        # lengths are guaranteed correct and unknown lengths need to 
        # slice to the end, which build_slice will handle.
        
        self._infer_length()
        self._build_slice()
        data = unpack_from[self.slice]
            
        # Pre-unpack calls on data
        # Modification vs non-modification is handled by the SmartyparseCallback
        data = self._callback_preunpack(data)
        
        # Parse data -> obj
        obj = self.parser.unpack(data)
        
        # Post-unpack calls on obj
        # Modification vs non-modification is handled by the SmartyparseCallback
        obj = self._callback_postunpack(obj)
        
        return obj
        
    def pack(self, obj, pack_into):
        # First check to see if the bytearray is large enough
        if len(pack_into) < self.offset:
            # Too small to even start. Python will be hard-to-predict
            # here (see above). Raise.
            # print(this_obj)
            # print(fieldname)
            raise ParseError('Attempt to assign out of range; cannot infer padding.')
            
        # Next, build the slice.
        self._build_slice(pack_into=pack_into)
        
        # Pre-pack calls on obj
        # Modification vs non-modification is handled by the SmartyparseCallback
        obj = self._callback_prepack(obj)
        
        # Parse obj -> data
        data = self.parser.pack(obj)
        
        # Post-pack calls on data
        # Modification vs non-modification is handled by the SmartyparseCallback
        data = self._callback_postpack(data)
            
        # Now infer/check length and pack it into the object
        self._infer_length(len(data))
        pack_into[self.slice] = data
        
        # And for consistency, return the packed object
        return pack_into
        
    def __repr__(self):
        ''' Some limited handling of subclasses is included.
        '''
        c = type(self).__name__
        return c + '(parser=' + repr(self.parser) + ', ' + \
                    'offset=' + repr(self.offset) + ', ' + \
                    'length=' + repr(self.length) + ', ' + \
                    'callbacks=' + repr(self.callbacks) + ')'


class ListyParser(_ParsableBase):
    '''
    Once serialized, there are only two ways to denote ending a list:
    1. An end tag
    2. Reaching a predetermined limit (like EOF or length)
    
    terminant=None will run for entire file (or entire slice)
    parsers are a list of parsers. It will try them, in that order,
    until one works.
    
    require_term defines behavior when encountering EOF before a the
    defined terminant. True will error out if this condition occurs;
    False will ignore and continue parsing.
    
    Terminant will be prepended to the list. If it happens first, list
    will terminate.
    
    Terminant is passed the packed object to pack. Note that this step
    passes the actual mutable object, so any operations that change its 
    size or otherwise mutate the object will result in unintended 
    consequences.
    
    Otherwise, terminant is a ParseHelper-like object. Will be tried 
    after each list unit while parsing, and appended while building. 
    Will immediately close list at first successful termination.
    
    Equals comparison will currently fail for reloads, since the lists
    produced will not test for equivalency of each item. Must instead 
    iterate over each object in both and test for equivalency there.
    That's messy for nested lists; eventually support for this will be
    added.
    '''
    def __init__(self, parsers, terminant=None, require_term=True, offset=0, callbacks=None):
        super().__init__(offset, callbacks)
        self.require_term = require_term
        self.terminant = terminant
        self.parsers = parsers
        self.length = None
        
    @property
    def terminant(self):
        return self._terminant
        
    @terminant.setter
    def terminant(self, value):
        self._terminant = value
        # if value != None:
        #     self._terminant = value
        # else:
        #     self._terminant = ParseHelper(parsers.Null())
            
    @terminant.deleter
    def terminant(self):
        self.terminant = None
        
    @property
    def _unpack_try_order(self):
        if self.terminant:
            return [self.terminant] + self.parsers
        else:
            return self.parsers
        
    @property
    def parser(self):
        # ListyParsers are their own parsers.
        return self
        
    def _attempt_pack_single(self, obj, pack_into, seeker):
        # Iterates through available parsers and returns length to advance
        seeker_advance = 0
        
        # I should change this nomenclature to differentiate between 
        # parsables like ParseHelper and the actual parsers
        for parser in self.parsers:
            parser.offset = seeker
            parser._infer_length()
            
            try:
                parser.pack(obj=obj, pack_into=pack_into)
                seeker_advance = parser.length or 0
                break
            except ParseError:
                pass
            finally:
                # This is, in fact, also executed when departing via break
                parser.offset = 0
        # This will only execute if break was not called, indicating no
        # successful parser discovery.
        else:
            raise ParseError('Could not find a valid parser for iterant.')
            
        return seeker_advance
        
    def pack(self, obj, pack_into=None):
        ''' Automatically assembles a message from an indefinite-length
        list. Objects to pack must be iterables and are returned as 
        tuples when unpacking.
        
        Note that this tries to infer the correct parser length for each
        parser, in order. Once again, if ANY matches, it will 
        automatically use the first match.
        '''        
        # This should eventually be done with more intelligent preallocation
        # than a blatant punt (if possible; might not be.)
        packed = bytearray()
        # Cannot do pack_into = pack_into or bytearray() because empty
        # bytearray evaluates to False.
        
        # Use this to control the "cursor" position
        # When nested, the parser is passed a slice. This is gross, but it's
        # getting the job done I suppose.
        # seeker = self.offset
        seeker = 0
        
        # Pre-pack calls on obj
        # Modification vs non-modification is handled by the SmartyparseCallback
        obj = self._callback_prepack(obj)
        
        # Parse each of the individual objects
        for this_obj in obj:
            # Advance the seeker
            seeker_advance = self._attempt_pack_single(this_obj, packed, seeker)
            seeker += seeker_advance
        
        # Now call the terminant on the packed data
        if self.terminant:
            self.terminant.offset = seeker
            self.terminant.pack(obj=packed, pack_into=packed)
            self.terminant.offset = 0
        
        # Finally, call the post-pack callback and return.
        packed = self._callback_postpack(packed)
        
        if pack_into == None:
            pack_into = bytearray()
            
        # Calculate the length from the observed difference between the 
        # final seeker position and the start offset
        # self.length = seeker - self.offset
        self.length = len(packed)
        # Now build the slice, which is only used if we're nested.
        self._build_slice(pack_into=pack_into)
            
        # Freeze my own shit before returning, or we get errors.
        pack_into[self.slice] = bytes(packed)
        return pack_into
        
    def _attempt_unpack_single(self, unpack_from, load_into, seeker):
        # Tries all parsers for the given position, returning the advance
        # and terminant=True/False if successful. Raise parseerror otherwise.
        # I should change this nomenclature to differentiate between 
        # parsables like ParseHelper and the actual parsers
        for parser in self._unpack_try_order:
            parser.offset = seeker
            parser._infer_length()
            
            try:
                obj = parser.unpack(unpack_from=unpack_from)
                load_into.append(obj)
                seeker_advance = parser.length or 0
                break
            except ParseError:
                pass
            finally:
                # This is, in fact, also executed when departing via break
                parser.offset = 0
        # This will only execute if break was not called, indicating no
        # successful parser discovery.
        else:
            raise ParseError('Could not find a valid parser for iterant.')
            
        # Return the offset and if it was the terminant.
        return seeker_advance, parser is self.terminant
        
    def unpack(self, unpack_from):
        # print(self.length)
        # Create output object and reframe as memoryview to avoid copies
        unpacked = []
        data = memoryview(unpack_from)
        self._infer_length()
        self._build_slice()
        # Error trap if no known length but preunpack callback:
        if self.length == None and self.callback_preunpack:
            raise ParseError('Cannot call pre-unpack callback with '
                                'indeterminate length. Your format may '
                                'be impossible to explicitly unpack.')
        # We can always unambiguously call this now, thanks to above.
        self._callback_preunpack(data[self.slice])
        
        # Use this to control the "cursor" position
        seeker = self.offset
        
        # Repeat until we get a terminate signal or we're at the EOF
        terminate = False
        endpoint = self.slice.stop or len(unpack_from)
        while seeker < endpoint and not terminate:
            seeker_advance, terminate = self._attempt_unpack_single(data, unpacked, seeker)
            seeker += seeker_advance
            
        # If we hit the terminant, remove value from unpacked, else 
        # check if we should have terminated. Not sure if awkward.
        if terminate:
            terminant = unpacked.pop()
        # This will be called if (and only if) EOF is encountered
        # without seeing a terminate.
        else:
            self._verify_termination()
                
        # Finally, we need to callback and return, freezing to a tuple for 
        # performance reasons
        unpacked = tuple(self._callback_postunpack(unpacked))
        return unpacked
        
    def _verify_termination(self):
        if self.terminant and self.require_term:
            raise ParseError('EOF encountered without required list termination.')
        else:
            return True


class SmartyParser(_ParsableBase):
    ''' One-stop shop for easy parsing. No muss, no fuss, just coconuts.
    '''
    def __init__(self, offset=0, callbacks=None):
        # Initialize offset.
        # This is required to prevent race condition / call before assignment
        # in super, because offset.setter references offset.
        self._offset = 0
        
        # These are used as buffers when linking data to metadata in 
        # link_forward and link_backward
        self._override = {}
        self._cache = {}
        
        self._control = collections.OrderedDict()
        self.length = None
        self._exclude_from_obj = set()
        # This will instantiate self._obj with an empty object definition.
        self._update_obj()
        # This is a little ghetto but whatever?
        self._defer_eval = ({}, {})
        
        # Call this last so that self._control doesn't wig out
        super().__init__(offset, callbacks)
        
    def __setitem__(self, name, value):
        ''' These are necessary to remember parsing order.
        '''
        self._control[name] = value
        self._update_obj()
        self._defer_eval[1][name] = []
        
    def __getitem__(self, name):
        ''' These are necessary to remember parsing order.
        '''
        return self._control[name]
        
    def __delitem__(self, name):
        ''' These are necessary to remember parsing order.
        '''
        del self._control[name]
        self._update_obj()
        
    def _infer_length(self, *args, **kwargs):
        result = super()._infer_length(*args, **kwargs)
        # As a last resort, try discovering if we've a static length
        if result == None:
            try:
                static_length = 0
                for parser in self._control.values():
                    static_length += parser.length
                result = static_length
            except (TypeError, AttributeError):    
                pass
        self.length = result
        
    @property
    def parser(self):
        # Smartyparsers are their own parsers.
        return self
        
    @property
    def obj(self):
        ''' Defines the required data format for packing something, or 
        what is returned when unpacking data.
        '''
        return self._obj
        
    @property
    def _exclude_from_obj(self):
        return self.__exclude
        
    @_exclude_from_obj.setter
    def _exclude_from_obj(self, value):
        self.__exclude = value
        self._update_obj()
        
    @_exclude_from_obj.deleter
    def _exclude_from_obj(self, value):
        del self.__exclude[value]
        self._update_obj()
        
    def _update_obj(self):
        ''' Refreshes the object definition.
        '''
        self._obj = _smartyobject([item for item in list(self._control)
                                   if item not in self._exclude_from_obj])
    
    def link_forward(self, source_name, link_name, f_pack, f_unpack, exclude=True):
        ''' Use this when the metadata follows the data in the packed
        binary file (for example: checksums).
        '''
        raise NotImplementedError('Backward linking not yet supported.')
        
    def link_backward(self, source_name, link_name, f_pack, f_unpack, exclude=True):
        ''' Use this when the metadata preceeds the data in the packed
        binary file (for example: length followed by string in eg 
        Pascal string).

        source_name is the keyname for the data. 
        link_name is the keyname for the metadata. 
        f_pack is called on the PACKED data and the UNPACKED metadata 
            (which is always None if exclude=True) to create the actual
            metadata. It MUST return the object to pack into the 
            metadata. It consumes self[source_name].callback_postpack
        f_unpack is called on the UNPACKED metadata and the PACKED data
            to modify the PARSING of the data. It MUST return the parser 
            for the data.
        exclude determines whether or not to exclude the metadata key 
            from object ingestion/creation. If True, the SmartyParser
            will ignore any value passed in the object, eliminating it
            as a requirement for parsing. If False, 
        
        
        Okay, listen up. the RIGHT way to do this is to think of it this
        way:
            + Linking never modifies parsers
            + Linking only modifies data
        So, put in order,
            1. packing starts with unpacked metadata and packed data.
               From that, it generates packed metadata.
                    + With ex. a MUID, that means you'd start with a 
                      precomputed hash dumped to bytes, as well as a 
                      value indicating which hash suite to use, and 
                      those two are passed to the function to create the 
                      metadata. In that case it would just return the 
                      hash identifier (metadata) back.
                    + With ex. a length, that means you'd start with a 
                      precomputed blob dumped to bytes, and None for the
                      unpacked length. Those are passed to the function,
                      and it returns the calculated length back. Presto.
            2. unpacking startes with unpacked metadata and packed data.
               From that, it MUTATES THE PACKED DATA.
                    + With ex. a MUID, that results in running a lookup,
                      and slicing the data to the appropriate length. 
                      That slice is then passed to the unpacker, instead
                      of the whole file.
                    + With ex. a length, essentially the same thing
                      happens.
        HOWEVER, this is going to fuck up the seeker, and there's an 
        argument to be made that it also completely defeats the purpose
        of having the parsers keep track of their own slices. I mean,
        you're essentially taking a roundabout way to modify the slice
        in this case, since ultimately parser.slice, which uses 
        parser.length to build itself, is equivalent to pre-computing
        a slice.
        
        DECISION: tabled until major library rewrite.
        '''
        raise NotImplementedError('Forward linking not yet supported.')
        
    def link_length(self, data_name, length_name):
        ''' This way, the SmartyParser will handle the length of the 
        data field and the value of the length field completely on its
        own. Lengths will be None before defined, and set during run.
        Should be easy to make it play nicely with memoization down the
        road.
        '''
        # ------------ Order management --------------------------------
        # It isn't possible to have a length field *after* the data when
        # being linked in this manner (unless it's redundant, in which
        # case it should NOT be lengthlinked), because otherwise the
        # parsing mechanism will be unable to determine the data's len
        # during unpacking. SO, enforce that here.
        if list(self._control.keys()).index(data_name) < \
            list(self._control.keys()).index(length_name):
                raise ValueError('Lengths cannot follow their linked data, or objects '
                                 'would be impossible to unpack.')
        
        # ------------ Unpacking management ----------------------------
        # Before unpacking the length field, we know basically nothing.
        # State check: length {len: X, val: ?}; data {len: None, val: ?}
        # Now unpack the length, and then this gets called:
        def postunpack_len(unpacked_length, data_name=data_name):
            # print('postunpack length ', unpacked_length)
            self._control[data_name].length = unpacked_length
        self._control[length_name].register_callback('postunpack', postunpack_len)
        # State check: length {len: X, val: n}; data {len: n, val: ?}
        # Now we unpack the data, resulting in...
        # State check: length {len: X, val: n}; data {len: n, val: Y}
        # Which calls this...
        def postunpack_dat(unpacked_data, data_name=data_name):
            # print('postunpack data')
            pass
            # del self._control[data_name].length
        self._control[data_name].register_callback('postunpack', postunpack_dat)
        # Which resets data to its original state.
        
        # ------------ Packing management ------------------------------
        # Before packing the data field, we know basically nothing.
        # BUT, we need to enforce that against previous calls, which may
        # have left a residual length in the parser from _infer_length()
        def prepack_dat(obj_dat, data_name=data_name):
            del self._control[data_name].length
        self._control[data_name].register_callback('prepack', prepack_dat)
        # State check: length {len: X, val: ?}; data {len: ?, val: ?}
        # Now we go to pack the length, but hit the deferred call.
        # Now we get around to packing the data, and...
        # State check: length {len: X, val: ?}; data {len: n, val: Y}
        # Now we get to the deferred call for the length pack, so we...
        def prepack_len(obj_len, data_name=data_name):
            # This is a deferred call, so we have a window to grab the real 
            # length from the parser.
            return self._control[data_name].length
        self._control[length_name].register_callback('prepack', prepack_len, modify=True)
        # State check: length {len: X, val: n}; data {len: n, val: Y}
        # There is no need for a state reset, because we've injected the
        # length directly into the parser, bypassing its state entirely.
        
        # ------------ Housekeeping ------------------------------------
        # Exclude the length field from the input/output of pack/unpack
        self._exclude_from_obj.add(length_name)
        self._defer_eval[0][length_name] = data_name
        
    def _generate_deferred(self, fieldname, parser, obj, pack_into):
        # Figure out what parser we wait for
        waitfor = self._defer_eval[0][fieldname]
        # Save state with that parser's _defer_eval
        
        def deferred_call(fieldname=fieldname, offset=parser.offset, length=parser.length):
            # Save the current state
            length_buffer = self._control[fieldname].length
            offset_buffer = self._control[fieldname].offset
            # Restore the deferred state and run it
            # Note: this cannot use the slice, in case open_ended=True
            self._control[fieldname].length = length
            self._control[fieldname].offset = offset
            self._control[fieldname].pack(
                obj=obj[fieldname], 
                pack_into=pack_into)
            # Now call anything that was waiting on us. Late-binding, 
            # so we won't miss anything.
            for deferred in self._defer_eval[1][fieldname]:
                deferred()
            # Restore the current state
            self._control[fieldname].length = length_buffer
            self._control[fieldname].offset = offset_buffer
        
        # Add that function into the appropriate register
        self._defer_eval[1][waitfor].append(deferred_call)
        
    def pack(self, obj, pack_into=None):
        ''' Automatically assembles a message from an object. The object
        must have data accessible via __getitem__(key), with keys
        matching the SmartyParser definition.
        
        --------------
        
        This would be a good place to add in freezing of slices for
        static fields. Later optimization for later time.
        
        --------------
        
        This should be refactored to actually use self.offset in seeker.
        That will require major (Very beneficial) changes. To manage 
        that with nested constructions will require some kind of
        termination mechanism smarter than slicing, and then a checking
        mechanism to ensure we're not past our slice, and (maybe) some 
        error correction for silliness like partial fields.
        
        --------------
        
        Once upon a nonexistent time, this also supported:
        pack_into=None, offset=0
        
        build_into places it into an existing bytearray.
        offset is only used with build_into, and determines the start
            point for the parsed object chain.
            
        However, this support was removed, due to inconsistent behavior
        between bytearray() and memoryview(bytearray()), which basically
        defeated the whole point of pack_into.
        
        See for yourself:
        >>> a = bytearray()
        >>> b = b'1234'
        >>> a[0:] = b
        >>> a
        bytearray(b'1234')
        >>> a[4] = b't'
        Traceback (most recent call last):
          File "<stdin>", line 1, in <module>
        IndexError: bytearray index out of range
        >>> a[4:] = b'test'
        >>> a
        bytearray(b'1234test')
        >>> a[100:] = b'padding?'
        >>> a
        bytearray(b'1234testpadding?')
        >>> len(a)
        16
        >>> a1 = memoryview(bytearray())
        >>> a1[0:] = b
        Traceback (most recent call last):
          File "<stdin>", line 1, in <module>
        TypeError: memoryview assignment: lvalue and rvalue have different structures
        '''
        # Add any exclusively avoided fields (currently only lengthlinked ones)
        # into obj as None, in case they (probably) have not been defined.
        for key in self._exclude_from_obj:
            obj[key] = None
        
        # This should eventually be done with more intelligent preallocation
        # than a blatant punt
        packed = bytearray()
        # Cannot do pack_into = pack_into or bytearray() because empty
        # bytearray evaluates to False.
        
        # Use this to control the "cursor" position
        # seeker = self.offset
        seeker = 0
        
        # Pre-pack calls on obj
        # Modification vs non-modification is handled by the SmartyparseCallback
        obj = self._callback_prepack(obj)
        
        # Don't use items, so that we can modify the parsehelpers themselves
        for fieldname in self._control:
            parser = self._control[fieldname]
            this_obj = obj[fieldname]
            call_after_parse = []
            padding = b''
            
            # Save length to restore later
            oldlen = parser.length
            
            # Don't forget this comes after the state save
            parser.offset = seeker
            # Check to see if the bytearray is large enough (is handled by
            # the ParseHelper, actually)
                
            # Redundant with pack, but not triply so. Oh well.
            parser._infer_length()
            # seeker_advance = parser.length or 0
                
            # Check to see if this is a delayed execution thingajobber
            if fieldname in self._defer_eval[0]:
                self._generate_deferred(fieldname, parser, obj, packed)
                # Inject any needed padding.
                parser._pack_padding(pack_into=packed)
            # If not delayed, add any dependent deferred evals to the todo list
            else:
                call_after_parse = self._defer_eval[1][fieldname]
                # Only do this when not deferred.
                parser.pack(obj=this_obj, pack_into=packed)
                
            # Advance the seeker BEFORE the finally block resets the length
            seeker += parser.length or 0
            
            # And perform any scheduled deferred calls
            # IT IS VERY IMPORTANT TO NOTE THAT THIS HAPPENS BEFORE
            # RESTORING THE LENGTH AND OFFSET FROM THE ORIGINAL PARSER.
            for deferred in call_after_parse:
                deferred()
                
            # Reset the parser's offset
            parser.offset = 0
        
        # Finally, call the post-pack callback and return.
        packed = self._callback_postpack(packed)
        
        if pack_into == None:
            pack_into = bytearray()
            
        # Calculate the length from the observed difference between the 
        # final seeker position and the start offset
        # self.length = seeker - self.offset
        self.length = len(packed)
        # Now build the slice, which is only used if we're nested.
        self._build_slice(pack_into=pack_into)
            
        # Freeze my own shit before returning, or we get errors.
        pack_into[self.slice] = bytes(packed)
        return pack_into
        
    def unpack(self, unpack_from):
        ''' Automatically unpacks an object from message.
        
        Returns a SmartyParseObject.
        '''
        # Construct the output and reframe as memoryview for performance
        unpacked = self.obj()
        data = memoryview(unpack_from)
        # Force a length reset. Gross, but works. If static, will be 
        # recalculated with _infer_length.
        self.length = None
        # Some other init stuff
        self._infer_length()
        self._build_slice()
        # Error trap if no known length but preunpack callback:
        if self.length == None and self.callback_preunpack:
            raise ParseError('Cannot call pre-unpack callback with '
                                'indeterminate length. Your format may '
                                'be impossible to explicitly unpack.')
        
        # We can always unambiguously call this now, thanks to above.
        self._callback_preunpack(data[self.slice])
        
        # Use this to control the "cursor" position
        seeker = self.offset
        
        # Don't use items, so that we can modify the parsehelpers themselves
        for fieldname in self._control:
            parser = self._control[fieldname]
            
            # Save length to restore later
            oldlen = parser.length
            # Don't forget this comes after the state save
            parser.offset = seeker
            # Redundant with pack, but not triply so. Oh well.
            parser._infer_length()
            
            # Previously, this is where we did this:
            # -----
            # # Check length to add
            # seeker_advance = parser.length
            # -----
            # But, since we've removed the callback to clear the 
            # length of any lengthlinked data field after loading,
            # we can now move it after. Also, this was causing bugs.
                
            # Aight we're good to go, but only return stuff that matters
            obj = parser.unpack(data)
            if fieldname not in self._exclude_from_obj:
                unpacked[fieldname] = obj
                
            # print('seeker   ', seeker)
            # print('newlen   ', parser.length)
            # print('slice    ', parser.slice)
            # print('data     ', bytes(data[parser.slice]))
            # print('-----------------------------------------------')
                
            # Check length to add
            seeker_advance = parser.length
            
            # If we got this far, we should advance the seeker accordingly.
            # Use sliced instead of length in case postunpack callbacks 
            # got rid of it.
            seeker += seeker_advance
            
            # Finally, reset the parser offset.
            parser.offset = 0
                
            # Infer lengths and then check them
            self.length = seeker - self.offset
            self._infer_length()
            
        # Post-unpack calls on obj
        # Modification vs non-modification is handled by the SmartyparseCallback
        unpacked = self._callback_postunpack(unpacked)
        
        # Redundant if this wasn't newly created, but whatever
        return unpacked