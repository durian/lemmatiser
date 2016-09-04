#!/usr/bin/env python3
#
import getopt, sys, os
import re
from bs4 import BeautifulSoup

# ----------------------------------------------------------------------------
#
# convert_pp.py: converts from betacode to UTF-8, and post processes
#                final sigmas.
#                Computes IDs like "page383-section383b_SP_Ἑρμογένησ",
#                depending on information in the XML.
#
# Usage:
#  python3 convert_pp.py -f plat.laws_gk.xml
#
# Optional arguments:
#  -m cltk      :uses the cltk beta-utf8 converter
#  -s           :split lines on "."
#  -v           :verbose utput
#
# Converted output in plat.laws_gk.brat
#
# Needs: TrieConvert.py and/or CLTK installed.
#
# ----------------------------------------------------------------------------

# Convert beta to utf8
try:
    from cltk.corpus.greek.beta_to_unicode import Replacer
    from lxml import etree
    r = Replacer()
except:
    print(" No CLTK toolkit found." )
    r = None
    
# Or this way
try:
    import TrieConvert
    t = TrieConvert.beta2unicodeTrie()
except:
    print( "TrieConvert not found." )
    t = None

if not t and not r:
    print("No conversion possible.")
    sys.exit(1)
    
afile   = None
split   = False
verbose = False
mode    = "trie"

# Pattern for final sigma conversion (need greek colon?)
SRCH = "σ"
REPL = "ς"
pattern = re.compile(r"("+SRCH+")($|[.:;]|\))", re.UNICODE)
#                         ^^^^sigma
#                                 ^ end of line
#                                   ^^^^^ or .:;
#                                         ^^^ or )
#
def final_sigma(l):
    cnt = 0
    it = re.finditer(pattern, l)
    a = 0 #start position (anchor)
    new_l = ""
    for match in it:
        if verbose:
            print( "MATCH", match.group(1)+match.group(2), match.span(), "..."+l[int(match.span()[0])-4:int(match.span()[1])+2]+"..." )
        sb = match.span()[0] #span begin
        se = match.span()[1] #span end
        new_l += l[a:sb] + REPL + l[sb+1:se] #prematch, changed sigma, and rest
        cnt += 1
        a = se #anchor at end of match for next iteration
    new_l += l[a:] #rest of the line
    return new_l, cnt

def beta2utf(form):
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
        uniform, cntc = re.subn(":", "·", uni_form) #count?
        return uni_form

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
        if self.speaker:
            id += "_SP_"+self.speaker
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
    opts, args = getopt.getopt(sys.argv[1:], "f:m:sv", [])
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
    elif o in ("-v"):
        verbose = True
    else:
        assert False, "unhandled option"

if not afile:
    print("Need a file.")
    sys.exit(1)

# UTF8 output
file_n, file_e = os.path.splitext(afile)
bratfile = file_n + ".brat"

tei = open(afile).read()
soup = BeautifulSoup(tei)

if verbose:
    print(soup.prettify())
    print

#

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
        sps_siblings = div1.descendants #.body.div1.children
        sps_siblings_iter = iter(sps_siblings)
        for sib in sps_siblings_iter:
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
                    bf.write( my_id.get_id()+"\n" )
                #next(sps_siblings_iter, None) #milestone can contain text
                #use next_element ?
                #print( "NEXT", sib.next_element )
                continue
            if sib.name == "speaker":
                my_id.parse_speaker(sib)
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
                next(sps_siblings_iter, None) #don't keep?
                continue
            if sib.name == "q": #like DEL
                print("Q", sib)
                next(sps_siblings_iter, None) #don't keep?
                continue
            if sib.name == "cit": #like DEL
                print("CIT", sib)
                next(sps_siblings_iter, None) #don't keep?
                continue
            # from the following tags we include <tag>contents</tag>
            if sib.name in ["p", "sp", "add", "quote", "gap", "text", "emph"]:
                continue #handle on next level
            if sib.name: # and sib.name not in ["del", "milestone", "speaker", "bibl", "l", "q"]:
                print("\nUNHANDLED", sib.name)
                #print( sib.prettify() )
                sys.exit(1)
            # left is text
            if len(sib.strip()) > 0:
                print("BETAC", sib.strip())
                if split:
                    sentences = re.split(r"(\.\s*)", sib)
                else:
                    sentences = [ sib.strip() ]
                i = 0
                while i < len(sentences):
                    form = sentences[i].strip().upper()  # make upper case for Beta Code converter
                    if not form:
                        i += 1
                        continue
                    if i < len(sentences)-1 and sentences[i+1].strip() == ".":
                        form += " ."
                        i += 1
                    uni_form = beta2utf(form)
                    print("GREEK", uni_form)
                    bf.write(uni_form+"\n")
                    i += 1

print( "READY")
print( "OUTPUT:", bratfile )
                    
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
