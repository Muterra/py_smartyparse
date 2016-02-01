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

__all__ = ['ParseHelper', 'SmartyParser']

# Global dependencies
import abc
import collections
import inspect


# ###############################################
# Helper objects
# ###############################################


class _CallHelper():
    ''' Clever callable class wrapper for callbacks in ParseHelper.
    '''
    def __init__(self, func, modify=False):
        self.func = func
        self.modify = modify
        
    def __call__(self, arg):
        ''' If modify is true, we'll return a modified version of the
        argument.
        
        If modify is false, we'll return the original argument.
        '''
        if self.func == None:
            result = arg
        elif self.modify:
            result = self.func(arg)
        else:
            # Discard the function's return
            self.func(arg)
            result = arg
            
        return result
        
    @property
    def func(self):
        return self._func
        
    @func.setter
    def func(self, func):
        ''' Not a guarantee that the callback will correctly execute,
        just that it is correctly formatted for use as a callback.
        '''
        # Use None as a "DNE"
        if func != None:
            if not callable(func):
                raise TypeError('Callbacks must be callable.')
            func_info = inspect.getargspec(func)
            required_argcount = len(func_info.args) - len(func_info.defaults)
            if required_argcount != 1:
                raise ValueError('Callbacks must take exactly one non-default argument.')
            
        # Okay, should be good to go
        self._func = func
        
    def __repr__(self):
        ''' Some limited handling of subclasses is included.
        '''
        c = type(self).__name__
        return c + '(func=' + repr(self.func) + ', modify=' + repr(self.modify) + ')'
        

def _smartyobject(fieldnames):
    ''' Class generator function for SmartyParser objects.
    '''
    class SmartyParseObject():
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


# ###############################################
# SmartyParsers and ParseHelper
# ###############################################


class ParseHelper():
    ''' This is a bit messy re: division of concerns. 
    It's getting cleaner though!
    
    Should get rid of the messy unpack vs unpack_from, pack vs pack_into.
    Replace with very simple slice, callback, parse combo. Will need
    to support an optional slice override argument for packing and, I 
    suppose, unpacking.
    '''
    CALLBACK_FORMAT = collections.namedtuple(
            typename = 'ParseCallbackDeclaration',
            field_names = ['func', 'modify']
        )
    
    def __init__(self, parser, offset=0, length=None, callbacks=None):
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
        self._slice = None
        self._offset = offset
        self._length = length
        self._parser = parser
        self.register_callback('prepack', None)
        self.register_callback('preunpack', None)
        self.register_callback('postpack', None)
        self.register_callback('postunpack', None)
        
        callbacks = callbacks or {}
        
        for call_on, func_def in callbacks.items():
            self.register_callback(call_on=call_on, *func_def)
        
    def unpack(self, data):
        # Check/infer lengths. Awkwardly redundant with unpack_from, but
        # necessary to ensure data length always matches parser length
        self._infer_length(data)
            
        # Pre-unpack calls on data
        # Modification vs non-modification is handled by the CallHelper
        data = self._callback_preunpack(data)
        
        # Parse data -> obj
        obj = self._parser.unpack(data)
        
        # Post-unpack calls on obj
        # Modification vs non-modification is handled by the CallHelper
        obj = self._callback_postunpack(obj)
        
        return obj
        
    def unpack_from(self, data):
        # Awkwardly redundant with unpack, but necessary for slice handling.
        self._infer_length(data)
        self._build_slice()
        return self.unpack(raw[self._slice])
        
    def pack(self, obj):
        # Pre-pack calls on obj
        # Modification vs non-modification is handled by the CallHelper
        obj = self._callback_prepack(obj)
        
        # Parse obj -> data
        data = self._parser.pack(obj)
        
        # Post-pack calls on data
        # Modification vs non-modification is handled by the CallHelper
        data = self._callback_postpack(data)
            
        # Now infer/check length and return
        self._infer_length(data)
        return data
        
    def pack_into(self, obj, into, override_slice=False):
        if override_slice:
            into[override_slice] = self.pack(obj)
        else: 
            self._build_slice()
            into[self._slice] = self.pack(obj)
        
    def register_callback(self, call_on, func, modify=False):
        if call_on == 'preunpack':
            self.callback_preunpack = (func, modify)
        elif call_on == 'postunpack':
            self.callback_postunpack = (func, modify)
        elif call_on == 'prepack':
            self.callback_prepack = (func, modify)
        elif call_on == 'postpack':
            self.callback_postpack = (func, modify)
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
        return self.CALLBACK_FORMAT(
            self._callback_preunpack.func, 
            self._callback_preunpack.modify)
        
    @callback_preunpack.setter
    def callback_preunpack(self, value):
        self._callback_preunpack = _CallHelper(*value)
        
    @property
    def callback_postunpack(self):
        return self.CALLBACK_FORMAT(
            self._callback_postunpack.func, 
            self._callback_postunpack.modify)
        
    @callback_postunpack.setter
    def callback_postunpack(self, value):
        self._callback_postunpack = _CallHelper(*value)
        
    @property
    def callback_prepack(self):
        return self.CALLBACK_FORMAT(
            self._callback_prepack.func, 
            self._callback_prepack.modify)
        
    @callback_prepack.setter
    def callback_prepack(self, value):
        self._callback_prepack = _CallHelper(*value)
        
    @property
    def callback_postpack(self):
        return self.CALLBACK_FORMAT(
            self._callback_postpack.func, 
            self._callback_postpack.modify)
        
    @callback_postpack.setter
    def callback_postpack(self, value):
        self._callback_postpack = _CallHelper(*value)
        
    @property
    def length(self):
        # __len__ MUST return something interpretable as int. If 
        # self._length is None, this raises an error. Use this property 
        # instead of defining __len__ or returning an ambiguous zero.
        return self._length
        
    @length.setter
    def length(self, length):
        # Will need to be wrapped if used in callback
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
        self._offset = None
        
    def _build_slice(self, open_ended=False):
        start = self._offset
        if self.length == None or open_ended:
            stop = None
        else:
            stop = self._offset + self.length
        self._slice = slice(start, stop)
        
    def _infer_length(self, data=None):
        ''' Attempts to infer length from the parser, or, barring that,
        from the data itself.
        
        IF PASSING DATA, MAKE SURE IT'S BYTES! Otherwise, expect errors,
        bugs, implosions, etc.
        
        If self._length is defined, will return that instead.
        '''
        # Figure out what expects what
        self_expectation = self.length
        parser_expectation = self._parser.length
        try:
            data_expectation = len(data)
        except TypeError:
            data_expectation = None
        
        # Check for consistency and decide on outputs
        # If we have a length defined for the ParseHelper, prefer that
        if self_expectation != None:
            # Return a result only if all defined lengths match
            if (parser_expectation != None and self_expectation != parser_expectation) or \
               (data_expectation != None and data_expectation != self_expectation):
                    # print('self:   ', self_expectation)
                    # print('parser: ', parser_expectation)
                    # print('data:   ', data_expectation)
                    raise RuntimeError('ParseHelper expected length does not '
                                       'match both _Parser and data lengths.')
            else: 
                result = self_expectation
        # If we have a length defined for the _Parser, choose that next
        elif parser_expectation != None:
            # Return a result only if all defined lengths match
            if data_expectation != None and parser_expectation != data_expectation:
                    raise RuntimeError('_Parser expected length does not '
                                       'match data length.')
            else: 
                result = parser_expectation
        # Fallback on data expectation
        else:
            result = data_expectation
            
        # And finally, update our length
        self.length = result
        
    def __repr__(self):
        ''' Some limited handling of subclasses is included.
        '''
        c = type(self).__name__
        return c + '(parser=' + repr(self._parser) + ', ' + \
                    'offset=' + repr(self.offset) + ', ' + \
                    'length=' + repr(self.length) + ', ' + \
                    'callbacks=' + repr(self.callbacks) + ')'


class SmartyParser():
    ''' One-stop shop for easy parsing. No muss, no fuss, just coconuts.
    '''
    def __init__(self):
        self._control = collections.OrderedDict()
        self._exclude_from_obj = set()
        # This will instantiate self._obj with an empty object definition.
        self._update_obj()
        # This is a little ghetto but whatever?
        self._defer_eval = ({}, {})
        
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
        
        # ------------ Loading management ------------------------------
        # Before unpacking the length field, we know basically nothing.
        # State check: length {len: X, val: ?}; data {len: None, val: ?}
        # Now unpack the length, and then this gets called:
        def postunpack_len(unpacked_length, data_name=data_name):
            # print('postunpack length')
            self._control[data_name].length = unpacked_length
            self._control[data_name]._build_slice()
        self._control[length_name].register_callback('postunpack', postunpack_len)
        # State check: length {len: X, val: n}; data {len: n, val: ?}
        # Now we unpack the data, resulting in...
        # State check: length {len: X, val: n}; data {len: n, val: Y}
        # Which calls this...
        def postunpack_dat(unpacked_data, data_name=data_name):
            # print('postunpack data')
            del self._control[data_name].length
            self._control[data_name]._build_slice()
        self._control[data_name].register_callback('postunpack', postunpack_dat)
        # Which resets data to its original state.
        
        # ------------ packing management ------------------------------
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
        
    @property
    def obj(self):
        ''' Defines the required data format for packing something, or 
        what is returned when unpacking data.
        '''
        return self._obj
        
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
        
    def pack(self, obj):
        ''' Automatically assembles a message from an object. The object
        must have data accessible via __getitem__(key), with keys
        matching the SmartyParser definition.
        
        --------------
        
        This would be a good place to add in freezing of slices for
        static fields. Later optimization for later time.
        
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
        # into obj as None
        for key in self._exclude_from_obj:
            obj[key] = None
        
        # This should eventually be done with more intelligent preallocation
        # than a blatant punt
        pack_into = bytearray()
        
        # Use this to control the "cursor" position
        seeker = 0
        
        for fieldname, parser in self._control.items():
            data = obj[fieldname]
            call_after_parse = []
            
            # Try/finally: must be sure to reset slice offset to stay atomic-ish
            try:
                # Save length to restore later
                oldlen = parser.length
                oldoffset = parser.offset
                # Don't forget this comes after the state save
                parser.offset += seeker
                # Redundant with pack, but not triply so. Oh well.
                parser._infer_length()
                parser._build_slice()
                # Initialize
                seeker_advance = 0
                
                # Check to see if the bytearray is large enough
                if len(pack_into) < parser.offset:
                    # Too small to even start. Python will be hard-to-predict
                    # here (see above). Raise.
                    raise RuntimeError('Attempt to assign out of range; cannot infer padding.')
                    
                # Check to see if this is a delayed execution thingajobber
                if fieldname in self._defer_eval[0]:
                    self._generate_deferred(fieldname, parser, obj, pack_into)
                    # And don't forget to override parsing and lookup.
                    # If the object is too small for the next field, pad it out
                    if len(pack_into) < parser._slice.stop:
                        pack_into[parser.offset:] = bytearray(parser.length)
                    
                # If not delayed, add any dependent deferred evals to the todo list
                else:
                    call_after_parse = self._defer_eval[1][fieldname]
                    
                    # Check the tail end *after* dealing with delayed execution
                    # so we don't accidentally erase the slice before saving it.
                    if parser._slice.stop != None and len(pack_into) < parser._slice.stop:
                        # Too small, so rebuild slice to infinity
                        parser._build_slice(open_ended=True)
                        
                    # Check on seeker_advance -- if, for example, with length 
                    # link, we're about to remove a length, figure it out first
                    seeker_advance += parser.length or 0
                    
                    # Only do this when not deferred.
                    parser.pack_into(data, pack_into)
                    
                # Advance the seeker BEFORE the finally block resets the length
                # But first make sure we haven't already done it
                if not seeker_advance:
                    seeker_advance += parser.length or 0
                # We do, in fact, already have a seeker_advance, but it may
                # not be current. 
                else:
                    # Check if we have a better value (not None). Update if so.
                    if parser.length != None:
                        seeker_advance = parser.length
                seeker += seeker_advance
                # seeker += parser.length
                
                # And perform any scheduled deferred calls
                # IT IS VERY IMPORTANT TO NOTE THAT THIS HAPPENS BEFORE
                # RESTORING THE LENGTH AND OFFSET FROM THE ORIGINAL PARSER.
                for deferred in call_after_parse:
                    deferred()
                
            finally:
                # Reset the position and len so that future parses don't break
                parser.length = oldlen
                parser.offset = oldoffset
            
        return pack_into
        
    def _generate_deferred(self, fieldname, parser, obj, pack_into):
        # Figure out what parser we wait for
        waitfor = self._defer_eval[0][fieldname]
        # Save state with that parser's _defer_eval
        
        def deferred_call(fieldname=fieldname, loc=parser._slice):
            # First do the delayed data evaluation
            self._control[fieldname].pack_into(
                obj=obj[fieldname], 
                into=pack_into, 
                override_slice=loc)
            # Now call anything that was waiting on us.
            for deferred in self._defer_eval[1][fieldname]:
                deferred()
        
        # Add that function into the appropriate register
        self._defer_eval[1][waitfor].append(deferred_call)
        
    def unpack(self, message):
        ''' Automatically unpacks an object from message.
        
        Returns a SmartyParseObject.
        '''        
        # Construct the output and reframe as memoryview for performance
        unpacked = self.obj()
        data = memoryview(message)
        
        # Use this to control the "cursor" position
        seeker = 0
        
        for fieldname, parser in self._control.items():
            # Try/finally: must be sure to reset slice offset to stay atomic-ish
            try:
                # Save length to restore later
                oldlen = parser.length
                oldoffset = parser.offset
                # Don't forget this comes after the state save
                parser.offset += seeker
                # Redundant with pack, but not triply so. Oh well.
                parser._infer_length()
                parser._build_slice()
                
                # Go ahead and try to parse it, catching an indexerror
                try:
                    sliced = data[parser._slice]
                except IndexError:
                    raise IndexError('Data wrong size (too small?) for parsing chain.')
                    
                # print('seeker   ', seeker)
                # print('offset   ', parser.offset)
                # print('old off  ', oldoffset)
                # print('oldlen   ', oldlen)
                # print('slice    ', parser._slice)
                # print('bytelen  ', parser.length)
                # print('slicelen ', len(sliced))
                # print('data     ', bytes(sliced))
                # print('unpacked   ', unpacked)
                # print('-----------------------------------------------')
                
                if parser.length != None and len(sliced) != parser.length:
                    raise ValueError('Parser slice length differs from data slice.')
                    
                # Aight we're good to go, but only return stuff that matters
                obj = parser.unpack(sliced)
                if fieldname not in self._exclude_from_obj:
                    unpacked[fieldname] = obj
                
                # If we got this far, we should advance the seeker accordingly.
                # Use sliced instead of length in case postunpack callbacks 
                # got rid of it.
                seeker += len(sliced)
                
            finally:
                # Reset the position and len so that future parses don't break
                parser.length = oldlen
                parser.offset = oldoffset
            
        # Redundant if this wasn't newly created, but whatever
        return unpacked