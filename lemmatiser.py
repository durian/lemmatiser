#!/usr/bin/env python3
#
#
import re
import getopt, sys, os
from collections import Counter
from operator import attrgetter

'''
Lemmatiser -- Work in Progress
------------------------------

USAGE:
  lemmatiser.py -f <TEST FILE>
  - Loads lexicon file automatically; greek_Haudag.pcases.lemma.lex.
  - Extra word-lemma-tags can be added to extra-wlp.txt (for example
    punctuation).
  - Produces two output files:
    out-stats.txt: word, lemma, full lemma, info
                   followed by statistics
    out-wlt.txt: word lemma tag

greek_Haudag.pcases.lemma.lex (proiel):

ἀλλήλων ἀλλήλων Pc-p---mg--i    25
ἀλλήλων ἀλλήλων Pc-p---ng--i    4
ἀλληλέων        ἀλληλέων        Pc-p---fg--i    2
ἀλληλέων        ἀλληλέων        Pc-p---mg--i    1
'''

debug = False
def DBG(*strs):
    if debug:
        sys.stderr.write("DBG:"+"".join(str(strs))+"\n")
        
class Word:
    def __init__(self, w):
        self.word   = w
        self.lemmas = {} #key is the tag?
    def __repr__(self):
        return "|"+self.word+"|"+str(len(self.lemmas))+"|"
        
class Lemma:
    def __init__(self, w, l, t, f):
        self.word  = w
        self.lemma = l
        self.tag   = t
        self.src   = "unknown"
        try:
            self.freq  = int(f)
        except ValueError:
            print( w, l, t )
            sys.exit(1)
    def __repr__(self):
        return "/"+self.word+"/"+self.lemma+"/"+self.tag+"/"+str(self.freq)+"/"+str(self.src)+"/"

greekHDfile = "greek_Haudag.pcases.lemma.lex"
ghd_words = {}
filename  = None # test file
extrafile = "extra-wlt.txt"
outprefix = "out"

try:
    opts, args = getopt.getopt(sys.argv[1:], "f:l:o:", [])
except getopt.GetoptError as err:
    print(str(err))
    sys.exit(1)
for o, a in opts:
    if o in ("-f"):
        filename = a
    elif o in ("-l"): #specify other lexicon
         greekHDfile = a
    elif o in ("-o"):
        outprefix = a
    else:
        assert False, "unhandled option"

line_count = 0
print( "READING", greekHDfile, file=sys.stderr )
with open(greekHDfile, 'r') as f:
    '''
    WORD            LEMMA       TAG             COUNT
    ἀλλήλοις       	ἀλλήλων	Pc-p---md--i   	5
    ἀλλήλοις       	ἀλλήλων	Pc-p---nd--i   	2
    ἀλλήλοισι      	ἀλλήλων	Pc-p---md--i   	9
    '''
    for l in f:
        l = l.strip()
        if len(l) > 0 and l[0] == "#":
            print( "SKIP", l, file=sys.stderr )
            continue
        bits = l.split()
        if len(bits) != 4:
            print( "SKIP", l, file=sys.stderr )
            continue
        line_count += 1
        word  = bits[0]
        lemma = bits[1]
        tag   = bits[2]
        freq  = int(bits[3])
        DBG(word, lemma, tag, freq)
        #DBG(ghd_words.keys())
        if word in ghd_words.keys():
            word_entry = ghd_words[word]
            new_lemma = Lemma(word, lemma, tag, freq)
            new_lemma.src = "proiel"
            word_entry.lemmas[tag] = new_lemma
            DBG("append entry", word)
        else:
            word_entry = Word(word)
            new_lemma = Lemma(word, lemma, tag, freq)
            new_lemma.src = "proiel"
            word_entry.lemmas[tag] = new_lemma
            # Deze p-gevallen lijst bevat woordvorm-pos combinaties
            # die nog niet in de andere twee proiel gevallen stonden
            # en deze zijn te herkennen aan hun frequentie van 0 !
            ghd_words[word] = word_entry
            DBG("new entry", word)
DBG(len(ghd_words), line_count)

# At the moment we have punctuation here.
# format is word-lemma-tag
#
if extrafile:
    print( "READING", extrafile, file=sys.stderr )
    with open(extrafile, 'r') as f:
        for l in f:
            l = l.strip()
            if len(l) > 0 and l[0] == "#":
                print( "SKIP", l, file=sys.stderr )
                continue
            bits = l.split()
            if len(bits) != 3:
                print( "SKIP", l, file=sys.stderr )
                continue
            line_count += 1
            word  = bits[0]
            lemma = bits[1]
            tag   = bits[2]
            DBG(word, lemma, tag)
            if word in ghd_words.keys():
                word_entry = ghd_words[word]
                if tag in word_entry.lemmas: #indexed by tag
                    word_entry.lemmas[tag].freq += 1
                    DBG("PLUS ONE", lemma, tag)
                else:
                    new_lemma = Lemma(word, lemma, tag, 1)
                    new_lemma.src = "extra"
                    word_entry.lemmas[tag] = new_lemma
                    DBG("append entry", word)
            else:
                word_entry = Word(word)
                new_lemma = Lemma(word, lemma, tag, freq)
                new_lemma.src = "extra"
                word_entry.lemmas[tag] = new_lemma
                ghd_words[word] = word_entry
                DBG("new entry", word)

# Print top-3 most lemmas
sorted_words = sorted(ghd_words, key=lambda k: len(ghd_words[k].lemmas), reverse=True)
for x in sorted_words[0:3]:
    print( ghd_words[x], file=sys.stderr )
    # print top-3 frequent lemmas
    for l in sorted(ghd_words[x].lemmas.values(), key=attrgetter('freq'), reverse=True)[0:3]:
        print( " ", l, file=sys.stderr )

# Count lemmatisation stats
lemmatiser_stats = Counter()

# Possible lemmatiser "strategies"
strategies = {
    "MLDTHF" : "multi lemmas, different pos tag, highest frequency",
    "MLSTHF" : "multi lemmas, same pos tag, highest frequency",
    "MLSTOF" : "multi lemmas, same pos tag, other frequency",
    "OLDT"   : "one lemma, different pos tag",
    "OLST"   : "one lemma, same pos tag",
    "UNKNOWN": "unknown"
    }

# Prefill Counter
lemmatiser_stats["lemmatised-correct"] = 0
lemmatiser_stats["lemmatised-wrong"] = 0
lemmatiser_stats["unknown"] = 0
lemmatiser_stats["unknown -wrong"] = 0
for s in strategies:
    lemmatiser_stats[strategies[s]] = 0
    lemmatiser_stats[strategies[s]+" -correct"] = 0
    lemmatiser_stats[strategies[s]+" -wrong"] = 0

'''
Lemmatiser strategy:

Check if word in dictionary.

If it is:
  1) If it has only one lemma entry, return it.
     ("one lemma, same pos tag" / "one lemma, different pos tag")
  2) Go through the lemmas:
     a) if a lemma with a similar pos tag is found, return it.
        ("multiple lemmas, same pos tag, highest frequency" / "multi lemmas, same pos tag, other frequency")
     b) otherwise, return the most frequent lemma.
        ("multi lemmas, different pos tag, highest frequency")

If it is not:
  return None.
  ("unknown")
'''
def lemmatise(word, tf_lemma, tag):
    print( "lemmatise(", word, tf_lemma, tag, ")" )
    #
    # Check if word in greek_HD
    #
    if word in ghd_words.keys():
        # The word is in our dictionary
        word_entry = ghd_words[word]
        print( "WORD IS IN LEXICON", word_entry )
        # instead of if-then, always take max, but for statistics maybe seperate
        #
        # Check the number of lemmas for this word. If one, the first one is max. freq.
        sorted_lemmas = sorted(word_entry.lemmas.values(), key=attrgetter('freq'), reverse=True)
        print( sorted_lemmas )
        # If only one entry, return it no matter the postag.
        if len(sorted_lemmas) == 1: #UNIQUE 
            print( "ONE LEMMA" )
            the_lemma = sorted_lemmas[0]
            if compare_postags(tag, the_lemma.tag):
                return (sorted_lemmas[0], "OLST") # one lemma, same pos tag
            else:
                return (sorted_lemmas[0], "OLDT") # one lemma, different pos tag
        #
        # Not unique, more lemma entries for word
        #
        max_freq = sorted_lemmas[0].freq
        for the_lemma in sorted_lemmas:
            print( "LEMMA", the_lemma )
            # First try to find the right postag
            if compare_postags(tag, the_lemma.tag):
                print( "POSTAG MATCH", tag, the_lemma )
                # was this a max_freq tag?
                if the_lemma.freq == max_freq:
                    return (the_lemma, "MLSTHF") #multi lemmas, same pos tag, highest frequency
                else:
                    return (the_lemma, "MLSTOF") #multi lemmas, same pos tag, other frequency
        # If we end up here, there is no postag match at all, return top-frequency one
        return (sorted_lemmas[0], "MLDTHF") #multi lemmas, different pos tag, highest frequency
    print( "UNKNOWN WORD" )
    return (None, "UNKNOWN")

def extract_postag(tag, l):
    return tag[0:l]

# Compare tag from test file to lemmatiser tag.
def compare_postags(tf_tag, l_tag):
    l = min(len(tf_tag), len(l_tag))
    #print( l, tf_tag, tf_tag[0:l], l_tag, l_tag[0:l] )
    return extract_postag(tf_tag, l) == extract_postag(l_tag, l)
    
# ---

# Test file format:
# ἔργα    ἔργον   N--p---nn-
#
if not filename:
    print( "NOTHING TO DO...", file=sys.stderr )
    sys.exit(0)

outfile    = outprefix + "-stats.txt"
outwltfile = outprefix + "-wlt.txt"

# Process test file
lcount = 0
if filename:
    with open(filename, 'r') as f:
        with open(outfile, 'w') as of:
            with open(outwltfile, 'w') as ofwlt:
                for l in f:
                    l = l.strip()
                    if not l:
                        continue
                    bits = l.split()
                    if 0 < len(bits) < 3: #only text/words
                        word   = bits[0]
                        lemma  = ""
                        tag    = ""
                    if len(bits) >= 3:
                        word   = bits[0]
                        lemma  = bits[1]
                        tag    = bits[2]
                    print("")
                    lcount += 1
                    the_lemma, ltype = lemmatise( word, lemma, tag )
                    ltype = strategies[ltype]
                    lemmatiser_stats[ltype] += 1
                    if the_lemma:
                        print( "lemma =", the_lemma, ltype )
                        # Instead of repr(the_lemma) write number of lemmas, list lemma:freq.?
                        of.write( word+"\t"+the_lemma.lemma+"\t"+repr(the_lemma)+"\t"+ltype+"\n" )
                        #
                        ofwlt.write(word+"\t"+the_lemma.lemma+"\t"+the_lemma.tag+"\n")
                        if the_lemma.lemma == lemma:
                            lemmatiser_stats[ltype+" -correct"] += 1
                            lemmatiser_stats["lemmatised-correct"] += 1
                            print( "correct" )
                        else:
                            print( "wrong" )
                            lemmatiser_stats[ltype+" -wrong"] += 1
                            lemmatiser_stats["lemmatised-wrong"] += 1
                    else: #not the_lemma
                        of.write( word+"\tUNKNOWN\tNONE\t"+ltype+"\n" )
                        ofwlt.write( word+"\tNONE\tNONE\n" )
                        lemmatiser_stats[ltype+" -wrong"] += 1
            
with open(outfile, 'a') as of:
    lemmatised_count = lemmatiser_stats["lemmatised-wrong"]+lemmatiser_stats["lemmatised-correct"]
    correct_count    = lemmatiser_stats["lemmatised-correct"]
    print( "#\n# line count", lcount, "lemmatised_count", lemmatised_count, file=of ) #diff is unknowns

    for stat, count in sorted(lemmatiser_stats.items()):
    #for stat, count in lemmatiser_stats.most_common():
        print( "# {0:<60} {1:5n}".format(stat, count), file=of )

    print( "# Correct (lemmatised only, no unknowns)", round(correct_count*100.0 / lemmatised_count, 2), file=of )
    print( "# Correct (lcount)", round(correct_count*100.0 / lcount, 2), file=of )

print( "\nOutput in" )
print( " ", outfile )
print( " ", outwltfile )