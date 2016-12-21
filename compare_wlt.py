#!/usr/bin/env python3
#
#
import re
import getopt, sys, os
from collections import Counter

# versions
# 2016-12-15 added -t option.
# 2016-12-19 Fixes and improvements

debug = False
def DBG(*strs):
    if debug:
        sys.stderr.write("DBG:"+"".join(str(strs))+"\n")

testfilename = None # -wlt.txt
goldfilename = None
statsmode = False # if -wlt is really -stats, count strategies. Gold is assumed wlt only.
taglen = 255 #compare full tags, otherwise length specified

try:
    opts, args = getopt.getopt(sys.argv[1:], "f:g:st:", [])
except getopt.GetoptError as err:
    print(str(err))
    sys.exit(1)
for o, a in opts:
    if o in ("-f"):
        testfilename = a # wlt output
    elif o in ("-g"): # gold set, always wlt format
         goldfilename = a
    elif o in ("-s"): # the "-f FILE" is a stats file from lemmatiser
         statsmode = True
    elif o in ("-t"): #length of pos tag to compare, "-t 1" for first char only
         taglen = int(a)
    else:
        assert False, "unhandled option"

def remove_hash(lemma):
    if '#' in lemma:
        hidx = lemma.find('#')
        lemma = lemma[0:hidx]
    return lemma

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
            #
            if not statsmode:
                if len(fbits) < 3 or len(gbits) < 3: #need at least 3
                    continue
                # compare word to make sure we are comparing the same data
                if fbits[0] != gbits[0]:
                    if not "," in fbits[0]:
                        print( "DATA DIFF." )
                        print( fl )
                        print( gl )
                        sys.exit(1)
                # Lemma
                if remove_hash(fbits[1]) == remove_hash(gbits[1]):
                    stats["lemma correct"] += 1
                else:
                    stats["lemma wrong"] += 1
                # Tag
                if fbits[2][0:taglen] == gbits[2][0:taglen]:
                    stats["tag correct"] += 1
                else:
                    stats["tag wrong"] += 1
                stats["lines"] += 1
            else:
                # Ἡροδότου        Ἡρόδοτος        Ne-s---mg-      /Ἡροδότου/Ἡρόδοτος/Ne-s---mg-/1/greek_Haudag/   one lemma, but different pos tag
                if len(fbits) != 5 or len(gbits) != 3: # gold file always 3...
                    print( len(fbits), fl )
                    print( len(gbits), gl )
                    sys.exit(1)
                # compare word to make sure we are comparing the same data
                if fbits[0] != gbits[0]:
                    if not "," in fbits[0]: # The frog output had quotes around the ","
                        print( "DATA DIFF." )
                        print( fl )
                        print( gl )
                        sys.exit(1)                
                # Lemma, also pos 1
                if remove_hash(fbits[1]) == remove_hash(gbits[1]):
                    stats["lemma correct"] += 1
                else:
                    stats["lemma wrong"] += 1
                # tag (t) is /ἄνευ/ἄνευ/R----------n/20/proiel/
                t = fbits[3]
                tbits = t.split("/") # ['', 'ἄνευ', 'ἄνευ', 'R----------n', '20', 'proiel', '']
                if len(tbits) != 7:
                    continue
                corpus = tbits[5]
                stats[corpus] += 1
                #print( "["+fbits[2]+"]", "["+gbits[2]+"]")
                if fbits[2][0:taglen] == gbits[2][0:taglen]: #fbits[2] or tbits[3]
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
if total_lemma > 0:
    for x in ["lemma correct", "lemma wrong"]:
        print( "# {0:<40} {1:5n} {2:6.2f}".format(x, stats[x], stats[x]*100.0/total_lemma ) ) 

total_tag = stats["tag correct"] + stats["tag wrong"]
if total_tag > 0:
    for x in ["tag correct", "tag wrong"]:
        print( "# {0:<40} {1:5n} {2:6.2f}".format(x, stats[x], stats[x]*100.0/total_tag ) ) 

