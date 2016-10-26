#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
import getopt
import sys
import time
import os
import datetime
import random
import re

"""
Split a file into 90-10 parts.

Small files can give strange distributions:
python3 split_10cv.py -f bar -p10
21 2
[2, 2, 2, 2, 2, 2, 2, 2, 2, 3]

but:

python3 split_10cv.py -f bar -p12
21 1
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 10]

1.00 2016-10-26
"""

parts     = 10 # number of splits
part      =  0 # test file part
afile     = None

try:
    opts, args = getopt.getopt(sys.argv[1:], "f:p:P:", ["file="])
except getopt.GetoptError as err:
    print( str(err) )
    sys.exit(1)
for o, a in opts:
    if o in ("-f", "--file="):
        afile = a 
    elif o in ("-p"): 
        part = int(a)
    elif o in ("-P"): 
        parts = int(a)
    else:
        assert False, "unhandled option"

if parts < 1:
    print( "More than this!" )
    sys.exit(1)

def file_len(fname):
    i = 0
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1

num_lines = file_len(afile)
fold_size = int(num_lines/parts)
print( num_lines, fold_size )
fold_sizes = [fold_size] * parts
fold_sizes[parts-1] = num_lines - ( (parts-1)*fold_size )
print( fold_sizes )

# If part == 2
# [2, 2, 2, 2, 2, 2, 2, 2, 2, 3]
#        ^
#       test
# rest is train

test_start = sum( fold_sizes[0:part] )
test_end = test_start + fold_sizes[part]

file_out_train = afile+".cv"+'{0:02n}'.format(part)+".train"
file_out_test  = afile+".cv"+'{0:02n}'.format(part)+".test"

print( parts, part, test_start, test_end )
print( file_out_train )
print( file_out_test )

lc = 0
with open(afile) as fi:
    with open( file_out_train, "w" ) as fo_train:
        with open( file_out_test, "w" ) as fo_test:
            for l in fi:
                if test_start <= lc < test_end:
                    fo_test.write( l )
                else:
                    fo_train.write( l )
                lc += 1

