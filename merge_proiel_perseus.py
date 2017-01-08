# python3
#
# Merget de twee output files van rewrite_proiel en rewrite_perseus.
# 2016-06-15:
#  python3 merge_proiel_perseus.py -f greek_Haudag.pcases.lemma.lex.rewrite -F perseus-wlt.txt > proiel_v2_perseus_merged.txt
#
# 2017-01-08 We made a new greek_Haudag.pcases.lemma.lex.rewrite_new, so a new merge

import re
import getopt, sys, os
from collections import Counter

'''
This one merges w/o counts.... need a new version? Is it stil relevant?
'''

proifile = None
persfile = None

try:
    opts, args = getopt.getopt(sys.argv[1:], "f:F:", [])
except getopt.GetoptError as err:
    print(str(err))
    sys.exit(1)
for o, a in opts:
    if o in ("-f"):
        proifile = a
    elif o in ("-F"):
        persfile = a
    else:
        assert False, "unhandled option"
 
proi = Counter()
pers = Counter()
proi_w = Counter()
pers_w = Counter()
proi_l = Counter()
pers_l = Counter()
proi_t = Counter()
pers_t = Counter()
with open(proifile, 'r') as f:
    for l in f:
        l = l.strip()
        bits = l.split()
        if len(bits) != 4: #or 3? Counts are ignored anyway?, the rewrite_new has counts
            continue
        proi_w[bits[0]] += 1 #words
        proi_l[bits[1]] += 1 #lemma
        proi_t[bits[2]] += 1 #tag
        proi[l] += 1
sys.stderr.write("\nPROIEL\n")
sys.stderr.write("Number of WLP {0}\n".format(len(proi)))
sys.stderr.write("Most common: {0}\n".format( Counter(proi).most_common(1) ))
sys.stderr.write("Number of W   {0}\n".format(len(proi_w)))
sys.stderr.write("Most common: {0}\n".format( Counter(proi_w).most_common(3) ))
sys.stderr.write("Number of L   {0}\n".format(len(proi_l)))
sys.stderr.write("Most common: {0}\n".format( Counter(proi_l).most_common(3) ))
sys.stderr.write("Number of T   {0}\n".format(len(proi_t)))
sys.stderr.write("Most common: {0}\n".format( Counter(proi_t).most_common(3) ))

with open(persfile, 'r') as f:
    for l in f:
        l = l.strip()
        bits = l.split()
        if len(bits) != 3:
            continue
        pers_w[bits[0]] += 1 #words
        pers_l[bits[1]] += 1 #lemma
        pers_t[bits[2]] += 1 #tag
        pers[l] += 1

sys.stderr.write("\nPERSEUS\n")
sys.stderr.write("Number of WLP {0}\n".format(len(pers)))
sys.stderr.write("Most common: {0}\n".format( Counter(pers).most_common(1) ))
sys.stderr.write("Number of W   {0}\n".format(len(pers_w)))
sys.stderr.write("Most common: {0}\n".format( Counter(pers_w).most_common(3) ))
sys.stderr.write("Number of L   {0}\n".format(len(pers_l)))
sys.stderr.write("Most common: {0}\n".format( Counter(pers_l).most_common(3) ))
sys.stderr.write("Number of T   {0}\n".format(len(pers_t)))
sys.stderr.write("Most common: {0}\n".format( Counter(pers_t).most_common(3) ))

# Set theory
sys.stderr.write("\nWLP Intersection, PROIEL-PERSEUS\n")
merged = Counter()
merged = proi & pers 
sys.stderr.write("Number of merged {0}\n".format(len(merged)))
sys.stderr.write("Most common: {0}\n".format( Counter(merged).most_common(1) ))
#
sys.stderr.write("\nW Intersection, PROIEL-PERSEUS\n")
merged_w = Counter()
merged_w = proi_w & pers_w 
sys.stderr.write("Number of merged_w {0}\n".format(len(merged_w)))
sys.stderr.write("Most common: {0}\n".format( Counter(merged_w).most_common(3) ))
#
sys.stderr.write("\nL Intersection, PROIEL-PERSEUS\n")
merged_l = Counter()
merged_l = proi_l & pers_l 
sys.stderr.write("Number of merged_l {0}\n".format(len(merged_l)))
sys.stderr.write("Most common: {0}\n".format( Counter(merged_l).most_common(3) ))
#
sys.stderr.write("\nT Intersection, PROIEL-PERSEUS\n")
merged_t = Counter()
merged_t = proi_t & pers_t 
sys.stderr.write("Number of merged_t {0}\n".format(len(merged_t)))
sys.stderr.write("Most common: {0}\n".format( Counter(merged_t).most_common(3) ))

# ---

# Merging
sys.stderr.write("\nPROIEL-PERSEUS\n")

merged_wl = Counter() # eerst overlap bekijken

sys.stderr.write("\nBefore merge, PROIEL-PERSEUS\n")
for l in proi:
    bits = l.split()
    wl = bits[0] +" "+ bits[1]
    t = bits[2] # + " P"
    #merged_wl[wl] += 1
    if wl in merged_wl:
        merged_wl[wl].append(t)
    else:
        merged_wl[wl] = [t]
sys.stderr.write("len(merged_wl) = {0}\n".format(len(merged_wl)))
sys.stderr.write("{0}\n".format( Counter(merged_wl).most_common(3) ))

skips = 0
for l in pers:
    bits = l.split()
    wl = bits[0] +" "+ bits[1]
    if wl in merged_wl: #als al in merged_wl, niet toevoegen?
        #merged_wl[wl].append(bits[2])
        #sys.stderr.write("Skipping {0} {1}\n".format( l, merged_wl[wl] ))
        skips += 1
        pass
    else:
        merged_wl[wl] = [bits[2]]
        
sys.stderr.write("\nAfter merge, PROIEL-PERSEUS\n")
sys.stderr.write("len(merged_wl) = {0}\n".format(len(merged_wl)))
sys.stderr.write("{0}\n".format( Counter(merged_wl).most_common(3) ))
sys.stderr.write("Skipped {0}\n".format(skips))

sys.stderr.write("\nMERGED OUTPUT\n")
for wl in merged_wl:
    tags = merged_wl[wl]
    for t in tags:
        print( wl+" "+t )

    
#sys.stderr.write("{0}\n".format(len(merged)))
#mx = max(merged.keys(), key=(lambda k: merged[k]))
#print ( mx, merged[mx] )
#top-3 frequent
#s = sorted(merged, key=merged.get, reverse=True)
#for i in range(0,4,1):
#    sys.stderr.write( "{0}, {1}, {2}\n".format(i, s[i], merged[s[i]]) )
