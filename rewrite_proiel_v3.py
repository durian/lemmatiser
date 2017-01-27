# python3
#
# 2016-03-22 Bug fix after Skype call
# 2016-06-15 Adapted for new greek_Haudag.pcases.lemma.lex
# 2017-01-07 New version 3 with new rewrite rules
# 2017-01-08 Fixes
# 2017-01-27 More small fixes

import re
import getopt, sys, os
from unicodedata import normalize

'''
Transformaties op PROIEL tags (de volgorde is belangrijk):

*) positie 11 (strength) en 12 (inflection) komen te vervallen (dus van 12 posities terug naar 10).
*) Bij positie 10 wordt p herschreven tot -. 
*) Ne en Nb worden N-
*) Ma en Mo worden M-
*) alle woorden die G zijn in PROIEL worden C 
*) alle woorden die [ Df zijn in PROIEL EN in Perseus-wlt G] zijn worden G 
   (dus in 2 lexicons checken)
Let op: niet alle woorden die Df zijn in PROIEL moeten G worden, alleen die die in Perseus G zijn.
(we willen graag de partikels als aparte groep houden, vandaar deze kant op)

*) alle D* woorden (dwz rest Df, Du of Dq) die dan nog in PROIEL staan worden D-. 

USAGE: python3 rewrite_proiel_v3.py > greek_Haudag.pcases.lemma.lex.rewrite_new

DATA:
greek_Haudag.pcases.lemma.lex:
ἀλλήλων	ἀλλήλων	Pc-p---mg--i	25
ἀλλήλων	ἀλλήλων	Pc-p---ng--i	4
ἀλληλέων	ἀλληλέων	Pc-p---fg--i	2
ἀλληλέων	ἀλληλέων	Pc-p---mg--i	1
ἀλλήλοις	ἀλλήλων	Pc-p---md--i	5
ἀλλήλοις	ἀλλήλων	Pc-p---nd--i	2

OUTPUT TO STDOUT (suitable for lemmatiser_clam.py):
ἀλλήλων ἀλλήλων Pc-p---mg- 25
ἀλλήλων ἀλλήλων Pc-p---ng- 4
'''

afile = "greek_Haudag.pcases.lemma.lex"
pfile = "perseus-wlt.txt" 
simplify = False

try:
    opts, args = getopt.getopt(sys.argv[1:], "f:p:s", [])
except getopt.GetoptError as err:
    print(str(err))
    sys.exit(1)
for o, a in opts:
    if o in ("-f"):
        afile = a
    elif o in ("-p"):
        pfile = a
    elif o in ("-s"):
        simplify = True
    else:
        assert False, "unhandled option"

print( "GREEK HAUDAG FILE:", afile, file=sys.stderr )
print( "PERSEUS WLT FILE: ", pfile, file=sys.stderr )

# This is a one time thing, we read pwlt and keep it in memory. Unicode normalisation,
# ἀάατον ἀάατος A--s---fa-
# ἀάατος ἀάατος A--s---fn-
perseus = {} # word -> tag
with open(pfile, 'r') as f:
    for l in f:
        l = l.strip()
        bits = l.split()
        if len(bits) != 3:
            continue
        w = normalize('NFC', bits[0])
        l = normalize('NFC', bits[1])
        t = bits[2]
        # words plus lemma in perseus{} ?
        e = w + " " + l
        if e not in perseus:
            perseus[e] = t
print( pfile, "contains", len(perseus), "unique entries.", file=sys.stderr )

print( "REWRITING", afile, file=sys.stderr )
# Count NOPE and other entries
nope_cnt = 0
skipped  = 0
checked_in_perseus = 0
df_is_g_in_p = 0
with open(afile, 'r') as f:
    for l in f:
        l = l.strip()
        bits = l.split()
        # Ῥωμαῖοι	Ῥωμαῖος	A--p---mnp-i	2
        if len(bits) != 4:
            skipped += 1
            print( "SKIP:", l, "[wrong number of elements]", file=sys.stderr )
            continue
        if bits[1] == "NOPE": #hier was geen lemma beschikbaar
            nope_cnt += 1
            print( "NOPE:", l, "[lemma is NOPE]", file=sys.stderr )
            continue
        word  = normalize('NFC', bits[0])
        lemma = normalize('NFC', bits[1])
        tags  = bits[2:]
        # We have (had?) more tag-freq pairs per entry, so we enumerate.
        for n, k in enumerate(tags[:-1]):
            t = tags[n]    #tag
            f = tags[n+1]  #freq
            #print( t,f )
            if len(t) == 12:
                t = t[0:10] #laatste twee weghalen
                if t[9] == "p":
                    t = t[0:9]+"-" #t[9] = '-'
                if t[0:2] == "Ne" or t[0:2] == "Nb":
                    t = "N-"+t[2:]
                if t[0:2] == "Ma" or t[0:2] == "Mo":
                    t = "M-"+t[2:]
                if t[0:1] == "G":
                    t = "C"+t[1:]
                if t[0:2] == "Df": # check perseus for this one
                    e = word + " " + lemma
                    if e in perseus:
                        perseus_tag = perseus[e]
                        checked_in_perseus += 1
                        if perseus_tag[0] == "G":
                            t = "G"+t[1:]
                            df_is_g_in_p += 1
                        else: # if in perseus, but not G, D- like the rest of the D*
                            t = "D-"+t[2:]
                    else: # if not in perseus, D- like the rest of the D*
                        t = "D-"+t[2:]
                #Dq, en Du worden D- (Df is treated in the rule above)
                if  t[0:2] == "Dq" or t[0:2] == "Du":
                    t = "D-"+t[2:]
                # This was from rewrite_v2
                if simplify:
                    t = t[0]+'-'+t[2:]
                # Print the output tag(s)
                print( word, lemma, t, f ) 

sys.stderr.write("Skipped {0:4n} entries\n".format(skipped))
sys.stderr.write("Skipped {0:4n} NOPEs\n".format(nope_cnt))
sys.stderr.write("Checked {0:4n} entries in Perseus\n".format(checked_in_perseus))
sys.stderr.write("Found   {0:4n} Df/G entries in Perseus\n".format(df_is_g_in_p))
