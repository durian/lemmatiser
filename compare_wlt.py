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

testfilename = None # -wlt.txt
goldfilename = None
statsmode = False # if -wlt is relly -stats

try:
    opts, args = getopt.getopt(sys.argv[1:], "f:g:s", [])
except getopt.GetoptError as err:
    print(str(err))
    sys.exit(1)
for o, a in opts:
    if o in ("-f"):
        testfilename = a
    elif o in ("-g"): #lookup a lemma
         goldfilename = a
    elif o in ("-s"): #lookup a lemma
         statsmode = True
    else:
        assert False, "unhandled option"

stats = Counter()

with open(testfilename, 'r') as f:
    with open(goldfilename, 'r') as g:
        for fl in f:
            if len(fl) > 0 and fl[0] == "#":
                continue
            gl = g.readline()
            if len(gl) > 0 and gl[0] == "#":
                continue
            fl = fl.strip()
            gl = gl.strip()
            fbits = fl.split('\t')
            gbits = gl.split('\t')
            if not statsmode:
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
                stats["lines"] += 1
            else:
                # Ἡροδότου        Ἡρόδοτος        Ne-s---mg-      /Ἡροδότου/Ἡρόδοτος/Ne-s---mg-/1/greek_Haudag/   one lemma, but different pos tag
                if len(fbits) != 5 or len(gbits) != 3:
                    print( fl, gl )
                    continue
                # Lemma, also pos 1
                if fbits[1] == gbits[1]:
                    stats["lemma correct"] += 1
                else:
                    stats["lemma wrong"] += 1
                # tag (t) is /ἄνευ/ἄνευ/R----------n/20/proiel/
                t = fbits[3]
                tbits = t.split("/") # ['', 'ἄνευ', 'ἄνευ', 'R----------n', '20', 'proiel', '']
                if len(tbits) != 7:
                    continue
                corpus = tbits[5]
                #print( "["+fbits[2]+"]", "["+gbits[2]+"]")
                if fbits[2] == gbits[2]: #fbits[2] or tbits[3]
                    stats["tag correct"] += 1
                    stats["tag correct"+"/"+corpus] += 1
                    stats[fbits[4]+"/correct"] += 1
                    stats[fbits[4]+"/"+corpus+"/correct"] += 1
                else:
                    stats["tag wrong"] += 1
                    stats["tag wrong"+"/"+corpus] += 1
                    stats[fbits[4]+"/wrong"] += 1
                    stats[fbits[4]+"/"+corpus+"/wrong"] += 1
                # extra info
                stats[fbits[4]] += 1
                stats["lines"] += 1

for stat, count in sorted(stats.items()):
    #for stat, count in lemmatiser_stats.most_common():
    print( "# {0:<71} {1:5n}".format(stat, count) )
            
total_lemma = stats["lemma correct"] + stats["lemma wrong"]
for x in ["lemma correct", "lemma wrong"]:
    print( "# {0:<40} {1:5n} {2:6.2f}".format(x, stats[x], stats[x]*100.0/total_lemma ) ) 

total_tag = stats["tag correct"] + stats["tag wrong"]
for x in ["tag correct", "tag wrong"]:
    print( "# {0:<40} {1:5n} {2:6.2f}".format(x, stats[x], stats[x]*100.0/total_tag ) ) 

