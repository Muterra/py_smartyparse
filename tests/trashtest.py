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
from smartyparse import ListyParser
from smartyparse import parsers
from smartyparse import references
    
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
    
    # Nested formats
    tf_nest = SmartyParser()
    tf_nest['first'] = tf_1
    tf_nest['second'] = tf_1
    
    tf_nest2 = SmartyParser()
    tf_nest2['_0'] = ParseHelper(Int32())
    tf_nest2['_1'] = tf_1
    tf_nest2['_2'] = ParseHelper(Int32())
    
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
    tf_2['_12'] = ParseHelper(parsers.Padding(length=4))
    tf_2['_13'] = ParseHelper(parsers.String())
     
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
    
    tv3 = {
            'first': copy.deepcopy(tv1), 
            'second': copy.deepcopy(tv2)
        }
    
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
    tv4['_12'] = None
    tv4['_13'] = 'EOF'
    
    tv5 = {}
    tv5['_0'] = 42
    tv5['_1'] = copy.deepcopy(tv1)
    tv5['_2'] = -42
    
    print('-----------------------------------------------')
    print('Testing all "other" parsers...')
    # print('    ', tv4)
    
    bites4 = tf_2.pack(tv4)
    
    # print('Successfully packed.')
    # print('    ', bytes(bites4))
    
    recycle4 = tf_2.unpack(bites4)
    # Note that numerical precision prevents us from easily:
    # assert recycle4 == tv4
    
    # print('Successfully reunpacked.')
    # print(recycle4)
    
    # print('    ', tv5)
    
    bites5 = tf_nest2.pack(tv5)
    
    # print('Successfully packed.')
    # print('    ', bytes(bites5))
    
    recycle5 = tf_nest2.unpack(bites5)
    assert recycle5 == tv5
    print('Successfully reunpacked.')
    
    # print(recycle5)
    # print('-----------------------------------------------')
    
    print('-----------------------------------------------')
    print('Starting TV1, serial...')
    # print('    ', tv1)
    
    bites1 = tf_1.pack(tv1)
    
    # print('Successfully packed.')
    # print('    ', bytes(bites1))
    
    recycle1 = tf_1.unpack(bites1)
    assert recycle1 == tv1
    print('Successfully reunpacked.')
    
    # print(recycle1)
    # print('-----------------------------------------------')
    
    print('-----------------------------------------------')
    print('Starting TV2, serial...')
    # print('    ', tv2)
    
    bites2 = tf_1.pack(tv2)
    
    # print('Successfully packed.')
    # print('    ', bytes(bites2))
    
    recycle2 = tf_1.unpack(bites2)
    assert recycle2 == tv2
    print('Successfully reunpacked.')
    
    # print(recycle2)
    # print('-----------------------------------------------')
    
    print('-----------------------------------------------')
    print('Starting TV1, TV2 parallel...')
    # print('    ', tv1)
    
    bites1 = tf_1.pack(tv1)
    
    # print('Successfully packed TV1.')
    # print('    ', bytes(bites1))
    
    # print('    ', tv2)
    
    bites2 = tf_1.pack(tv2)
    
    # print('Successfully packed TV2.')
    # print('    ', bytes(bites2))
    
    recycle1 = tf_1.unpack(bites1)
    assert recycle1 == tv1
    print('Successfully reunpacked TV1.')
    
    # print(recycle1)
    
    recycle2 = tf_1.unpack(bites2)
    assert recycle2 == tv2
    print('Successfully reunpacked TV2.')
    
    # print(recycle2)
    
    print('-----------------------------------------------')
    print('Starting (nested) TV3...')
    # print(tv3)
    
    bites3 = tf_nest.pack(tv3)
    
    # print('-----------------------------------------------')
    # print('Successfully packed.')
    # print(bytes(bites3))
    # print('-----------------------------------------------')
    
    recycle3 = tf_nest.unpack(bites3)
    assert recycle3 == tv3
    print('Successfully reunpacked.')
    
    # print(recycle3)
    print('-----------------------------------------------')
    print('Testing toggle...')
    
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
    
    o1 = parent.pack(off)
    o2 = parent.pack(on)
    assert parent.unpack(o1) == off
    assert parent.unpack(o2) == on
    print('Success.')
    
    # -----------------------------------------------------------------
    print('-----------------------------------------------')
    print('Testing listyparser...')
        
    pastr = SmartyParser()    
    pastr['length'] = ParseHelper(parsers.Int8(signed=False))
    pastr['body'] = ParseHelper(parsers.String())
    pastr.link_length('body', 'length')
    
    tag_typed = SmartyParser()
    tag_typed['tag'] = ParseHelper(parsers.Int8(signed=False))
    tag_typed['toggle'] = None
    
    @references(tag_typed)
    def switch(self, tag):
        if tag == 0:
            self['toggle'] = ParseHelper(parsers.Int8(signed=False))
        elif tag == 1:
            self['toggle'] = ParseHelper(parsers.Int16(signed=False))
        elif tag == 2:
            self['toggle'] = ParseHelper(parsers.Int32(signed=False))
        elif tag == 3:
            self['toggle'] = ParseHelper(parsers.Int64(signed=False))
        else:
            self['toggle'] = pastr
    tag_typed['tag'].register_callback('prepack', switch)
    tag_typed['tag'].register_callback('postunpack', switch)
    
    tf_list = ListyParser(parsers=[tag_typed])
    tv_list = [
            {'tag': 0, 'toggle': 5}, 
            {'tag': 1, 'toggle': 51}, 
            {'tag': 65, 'toggle': {'body': 'hello world'}}, 
            {'tag': 2, 'toggle': 3453}
        ]
    tv_list_pack = tf_list.pack(tv_list)
    for it1, it2 in zip(tv_list, tf_list.unpack(tv_list_pack)):
        assert it1 == it2
    print('Success.')
    # assert tf_list.unpack(tv_list_pack) == tv_list
    
    # Can do some kind of check for len of self.obj to determine if there's 
    # only a single entry in the smartyparser, and thereby expand any 
    # objects to pack or objects unpacked.
    
    import IPython
    IPython.embed()