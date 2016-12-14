#!/usr/bin/env python3
#
#
import re
import getopt, sys, os
from unicodedata import normalize

'''
THIS ONE READS COLUMN FORMAT. THIS PROBABLY AFFECTS THE TAGGER (CONTEXT).

(venv) durian:lemmatiser_new pberck
python3 lemmatiser_cltk2.py  -f hdt_Books_forFrog.col.nutt
'''

debug = False
def DBG(*strs):
    if debug:
        sys.stderr.write("DBG:"+"".join(str(strs))+"\n")

try:
    from cltk.stem.lemma import LemmaReplacer
    cltk_lemmatiser = LemmaReplacer('greek')
    from cltk.tag.pos import POSTag
    cltk_tagger = POSTag('greek')
except:
    print(" No CLTK toolkit found." )
    sys.exit(1)

print( "CLTK ok." )

filename = None

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

if not filename:
    sys.exit(0)
    
outfilename = filename + ".CLTK-wlt.txt"
lc = 0

with open(filename, 'r') as f:
    with open(outfilename, 'w') as of:
        for l in f:
            l = l.strip()
            bits = l.split()
            if len(bits) != 3:
                continue
            w = normalize('NFC', bits[0])
            l = normalize('NFC', bits[1])
            t = bits[2]
            lemma = cltk_lemmatiser.lemmatize( w )[0]
            #tag   = cltk_tagger.tag_ngram_123_backoff( w )[0]
            tag   = cltk_tagger.tag_tnt( w )[0]
            # tags are all caps
            # καὶ [('καὶ', 'C--------')]
            # δι’ [('δι', None), ('’', '---------')]
            if '#' in lemma:
                hidx = lemma.find('#')
                lemma = lemma[0:hidx]
            print( w, "\t", lemma, "\t", tag[1], file=of )
            lc += 1
