#!/usr/bin/env python3
#
#
import re
import getopt, sys, os
from collections import Counter
from operator import attrgetter
import random
import glob
from unicodedata import normalize

have_frog = False
try:
    import frog
    have_frog = True
except:
    print( "No Frog", file=sys.stderr )

VERSION = "1.2.3"

'''
Lemmatiser -- Work in Progress
Version with Frog/Python interface, for CLI
-------------------------------------------

USAGE:
  lemmatiser.py -f <TEST FILE> -s OUT
  - Loads lexicon file automatically; greek_Haudag.pcases.lemma.lex.
  - greek_Haudag entries take priority over proiel_v3_perseus_merged.txt
    and extra-wlt.txt files.
  - Uses Frog for POS tagging and unknown words.
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
  Lexicon is contained in dictionary ghd_words[].

  ghd_words["word"] contains a Word object.

  Word object contains lemmas{}, indexed by POS-tag.

  Example entry:
  τῶν, 14
    τῶν, ὁ, S--p---mg-,  1163
    τῶν, ὁ, S--p---qg-,   660
    τῶν, ὁ, S--p---ng-,   211

  The lemmatiser looks up a word in the text in ghd_words, and tries 
  to determine the correct lemma based on frequency info and/or POS-tag.

ALGORITME:

Roep Frog aan met het woord om de POS te bepalen
Zoek woord op in lexicon lijst
als maar 1 lemma: neem dat als antwoord
als meerdere lemmas:
  zoek naar een lemma met dezelfde POS-tag als in de text
  als gevonden: neem dat als antwoord
  niet gevonden, neem het lemma met de hoogste count als antwoord
als niet in lijst: roep Frog aan
'''

debug = False
def DBG(*strs):
    if debug:
        sys.stderr.write("DBG:"+"".join(str(strs))+"\n")
        
class Word:
    def __init__(self, w):
        self.word   = normalize('NFC', w)
        self.lemmas = {} #key is the tag
    def __repr__(self):
        return "|"+self.word+"|"+str(len(self.lemmas))+"|"
    def __str__(self):
        return self.word+", "+str(len(self.lemmas))
        
class Lemma:
    def __init__(self, w, l, t, f):
        self.word  = normalize('NFC', w)
        self.lemma = l
        self.tag   = t
        self.src   = "unknown"
        try:
            self.freq  = int(f)
        except ValueError:
            print( "FREQUENCY ERROR", w, l, t )
            sys.exit(1)
    def __repr__(self):
        return "/"+self.word+"/"+self.lemma+"/"+self.tag+"/"+str(self.freq)+"/"+str(self.src)+"/"
    def __str__(self):
        return self.word+", "+self.lemma+", "+self.tag+", "+"{0:5n}".format(self.freq)

greekHDfile = "greek_Haudag.pcases.lemma.lex.rewrite_20161202"
ghd_words   = {}
nofreqfile  = "proiel_v3_perseus_merged.txt"
filenames   = [] #list of globbed files
filename    = None # test file
extrafile   = "extra-wlt.txt"
frog_words  = {}
lookup_w    = None #specific word to look up
lookup_l    = None #specific lemma to look up
verbose     = False
wltmode     = False #if true, assume test file is columns; only first token is used
frog_cfg    = "frog.ancientgreek.template"
remove_root = True # default is to remove ROOT from brat files, -R to disable
suffix      = ".L"

callstr = " ".join(sys.argv)

try:
    opts, args = getopt.getopt(sys.argv[1:], "f:l:L:s:vw:DE:FM:RW", [])
except getopt.GetoptError as err:
    print(str(err))
    sys.exit(1)
for o, a in opts:
    if o in ("-f"):
        filenames = sorted(glob.glob(a))
    elif o in ("-l"): #lookup a specific lemma, print to screen
         lookup_l = a
    elif o in ("-L"): #choose another lexicon file
         greekHDfile = a
    elif o in ("-M"): #choose another merged (wlt) file
         nofreqfile = a
    elif o in ("-E"): #choose another extra-wlt (wlt) file
         extrafile = a
    elif o in ("-s"):
        suffix = "." + a
    elif o in ("-v"):
        verbose = True
    elif o in ("-w"): #lookup a specific word, print to screen
        lookup_w = a
    elif o in ("-D"):
        debug = True
    elif o in ("-F"): # disables Frog, use also when Frog not available
        have_frog = False #force ignore frog
        frog_cfg = None
    elif o in ("-R"):
        remove_root = not remove_root
    elif o in ("-W"):
        wltmode = True
    else:
        assert False, "unhandled option"

logfile     = "lemmatiser"+suffix+".log"
lgf = open(logfile, "w") #or append?
print( callstr, file=lgf, flush=True )

# Sanity checks, aborts if specified lexicon files not found.
files_found = True
for f in [greekHDfile, filename, nofreqfile, extrafile, frog_cfg]:
    if f and not os.path.exists( f ):
        print( "ERROR: FILE NOT FOUND:", f, file=lgf, flush=True )
        print( "ERROR: FILE NOT FOUND:", f, file=sys.stderr )
        files_found = False
if not files_found:
    lgf.close()
    sys.exit(1)

# Initialise Frog.
if have_frog:
    print( "INITIALISE FROG", file=sys.stderr )
    frog = frog.Frog(frog.FrogOptions(parser=True,tok=False,morph=False,mwu=False,chunking=False,ner=False), frog_cfg )

# Statistics on lexicon files.
line_count  = 0
new_entries = 0
zero_freq   = 0
doubles     = 0
conflicts   = 0

print( "READING", greekHDfile, file=sys.stderr )
print( "READING", greekHDfile, file=lgf, flush=True )
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
            print( "SKIP COMMENT", l, file=lgf, flush=True )
            continue
        bits = l.split()
        if len(bits) != 4:
            print( "SKIP NOT 4 FIELDS", l, file=lgf, flush=True )
            continue
        line_count += 1
        word  = normalize('NFC', bits[0])
        lemma = normalize('NFC', bits[1])
        tag   = bits[2]
        try:
            freq  = int(bits[3])
        except ValueError:
            print( "SKIP FREQUENCY ERROR", l, file=lgf, flush=True )
            continue
        if freq == 0:
            #print( "HAS 0 FREQUENCY", l, file=lgf, flush=True )
            zero_freq += 1
        DBG(word, lemma, tag, freq)
        # Store it.
        if word in ghd_words.keys():
            word_entry = ghd_words[word]
            new_lemma = Lemma(word, lemma, tag, freq)
            new_lemma.src = "greek_Haudag" #proiel
            # Note we assume unique word-tag combinations.
            if tag in word_entry.lemmas:
                # WHAT
                # τοσόνδε, τοσόσδε, Pd-s---na-,     5
                # τοσόνδε τοσόσδε Pd-s---na- 0
                # Normally, if the second one has a lower count, it is ignored.
                if True or freq > word_entry.lemmas[tag].freq:
                    if lemma != word_entry.lemmas[tag].lemma:
                        print( "CONFLICTING DOUBLE ENTRY", file=lgf, flush=True )
                        conflicts += 1
                    else:
                        print( "DOUBLE ENTRY", file=lgf, flush=True )
                    print( "STORED", word_entry.lemmas[tag], file=lgf, flush=True )
                    print( "   NEW", new_lemma, file=lgf, flush=True )
                    doubles += 1
            word_entry.lemmas[tag] = new_lemma
            DBG("append entry", word)
        else:
            word_entry = Word(word)
            new_lemma = Lemma(word, lemma, tag, freq)
            new_lemma.src = "greek_Haudag" #"proiel"
            word_entry.lemmas[tag] = new_lemma
            ghd_words[word] = word_entry
            new_entries += 1
            DBG("new entry", word)
print( "Added", new_entries, "new entries.", file=lgf, flush=True )
print( "Counted", zero_freq, "entries with frequency 0.", file=lgf, flush=True )
print( "Ignored", doubles, "double entries, of which", conflicts, "conflicts.", file=lgf, flush=True )

new_entries = 0
if nofreqfile:
    print( "READING", nofreqfile, file=sys.stderr )
    print( "READING", nofreqfile, file=lgf, flush=True )
    with open(nofreqfile, 'r') as f:
        for l in f:
            l = l.strip()
            if len(l) > 0 and l[0] == "#":
                print( "SKIP", l, file=lgf, flush=True )
                continue
            bits = l.split()
            if len(bits) != 3:
                print( "SKIP", l, file=lgf, flush=True )
                continue
            line_count += 1
            word  = normalize('NFC', bits[0])
            lemma = normalize('NFC', bits[1])
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
print( "Added", new_entries, "new entries.", file=lgf, flush=True )
new_entries = 0

# At the moment we have punctuation here.
# format is word-lemma-tag
#
if extrafile:
    print( "READING", extrafile, file=sys.stderr )
    print( "READING", extrafile, file=lgf, flush=True )
    with open(extrafile, 'r') as f:
        for l in f:
            l = l.strip()
            if len(l) > 0 and l[0] == "#":
                print( "SKIP COMMENT", l, file=lgf, flush=True )
                continue
            bits = l.split()
            if len(bits) != 3:
                print( "SKIP NOT 3 FIELDS", l, file=lgf, flush=True )
                continue
            line_count += 1
            word  = normalize('NFC', bits[0])
            lemma = normalize('NFC', bits[1])
            tag   = bits[2]
            if word in ghd_words.keys():
                word_entry = ghd_words[word]
                if tag in word_entry.lemmas: #indexed by tag
                    word_entry.lemmas[tag].freq += 1
                else:
                    new_lemma = Lemma(word, lemma, tag, 1)
                    new_lemma.src = "extra"
                    word_entry.lemmas[tag] = new_lemma
            else:
                word_entry = Word(word)
                new_lemma = Lemma(word, lemma, tag, freq)
                new_lemma.src = "extra"
                word_entry.lemmas[tag] = new_lemma
                ghd_words[word] = word_entry
                new_entries += 1
print( "Added", new_entries, "new entries.\n", file=lgf, flush=True )
new_entries = 0

# Print top-5 most frequent words, with top-5 lemmas
if verbose:
    sorted_words = sorted(ghd_words, key=lambda k: len(ghd_words[k].lemmas), reverse=True)
    for x in sorted_words[0:5]:
        print( ghd_words[x], file=sys.stderr )
        # print top-5 frequent lemmas
        for l in sorted( sorted(ghd_words[x].lemmas.values(), key=attrgetter('tag'), reverse=False), key=attrgetter('freq'), reverse=True)[0:5]:
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
    "FROG"   : "Frog lemma",
    "UNKNOWN": "unknown"
    }

# Prefill Counters
lemmatiser_stats["unknown"] = 0
for s in strategies:
    lemmatiser_stats[strategies[s]] = 0

'''
Lemmatiser strategy:

Check if word in dictionary.

If it is:
  1) If it has only one tag/lemma entry, return it.
     ("one lemma, same pos tag" / "one lemma, different pos tag")
  2) More than one tag/lemma entry: go through the tag/lemmas:
     a) if a lemma with a similar pos tag is found, return it.
        ("multiple lemmas, same pos tag, highest frequency" / "multi lemmas, same pos tag, other frequency")
     b) otherwise, return the most frequent tag/lemma.
        ("multi lemmas, different pos tag, highest frequency")
     *) sorting was non-deterministic if same count?
 
If it is not:
  1) Take Frog entry, and return it.
     ("Frog" / "Frog list")
  2) If this fails:
  return None.
  ("unknown")
'''

# Lemmatise using lexicon files, using tag generated by Frog.
def lemmatise(word, tag):
    if verbose:
        print( "lemmatise(", word, tag, ")" )
    #
    # Check if word in greek_HD
    #
    if word in ghd_words: #.keys():
        # The word is in our dictionary
        word_entry = ghd_words[word]
        if verbose:
            print( "WORD IS IN LEXICON", word_entry )
        # instead of if-then, always take max, but for statistics maybe seperate
        #
        # Check the number of lemmas for this word. If one, the first one is also max. freq.
        #sorted_lemmas = sorted(word_entry.lemmas.values(), key=attrgetter('freq'), reverse=True)
        sorted_lemmas = sorted( sorted(word_entry.lemmas.values(), key=attrgetter('tag'), reverse=False), key=attrgetter('freq'), reverse=True)
        if verbose:
            print( sorted_lemmas )
        # If only one entry, return it no matter the postag.
        if len(sorted_lemmas) == 1: #UNIQUE
            if verbose:
                print( "ONE LEMMA" )
            the_lemma = sorted_lemmas[0]
            if not tag: #data without tags to compare
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
            if compare_postags(tag, the_lemma.tag):
                if verbose:
                    print( "POSTAG MATCH", tag, the_lemma )
                # was this a max_freq tag?
                if the_lemma.freq == max_freq:
                    if not tag or tag == "": #data without tags to compare
                        return (the_lemma, "MLNTHF") #multi lemmas, no pos tag, highest frequency
                    else:
                        return (the_lemma, "MLSTHF") #multi lemmas, same pos tag, highest frequency
                else:
                    if not tag or tag == "": #data without tags to compare
                        return (the_lemma, "MLNTOF") #multi lemmas, no pos tag, other frequency
                    else:
                        return (the_lemma, "MLSTOF") #multi lemmas, same pos tag, other frequency
        # If we end up here, there is no postag match at all, return top-frequency one
        if not tag or tag == "": #data without tags to compare
            return (sorted_lemmas[0], "MLNTHF") #multi lemmas, no pos tag, highest frequency
        else:
            return (sorted_lemmas[0], "MLDTHF") #multi lemmas, different pos tag, highest frequency
    # Word not in ghd_words
    if verbose:
        print( "UNKNOWN WORD", word )
    return (None, "UNKNOWN")

def query_frog_sentence(words):
    if have_frog:
        try:
            frog_out  = frog.process(words)
            if verbose:
                print( "frog_out", frog_out )
            return frog_out
        except:
            print( "Unexpected Frog error:", sys.exc_info()[0] )
            sys.exit(1)
    return None

def extract_postag(tag, l):
    if tag:
        return tag[0:l]
    return ""

# Compare two tags, using the length of the shortest tag supplied.
def compare_postags(tf_tag, l_tag):
    if not tf_tag or not l_tag:
        return False
    l = min(len(tf_tag), len(l_tag))
    if l == 0:
        return False
    return extract_postag(tf_tag, l) == extract_postag(l_tag, l)

        
# ---------------------------------
# Process testfile(s)
# ---------------------------------

# Look up a single word from the lexicon, this is mostly for debugging
# and/or introspective purposes.
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
    print( lemmatise(lookup_l, "") )

# Test file format:
# Lines of Greek text
#
if not filenames:
    print( "\nNOTHING TO DO...", file=sys.stderr )
    lgf.close()
    sys.exit(0)

for filename in filenames:
    # Check for my own output, a bit crude but prevents the worse mistakes.
    if filename.endswith(".stats.txt") or filename.endswith(".wlt.txt"):
        continue
    
    print( "\nLEMMATISING", filename, file=sys.stderr )
    print( "LEMMATISING", filename, file=lgf, flush=True )

    # Reset Counters
    lemmatiser_stats["unknown"] = 0
    for s in strategies:
        lemmatiser_stats[strategies[s]] = 0

    # Output is put into these two files.
    outprefix  = filename
    outfile    = outprefix + suffix +".stats.txt"
    outwltfile = outprefix + suffix + ".wlt.txt"

    # Process test file.
    lcount = 0
    hcount = 0 #count hash lemmas "foo#1"
    wcount = 0 #words processed
    if filename:
        with open(filename, 'r') as f:
            with open(outfile, 'w') as of:
                with open(outwltfile, 'w') as ofwlt:
                    for l in f:
                        l = l.strip()
                        if not l:
                            continue
                        words = l.split()
                        # we need a "wlt" mode for hdt text. and check results
                        if wltmode:
                            words = [words[0]] 
                        if verbose:
                            print( "words", words )
                        if remove_root and words and words[0] == "ROOT":
                            words.pop(0)
                        words = [ normalize('NFC', w) for w in words ]
                        if have_frog:
                            frog_out = query_frog_sentence(" ".join(words) )
                        for word in words:
                            if verbose:
                                print( "\n", word, lcount, wcount )
                            # first frog for POS, then lemmatiser
                            if have_frog:
                                try:
                                    frog_word = frog_out.pop(0)
                                except IndexError:
                                    print( "ABORT. FROG OUTPUT EMPTY" )
                                    sys.exit(1)
                                if verbose:
                                    print( frog_word )
                                frog_w = normalize('NFC', frog_word["text"])
                                frog_l = normalize('NFC', frog_word["lemma"])
                                frog_t = frog_word["pos"]
                                if verbose:
                                    print( "frog("+str(word)+"):", frog_w, frog_l, frog_t )
                            else:
                                frog_t = None
                            # try our lemmatiser, with Frog pos tag
                            the_lemma, ltype = lemmatise( word, frog_t )
                            if verbose:
                                print( "lemmatiser:", word, frog_t, the_lemma, ltype )
                            # we possibly get (NONE, "UNKNOWN")
                            if not the_lemma:
                                #Use frog output for lemma as well
                                if have_frog and frog_w:
                                    the_lemma = Lemma(word, frog_l, frog_t, 0)
                                    the_lemma.src = "frog"
                                    ltype = "FROG"
                                else:
                                    the_lemma = None
                                    ltype = "UNKNOWN"
                            ltype = strategies[ltype]
                            lemmatiser_stats[ltype] += 1
                            if the_lemma:
                                # Note that the POS tag here is the one from the lexica,
                                # and not the one supplied by Frog.
                                if verbose:
                                    print( "lemma =", the_lemma )
                                    print( ltype )
                                #
                                ofwlt.write(word+"\t"+the_lemma.lemma+"\t"+the_lemma.tag+"\n")
                                of.write( word+"\t"+the_lemma.lemma+"\t"+the_lemma.tag+"\t"+repr(the_lemma)+"\t"+ltype+"\n" )
                            else: #not the_lemma
                                of.write( word+"\tUNKNOWN\tUNKNOWN\tNONE\t"+ltype+"\n" )
                                ofwlt.write( word+"\tNONE\tNONE\n" )
                            wcount += 1
                        lcount += 1

    with open(outfile, 'a') as of:
        print( "#", callstr, "["+VERSION+"]", file=of, flush=True )
        print( "#\n# line count", lcount, "word count", wcount, file=of, flush=True ) 

        for stat, count in sorted(lemmatiser_stats.items()):
        #for stat, count in lemmatiser_stats.most_common():
            print( "# {0:<60} {1:5n}".format(stat, count), file=of, flush=True )        

    print( "\nOutput in", file=lgf, flush=True )
    print( " ", outfile, file=lgf, flush=True )
    print( " ", outwltfile, file=lgf, flush=True )
    print( "\nOutput in", file=sys.stderr )
    print( " ", outfile, file=sys.stderr )
    print( " ", outwltfile, file=sys.stderr )

# -- EOT
