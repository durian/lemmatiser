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

# -----

We should count both .txt and .ann files.

The .txt files for the general statistics, number of sentences/words, etc.

The .ann files to count the complements etc.
'''

filenames = [] # Should be the *.txt files, and we figure out the .ann names from these
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
#
stats["compl"] = 0 # number of complements

long = {}
long["fc"] = "Aantal bestanden"
long["wc"] = "Aantal woorden"
long["sc"] = "Aantal zinnen"
#
long["compl"] = "Aantal 'Complement' annotaties"

# ----
# Process
# ----

for filename in filenames:
    filebase, fileext = os.path.splitext(filename)
    if not fileext == ".txt":
        continue
    # We read the .txt file first, which should be the plain filename we supplied.
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
    # ----
    # We read the .ann file next
    # ----
    filename = filebase + ".ann"
    if not os.path.isfile( filename ):
        print( "ERROR: annotation file not found.", file=sys.stderr )
        sys.exit(1)
    print( "FILE:", filename, file=sys.stderr )
    complement = {}
    with open(filename, 'r') as f:
        for l in f:
            l = l.strip()
            bits = l.split("\t")
            if len(bits) != 3:
                continue
            # T4      Complement 46 156       αὖθις μείζονι...
            ann_id   = bits[0]
            ann_info = bits[1].split()
            ann_type = ann_info[0]
            words = [ normalize('NFC', w) for w in bits[2].split() ]
            if ann_type == "Complement":
                # Write out/count the current complement
                if complement:
                    print( repr(complement) )
                stats["compl"] += 1
                #complement[
    
for stat, count in sorted(stats.items()):
    print( "{0:<40} {1:5n}".format(long[stat], count) )
