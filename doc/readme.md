# Overview

SmartyParse provides two public parsing objects:

+ ```ParseHelper```
+ ```SmartyParser```

one convenience decorator for callback creation:

+ ```@references()```

as well as several parsing primitives:

+ Binary blobs (```parsers.Blob```)
+ Padding blobs (```parsers.Padding```)
+ Null objects (```parsers.Null```)
+ 8-bit integers (```parsers.Int8```)
+ 16-bit integers (```parsers.Int16```)
+ 32-bit integers (```parsers.Int32```)
+ 64-bit integers (```parsers.Int64```)
+ Floats, both single and double (```parsers.Float```)
+ Byte-oriented booleans (```parsers.ByteBool```)
+ Strings, in many encodings (```parsers.String```)

and an optional abstract base class for defining your own parsers:

+ ```parsers.ParserBase```

Most parsers support both big- and little-endian output, and all integers are availble in both signed and unsigned formats.

For ease of explanation, the below will use the following very simple file (```example.ext```) for explanations:

| Offset | Length | Description |
| ----   | ----   | ----        |
| 0      | 4      | Int32 U     |
| 4      | 8      | Int32 U     |
| 8      | 2      | Int16 U     |
| 10     | 8      | Int64 S     |

# ParseHelper

ParseHelpers do exactly that: they are a helper class that assists with the parsing of an individual atomic field. In ```example.ext```, each of the four integers will have its own ParseHelper. ParseHelpers keep track of their parser, their offset from the start of the file, and their length, and use these to calculate a slice of the whole file to parse.

You can also use ParseHelpers to register callbacks to call immediately before and/or after parsing. These callbacks *may* (but are not required to) modify the parsed object/data.

## ```class ParseHelper(parser, offset=0, length=None, callbacks=None)```

**parser** see ParseHelper().parser below.

**offset** see ParseHelper().offset below.

**length** see ParseHelper().length below.

**callbacks** see ParseHelper().callbacks below. When specified as an argument, they must be passed as ```None```, or a ```dict```-like container of tuples that match the following form:

```python
{
    'prepack': callable func,
    'postpack': callable func,
    'preunpack': callable func,
    'postunpack': callable func
}
```

There may be as many or as few callbacks in the arg as you would like to declare. See callbacks below for more information.

### ```ParseHelper().parser```

Read/write attribute. An instance of an object that complies with the ```parsers.ParserBase``` abstract base class. It is used for the actual conversion between binary bytes and python objects. In theory it can be modified, even during the parsing process, but this is untested water.

### ```ParseHelper().offset```

Read/write attribute. The beginning of the slice used for parsing. SmartyParsers ignore any argument you pass here, and will in fact override it, so it is only useful on its own for manual/custom parsing of data. It defaults to 0.

Offsets may be removed (set to zero) using the ```del``` keyword.

### ```ParseHelper().length```

Read/write attribute. The current declared size, in bytes, of the resulting binary object. A length of None will cause the ParseHelper to attempt to infer its own length during parsing, first from the ParseHelper.parser, then from the data it's operating on. It may be mutated by SmartyParsers during the parsing process, depending on its correctness. Ambiguous or conflicting length inferences will raise a ```RuntimeError```.

Lengths may be removed (set to None) using the ```del``` keyword.

### ```ParseHelper().slice```

Read-only attribute. The ```slice``` object for segmenting the file. In the second ParseHelper for ```example.ext```, this would be ```slice(4, 8, None)```. *Note: may only be correct during building process. Mostly reserved for future use in freezing formats for performance reasons.* May also be useful for callbacks, which should always have access to the correct slice.

### ```ParseHelper().callbacks```

Read-only attribute. A quick-reference description of all declared callbacks. Returns a dictionary with the following format:

```python
{
    'postpack': _SmartyparseCallback(func=None, modify=False),
    'postunpack': _SmartyparseCallback(func=None, modify=False),
    'prepack': _SmartyparseCallback(func=None, modify=False),
    'preunpack': _SmartyparseCallback(func=None, modify=False)
}
```

See the section on callback attributes below for more information regarding ```_SmartyparseCallback```s.

### ```ParseHelper().callback_preunpack```
### ```ParseHelper().callback_postunpack```
### ```ParseHelper().callback_prepack```
### ```ParseHelper().callback_postpack```

Read/write attributes. Sets the respective callback. Callbacks are called immediately before/after parsing. They will be passed a single positional argument when called:

+ preunpack is passed the bytes corresponding to the field being parsed (the slice, not the whole file)
+ postunpack is passed the python object created by the parser
+ prepack is passed the python object to pack
+ postpack is passed the bytes corresponding to the field being parsed

To set callbacks by attribute, simply set them equal to a callable object:

```ParseHelper().callback_prepack = func```

By default, these callables *will not* modify the object/data being built/parsed. Instead, the callback will be executed, and the original result of the building/parsing will be returned via ```build()```/```pack()```, ignoring the output of the callback:

```
callback_prepack(unpacked_object)
packed_bytes = pack(unpacked_object)
callback_postpack(packed_bytes)
return packed_bytes
```

If you would like the output of the callback to *replace* that value, like this:

```
modified_unpacked_object = callback_prepack(unpacked_object)
packed_bytes = pack(modified_unpacked_object)
modified_packed_bytes = callback_postpack(packed_bytes)
return modified_packed_bytes
```
then set the modify attribute of the respective callbacks to True:

```python
ParseHelper().callback_prepack.modify = True
ParseHelper().callback_postpack.modify = True
```

These can, of course, be mixed-and-matched on a per-callback basis.

Callbacks may be removed with the ```del``` keyword. This removes any callback function, and sets ```modify = False```.

##### ```_SmartyparseCallback``` objects

When registering a callable as a callback, smartyparse does not directly assign the function to the callback_???pack attribute. Instead, it wraps the function within a callable class, adding some helper functions in the process, including the management of modifying/not modifying input. The original callable is available at ```_SmartyparseCallback().func```. 

A ```_SmartyparseCallback``` object is always callable, and it will always respect its modify attribute, *even if its function is ```None```*. In that case, the callable is quite simply: 

```python
lambda *args, **kwargs: None
```

and calling such an object with ```modify=True``` will **always** result in a return of None, completely ignoring any passed arguments.

**Note that _SmartyparseCallbacks are a non-public API subject to change at any time.** You're welcome to use them, but don't complain if future updates break compatibility with no warning!

### ```ParseHelper().register_callback(call_on, func, modify=False)```

Register a callback via method. call_on must be a string from the following:

+ ```'prepack'```
+ ```'postpack'```
+ ```'preunpack'```
+ ```'postunpack'```

Does not return a value.

### ```ParseHelper().pack(obj, pack_into)```

Packs the python ```obj``` into the mutable bytearray-like ```pack_into``` according to ```self.slice```. It returns the modified ```pack_into```, but because it mutates ```pack_into``` without copying, there is no need to update any existing references.

### ```ParseHelper().unpack(unpack_from)```

Unpacks a python ```obj``` from the bytes-like ```unpack_from``` according to ```self.slice```. Returns the object.

# SmartyParser

SmartyParsers are used to form file/packet/message formats from ParseHelpers. They handle automatically updating ParseHelpers according to their positions in the file, and support dynamic operations between individual ParseHelpers. Creative use of ParseHelper callbacks can result in a tremendous amount of flexibility from SmartyParsers.

SmartyParsers are also fully nestable, though they do not yet support end flags, so nested indefinite-length constructs are not yet possible.

Fields are defined using getitem and setitem, just like a dict. For example, this definition will correctly parse ```example.ext``` files:

```python
from smartyparse import SmartyParser
from smartyparse import ParseHelper
import smartyparse.parsers

example = SmartyParser()
example['_0'] = ParseHelper(parsers.Int32(signed=False))
example['_1'] = ParseHelper(parsers.Int32(signed=False))
example['_2'] = ParseHelper(parsers.Int16(signed=False))
example['_3'] = ParseHelper(parsers.Int32(signed=True))
```

**Note that keys must be:**

1. Strings
2. Valid python identifiers (anything you could assign as an attribute to an object). If you aren't sure, you can always check using ```str.isidentifier('foo')```.

Removing both of these constraints is on the to-do list.

### ```SmartyParser().offset```
### ```SmartyParser().length```
### ```SmartyParser().slice```
### ```SmartyParser().callbacks```
### ```SmartyParser().callback_preunpack```
### ```SmartyParser().callback_postunpack```
### ```SmartyParser().callback_prepack```
### ```SmartyParser().callback_postpack```
### ```SmartyParser().register_callback()```
### ```SmartyParser().unpack(unpack_from)```

These attributes and functions are identical to ParseHelper.

### ```SmartyParser().obj```

Read-only attribute. Describes what kind of object the SmartyParser expects to see when called. Also, the class of object returned (a memory-efficient dict-like construct) when calling SmartyParser().unpack(data).

Calling this on the ```example``` SmartyParser of ```example.ext``` we created above would result in:

```python
>>> example.obj
<class 'SmartyParseObject'>: _smartyobject(['_0', '_1', '_2', '_3'])
>>> str(example.obj)
"SmartyParseObject class: {'_0', '_1', '_2', '_3'}"
```

As suggested by the ```repr()```, this can be created through 

```python
import smartyparse
smartyparse.core._smartyobject(['_0', '_1', '_2', '_3'])
```

but this is a non-public API and subject to change without warning.

### ```SmartyParser().parser```

Very similar to ParseHelper().parser, but read-only, and will always return self: a SmartyParser is its own parser, with its own pack and unpack methods.

### ```SmartyParser().pack(obj, pack_into=None)```

Very similar to ParseHelper().pack(), but pack_into is optional. If supplied, the SmartyParser will use its length and offset attributes to insert the packed bytes into the object. In both cases, pack_into (or a new bytes object) will be returned.

The ```obj``` being passed to pack must conform to ```SmartyParser().obj```. In other words, it must be dict-like, with each key in the ```SmartyParser()``` corresponding to the appropriate key: value pair in ```obj```.

Using the ```example.ext``` SmartyParser from above, this would be a valid object to pass:

```python
{
    '_0': 42,
    '_1': 84,
    '_2': 168,
    '_3': -101
}
```

### ```SmartyParser().link_length(data_name, length_name)```

This is a convenience method provided to automatically generate and apply callbacks to existing ParseHelpers, such that the ParseHelper at ```length_name``` will always correspond to the length of the field at ```data_name```. This relationship is enforced only *during parsing*, but it is bidirectional.

Once declared, any values within ```obj```s passed to ```pack()``` under the ```length_name``` key will be ignored. Similarly, the resulting length value will not be included in the result of ```unpack()```.

For example, with the following file:

| Offset  | Length | Description  |
| ----    | ----   | ----         |
| 0       | 4      | Int32 U, *n* |
| 4       | *n*    | Blob         |
| 4 + *n* | 4      | Int32 U      |

```python
from smartyparse import SmartyParser
from smartyparse import ParseHelper
import smartyparse.parsers

lengthlinked = SmartyParser()
lengthlinked['length'] = ParseHelper(parsers.Int32(signed=False))
lengthlinked['data'] = ParseHelper(parsers.Blob())
lengthlinked['_2'] = ParseHelper(parsers.Int32(signed=False))
lengthlinked.link_length(data_name='data', length_name='length')

packable_obj = {
        'data': b'Hello world',
        '_2': 42
    }
    
packed = lengthlinked.pack(packable_obj)
```

# @references()

When creating callbacks, it's often desirable that they behave like methods in the parent object. For example, if you're trying to create a self-describing format, it's very useful for callbacks on ```ParseHelper```s to have access to their containing ```SmartyParser```s, thereby allowing the parsers to easily mutate the parent. This mechanism is extremely powerful; it is also a little awkward to define on its own.

To facilitate this process, smartyparse includes a convenience decorator, ```@references(obj)```. It will automatically inject ```obj``` as the first argument to the function. Here is a simple example of its use:

```python
from smartyparse import SmartyParser
from smartyparse import ParseHelper
from smartyparse import references
from smartyparse.parsers import Int8
from smartyparse.parsers import Blob

parent = SmartyParser()
parent['switch'] = ParseHelper(Int8(signed=False))
parent['light'] = None

@references(parent)
def decide(self, switch):
    if switch == 1:
        self['light'] = ParseHelper(Int8())
    else:
        self['light'] = ParseHelper(Blob(length=11))
        
parent['switch'].register_callback('prepack', decide)
parent['switch'].register_callback('postunpack', decide)
        
off = {'switch': 1, 'light': -55}
on = {'switch': 0, 'light': b'Hello world'}
```

```python
>>> parent.pack(off)
bytearray(b'\x01\xc9')
>>> parent.pack(on)
bytearray(b'\x00Hello world')
```

# Parsers

All parsers must expose two methods and one attribute:

+ ```self.pack(self, obj)``` Converts any python object into bytes-like object. This is an ```abc.abstractmethod``` in the supplied ParserBase.
+ ```self.unpack(self, data)``` Converts any bytes-like object into python object. This is an ```abc.abstractmethod``` in the supplied ParserBase.
+ ```self.length``` (Usually) read-only attribute describing a static parser length -- for example, ```Int8``` has a static length of ```1``` (byte). If unknown or dynamic, use ```None```. ParserBase sets this to ```None``` for you (*as a class variable*) when creating your own parsers, but it can be trivially overwritten.

Internally, some parsers make use of ```memoryview```. [Memoryviews](https://docs.python.org/3/library/stdtypes.html#memoryview) provide efficient access to the raw buffer of the bytes in question, but may sometimes raise compatibility errors. If you get one, simply call the ```bytes()``` or ```bytearray()``` constructor on the memoryview.

### ```parsers.Blob(length=None)```

Arbitrary binary bytes. Creates a bytes object from a bytes-like object on pack, and a memoryview on unpack. Can be given a fixed, static length by defining the length argument. Once declared, this length cannot be changed.

### ```parsers.Padding(length, padding_byte=b'\x00')```

Padding bytes. Ignores anything passed to it in pack and unpack. Always returns ```length``` bytes of ```padding_byte``` on pack, and ```None``` on unpack.

### ```parsers.Null()```

Not particularly useful. Packs nothing (```b''```), returns None.

### ```parsers.Int8(signed=True, endian='big')```
### ```parsers.Int16(signed=True, endian='big')```
### ```parsers.Int32(signed=True, endian='big')```
### ```parsers.Int64(signed=True, endian='big')```

The integer packers are differentiated by their bit length (ex: ```Int32``` is a 32-bit/4-byte integer). All may be signed or unsigned. This is evaluated based on the truth value of the signed argument, so ```signed=0``` will be unsigned, ```signed='foo'``` will be signed, etc.

```endian``` may be ```'big'``` or ```'little'```.

### ```parsers.Float(double=True, endian='big')```

Single- and double-precision floats. Single-precision floats are IEEE 754 binary32 32-bit (4-byte) floats. Double-precision floats are IEEE 754 binary64 64-bit (8-byte) doubles.

### ```parsers.ByteBool(endian='big')```

A one-byte boolean. More or less a wrapper on the struct.pack for booleans.

### ```parsers.String(encoding='utf-8')```

A string (I bet you weren't expecting that!). All Python standard encodings are supported. See [here](https://docs.python.org/3/library/codecs.html#standard-encodings) for their string representations.

parsers.String() does not currently support fixed lengths. Instead, use a fixed-length binary blob and pre-encode the data using str.encode (pre-decode using bytes.decode). This can be done using a pre-pack/pre-unpack callback, if so desired.