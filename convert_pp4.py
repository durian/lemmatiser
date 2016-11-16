#!/usr/bin/env python3
#
import getopt, sys, os
import re
from bs4 import BeautifulSoup

# ----------------------------------------------------------------------------
#
# convert_pp2.py: converts from betacode to UTF-8, and post processes
#                 final sigmas.
#                 Computes IDs like "<id>page383-section383b</id>
#                 and <speaker>Ἑρμογένησ</speaker>
#                 depending on information in the XML.
#
# Usage:
#  python3 convert_pp2.py -f plat.laws_gk.xml
#  ... (lots of output)
#  READY
#  OUTPUT: plat.laws_gk.brat
#
# Optional arguments:
#  -m cltk      :uses the cltk beta-utf8 converter instead of
#                TrieConvert.py
#  -s           :split lines on "."
#  -t           :tokenise lines
#  -v           :verbose output
#  -S           :speaker ID in ID
#
# Converted output in plat.laws_gk.brat
#
# Needs: bs4 and TrieConvert.py and/or CLTK installed.
# ( easy_install beautifulsoup4 )
# ( pip install  beautifulsoup4 )
#
# ----------------------------------------------------------------------------

# Convert beta to utf8
try:
    from cltk.corpus.greek.beta_to_unicode import Replacer
    from lxml import etree
    r = Replacer()
    # and 20150804:
    from cltk.tokenize.sentence import TokenizeSentence
    from cltk.stop.greek.stops import STOPS_LIST
    tokenizer = TokenizeSentence('greek')
    #
    from nltk.tokenize.punkt import PunktLanguageVars
    plv = PunktLanguageVars() #not useful
except:
    print(" No CLTK/NTLK toolkits found." )
    r = None

#tokenizer.tokenize_sentences(sentence)
#tokens = plv.word_tokenize(sentence.lower())
    
# Or this way
try:
    import TrieConvert
    t = TrieConvert.beta2unicodeTrie()
except:
    print( "TrieConvert not found." )
    t = None

if not t and not r:
    print("No conversion/tokenisation possible.")
    sys.exit(1)
    
afile    = None
split    = False
tokenise = False
verbose  = False
mode     = "trie"

# Pattern for final sigma conversion (need greek colon?)
SRCH = "σ"
REPL = "ς"
#
def final_sigma(l):
    cnt = 0
    new_l = ""
    new_l = []
    for w in l.split():
        if  w[-1] == SRCH:
            new_w = w[:-1] + REPL
            if verbose:
                print( "endsigma", w, "->", new_w )
            cnt += 1
        elif len(w) > 1 and w[-2] == SRCH and w[-1] in [".", ","]: # the Trie seems to do these
            new_w = w[:-2] + REPL + w[-1]
            if verbose:
                print( "endsigma", w, "->", new_w )
            cnt += 1
        else:
            if verbose:
                pass
                #print( "e =", w )
            new_w = w
        new_l.append(new_w)
    return " ".join(new_l), cnt

def beta2utf(form):
    #return form #for quick testing
    if mode == "none":
        return form
    if mode == "cltk":
        if r:
            uni_form = r.beta_code(form)
            return uni_form
        else:
            print( "CLTK not present." )
            sys.exit(1)
    else:    
        uni_form, b = t.convert(form)
        if b:
            print( "----------> ERROR <-----------" )
            bf.write( "----------> ERROR <-----------\n" )
            print( uni_form )
            print( form )
            bf.write( uni_form+"\n" )
            bf.write( form+"\n" )
            print
            print( b )
            bf.write( b+"\n" )
            sys.exit(1)
        uniform, cnt  = final_sigma(uni_form)
        uniform, cntc = re.subn(":", "·", uniform) #count?
        return uniform

class ID():
    def __init__(self):
        self.current_id = {}
        for i in ["book", "chapter", "page", "section"]:
            self.current_id[i] = "?"
        self.book = ""
        self.chapter = ""
        self.page = ""
        self.para = ""
        self.section = ""
        self.speaker = ""
    def get_id(self):
        id = ""
        # skip if "?" ? Allow to set on startup for missing/start?
        for i in ["book", "chapter", "page", "section"]:
            if str(self.current_id[i]) != '?':
                id += i + "" + str(self.current_id[i])+ "-"
        id = id[:-1]
        return id
    def parse_speaker(self, sib):
        if sib:
            form = sib.string.strip().upper()  # make upper case for Beta Code converter
            uni_form = beta2utf(form)
            self.speaker = uni_form 
            print( "NEW ID", self.get_id() )
    def parse(self, sib):
        if sib.name == "milestone":
            old_id = self.get_id()
            try:
                unit = sib["unit"]
            except KeyError:
                unit = None
            try:
                n = sib["n"]
            except KeyError:
                n = None
            try:
                ed = sib["ed"]
            except KeyError:
                ed = None
            if unit and n:
                self.current_id[unit] = n
                if self.get_id() != old_id:
                    #print( "OLD ID", old_id )
                    print( "NEW ID", self.get_id() )
            return old_id != self.get_id() #return True if changed
        elif sib.name == "div1": #has book info
            try:
                typ = sib["type"]
            except KeyError:
                typ = None
            try:
                n = sib["n"]
            except KeyError:
                n = None
            my_id.current_id[typ] = n
            print( "NEW ID", self.get_id() )
    
try:
    opts, args = getopt.getopt(sys.argv[1:], "f:m:stv", [])
except getopt.GetoptError as err:
    print(str(err))
    sys.exit(1)
for o, a in opts:
    if o in ("-f"):
        afile = a
    elif o in ("-m"):
        mode = a
    elif o in ("-s"):
        split = True
    elif o in ("-t"):
        tokenise = True
    elif o in ("-v"):
        verbose = True
    else:
        assert False, "unhandled option"

if not afile:
    print("Need a file ("+sys.argv[0]+" -f FILE).")
    sys.exit(1)

# UTF8 output
file_n, file_e = os.path.splitext(afile)
bratfile = file_n + ".brat"

tei = open(afile).read()
soup = BeautifulSoup(tei, ['lxml', 'xml'])

if verbose:
    print(soup.prettify())
    print
    print
    #print( soup.findAll('sp') )
    print( len(soup.findAll('sp')) )
    print
    print
    #print( soup.findAll('p') )
    print( len(soup.findAll('p')) )
    sys.exit(1)

#
def handle_sib0(sib, level=0, hist=[]):
    print( "ENTER ->", level, hist, sib.name )
    for x in sib.find_next(): #could be none
        print( x )
        try:
            x_children = x.find_all() #also contents/siblings
            #print( level ) #, repr(sib_children) )
            for child in x_children:
                handle_sib(child, level+1, hist + [x.name])
        except AttributeError:
            print( level, "NO CHILDREN", repr(sib) )
    print( "LEAVE <-", sib.name )

# GLOBAL
#
output = []
stats = {}

def output_converted(sib, output, hist=[]):
    print( sib, hist )
    if len(sib.strip()) > 0:
        print("BETAC", sib.strip())
        sentences = [ sib.strip() ]
        i = 0
        while i < len(sentences):
            form = sentences[i].strip().upper()  # make upper case for Beta Code converter
            if not form:
                i += 1
                continue
            #if i < len(sentences)-1 and sentences[i+1].strip() == ".":
            #    form += " ."
            #    i += 1
            uni_form = beta2utf(form)
            print("GREEK", uni_form)
            # tokenise here, this is more like an alternative for "split" above
            output.append(uni_form)
            i += 1
        #bf.write( ' '.join( output )+"\n" )
    return output

def write_output(output, bf):
    s = ""
    x = ' '.join(output)
    tmp = x.split() #make sure only single spaces
    x = ' '.join(tmp)
    for w in x.split():
        if w[-1:] == ".":
            s += w[:-1] + " ."
            form = s.strip().upper()  # make upper case for Beta Code converter
            uni_form = beta2utf(form)
            bf.write( uni_form+"\n" )
            s = ""
        elif w[-1:] == ",":
            s += w[:-1] + " , "
        else:
            if w not in ['\n', '\t']:
                s += w + " "
    if s:
        form = s.strip().upper()  # make upper case for Beta Code converter
        uni_form = beta2utf(form)
        bf.write( uni_form+"\n" )
                
def handle_sib(sib, bf, level=0, hist=[]):
    global output, stats
    #print( "ENTER ->", level, hist, sib.name )
    # before milestone and speaker, output?
    if sib.name == "milestone":
        write_output(output, bf)
        output = []
        if my_id.parse(sib):
            bf.write( "\n<id>"+my_id.get_id()+"</id>\n" ) #maybe between <id>
        #return #assume no text inside milestone
    if sib.name == "speaker": #sp?
        write_output(output, bf)
        output = []
        my_id.parse_speaker(sib)
        bf.write( "\n<speaker>"+my_id.speaker+"</speaker>\n" )
        return #need a return, otherwise we include speaker as CONTENTS also
    # decide on high level if to skip here (output?)
    if sib.name in ["del", "bibl"]: #SKIP ["l"] 
        print( "SKIP:", sib )
        path = ["SKIP"] + hist
        try:
            stats[repr(path)] += 1
        except KeyError:
            stats[repr(path)] = 1
        return 
    try:
        for x in sib.contents:
            # print( "CONTENTS", x )
            if x.name:
                handle_sib(x, bf, level+1, hist+[x.name])
            else:
                print( "CONTENTS", x, hist, output )
                #bf.write( x + "\n" )
                if sib:
                    output.append( x )
                    #converted_output = output_converted(x, output, hist)
                    #if converted_output:
                    #    print( "COUT", converted_output )
                    #    bf.write( ' '.join( converted_output )+"\n" )
    except AttributeError:
        print( "NONE" )
    #print( "LEAVE <-", sib.name )
    try:
        stats[repr(hist)] += 1
    except KeyError:
        stats[repr(hist)] = 1

my_id = ID()
'''
Plato:
<body>
<div1 type="book" n="1">
<milestone unit="page" n="624"/>
Thuc:
<body>
<div1 n="1" type="book"><p>
<milestone unit="chapter" n="1"/>
'''
with open(bratfile, "w") as bf:
    div1s = soup.findAll('div1')
    if len(div1s) == 0:
        div1s = soup.findAll('group')
    if len(div1s) == 0:
        div1s = soup.findAll('body')    
    for div1 in div1s:
        my_id.parse(div1)
        bf.write( "<id>"+my_id.get_id()+"</id>\n" ) #maybe between <id>
        handle_sib(div1, bf, 0, [div1.name])
        write_output( output, bf )
    
'''            
            #print()
            #print("\n", sib, sib.name, sib.string)
            # PJB still messy, if time, redo
            #
            p = sib.parent
            if sib.name == "del":
                print("DEL", sib)
                next(sps_siblings_iter, None) #skip this one
                continue
            if sib.name == "milestone":
                if my_id.parse(sib):
                    # HERE WE SHOULD WRITE OUTPUT
                    bf.write( ' '.join( output )+"\n" )
                    output = []
                    bf.write( "\n<id>"+my_id.get_id()+"</id>\n" ) #maybe between <id>
                #next(sps_siblings_iter, None) #milestone can contain text
                #use next_element ?
                #print( "NEXT", sib.next_element )
                continue
            if sib.name == "speaker":
                my_id.parse_speaker(sib)
                # maybe no ouput if speaker ID in ID tag
                # HERE WE SHOULD WRITE OUTPUT
                bf.write( ' '.join( output )+"\n" )
                output = []
                bf.write( "\n<speaker>"+my_id.speaker+"</speaker>\n" )
                next(sps_siblings_iter, None) #don't keep?
                continue
            if sib.name == "bibl": #like DEL
                print("BIBL", sib)
                next(sps_siblings_iter, None) #don't keep?
                continue
            # the contents of the following tags is not included
            if sib.name in ["castlist", "castitem", "role", "term"]: #like DEL
                print("CAST", sib)
                next(sps_siblings_iter, None) #don't keep?
                continue
            if sib.name == "l": #like DEL
                print("L", sib)
                #
                # For pass2 we could add output like this: (convert string!)
                # bf.write("<L>"+sib.string+"</L>\n") #or sib.get_text()
                # or just a <L>..</L> and the string on the next line,
                # like the speaker texts.
                #
                next(sps_siblings_iter, None) #don't keep?
                continue
            if sib.name == "q": #like DEL
                print("Q", sib) #shoudl take sib in (recursive) routine
                sys.exit(1)
                next(sps_siblings_iter, None) #don't keep?
                continue
            if sib.name == "cit": #like DEL
                print("CIT", sib)
                next(sps_siblings_iter, None) #don't keep?
                continue
            # from the following tags we include <tag>contents</tag>
            if sib.name in ["p", "sp", "add", "quote", "gap", "text", "emph"]:
                # TODO, sp moet annotatie worden, <sp> is alles van speaker.
                # TODO betere XML parsing...
                # output quote here?
                # problem: introduces linefeeds... assemble in pass2?
                if sib.name == "add":
                    print( "ADD:"+sib.string )
                continue #handle on next level
            if sib.name: # and sib.name not in ["del", "milestone", "speaker", "bibl", "l", "q"]:
                print("\nUNHANDLED", sib.name)
                #print( sib.prettify() )
                sys.exit(1)
            # left is text
            if len(sib.strip()) > 0:
                print("BETAC", sib.strip())
                sentences = [ sib.strip() ]
                i = 0
                while i < len(sentences):
                    form = sentences[i].strip().upper()  # make upper case for Beta Code converter
                    if not form:
                        i += 1
                        continue
                    #if i < len(sentences)-1 and sentences[i+1].strip() == ".":
                    #    form += " ."
                    #    i += 1
                    uni_form = beta2utf(form)
                    print("GREEK", uni_form)
                    # tokenise here, this is more like an alternative for "split" above
                    output.append(uni_form)
                    i += 1
    bf.write( ' '.join( output )+"\n" )
    output = []

print( "READY")
print( "OUTPUT:", bratfile )
'''
print( "Stats:" )
for s in sorted(stats, key=stats.get, reverse=True): #s is repr() strings
    if s[2:6] != "SKIP":
        print( s, stats[s] )
print("---")
for s in sorted(stats, key=stats.get, reverse=True):
    if s[2:6] == "SKIP":
        print( s, stats[s] )

print( "OUTPUT", bratfile )

'''
UNHANDLED:

<quote type="verse"><l met="dactylic">au(/th toi di/kh e)sti\ qew=n oi(\ *)/olumpon e)/xousin,</l></quote>

<bibl n="Hom. Od. 19.43">Hom. Od. 19.43</bibl>

<bibl n="Hom. Il. 2.108">
 Hom. Il. 2.108
</bibl>

<cit>
 <quote type="verse">
  <l met="c">
   e)/nqa ke sh\ boulh\ dhlh/setai, oi(=' a)goreu/eis.
  </l>
 </quote>
 <bibl>
  Hom. Il. 14.96
 </bibl>
</cit>

<term>fai/netai</term>

<emph>mh/pw me/g' ei)/ph|s</emph>

STRANGE:
BETAC a)lhqe/stata le/geis, w)= *me/gille, kai\ e)gw\ poih/sw tau=q' ou(/tws kai\ <su\> sulla/mbane.
GREEK ἀληθέστατα λέγεις, ὦ Μέγιλλε, καὶ ἐγὼ ποιήσω ταῦθ’ οὕτως καὶ <σὺ> συλλάμβανε.
'''


