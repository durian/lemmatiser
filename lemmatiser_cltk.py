#!/usr/bin/env python3
#
#
import re
import getopt, sys, os
from unicodedata import normalize

'''
(venv) durian:lemmatiser_new pberck
python3 lemmatiser_cltk.py  -f hdt_Books_forFrog.col.s
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
            ln = normalize('NFC', l)
            lemmas = cltk_lemmatiser.lemmatize( ln )
            tags   = cltk_tagger.tag_ngram_123_backoff( ln )
            words = ln.split()
            '''
            print( "words" )
            for w in words:
                print( w )
            print( "lemmas" )
            for l in lemmas:
                print( l )
            print( "tags" )
            for t in tags:
                print( t )
            '''
            assert len(words) == len(lemmas) == len(tags), "Truncated output? %r %r %r %r" % (len(words), len(lemmas), len(tags), lc)
            for w in words:
                lemma = lemmas.pop()
                tag = tags.pop()
                if len(tag) != 2:
                    print( "ERROR IN TAG" )
                    sys.exit(2)
                print( w, "\t", lemma, "\t", tag[1], file=of )
            lc += 1
