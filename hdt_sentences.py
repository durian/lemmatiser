#!/usr/bin/env python3
#
#
import re
import getopt, sys, os

debug = False
def DBG(*strs):
    if debug:
        sys.stderr.write("DBG:"+"".join(str(strs))+"\n")

filename = "hdt_Books_forFrog.col"

try:
    opts, args = getopt.getopt(sys.argv[1:], "f:", [])
except getopt.GetoptError as err:
    print(str(err))
    sys.exit(1)
for o, a in opts:
    if o in ("-f"):
        filename = a
    else:
        assert False, "unhandled option"

outfilename = filename + ".s"
s = []

with open(filename, 'r') as f:
    with open(outfilename, 'w') as of:
        for l in f:
            l = l.strip()
            if l.startswith("<utt>"):
                print( " ".join(s), file=of )
                s = []
                continue
            bits = l.split()
            if len(bits) != 3:
                continue
            s.append( bits[0] )
