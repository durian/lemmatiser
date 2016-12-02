#!/usr/bin/env python3
#
#
import re
import getopt, sys, os
from collections import Counter


debug = False
def DBG(*strs):
    if debug:
        sys.stderr.write("DBG:"+"".join(str(strs))+"\n")

testfilename = None
goldfilename = None

try:
    opts, args = getopt.getopt(sys.argv[1:], "f:g:", [])
except getopt.GetoptError as err:
    print(str(err))
    sys.exit(1)
for o, a in opts:
    if o in ("-f"):
        testfilename = a
    elif o in ("-g"): #lookup a lemma
         goldfilename = a
    else:
        assert False, "unhandled option"

stats = Counter()
    
with open(testfilename, 'r') as f:
    with open(goldfilename, 'r') as g:
        for fl in f:
            gl = g.readline()
            fbits = fl.split()
            gbits = gl.split()
            if len(fbits) != 3 or len(gbits) != 3:
                continue
            # Lemma
            if fbits[1] == gbits[1]:
                stats["lemma correct"] += 1
            else:
                stats["lemma wrong"] += 1
            # Tag
            if fbits[2] == gbits[2]:
                stats["tag correct"] += 1
            else:
                stats["tag wrong"] += 1

total_lemma = stats["lemma correct"] + stats["lemma wrong"]
for x in ["lemma correct", "lemma wrong"]:
    print( "# {0:<40} {1:5n} {2:6.2f}".format(x, stats[x], stats[x]*100.0/total_lemma ) ) 

total_tag = stats["tag correct"] + stats["tag wrong"]
for x in ["tag correct", "tag wrong"]:
    print( "# {0:<40} {1:5n} {2:6.2f}".format(x, stats[x], stats[x]*100.0/total_tag ) ) 

