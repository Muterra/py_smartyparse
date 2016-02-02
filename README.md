# Smartyparse

Smartyparse is an intelligent general-purpose binary parsing, marshalling, serializing, etc library. Capable of dynamic operations, self-describing formats, nested formats, etc. Use it to encode, decode, and develop binary formats quickly and easily. It supports ```python>=3.3```.

Smartyparse is under development as part of the Ethyr encrypted email-like messaging application. **If you would like to support either Smartyparse or Ethyr, please consider contributing to our [IndieGoGo campaign](https://www.indiegogo.com/projects/ethyr-modern-encrypted-email).**

[![Code Climate](https://codeclimate.com/github/Muterra/py_smartyparse/badges/gpa.svg)](https://codeclimate.com/github/Muterra/py_smartyparse)
[![Issue Count](https://codeclimate.com/github/Muterra/py_smartyparse/badges/issue_count.svg)](https://codeclimate.com/github/Muterra/py_smartyparse)
[![Build Status](https://travis-ci.org/Muterra/py_smartyparse.svg?branch=master)](https://travis-ci.org/Muterra/py_smartyparse)

-------------

# Installation

Smartyparse is currently in pre-release alpha status. It *is* available on pip, but you must explicitly allow prerelease versions like this:

    pip install --pre smartyparse
    
Smartyparse has no external dependencies at this time (beyond the standard library), though building it from source will require pandoc and pypandoc:

    sudo apt-get install pandoc
    pip install pypandoc
    
# Example usage

Coming soon.

# Todo

(In no particular order)

+ Support bit orientation
+ Support endianness of binary blobs (aka transforming from little to big)
+ Support memoization of static SmartyParsers for extremely performant parsing
+ Support memoization of partially-static smartyparsers for better-than-completely-dynamic parsing

# Misc API notes

+ For strings, all Python standard encodings are supported. See [here](https://docs.python.org/3/library/codecs.html#standard-encodings) for their string representations.
+ Strings do not currently support fixed lengths. Instead, use a fixed-length binary blob and pre-encode the data using str.encode (pre-decode using bytes.decode). This can be done using a pre-pack/pre-unpack callback, if so desired.
+ SmartyParser fieldnames currently **must** be valid identifier strings (anything you could assign as an attribute). If you want to programmatically check validity, use ```'foo'.isidentifier()```, but SmartyParser will raise an error if you try to assign an invalid fieldname. This is the result of using ```__slots__``` for some memory optimization, which is a compromise between default dict behavior and memory use. If you're parsing a ton of objects, it will be very helpful for memory consumption.
+ Due to numeric imprecision, floats and doubles can potentially break equivalence (ie ```start == reloaded```) when comparing the before and after of packing -> unpacking the same object.