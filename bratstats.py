# python3
#
# 2017-01-13 Version 1

import re, glob
import getopt, sys, os
from unicodedata import normalize
from collections import Counter

'''
Counts statistics on brat .txt and .ann files

Dit is een lijstje met aantallen die ik graag zou willen weten:

number of words
number of sentences
number of complements
number of complements that contain a root
average number of word of complements, in general and for direct vs indirect complements
number of direct complements
number of indirect complements
number of NP complements
number of mixed complements
do attitude verbs occur with direct complements?
do δὴ and δή occur in complements? (mogen samen genomen worden)
do γὰρ and γάρ occur in a complement after root (mogen samengenomen worden, hoeft niet per se meteen achter root, maar ergens daarna)

'''

filenames = []
filename  = None

try:
    opts, args = getopt.getopt(sys.argv[1:], "f:", [])
except getopt.GetoptError as err:
    print(str(err))
    sys.exit(1)
for o, a in opts:
    if o in ("-f"):
        filenames = sorted(glob.glob(a))
    else:
        assert False, "unhandled option"

stats = Counter()
stats["fc"] = 0 # file count
stats["wc"] = 0 # word count
stats["sc"] = 0 # sentence count

long = {}
long["fc"] = "Aantal bestanden"
long["wc"] = "Aantal woorden"
long["sc"] = "Aantal zinnen"

for filename in filenames:
    print( "FILE:", filename, file=sys.stderr )
    with open(filename, 'r') as f:
        stats["fc"] += 1
        for l in f:
            l = l.strip()
            words = l.split()
            if not words:
                continue
            if words[0] == "ROOT":
                words = words[1:]
            # We normalise all Greek we read nowadays.
            words = [ normalize('NFC', w) for w in words ]
            stats["wc"] += len(words)
            stats["sc"] += 1

for stat, count in sorted(stats.items()):
    print( "{0:<40} {1:5n}".format(long[stat], count) )
