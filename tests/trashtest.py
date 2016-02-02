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
    
    test_nest = SmartyParser()
    test_nest['first'] = tf_1
    test_nest['second'] = tf_1
    
    tv3 = {'first': tv1, 'second': tv2}
    
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
    
    bites3 = test_nest.pack(tv3)
    
    print('-----------------------------------------------')
    print('Successfully packed.')
    print(bytes(bites3))
    print('-----------------------------------------------')
    
    recycle3 = test_nest.unpack(bites3)
    
    print('-----------------------------------------------')
    print('Successfully reunpacked.')
    print(recycle3)
    print('-----------------------------------------------')
    
    import IPython
    IPython.embed()