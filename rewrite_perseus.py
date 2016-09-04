# python3
#
# 2016-03-22
# Eerste conversie SQL dump - de output heeft een tweede conversie slag nodig
# om de complexere P tags erin te zetten.
#
import re
import getopt, sys, os
from collections import Counter

'''
In Perseus betekent dit dat er na positie 1 een positie wordt tussengevoegd,
die by default wordt ingevuld met -, maar bij de categorie P een letter kan
krijgen (later).

Verder blijft alles staan behalve dat als er in Perseus op positie 1 een t
staat, daar een v komt te staan en dan op positie 5 (of 6, als bovenstaande al
is doorgevoerd) een p komt.

python3 rewrite_perseus.py -f hib_sqldump_word_lemma_tag.utf8 > hib_sql.out.txt

Input formaat:
ἀβουλία νσφγ n-s---fg-
ἀβουλία νσφγ n-s---fg-
ἁβρότησ νσφγ n-s---fg-
ἁβρότησ νσφγ n-s---fg-
Ἄβυδοσ νσφγ n-s---fg-
...

Output:
ἀάατοσ ασφα A--s---fa-
ἀάατοσ ασφα A--s---fa-
ἀάατοσ ασφν A--s---fn-

2016-04-12
(venv) durian:lemmatiser pberck
python3 rewrite_perseus.py -f 04_perseus/d638f82gs4.txt.utf8b > 04_perseus/d638f82gs4.txt.utf8b.rwrt

2016-05-02
Extra filtering voor "rare karakters"

'''

afile = None

try:
    opts, args = getopt.getopt(sys.argv[1:], "f:P", [])
except getopt.GetoptError as err:
    print(str(err))
    sys.exit(1)
for o, a in opts:
    if o in ("-f"):
        afile = a
    else:
        assert False, "unhandled option"

output = Counter()
dubbels = 0
with open(afile, 'r') as f:
    for l in f:
        l = l.strip()
        bits = l.split()
        if len(bits) != 3:
            continue
        tag = bits[2]
        # 2016-05-02 extra filter
        b0 = bits[0]
        b1 = bits[1]
        for c in "^-)—/—+": #ἀλγείν’ ἄπισθ’
            #τἀμ’ ἡμός A--s---fd-  #OK apostrofe was OK
            #’μῇ ἡμός A--s---fd-
            #’μ’ ἡμός A--s---fd-
            bits[0] = bits[0].replace(c, '') #is this UTF8 safe?
            bits[1] = bits[1].replace(c, '')
        '''
        if b0 != bits[0]:
            print( "DIFF", b0, bits[0] )
        if b1 != bits[1]:
            print( "DIFF", b1, bits[1] )
        '''
        # -- end extra filter
        #print( tags )
        if tag[0] in "vnadgcrpm":
            tag = tag[0].upper() + '-' + tag[1:] #eerste letter -> hoofdletter
        if tag[0] == 't':
            # ἀγωνίζομαι τσρεφϝ V--srpefv-
            # t-sr-ema-
            # 12345
            # V--srpema-
            # 123456
            tag = 'V-' + tag[1:4] + 'p' + tag[5:]
        if tag[0] == 'e':
            tag = 'I-' + tag[1:]
        # 2015-05-02 ontdubbelen
        out = bits[0]+' '+bits[1]+' '+tag
        if not out in output:
            print( out )
            output[out] = 1
        else:
            dubbels += 1
sys.stderr.write("Dubbels: "+str(dubbels)+"\n" )
