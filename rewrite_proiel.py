# python3
#
# 2016-03-22 bug fix after Skype call
#
import re
import getopt, sys, os

'''
Bij PROIEL tags: positie 11 (strength) en 12 (inflection) komen te vervallen.
Bij positie 10 wordt p herschreven tot -.
Eventueel later: Ne en Nb worden N-, Df, Dq, en Du worden D-.

usage: python rewrite.py -f greek.lex {-e voor "eventueel later"}

Software/Lemmatizer/Prep/greek_Haudag.lemma.lex
Αἰάκεα	Αἰάκης	3	Ne-s---ma--i	3
Αἰάκεος	Αἰάκης	2	Ne-s---mg--i	2
Αἰάκεϊ	Αἰάκης	1	Ne-s---md--i	1

Output:
python3 rewrite_proiel.py -f ~/SurfdriveRadboud/Shared/GreekPerspectives\ \(2\)/Software/Lemmatizer/Prep/greek_Haudag.lemma.lex 
Αἰάκεα Αἰάκης Ne-s---ma-
Αἰάκεος Αἰάκης Ne-s---mg-
Αἰάκεϊ Αἰάκης Ne-s---md-
Αἰάκης Αἰάκης Ne-s---mn-
...
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

    
with open(afile, 'r') as f:
    for l in f:
        l = l.strip()
        bits = l.split()
        if len(bits) < 5:
            continue
        if bits[1] == "NOPE": #hier was geen lemma beschikbaar
            continue
        tags = bits[3:]
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
                    #Df, Dq, en Du worden D-
                    if t[0:2] == "Df" or t[0:2] == "Dq" or t[0:2] == "Du":
                        print(t)
                        t = "D-"+t[2:]
                if simplify:
                    t = t[0]+'-'+t[2:]
                print( bits[0], bits[1], t ) 
            
