'''
A frighteningly simple load-reload-reuse test sequence..

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
    
from smartyparse.parsers import Blob
from smartyparse.parsers import Int8
from smartyparse.parsers import Int16
from smartyparse.parsers import Int32
from smartyparse.parsers import Int64
from smartyparse.parsers import Null

# ###############################################
# Setup
# ###############################################

test_format = SmartyParser()
test_format['magic'] = ParseHelper(Blob(length=4))
test_format['version'] = ParseHelper(Int32(signed=False))
test_format['cipher'] = ParseHelper(Int8(signed=False))
test_format['body1_length'] = ParseHelper(Int32(signed=False))
test_format['body1'] = ParseHelper(Blob())
test_format['body2_length'] = ParseHelper(Int32(signed=False))
test_format['body2'] = ParseHelper(Blob())
test_format.link_length('body1', 'body1_length')
test_format.link_length('body2', 'body2_length')
    
test_nest = SmartyParser()
test_nest['first'] = test_format
test_nest['second'] = test_format
 
tv1 = {}
tv1['magic'] = b'[00]'
tv1['version'] = 1
tv1['cipher'] = 2
tv1['body1'] = b'[test byte string, first]'
tv1['body2'] = b'[test byte string, 2nd]'
     
tv2 = {}
tv2['magic'] = b'[aa]'
tv2['version'] = 1
tv2['cipher'] = 2
tv2['body1'] = b'[new test byte string, first]'
tv2['body2'] = b'[new test byte string, 2nd]'

tv3 = {'first': copy.deepcopy(tv1), 'second': copy.deepcopy(tv2)}

# ###############################################
# Testing
# ###############################################

def test():
    # ------------------------------------------------------------------
    # Test serial loading
    # ------------------------------------------------------------------
    
    # Test first vector
    bites1 = test_format.pack(tv1)
    recycle1 = test_format.unpack(bites1)
    assert recycle1 == tv1
    
    # Test second vector
    bites2 = test_format.pack(tv2)
    recycle2 = test_format.unpack(bites2)
    assert recycle2 == tv2
    
    # Test nested vector
    bites3 = test_nest.pack(tv3)
    recycle3 = test_nest.unpack(bites3)
    assert recycle3 == tv3
    
    # ------------------------------------------------------------------
    # Test serial loading
    # ------------------------------------------------------------------
    
    # Setup vectors
    bites1 = test_format.pack(tv1)
    bites2 = test_format.pack(tv2)
    bites3 = test_nest.pack(tv3)
    
    # Recycle vectors
    recycle1 = test_format.unpack(bites1)
    recycle2 = test_format.unpack(bites2)
    recycle3 = test_nest.unpack(bites3)
    
    # Assertions
    assert recycle1 == tv1
    assert recycle2 == tv2
    assert recycle3 == tv3
    
                
if __name__ == '__main__':
    test()