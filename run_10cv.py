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
import glob
import subprocess 

"""
1.00 2016-10-25

python3 split_10.py -f hdt_Books_forFrog.col -p10
95948 9594
[9594, 9594, 9594, 9594, 9594, 9594, 9594, 9594, 9594, 9602]
OUTPUT: hdt_Books_forFrog.col.cv00
OUTPUT: hdt_Books_forFrog.col.cv01
...
OUTPUT: hdt_Books_forFrog.col.cv08
OUTPUT: hdt_Books_forFrog.col.cv09

python3 run_10cv.py -f 'hdt_Books_forFrog.col.cv??'

['hdt_Books_forFrog.col.cv00', 'hdt_Books_forFrog.col.cv01', 'hdt_Books_forFrog.col.cv02', 'hdt_Books_forFrog.col.cv03', 'hdt_Books_forFrog.col.cv04', 'hdt_Books_forFrog.col.cv05', 'hdt_Books_forFrog.col.cv06', 'hdt_Books_forFrog.col.cv07', 'hdt_Books_forFrog.col.cv08', 'hdt_Books_forFrog.col.cv09']
...[output]...
hdt_Books_forFrog.col.cv09-stats.txt:
# Correct (lemmatised only, no unknowns) 98.26
98.26
# Correct (lcount) 88.8
88.8

Average correct_lcount 89.34
Average correct_lemmatised 98.65
"""

files = []
try:
    opts, args = getopt.getopt(sys.argv[1:], "f:", ["files="])
except getopt.GetoptError as err:
    print( str(err) )
    sys.exit(1)
for o, a in opts:
    if o in ("-f", "--files="):
        files = sorted(glob.glob(a))
    else:
        assert False, "unhandled option"

print( files )

for n, f in enumerate(files):
    cmd = [ "python3", "lemmatiser.py", "-f", f, "-o", f ]
    print( "\n--------\n" )
    print( " ".join(cmd) )
    x = subprocess.run( cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True )
    out = x.stdout
    for l in str(out).split('\n'):
        if "SKIP" not in l:
            print( l )

print( "\n----------------\n" )

'''
The regexpen are hard coded for the grepped lemmatiser output:
hdt_Books_forFrog.col.cv02-stats.txt:
# Correct (lemmatised only, no unknowns) 98.61
# Correct (lcount) 89.37
'''
correct_lcount = 0;
pattern0 = re.compile(r"# Correct \(lcount\) ([\d.]+)", re.UNICODE)
correct_lemmatised = 0;
pattern1 = re.compile(r"# Correct \(lemmatised only, no unknowns\) ([\d.]+)", re.UNICODE)

num_res = 0
for n, f in enumerate(files):
    cmd = [ "grep", "Correct", f + "-stats.txt" ]
    print( f + "-stats.txt:" )
    x = subprocess.run( cmd, stdout=subprocess.PIPE, universal_newlines=True )
    out = x.stdout
    num_res += 1
    for l in str(out).split('\n'):
        print( l )
        m = re.search(pattern0, l)
        if m:
            #print( m.group(1) )
            correct_lcount += float(m.group(1))
        m = re.search(pattern1, l)
        if m:
            #print( m.group(1) )
            correct_lemmatised += float(m.group(1))

print( "Average correct_lcount", round(correct_lcount / num_res, 2) )
print( "Average correct_lemmatised", round(correct_lemmatised / num_res, 2) )
