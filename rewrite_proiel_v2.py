# python3
#
# 2016-03-22 bug fix after Skype call
# 2016-06-15 Rewriting the new greek_Haudag.pcases.lemma.lex, SPECIAL VERSION FOR THIS
#
import re
import getopt, sys, os

'''
Bij PROIEL tags: positie 11 (strength) en 12 (inflection) komen te vervallen.
Bij positie 10 wordt p herschreven tot -.
Eventueel later: Ne en Nb worden N-, Df, Dq, en Du worden D-.

usage: python rewrite_proiel_v2.py -f greek.lex {-e voor "eventueel later"}

NIEUW FORMAAT:
greek_Haudag.pcases.lemma.lex:
ἀλλήλων	ἀλλήλων	Pc-p---mg--i	25
ἀλλήλων	ἀλλήλων	Pc-p---ng--i	4
ἀλληλέων	ἀλληλέων	Pc-p---fg--i	2
ἀλληλέων	ἀλληλέων	Pc-p---mg--i	1
ἀλλήλοις	ἀλλήλων	Pc-p---md--i	5
ἀλλήλοις	ἀλλήλων	Pc-p---nd--i	2

Output:
python3 rewrite_proiel_v2.py -f greek_Haudag.pcases.lemma.lex
ἀλλήλων ἀλλήλων Pc-p---mg-
ἀλλήλων ἀλλήλων Pc-p---ng-
ἀλληλέων ἀλληλέων Pc-p---fg-
...

2016-06-15: Peters-Mac-Pro:20160615 pberck$
2016-06-15: python3 rewrite_proiel_v2.py -f greek_Haudag.pcases.lemma.lex  > greek_Haudag.pcases.lemma.lex.rewrite
2016-06-15: Skipped 10 NOPEs
2016-06-15: Did 0 'eventuele' fixes
'''

afile = None
eventueel_later = False
simplify = False #Changes Nb into N-, etc

try:
    opts, args = getopt.getopt(sys.argv[1:], "ef:s", [])
except getopt.GetoptError as err:
    print(str(err))
    sys.exit(1)
for o, a in opts:
    if o in ("-f"):
        afile = a
    elif o in ("-e"):
        eventueel_later = True
    elif o in ("-s"):
        simplify = True
    else:
        assert False, "unhandled option"

nope_cnt = 0
later_cnt = 0
with open(afile, 'r') as f:
    for l in f:
        l = l.strip()
        bits = l.split()
        # Ῥωμαῖοι	Ῥωμαῖος	A--p---mnp-i	2
        if len(bits) != 4:
            continue
        if bits[1] == "NOPE": #hier was geen lemma beschikbaar
            nope_cnt += 1
            continue
        tags = bits[2:]
        #print( tags )
        for n, k in enumerate(tags[:-1]):
            t = tags[n]    #tag
            f = tags[n+1]  #freq
            #print( t,f )
            if len(t) == 12:
                t = t[0:10] #laatste twee weghalen
                if t[9] == "p":
                    t = t[0:9]+"-" #t[9] = '-'
                    #t[9] = '-'
                if eventueel_later:
                    if t[0:2] == "Ne" or t[0:2] == "Nb":
                        t = "N-"+t[2:]
                        later_cnt += 1
                        #print( t )
                    #Df, Dq, en Du worden D-
                    if t[0:2] == "Df" or t[0:2] == "Dq" or t[0:2] == "Du":
                        #print( t )
                        t = "D-"+t[2:]
                        later_cnt += 1
                if simplify:
                    t = t[0]+'-'+t[2:]
                print( bits[0], bits[1], t ) 

sys.stderr.write("Skipped {0} NOPEs\n".format(nope_cnt))
sys.stderr.write("Did {0} 'eventuele' fixes\n".format(later_cnt))
