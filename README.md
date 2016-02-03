# Smartyparse

Smartyparse is an intelligent general-purpose binary parsing, marshalling, serializing, etc library. Capable of dynamic operations, self-describing formats, nested formats, etc. Use it to encode, decode, and develop binary formats quickly and easily. It supports ```python>=3.3```.

Smartyparse is under development as part of the [Muse protocol](https://github.com/Muterra/doc-muse) implementation used in the [Ethyr](https://www.ethyr.net) encrypted email-like messaging application. **If you would like to support Smartyparse, Muse, or Ethyr, please consider contributing to our [IndieGoGo campaign](https://www.indiegogo.com/projects/ethyr-modern-encrypted-email).**

[![Code Climate](https://codeclimate.com/github/Muterra/py_smartyparse/badges/gpa.svg)](https://codeclimate.com/github/Muterra/py_smartyparse)
[![Issue Count](https://codeclimate.com/github/Muterra/py_smartyparse/badges/issue_count.svg)](https://codeclimate.com/github/Muterra/py_smartyparse)
[![Build Status](https://travis-ci.org/Muterra/py_smartyparse.svg?branch=master)](https://travis-ci.org/Muterra/py_smartyparse)

**As an explicit warning,** this is a very, very new library, and you are likely to run into some bugs. Pull requests are welcome, and I apologize for the sometimes messy source.

-------------

# Installation

Smartyparse is currently in pre-release alpha status. It *is* available on pip, but you must explicitly allow prerelease versions like this:

    pip install --pre smartyparse
    
Smartyparse has no external dependencies at this time (beyond the standard library), though building it from source will require pandoc and pypandoc:

    sudo apt-get install pandoc
    pip install pypandoc
    
# Example usage

See [/doc](https://github.com/Muterra/py_smartyparse) for full API documentation.

**Declaring a simple length -> data object:**

| Offset | Length | Description  |
| ----   | ----   | ----         |
| 0      | 4      | Int32 U, *n* |
| 4      | *n*    | Blob         |

```python
from smartyparse import SmartyParser
from smartyparse import ParseHelper
import smartyparse.parsers

unknown_blob = SmartyParser()
unknown_blob['length'] = ParseHelper(parsers.Int32(signed=False))
unknown_blob['data'] = ParseHelper(parsers.Blob())
unknown_blob.link_length(data_name='data', length_name='length')
```

**Nesting that to define a simple file:**

| Offset         | Length | Description  |
| ----           | ----   | ----         |
| 0              | 4      | Magic 'test' |
| 4              | 4      | Int32 U, *n* |
| 8              | *n*    | Blob         |
| 8 + *n*        | 4      | Int32 U, *m* |
| 12 + *n*       | *m*    | Blob         |
| 12 + *n* + *m* | 4      | Int32 U      |

```python
test = SmartyParser()
test['magic'] = ParseHelper(parsers.Blob(length=4))
test['blob1'] = unknown_blob
test['blob2'] = unknown_blob
test['tail'] = ParseHelper(parsers.Int32(signed=False))
```

**An object to pack into the above:**

```python
test_obj = {
    'magic': b'test',
    'blob1': {
        'data': b'Hello world!'
    },
    'blob2': {
        'data': b'Hello, world?'
    },
    'tail': 123
}
```

*Why the awkward dict for the blobs?* Well, because SmartyParser objects aren't usually intended for things as simple as a length <-> value pair. It would make a lot more sense if it were 'header' and 'body', wouldn't it?

**Packing and recycling the above object:**

```python
>>> packed = test.pack(test_obj)
>>> test_obj_reloaded = test.unpack(packed)
>>> test_obj == test_obj_reloaded
True
```

# Todo

(In no particular order)

+ Change SmartyParserObject to use slots for storage, but not for item names (essentially removing attribute-style access, which isn't documented anyways)
+ Write .bmp library showcase
+ Move/mirror documentation to readthedocs
+ Add padding generation method (in addition to constant byte)
+ Add pip version badge: ```[![PyPi version](https://pypip.in/v/$REPO/badge.png)](https://github.com/Muterra/py_smartyparse)``` above.
+ Support bit orientation
+ Support endianness of binary blobs (aka transforming from little to big)
+ Support memoization of static SmartyParsers for extremely performant parsing
+ Support memoization of partially-static smartyparsers for better-than-completely-dynamic parsing
+ Autogeneration of integration test suite from API spec in /doc/
+ Random self-describing format declaration and testing
+ Performance testing
+ Add customized [pep8](http://pep8.readthedocs.org/en/latest/) to [codeclimate testing](https://docs.codeclimate.com/v1.0/docs/pep8), as per (as yet unpublished) Muterra code style guide
+ Support for "end flags" for indeterminate-length lists

# Misc API notes

+ SmartyParser fieldnames currently **must** be valid identifier strings (anything you could assign as an attribute). If you want to programmatically check validity, use ```'foo'.isidentifier()```, but SmartyParser will raise an error if you try to assign an invalid fieldname. This is the result of using ```__slots__``` for some memory optimization, which is a compromise between default dict behavior and memory use. If you're parsing a ton of objects, it will be very helpful for memory consumption.
+ Due to numeric imprecision, floats and doubles can potentially break equivalence (ie ```start == reloaded```) when comparing the before and after of packing -> unpacking the same object.