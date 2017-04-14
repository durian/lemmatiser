# python3
#
import re

'''
usage: python convert_tags.py

*) Input filename hdt.xml en output filename hdt.postag.xml zijn hard-coded.
*) hdt.xml moet in dezelfde directory liggen als convert_tags.py
*) leest de mapping uit tagsmap.txt in dezelfde directory
*) n/cltk moet geinstalleerd zijn
*) Python 3.4


python3 convert_tags.py

Converts the part-of-speech=".." and  morphology=".." tag to an all inclusive postag.

hdt.xml:        <token id="867275" form="ἥδε" citation-part="1.1.0" lemma="ὅδε" part-of-speech="Pd" morphology="-s---fn--i" head-id="867274" relation="atr" presentation-after=", "/>

Converted:
hdt.postag.xml: <word id="867275" form="ἥδε" citation-part="1.1.0" lemma="ὅδε" head-id="867274" relation="atr" presentation-after=", " postag="p-s---fn-" />

'''

morpos = {} # { 'gender': 5, 'number': 1, ... }
mormap = {} # [2] = { "p" : [4, "p"],
            #         "i" : [4, "i"], ... }
i = 0;
for m in ["person", "number", "tense", "mood", "voice", "gender", "case", "degree", "strength", "inflection"]:
    morpos[m] = i
    mormap[i] = {}
    i += 1
#print( morpos )
#print( mormap )

posmap = {} # { "A-" : [1, "a"], ... }
    
tm_file = "tagsmap.txt"
with open(tm_file, 'r') as f:
    for l in f:
        l = l.strip()
        bits = l.split()
        if len(bits) == 4:
            #print( bits[0],bits[1], "->", bits[2],bits[3] )
            if bits[0] == "part-of-speech":
                posmap[ bits[1] ] = [ bits[2], bits[3] ]
            else:
                the_morpos = morpos[bits[0]] # person -> 0
                #print( "the_morpos("+bits[0]+") =", morpos[bits[0]] )
                the_proieltag = bits[1]
                #print( "proiel tag =", the_proieltag )
                #print( "perseus =", [ bits[2], bits[3] ] )
                try:
                    mormap[ the_morpos ][ the_proieltag ] += [ bits[2], bits[3] ]
                except KeyError:
                    mormap[ the_morpos ][ the_proieltag ] = [ bits[2], bits[3] ]
for x in mormap:
    #print( x, mormap[x] )
    pass
#print( posmap )

# read hdt.xml file

xml_file = "hdt.xml"
out_file = "hdt.postag.xml"
with open(xml_file, 'r') as f:
    with open(out_file, "w", encoding="utf8") as of:
        for l in f:
            l = l.rstrip()
            # problem:  relation="atr" presentation-after=" "/>
            #                                              ^ for split
            lp = ""
            inq = False;
            for x in l:
                if x == '"':
                    inq = not inq
                    lp += x
                    continue
                if inq and x == ' ':
                    x = 'Q'; # "Q" was not in hdt.xml
                lp += x
            l = lp
            #
            if l.endswith( "/>" ): #this separates "/>" from being
                l = l[:-2]+" />"   #connected to the last string
            bits = l.split()
            if bits[0] == "</token>":
                of.write( "</word>\n" )
                continue
            if bits[0] != "<token":
                l = l.replace("Q", " "); #put the space back
                of.write( l + "\n" )
                continue
            bits[0] = "<word"
            space = re.search(r'[^ ]', l).start()
            # postag is both part-of-speech and morphology
            perseus_postag = [ "-","-","-","-","-","-","-","-","-" ] # "---------"
            new_l = " " * space
            for b in bits:
                #print( "b =",  b )
                if b.endswith("/>"):
                    # at the end, create new postag from part-of-speech and morphology
                    new_l += "postag=\"" + "".join(perseus_postag) + "\" />"
                    new_l = new_l.replace("Q", " "); #put the space back
                    #print( new_l )
                    of.write( new_l + "\n" )
                    continue
                elif b.endswith(">"):
                    # at the end, create new postag from part-of-speech and morphology
                    # print 'b' without closing ">"
                    new_l += b[:-1] + " postag=\"" + "".join(perseus_postag) + "\">"
                    new_l = new_l.replace("Q", " "); #put the space back
                    #print( new_l )
                    of.write( new_l + "\n" )
                    continue
                kv = b.split("=")
                if len(kv) != 2:
                    new_l += b + " "
                    continue
                k = kv[0]
                v = kv[1][1:-1] #remove ""
                #print( k, v )
                if k == "part-of-speech":
                    #print( posmap[v] )
                    perseus_pos = int(posmap[v][0]) - 1 # first one, NB - 1, string pos 0
                    perseus_tag = posmap[v][1]
                    if perseus_tag != '?':
                        perseus_postag[perseus_pos] = perseus_tag
                elif k == "morphology":
                    for i in range(0, len(v)):
                        mor = v[i] # v[1] = 's'
                        #print( i, "mor", mor )
                        if mor != '-':
                            #print( "mormap", mormap[i][mor] )
                            perseus_pos = int(mormap[i][mor][0]) - 1 #note the - 1
                            perseus_tag = mormap[i][mor][1]
                            if perseus_tag != '?':
                                perseus_postag[perseus_pos] = perseus_tag
                else:
                    new_l += b + " "
            
            
