'''
Scratchpad for test-based development.

LICENSING
-------------------------------------------------

smartyparse: A python library for Muse object manipulation.
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

import sys
import collections
import copy

from smartyparse import SmartyParser
from smartyparse import ParseHelper
from smartyparse import parsers
    
from smartyparse.parsers import Blob
from smartyparse.parsers import Int8
from smartyparse.parsers import Int16
from smartyparse.parsers import Int32
from smartyparse.parsers import Int64
from smartyparse.parsers import Null

# ###############################################
# Testing
# ###############################################
                
if __name__ == '__main__':
    # Generic format
    tf_1 = SmartyParser()
    tf_1['magic'] = ParseHelper(Blob(length=4))
    tf_1['version'] = ParseHelper(Int32(signed=False))
    tf_1['cipher'] = ParseHelper(Int8(signed=False))
    tf_1['body1_length'] = ParseHelper(Int32(signed=False))
    tf_1['body1'] = ParseHelper(Blob())
    tf_1['body2_length'] = ParseHelper(Int32(signed=False))
    tf_1['body2'] = ParseHelper(Blob())
    tf_1.link_length('body1', 'body1_length')
    tf_1.link_length('body2', 'body2_length')
    
    tf_nest = SmartyParser()
    tf_nest['first'] = tf_1
    tf_nest['second'] = tf_1
    
    # More exhaustive, mostly deterministic format
    tf_2 = SmartyParser()
    tf_2['_0'] = ParseHelper(parsers.Null())
    tf_2['_1'] = ParseHelper(parsers.Int8(signed=True))
    tf_2['_2'] = ParseHelper(parsers.Int8(signed=False))
    tf_2['_3'] = ParseHelper(parsers.Int16(signed=True))
    tf_2['_4'] = ParseHelper(parsers.Int16(signed=False))
    tf_2['_5'] = ParseHelper(parsers.Int32(signed=True))
    tf_2['_6'] = ParseHelper(parsers.Int32(signed=False))
    tf_2['_7'] = ParseHelper(parsers.Int64(signed=True))
    tf_2['_8'] = ParseHelper(parsers.Int64(signed=False))
    tf_2['_9'] = ParseHelper(parsers.Float(double=False))
    tf_2['_10'] = ParseHelper(parsers.Float())
    tf_2['_11'] = ParseHelper(parsers.ByteBool())
    tf_2['_12'] = ParseHelper(parsers.String())
     
    tv1 = {}
    tv1['magic'] = b'[00]'
    tv1['version'] = 1
    tv1['cipher'] = 2
    tv1['body1'] = b'[tv1 byte string, first]'
    tv1['body2'] = b'[tv1 byte string, 2nd]'
     
    tv2 = {}
    tv2['magic'] = b'[aa]'
    tv2['version'] = 5
    tv2['cipher'] = 6
    tv2['body1'] = b'[new test byte string, first]'
    tv2['body2'] = b'[new test byte string, 2nd]'
    
    tv3 = {'first': copy.deepcopy(tv1), 'second': copy.deepcopy(tv2)}
    
    tv4 = {}
    tv4['_0'] = None
    tv4['_1'] = -10
    tv4['_2'] = 11
    tv4['_3'] = -300
    tv4['_4'] = 301
    tv4['_5'] = -100000
    tv4['_6'] = 100001
    tv4['_7'] = -10000000000
    tv4['_8'] = 10000000001
    tv4['_9'] = 11.11
    tv4['_10'] = 1e-50
    tv4['_11'] = True
    tv4['_12'] = 'EOF'
    
    print('-----------------------------------------------')
    print('Testing all "other" parsers...')
    print('    ', tv4)
    
    bites4 = tf_2.pack(tv4)
    
    print('Successfully packed.')
    print('    ', bytes(bites4))
    
    recycle4 = tf_2.unpack(bites4)
    
    print('Successfully reunpacked.')
    print(recycle4)
    print('-----------------------------------------------')
    
    print('-----------------------------------------------')
    print('Starting TV1, serial...')
    print('    ', tv1)
    
    bites1 = tf_1.pack(tv1)
    
    print('Successfully packed.')
    print('    ', bytes(bites1))
    
    recycle1 = tf_1.unpack(bites1)
    
    print('Successfully reunpacked.')
    print(recycle1)
    print('-----------------------------------------------')
    
    print('-----------------------------------------------')
    print('Starting TV2, serial...')
    print('    ', tv2)
    
    bites2 = tf_1.pack(tv2)
    
    print('Successfully packed.')
    print('    ', bytes(bites2))
    
    recycle2 = tf_1.unpack(bites2)
    
    print('Successfully reunpacked.')
    print(recycle2)
    print('-----------------------------------------------')
    
    print('-----------------------------------------------')
    print('Starting TV1, parallel...')
    print('    ', tv1)
    
    bites1 = tf_1.pack(tv1)
    
    print('Successfully packed TV1.')
    print('    ', bytes(bites1))
    
    print('-----------------------------------------------')
    print('Starting TV2, parallel...')
    print('    ', tv2)
    
    bites2 = tf_1.pack(tv2)
    
    print('Successfully packed TV2.')
    print('    ', bytes(bites2))
    print('-----------------------------------------------')
    
    recycle1 = tf_1.unpack(bites1)
    
    print('-----------------------------------------------')
    print('Successfully reunpacked TV1.')
    print(recycle1)
    
    recycle2 = tf_1.unpack(bites2)
    
    print('-----------------------------------------------')
    print('Successfully reunpacked TV2.')
    print(recycle2)
    
    print('-----------------------------------------------')
    print('-----------------------------------------------')
    print('Starting (nested) TV3...')
    print(tv3)
    print('-----------------------------------------------')
    
    bites3 = tf_nest.pack(tv3)
    
    print('-----------------------------------------------')
    print('Successfully packed.')
    print(bytes(bites3))
    print('-----------------------------------------------')
    
    recycle3 = tf_nest.unpack(bites3)
    
    print('-----------------------------------------------')
    print('Successfully reunpacked.')
    print(recycle3)
    print('-----------------------------------------------')
    
    import IPython
    IPython.embed()