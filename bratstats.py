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

class Complement:
    # T13	Complement 96 153	ἐν μέρει τινὶ τῆς χώρας Κύκλωπες καὶ Λαιστρυγόνες οἰκῆσαι
    def __init__(self, id):
        self.id   = id
        self.type = "?"
        self.words = []
        self.head = "?" 
        self.span = [] # pairs of [start, end]
    def __repr__(self):
        return "|"+self.id+"|"
    def __str__(self):
        return "Complement:"+self.id+" type:"+self.type+" words:"+str(len(self.words))+" span:"+repr(self.span)
    
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
stats["compl_i"] = 0 # indirect
stats["compl_d"] = 0 # direct
stats["compl_np"] = 0 

long = {}
long["fc"] = "Aantal bestanden"
long["wc"] = "Aantal woorden"
long["sc"] = "Aantal zinnen"
#
long["compl"] = "Aantal 'Complement' annotaties"
long["compl_i"] = "Aantal indirekte 'Complement' annotaties"
long["compl_d"] = "Aantal direkte 'Complement' annotaties"
long["compl_np"] = "Aantal NP 'Complement' annotaties"
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
    complements = {} # Complements by id
    with open(filename, 'r') as f:
        for l in f:
            l = l.strip()
            bits = l.split("\t")
            if len(bits) < 2:
                continue
            # T4      Complement 46 156       αὖθις μείζονι...
            ann_id   = bits[0]
            ann_info = bits[1].split()
            ann_type = ann_info[0]
            if len(bits) == 3:
                words = [ normalize('NFC', w) for w in bits[2].split() ]
            else:
                words = []
            if ann_type == "Complement": #compl-head compl-chunk ?
                # Write out/count the current complement
                # Or save all of them, because the order is random in the .ann files?
                complements[ann_id] = Complement(ann_id)
                # spans could look like this:
                '''
                T13 Complement 96 153
                T17 Complement 156 158;163 173
                '''
                spans = " ".join(ann_info[1:]) # The string after "Complement"
                for span in spans.split(";"): # spans are seperated by a ";"
                    xy = span.split() # and consist of a start and end position
                    if len(xy) == 2:
                        complements[ann_id].span.append( [int(xy[0]),int(xy[1])] )
                    else:
                        print( "ERROR" )
                        sys.exit(2)
                stats["compl"] += 1
                complements[ann_id].words = words
                print( complements[ann_id] )
            # We build up the Complements first, count when file is done
            if ann_type == "compl-type":
                # compl-type T6 indirect
                # print( bits )
                compl_id   = ann_info[1] #points to the Complement id
                compl_type = ann_info[2]
                complements[compl_id].type = compl_type
                print( complements[compl_id] )

for stat, count in sorted(stats.items()):
    try:
        print( "{0:<40} {1:5n}".format(long[stat], count) )
    except KeyError:
        print( "# {0:<40} {1:5n}".format(stat, count) )
