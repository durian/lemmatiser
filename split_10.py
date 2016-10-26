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
Split a file into equal parts.

Small files can give strange distributions:
python3 split_10.py -f bar -p10
21 2
[2, 2, 2, 2, 2, 2, 2, 2, 2, 3]

but:

python3 split_10.py -f bar -p12
21 1
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 10]

python3 split_10.py -f hdt_Books_forFrog.col -p10
95948 9594
[9594, 9594, 9594, 9594, 9594, 9594, 9594, 9594, 9594, 9602]

1.00 2016-10-25
"""

parts     = 10
afile     = None

try:
    opts, args = getopt.getopt(sys.argv[1:], "f:p:", ["file="])
except getopt.GetoptError as err:
    print( str(err) )
    sys.exit(1)
for o, a in opts:
    if o in ("-f", "--file="):
        afile = a 
    elif o in ("-p"): 
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

with open(afile) as fi:
    for p in range(parts):
        file_out = afile+".cv"+'{0:02n}'.format(p)
        with open( file_out, "w" ) as fo:
            print( "OUTPUT:", file_out )
            for x in range(fold_sizes[p]):
                l = fi.readline()
                fo.write(l)

