#!/usr/bin/env python3
#
#
import re
import getopt, sys, os
from collections import Counter
from operator import attrgetter
import random

have_frog = False
try:
    import frog
    have_frog = True
except:
    print( "No Frog", file=sys.stderr )

'''
Lemmatiser -- Work in Progress
------------------------------

USAGE:
  lemmatiser.py -f <TEST FILE> -o OUT
  - Loads lexicon file automatically; greek_Haudag.pcases.lemma.lex.
  - Extra word-lemma-tags can be added to extra-wlp.txt (for example
    punctuation).
  - Produces two output files (and lots of output to the screen):
    OUT-stats.txt: word, lemma, tag, full lemma, info
                   followed by statistics
    OUT-wlt.txt: word lemma tag
                 output from the lemmatiser
  -Removes "#." from lemmas in the test data.

  lemmatiser.py -w τῶν
  - Looks up word in lexicon, prints associated lemmas.

  lemmatiser.py -l ὕπνος
  - Looks up lemma in lexicon.

SCREEN OUTPUT (when using "-v"):
  lemmatise( ταῦτα οὗτος P--p---nn- )                 :input from test file
  WORD IS IN LEXICON ταῦτα, 2                         :it has 2 entries in lexicon
  [/ταῦτα/οὗτος/Pd-p---na--i/682/proiel/, /ταῦτα/οὗτος/Pd-p---nn--i/136/proiel/]
  LEMMA ταῦτα, οὗτος, Pd-p---na--i,   682             :first lexicon entry
  LEMMA ταῦτα, οὗτος, Pd-p---nn--i,   136             :second lexicon entry
  lemma = ταῦτα, οὗτος, Pd-p---na--i,   682           :chosen lemmatisation
  multi lemmas, different pos tag, highest frequency  :lemmatiser justification
  correct                                             :score using test file

FILE OUTPUT:
  τὸν     ὁ       S--s---ma-      /τὸν/ὁ/S--s---ma-/2374/proiel/  CORRECT multi lemmas, same pos tag, highest frequency
  χῶρον   χῶρος   N--s---ma-      /χῶρον/Χῶρος/N--s---ma-/0/nofreq/       WRONG   multi lemmas, same pos tag, other frequency

TEST FILE:
  hdt_Books_forFrog.col
  
  Ἡροδότου	Ἡρόδοτος	N--s---mg-
  Ἁλικαρνησσέος	Ἁλικαρνασσεύς	N--s---mg-

DATA STRUCTURES:
  Lexicon is contained in ghd_words[].

  ghd_words["word"] contains a Word object.

  Word object contains lemmas{}, indexed by POS-tag.

  The lemmatiser looks up a word in the text in ghd_words, and tries 
  to determine the correct lemma based on frequency info and/or POS-tag.

ALGORITME:

Zoek woord op in lexicon lijst
als maar 1 lemma: neem dat als antwoord
als meerdere lemmas:
  zoek naar een lemma met dezelfde POS-tag als in de text
  als gevonden: neem dat als antwoord
  niet gevonden, neem het lemma met de hoogste count als antwoord
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
    def __str__(self):
        return self.word+", "+str(len(self.lemmas))
        
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
    def __str__(self):
        return self.word+", "+self.lemma+", "+self.tag+", "+"{0:5n}".format(self.freq)

greekHDfile = "greek_Haudag.pcases.lemma.lex.rewrite_pluslater"
ghd_words = {}
nofreqfile  = "proiel_v3_perseus_merged.txt"
#nof_word = {} #lets keep these seperate ?
filename  = None # test file
extrafile = "extra-wlt.txt"
frogfile = "testN.frog.out"
frog_words = {}
outprefix = "out"
lookup_w = None
lookup_l = None
verbose  = False
frog_cfg = "frog.cfg.template"

try:
    opts, args = getopt.getopt(sys.argv[1:], "f:l:L:o:vw:D", [])
except getopt.GetoptError as err:
    print(str(err))
    sys.exit(1)
for o, a in opts:
    if o in ("-f"):
        filename = a
    elif o in ("-l"): #lookup a lemma
         lookup_l = a
    elif o in ("-L"): #choose another lexicon file
         greekHDfile = a
    elif o in ("-o"):
        outprefix = a
    elif o in ("-v"):
        verbose = True
    elif o in ("-w"): #lookup a word
        lookup_w = a
    elif o in ("-D"):
        debug = True
    else:
        assert False, "unhandled option"

# Sanity checks

files_found = True
for f in [greekHDfile, filename, nofreqfile, extrafile, frogfile, frog_cfg]:
    if f and not os.path.exists( f ):
        print( "ERROR: FILE NOT FOUND:", f, file=sys.stderr )
        files_found = False
if not files_found:
    sys.exit(1)

if have_frog:
    print( "INIT FROG", file=sys.stderr )
    frog = frog.Frog(frog.FrogOptions(parser=False,tok=False,morph=False,mwu=False,chunking=False,ner=False), frog_cfg )

line_count = 0
new_entries = 0
zero_freq = 0
print( "READING", greekHDfile, file=sys.stderr )

with open(greekHDfile, 'r') as f:
    '''
    WORD            LEMMA       TAG             COUNT
    ἀλλήλοις            ἀλλήλων Pc-p---md--i    5
    ἀλλήλοις            ἀλλήλων Pc-p---nd--i    2
    ἀλλήλοισι           ἀλλήλων Pc-p---md--i    9
    '''
    for l in f:
        l = l.strip()
        if len(l) > 0 and l[0] == "#":
            print( "SKIP COMMENT", l, file=sys.stderr )
            continue
        bits = l.split()
        if len(bits) != 4:
            print( "SKIP NOT 4 FIELDS", l, file=sys.stderr )
            continue
        line_count += 1
        word  = bits[0]
        lemma = bits[1]
        tag   = bits[2]
        try:
            freq  = int(bits[3])
        except ValueError:
            print( "SKIP FREQUENCY ERROR", l, file=sys.stderr )
            continue
        if freq == 0:
            #print( "HAS 0 FREQUENCY", l, file=sys.stderr )
            zero_freq += 1
        DBG(word, lemma, tag, freq)
        #DBG(ghd_words.keys())
        if word in ghd_words.keys():
            word_entry = ghd_words[word]
            new_lemma = Lemma(word, lemma, tag, freq)
            new_lemma.src = "greek_Haudag" #proiel
            word_entry.lemmas[tag] = new_lemma
            DBG("append entry", word)
        else:
            word_entry = Word(word)
            new_lemma = Lemma(word, lemma, tag, freq)
            new_lemma.src = "greek_Haudag" #"proiel"
            word_entry.lemmas[tag] = new_lemma
            # Deze p-gevallen lijst bevat woordvorm-pos combinaties
            # die nog niet in de andere twee proiel gevallen stonden
            # en deze zijn te herkennen aan hun frequentie van 0 !
            ghd_words[word] = word_entry
            new_entries += 1
            DBG("new entry", word)
print( "Added", new_entries, "new entries." )
print( "Counted", zero_freq, "entries with frequency 0." )
new_entries = 0

if nofreqfile:
    print( "\nREADING", nofreqfile, file=sys.stderr )
    with open(nofreqfile, 'r') as f:
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
            freq  = 0 #unknown
            DBG(word, lemma, tag)
            if word in ghd_words.keys():
                word_entry = ghd_words[word]
                if tag in word_entry.lemmas: # if already present, do nothing, because
                    # we have it from first list
                    DBG("TAG ALREADY PRESENT", word, lemma, tag)
                else:
                    new_lemma = Lemma(word, lemma, tag, freq)
                    new_lemma.src = "merged" #"nofreq"
                    word_entry.lemmas[tag] = new_lemma
                    DBG("append entry", word)
                DBG("skip existing entry", word)
            else:
                word_entry = Word(word)
                new_lemma = Lemma(word, lemma, tag, freq)
                new_lemma.src = "merged" #"nofreq"
                word_entry.lemmas[tag] = new_lemma
                ghd_words[word] = word_entry
                new_entries += 1
                DBG("new entry", word)
print( "Added", new_entries, "new entries." )
new_entries = 0

# At the moment we have punctuation here.
# format is word-lemma-tag
#
if extrafile:
    print( "\nREADING", extrafile, file=sys.stderr )
    with open(extrafile, 'r') as f:
        for l in f:
            l = l.strip()
            if len(l) > 0 and l[0] == "#":
                print( "SKIP COMEMENT", l, file=sys.stderr )
                continue
            bits = l.split()
            if len(bits) != 3:
                print( "SKIP NOT 3 FIELDS", l, file=sys.stderr )
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
                new_entries += 1
                DBG("new entry", word)
print( "Added", new_entries, "new entries." )
new_entries = 0

# linear attempt at Frog file
frog_list = []
idx = 0
if frogfile:
    print( "\nREADING", frogfile, file=sys.stderr )
    with open(frogfile, 'r') as f:
        # 1	Ἡροδότου	Ἡροδότου		V--sapmmg-	0.500688
        # 2	Ἁλικαρνησσέος	Ἁλικαρνησσέος		V--sapmmn-	0.305347
        for l in f:
            if len(l) < 4:
                continue
            l = l.strip()
            bits = l.split()
            if len(bits) != 5:
                print( "SKIP NOT 5 FIELDS", l, file=sys.stderr )
                frog_list.append( [idx, "NONE", "NONE", "NONE"] )
                idx += 1
                continue
            word  = bits[1]
            lemma = bits[2]
            tag   = bits[3]
            frog_list.append( [idx, word, lemma, tag] )
            idx += 1

# Look up a single word from the lexicon
if lookup_w:
    print( "\nLOOKUP WORD", lookup_w )
    if lookup_w in ghd_words:
        print( "  ", ghd_words[lookup_w] )
        for l in sorted(ghd_words[lookup_w].lemmas.values(), key=attrgetter('freq'), reverse=True):
            print( "    ", l )

# Look up a single lemma in all words
if lookup_l:
    print( "\nLOOKUP LEMMA", lookup_l )
    for x in ghd_words:
        output = []
        for l in sorted(ghd_words[x].lemmas.values(), key=attrgetter('freq'), reverse=True):
            if l.lemma == lookup_l:
                output.append(l);
        if output:
            print( x )
            for o in output:
                print( "  ", o )

if lookup_l or lookup_w:
    sys.exit(1)

# Print top-3 most lemmas, with top-3 lemma
if verbose:
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
    "MLDTHF" : "multi lemmas, no pos tag match, highest frequency", #DT=different tag
    "MLNTHF" : "multi lemmas, no tag, highest frequency",
    "MLSTHF" : "multi lemmas, pos tag match, and highest frequency",
    "MLNTHF" : "multi lemmas, no tag, highest frequency",
    "MLSTOF" : "multi lemmas, pos tag match, but other frequency",
    "MLNTOF" : "multi lemmas, no tag, other frequency",
    "OLDT"   : "one lemma, but different pos tag",
    "OLST"   : "one lemma, same pos tag",
    "OLNT"   : "one lemma, no tag",
    "FROG"   : "Frog",
    "FROGF"  : "Frog file",
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
    if verbose:
        print( "lemmatise(", word, tf_lemma, tag, ")" )
    #
    # Check if word in greek_HD
    #
    if word in ghd_words.keys():
        # The word is in our dictionary
        word_entry = ghd_words[word]
        if verbose:
            print( "WORD IS IN LEXICON", word_entry )
        # instead of if-then, always take max, but for statistics maybe seperate
        #
        # Check the number of lemmas for this word. If one, the first one is max. freq.
        sorted_lemmas = sorted(word_entry.lemmas.values(), key=attrgetter('freq'), reverse=True)
        if verbose:
            print( sorted_lemmas )
        # If only one entry, return it no matter the postag.
        if len(sorted_lemmas) == 1: #UNIQUE
            if verbose:
                print( "ONE LEMMA" )
            the_lemma = sorted_lemmas[0]
            if tag == "": #data without tags to compare
                return (sorted_lemmas[0], "OLNT") # one lemma, no pos tag
            if compare_postags(tag, the_lemma.tag):
                return (sorted_lemmas[0], "OLST") # one lemma, same pos tag
            else:
                return (sorted_lemmas[0], "OLDT") # one lemma, different pos tag
        #
        # Not unique, more lemma entries for word
        #
        max_freq = sorted_lemmas[0].freq
        for the_lemma in sorted_lemmas:
            if verbose:
                print( "LEMMA", the_lemma )
            # First try to find the right postag
            # check for tag == ""
            if compare_postags(tag, the_lemma.tag):
                if verbose:
                    print( "POSTAG MATCH", tag, the_lemma )
                # was this a max_freq tag?
                if the_lemma.freq == max_freq:
                    if tag == "": #data without tags to compare
                        return (the_lemma, "MLNTHF") #multi lemmas, no pos tag, highest frequency
                    else:
                        return (the_lemma, "MLSTHF") #multi lemmas, same pos tag, highest frequency
                else:
                    if tag == "": #data without tags to compare
                        return (the_lemma, "MLNTOF") #multi lemmas, no pos tag, other frequency
                    else:
                        return (the_lemma, "MLSTOF") #multi lemmas, same pos tag, other frequency
        # If we end up here, there is no postag match at all, return top-frequency one
        if tag == "": #data without tags to compare
            return (sorted_lemmas[0], "MLNTHF") #multi lemmas, no pos tag, highest frequency
        else:
            return (sorted_lemmas[0], "MLDTHF") #multi lemmas, different pos tag, highest frequency
    if verbose:
        print( "UNKNOWN WORD" )
    return (None, "UNKNOWN")

def lemmatise_frog_file(word, lemma, tag, idx):
    #print( idx, frog_list[idx] )
    # [90158, 'ἐστὶ', 'εἰμί#1', 'V-3spia---']
    try:
        lemma = frog_list[idx][2]
        if '#' in lemma:
            hidx = lemma.find('#')
            lemma = lemma[0:hidx]
        frog_word = frog_list[idx][1]
        if frog_word != word:
            print( "FROG OUT OF SYNC" )
            sys.exit(1)
        new_lemma = Lemma(word, lemma, tag, 0)
        return ( new_lemma, "FROGF" )
    except:
        return (None, "UNKNOWN")

def lemmatise_frog(word, lemma, tag):
    #[{'index': '1', 'lemma': 'κρατήρ', 'pos': 'N--s---ma-', 'eos': True, 'posprob': 1.0, 'text': 'κρητῆρα'}]
    if have_frog:
        try:
            frog_out  = frog.process(word)
            the_lemma = frog_out[0]["lemma"]
            the_tag   = frog_out[0]["pos"]
            new_lemma = Lemma(word, the_lemma, tag, 0)
            return( new_lemma, "FROG" )
        except:
            pass
    return (None, "UNKNOWN")

def extract_postag(tag, l):
    return tag[0:l]

# Compare tag from test file to lemmatiser tag.
def compare_postags(tf_tag, l_tag):
    l = min(len(tf_tag), len(l_tag))
    if l == 0:
        return False
    #print( l, tf_tag, tf_tag[0:l], l_tag, l_tag[0:l] )
    return extract_postag(tf_tag, l) == extract_postag(l_tag, l)
    
# ---

# Test file format:
# ἔργα    ἔργον   N--p---nn-
#
if not filename:
    print( "\nNOTHING TO DO...", file=sys.stderr )
    sys.exit(0)
else:
    print( "\nLEMMATISING", filename, file=sys.stderr )
    
outfile    = outprefix + "-stats.txt"
outwltfile = outprefix + "-wlt.txt"

# Process test file
lcount = 0
hcount = 0 #count hash lemmas "foo#1"
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
                    if '#' in lemma:
                        idx = lemma.find('#')
                        lemma = lemma[0:idx]
                        hcount += 1
                    if verbose:
                        print("")
                    lcount += 1
                    #tag = "" # to test w/o the pos tag info
                    the_lemma, ltype = lemmatise( word, lemma, tag )
                    # we possibly get (NONE, "UNKNOWN WORD")
                    if not the_lemma:
                        #Call Frog 
                        if have_frog:
                            the_lemma, ltype = lemmatise_frog( word, lemma, tag )
                        elif frog_file:
                            the_lemma, ltype = lemmatise_frog_file( word, lemma, tag, lcount-1 )
                        else:
                            the_lemma = None
                            ltype = "UNKNOWN"
                    ltype = strategies[ltype]
                    lemmatiser_stats[ltype] += 1
                    if the_lemma:
                        if verbose:
                            print( "lemma =", the_lemma )
                            print( ltype )
                        # Instead of repr(the_lemma) write number of lemmas, list lemma:freq.?
                        ##of.write( word+"\t"+the_lemma.lemma+"\t"+repr(the_lemma)+"\t"+ltype+"\n" )
                        #of.write( word+"\t"+lemma+"\t"+tag+"\t"+repr(the_lemma)+"\t"+ltype+"\n" )
                        #
                        ofwlt.write(word+"\t"+the_lemma.lemma+"\t"+the_lemma.tag+"\n")
                        if the_lemma.lemma == lemma:
                            if verbose:
                                print( the_lemma.lemma, lemma )
                            lemmatiser_stats[ltype+" -correct"] += 1
                            lemmatiser_stats["lemmatised-correct"] += 1
                            if verbose:
                                print( "correct" )
                            of.write( word+"\t"+lemma+"\t"+tag+"\t"+repr(the_lemma)+"\t"+"CORRECT\t"+ltype+"\n" )
                        else:
                            if verbose:
                                print( "wrong" )
                            lemmatiser_stats[ltype+" -wrong"] += 1
                            lemmatiser_stats["lemmatised-wrong"] += 1
                            of.write( word+"\t"+lemma+"\t"+tag+"\t"+repr(the_lemma)+"\t"+"WRONG\t"+ltype+"\n" )
                    else: #not the_lemma
                        of.write( word+"\tUNKNOWN\tUNKNOWN\tNONE\tWRONG\t"+ltype+"\n" )
                        ofwlt.write( word+"\tNONE\tNONE\n" )
                        lemmatiser_stats[ltype+" -wrong"] += 1
#print( "hcount", hcount)

with open(outfile, 'a') as of:
    lemmatised_count = lemmatiser_stats["lemmatised-wrong"]+lemmatiser_stats["lemmatised-correct"]
    correct_count    = lemmatiser_stats["lemmatised-correct"]
    print( "#\n# line count", lcount, "lemmatised_count", lemmatised_count, file=of ) #diff is unknowns

    for stat, count in sorted(lemmatiser_stats.items()):
    #for stat, count in lemmatiser_stats.most_common():
        print( "# {0:<60} {1:5n}".format(stat, count), file=of )

    if lcount > 0:
        print( "# Correct (lcount)", round(correct_count*100.0 / lcount, 2), file=of )
    else:
        print( "# Correct (lcount) 0", file=of )
    if lemmatised_count > 0:
        print( "# Correct (lemmatised only, no unknowns)", round(correct_count*100.0 / lemmatised_count, 2), file=of )
    else:
        print( "# Correct (lemmatised only, no unknowns) 0", file=of )
        

print( "\nOutput in" )
print( " ", outfile )
print( " ", outwltfile )

'''
χῶρον   χῶρος   N--s---ma-      /χῶρον/Χῶρος/N--s---ma-/0/nofreq/       WRONG   multi lemmas, same pos tag, other frequency
'''
