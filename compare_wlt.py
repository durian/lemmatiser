#!/usr/bin/env python3
#
#
import re
import getopt, sys, os
from collections import Counter
from unicodedata import normalize

# versions
# 2016-12-15 added -t option.
# 2016-12-19 Fixes and improvements
# 2017-01-06 Lowercasing, normalisation, stripping of bits, error file

# --------
# Compares two wlt files, or one stats and one wlt file.
# example:
# python3 compare_wlt.py -f hdt_Books_forFrog.col.nutt.CLTK-wlt.txt -g hdt_Books_forFrog.col.nutt 
# --------

debug = False
def DBG(*strs):
    if debug:
        sys.stderr.write("DBG:"+"".join(str(strs))+"\n")

testfilename = None # -wlt.txt
goldfilename = None
statsmode = False # if -wlt is really -stats, count strategies. Gold is assumed wlt only.
taglen = 255 #compare full tags, otherwise length specified with -t option
lc = False
norm = False # Unicode normalisation

try:
    opts, args = getopt.getopt(sys.argv[1:], "f:g:lnst:", [])
except getopt.GetoptError as err:
    print(str(err))
    sys.exit(1)
for o, a in opts:
    if o in ("-f"):
        testfilename = a # wlt output
    elif o in ("-g"): # gold set, always wlt format
         goldfilename = a
    elif o in ("-l"): # Lowercase tokens before comparing
         lc = True
    elif o in ("-n"): # Normalise tokens
         norm = True
    elif o in ("-s"): # the "-f FILE" is a stats file from lemmatiser
         statsmode = True
    elif o in ("-t"): #length of pos tag to compare, "-t 1" for first char only
         taglen = int(a)
    else:
        assert False, "unhandled option"

outfile_l = testfilename + ".lemma_errors"

def remove_hash(lemma):
    if '#' in lemma:
        hidx = lemma.find('#')
        lemma = lemma[0:hidx]
    return lemma

stats  = Counter()
errors = Counter()

with open(testfilename, 'r') as f:
    with open(goldfilename, 'r') as g:
        for fl in f:
            if len(fl) > 0 and fl[0] == "#":
                continue
            gl = g.readline()
            if len(gl) > 0 and gl[0] == "#":
                continue
            fbits = fl.split('\t')
            fbits = [foo.strip() for foo in fbits]
            gbits = gl.split('\t')
            gbits = [foo.strip() for foo in gbits]
            #
            fbits[1] = remove_hash(fbits[1])
            gbits[1] = remove_hash(gbits[1])
            # Lowercase word and lemma
            # fl = [ foo.lower() for foo in fl[0:2]] + fl[2:]
            if lc:
                fbits[0] = fbits[0].lower()
                gbits[0] = gbits[0].lower()
                fbits[1] = fbits[1].lower()
                gbits[1] = gbits[1].lower()
            # Normalise (before or after lc?)
            if norm:
                fbits[0] = normalize('NFC', fbits[0])
                gbits[0] = normalize('NFC', gbits[0])
                fbits[1] = normalize('NFC', fbits[1])
                gbits[1] = normalize('NFC', gbits[1])
            #
            # Compare
            #
            if not statsmode:
                if len(fbits) < 3 or len(gbits) < 3: #need at least 3
                    continue
                # compare word to make sure we are comparing the same data
                if fbits[0] != gbits[0]:
                    if not "," in fbits[0]:
                        print( "DATA DIFF." )
                        print( "["+fbits[0]+"]" )
                        print( "["+gbits[0]+"]" )
                        sys.exit(1)
                # Lemma
                if fbits[1] == gbits[1]:
                    stats["lemma correct"] += 1
                else:
                    stats["lemma wrong"] += 1
                    errors[ fbits[1]+" "+gbits[1] ] += 1
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
                        print( "["+fbits[0]+"]" )
                        print( "["+gbits[0]+"]" )
                        sys.exit(1)                
                # Lemma, also pos 1
                if fbits[1] == gbits[1]:
                    stats["lemma correct"] += 1
                else:
                    stats["lemma wrong"] += 1
                    errors[ fbits[1]+" "+gbits[1] ] += 1
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

callstr = " ".join(sys.argv)
print( "#", callstr )
print( "# Lemma errors in", outfile_l )

for stat, count in sorted(stats.items()):
    #for stat, count in lemmatiser_stats.most_common():
    print( "# {0:<71} {1:5n}".format(stat, count) )
            
total_lemma = stats["lemma correct"] + stats["lemma wrong"]
if total_lemma > 0:
    for x in ["lemma correct", "lemma wrong"]:
        print( "# {0:<40} {1:5n} {2:6.2f}".format(x, stats[x], stats[x]*100.0/total_lemma) ) 

total_tag = stats["tag correct"] + stats["tag wrong"]
if total_tag > 0:
    for x in ["tag correct", "tag wrong"]:
        print( "# {0:<40} {1:5n} {2:6.2f}".format(x, stats[x], stats[x]*100.0/total_tag) ) 

with open(outfile_l, "w") as of:
    print( "#", callstr, file=of )
    for x in ["lemma correct", "lemma wrong"]:
        print( "# {0:<40} {1:5n} {2:6.2f}".format(x, stats[x], stats[x]*100.0/total_lemma), file=of )
    print( "{0:<61} {1}".format("# Test Gold", "Count"), file=of )
    for x in errors.most_common():
        print( "{0:<61} {1:5n}".format(x[0], x[1]), file=of )
