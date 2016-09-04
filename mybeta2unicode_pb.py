# iris 2014-7-1
# adapt to TEI xml format of Thucydides
#
# PJB 2015-02/03/04 Added dbg and file writing, more codes.
#
# beta2unicode.py
#
# usage:
#  python2.7 mybeta2unicode.py plat.l_gk.xml
#
# Version 2004-11-23
#
# James Tauber
# http://jtauber.com/
#
# You are free to redistribute this, but please inform me of any errors
#
# USAGE:
#
# trie = beta2unicodeTrie()
# beta = "LO/GOS\n";
# unicode, remainder = trie.convert(beta)
#
# - to get final sigma, string must end in \n
# - remainder will contain rest of beta if not all can be converted

import time
DBGLIM = -1 #-1 all, #0 off #60 linelength
def dbg(msg):
    if DBGLIM == 0:
        return
    msg = msg.encode('utf-8')
    if dbgf:
        now = "" #time.strftime("%Y%m%d %H:%M:%S")+": "
        if DBGLIM > 0:
            if len(msg) > DBGLIM:
                H = int(DBGLIM/2)-2
                dbgf.write( now+msg[0:H]+" ... "+msg[-H:]+"\n" )
            else:
                dbgf.write( now+msg+"\n" )
        else:
            dbgf.write( now+msg+"\n" )

import re
import sys
def get_until(str, s, c): #("123 <tag>", 4, '>')
    pass
def munge(str):
    '''
    Should probably be rewritten with real HTML/XML parsing
    <milestone> has been taken
    <bibl ...>...</bibl>       <BIBL N="EUR. FR. 956">EUR. FR. 956</BIBL>
    <quote ...>                <QUOTE TYPE="VERSE">
    <l> 
    <l ...>                    <L MET="IAMBIC">
    '''
    i = 0
    bits = 0
    skiplist = [ "BIBL", "BIBL>", "SPEAKER", "SPEAKER>"] #need both because of features inside or not
    betastrlist = []
    txt = ""
    txts = []
    keep = False
    intag = False
    while i < len(str): #or split and per word? no, is glued to words
        c = str[i]
        if c == '<': #begin
            intag = True
            #scan until '>' ?
            if txt: #save text we had up to here
                betastrlist.append(txt)
                #print bits, txt
                bits += 1
            txt = ""
            tag = ""
            j = i
            while j < len(str) and str[j] != '>':
                try:
                    tag += str[j]
                    j += 1
                except IndexError:
                    print "Malformed"
                    sys.exit(2)
            if j < len(str):
                tag += str[j]
            #print "TAG", tag
            if str[j-1] == '/':
                #print "Direct close"
                pass
            tagname = tag.split()[0][1:] # "<BIBL foo" -> BIBL BIBL>
            if tagname in skiplist:
                # skip till first '>' (can we have nested? doesn't seem so.)
                #print "SKIP",
                j += 1
                skipped = ""
                while j < len(str) and str[j] != '>':
                    try:
                        skipped += str[j]
                        j += 1
                    except IndexError:
                        print "Malformed"
                        sys.exit(2)
                if j < len(str):
                    skipped += str[j]
                #print skipped
            i = j
        else:
            txt += str[i]
        i += 1
    if txt:
        betastrlist.append(txt)
        #print bits, txt
        bits += 1
    return betastrlist
            
#print munge('<X/>I(KANW=S U(PO\ SOU= TEQERA/PEUMAI. KAI/ MOI TO\ TOU= *EU)RIPI/DOU KATA\ KAIRO/N E)STIN EI)PEI=N, O(/TI SOI\ PRAGMA/TWN A)/LLWN POTE\ SUMPESO/NTWN&MDASH;<QUOTE TYPE="VERSE"><L MET="IAMBIC">EU)/CH| TOIOU=TON A)/NDRA SOI PARESTA/NAI.</L></QUOTE><BIBL N="EUR. FR. 956">EUR. FR. 956</BIBL>U(POMNH=SAI DE/ SE BOU/LOMAI DIO/TI KAI\ TW=N A)/LLWN TRAGW|DOPOIW=N OI( PLEI=STOI, O(/TAN U(PO/ TINOS A)POQNH/|SKONTA TU/RANNON EI)SA/GWSIN, A)NABOW=NTA POIOU=SIN&MDASH;<l><l/>A')
#sys.exit(1)
     
class Trie:
    def __init__(self):
        self.root = [None, {}]

    def add(self, key, value):
        curr_node = self.root
        for ch in key:
            curr_node = curr_node[1].setdefault(ch, [None, {}])
        curr_node[0] = value

    def find(self, key):
        curr_node = self.root
        for ch in key:
            try:
                curr_node = curr_node[1][ch]
            except KeyError:
                return None
        return curr_node[0]

    def findp(self, key):
        curr_node = self.root
        remainder = key
        for ch in key:
            try:
                curr_node = curr_node[1][ch]
            except KeyError:
                return (curr_node[0], remainder)
            remainder = remainder[1:]
        return (curr_node[0], remainder)

    def convert(self, keystring):
        valuestring = ""
        key = keystring
        while key:
            value, key = self.findp(key)
            if not value:
                return (valuestring, key)
            valuestring += value
        return (valuestring, key)

def beta2unicodeTrie():
    t = Trie()

    t.add("*A",      u"\u0391")
    t.add("*B",      u"\u0392")
    t.add("*G",      u"\u0393")
    t.add("*D",      u"\u0394")
    t.add("*E",      u"\u0395")
    t.add("*Z",      u"\u0396")
    t.add("*H",      u"\u0397")
    t.add("*Q",      u"\u0398")
    t.add("*I",      u"\u0399")
    t.add("*K",      u"\u039A")
    t.add("*L",      u"\u039B")
    t.add("*M",      u"\u039C")
    t.add("*N",      u"\u039D")
    t.add("*C",      u"\u039E")
    t.add("*O",      u"\u039F")
    t.add("*P",      u"\u03A0")
    t.add("*R",      u"\u03A1")
    t.add("*S",      u"\u03A3")
    t.add("*T",      u"\u03A4")
    t.add("*U",      u"\u03A5")
    t.add("*F",      u"\u03A6")
    t.add("*X",      u"\u03A7")
    t.add("*Y",      u"\u03A8")
    t.add("*W",      u"\u03A9")

    t.add("A",      u"\u03B1")
    t.add("B",      u"\u03B2")
    t.add("G",      u"\u03B3")
    t.add("D",      u"\u03B4")
    t.add("E",      u"\u03B5")
    t.add("Z",      u"\u03B6")
    t.add("H",      u"\u03B7")
    t.add("Q",      u"\u03B8")
    t.add("I",      u"\u03B9")
    t.add("K",      u"\u03BA")
    t.add("L",      u"\u03BB")
    t.add("M",      u"\u03BC")
    t.add("N",      u"\u03BD")
    t.add("C",      u"\u03BE")
    t.add("O",      u"\u03BF")
    t.add("P",      u"\u03C0")
    t.add("R",      u"\u03C1")

    t.add("S\n",    u"\u03C2")
    t.add("S,",     u"\u03C2,")
    t.add("S.",     u"\u03C2.")
    t.add("S:",     u"\u03C2:")
    t.add("S;",     u"\u03C2;")
    t.add("S]",     u"\u03C2]")
    t.add("S@",     u"\u03C2@")
    t.add("S_",     u"\u03C2_")
    t.add("S",      u"\u03C3")

    t.add("T",      u"\u03C4")
    t.add("U",      u"\u03C5")
    t.add("F",      u"\u03C6")
    t.add("X",      u"\u03C7")
    t.add("Y",      u"\u03C8")
    t.add("W",      u"\u03C9")

    t.add("I+",     U"\u03CA")
    t.add("U+",     U"\u03CB")

    t.add("A)",     u"\u1F00")
    t.add("A(",     u"\u1F01")
    t.add("A)\\",   u"\u1F02")
    t.add("A(\\",   u"\u1F03")
    t.add("A)/",    u"\u1F04")
    t.add("A(/",    u"\u1F05")
    t.add("E)",     u"\u1F10")
    t.add("E(",     u"\u1F11")
    t.add("E)\\",   u"\u1F12")
    t.add("E(\\",   u"\u1F13")
    t.add("E)/",    u"\u1F14")
    t.add("E(/",    u"\u1F15")
    t.add("H)",     u"\u1F20")
    t.add("H(",     u"\u1F21")
    t.add("H)\\",   u"\u1F22")
    t.add("H(\\",   u"\u1F23")
    t.add("H)/",    u"\u1F24")
    t.add("H(/",    u"\u1F25")
    t.add("I)",     u"\u1F30")
    t.add("I(",     u"\u1F31")
    t.add("I)\\",   u"\u1F32")
    t.add("I(\\",   u"\u1F33")
    t.add("I)/",    u"\u1F34")
    t.add("I(/",    u"\u1F35")
    t.add("O)",     u"\u1F40")
    t.add("O(",     u"\u1F41")
    t.add("O)\\",   u"\u1F42")
    t.add("O(\\",   u"\u1F43")
    t.add("O)/",    u"\u1F44")
    t.add("O(/",    u"\u1F45")
    t.add("U)",     u"\u1F50")
    t.add("U(",     u"\u1F51")
    t.add("U)\\",   u"\u1F52")
    t.add("U(\\",   u"\u1F53")
    t.add("U)/",    u"\u1F54")
    t.add("U(/",    u"\u1F55")
    t.add("W)",     u"\u1F60")
    t.add("W(",     u"\u1F61")
    t.add("W)\\",   u"\u1F62")
    t.add("W(\\",   u"\u1F63")
    t.add("W)/",    u"\u1F64")
    t.add("W(/",    u"\u1F65")

    t.add("A)=",    u"\u1F06")
    t.add("A(=",    u"\u1F07")
    t.add("H)=",    u"\u1F26")
    t.add("H(=",    u"\u1F27")
    t.add("I)=",    u"\u1F36")
    t.add("I(=",    u"\u1F37")
    t.add("U)=",    u"\u1F56")
    t.add("U(=",    u"\u1F57")
    t.add("W)=",    u"\u1F66")
    t.add("W(=",    u"\u1F67")

    t.add("*A)",     u"\u1F08")
    t.add("*)A",     u"\u1F08")
    t.add("*A(",     u"\u1F09")
    t.add("*(A",     u"\u1F09")
    #
    t.add("*(\A",    u"\u1F0B")
    t.add("*A)/",    u"\u1F0C")
    t.add("*)/A",    u"\u1F0C")
    t.add("*A(/",    u"\u1F0F")
    t.add("*(/A",    u"\u1F0F")
    t.add("*E)",     u"\u1F18")
    t.add("*)E",     u"\u1F18")
    t.add("*E(",     u"\u1F19")
    t.add("*(E",     u"\u1F19")
    #
    t.add("*(\E",    u"\u1F1B")
    t.add("*E)/",    u"\u1F1C")
    t.add("*)/E",    u"\u1F1C")
    t.add("*E(/",    u"\u1F1D")
    t.add("*(/E",    u"\u1F1D")

    t.add("*H)",     u"\u1F28")
    t.add("*)H",     u"\u1F28")
    t.add("*H(",     u"\u1F29")
    t.add("*(H",     u"\u1F29")
    t.add("*H)\\",   u"\u1F2A")
    t.add(")\\*H",   u"\u1F2A")
    t.add("*)\\H",    u"\u1F2A")
    #
    t.add("*H)/",    u"\u1F2C")
    t.add("*)/H",    u"\u1F2C")
    #
    t.add("*)=H",    u"\u1F2E")
    t.add("(/*H",    u"\u1F2F")
    t.add("*(/H",    u"\u1F2F")
    t.add("*I)",     u"\u1F38")
    t.add("*)I",     u"\u1F38")
    t.add("*I(",     u"\u1F39")
    t.add("*(I",     u"\u1F39")
    t.add("*)=I",    u"\u1F36") #PJB 20140407
    #
    #
    t.add("*I)/",    u"\u1F3C")
    t.add("*)/I",    u"\u1F3C")
    #
    #
    t.add("*I(/",    u"\u1F3F")
    t.add("*(/I",    u"\u1F3F")
    #
    t.add("*O)",     u"\u1F48")
    t.add("*)O",     u"\u1F48")
    t.add("*O(",     u"\u1F49")
    t.add("*(O",     u"\u1F49")
    #
    #
    t.add("*(\O",    u"\u1F4B")
    t.add("*O)/",    u"\u1F4C")
    t.add("*)/O",    u"\u1F4C")
    t.add("*O(/",    u"\u1F4F")
    t.add("*(/O",    u"\u1F4F")
    #
    t.add("*U(",     u"\u1F59")
    t.add("*(U",     u"\u1F59")
    #
    t.add("*(/U",    u"\u1F5D")
    #
    t.add("*(=U",    u"\u1F5F")
    
    t.add("*W)",     u"\u1F68")
    t.add("*W(",     u"\u1F69")
    t.add("*(W",     u"\u1F69")
    #
    #
    t.add("*W)/",    u"\u1F6C")
    t.add("*)/W",    u"\u1F6C")
    t.add("*W(/",    u"\u1F6F")
    t.add("*(/W",    u"\u1F6F")

    t.add("*A)=",    u"\u1F0E")
    t.add("*)=A",    u"\u1F0E")
    t.add("*A(=",    u"\u1F0F")
    t.add("*W)=",    u"\u1F6E")
    t.add("*)=W",    u"\u1F6E")
    t.add("*W(=",    u"\u1F6F")
    t.add("*(=W",    u"\u1F6F")

    t.add("A\\",    u"\u1F70")
    t.add("A/",     u"\u1F71")
    t.add("E\\",    u"\u1F72")
    t.add("E/",     u"\u1F73")
    t.add("H\\",    u"\u1F74")
    t.add("H/",     u"\u1F75")
    t.add("I\\",    u"\u1F76")
    t.add("I/",     u"\u1F77")
    t.add("O\\",    u"\u1F78")
    t.add("O/",     u"\u1F79")
    t.add("U\\",    u"\u1F7A")
    t.add("U/",     u"\u1F7B")
    t.add("W\\",    u"\u1F7C")
    t.add("W/",     u"\u1F7D")

    t.add("A)/|",   u"\u1F84")
    t.add("A(/|",   u"\u1F85")
    t.add("H)|",    u"\u1F90")
    t.add("H(|",    u"\u1F91")
    t.add("H)/|",   u"\u1F94")
    t.add("H)=|",   u"\u1F96")
    t.add("H(=|",   u"\u1F97")
    t.add("W)|",    u"\u1FA0")
    t.add("W(=|",   u"\u1FA7")

    t.add("A=",     u"\u1FB6")
    t.add("H=",     u"\u1FC6")
    t.add("I=",     u"\u1FD6")
    t.add("U=",     u"\u1FE6")
    t.add("W=",     u"\u1FF6")

    t.add("I\\+",   u"\u1FD2")
    t.add("I/+",    u"\u1FD3")
    t.add("I+/",    u"\u1FD3")
    t.add("U\\+",   u"\u1FE2")
    t.add("U/+",    u"\u1FE3")

    t.add("A|",     u"\u1FB3")
    t.add("A/|",    u"\u1FB4")
    t.add("H|",     u"\u1FC3")
    t.add("H/|",    u"\u1FC4")
    t.add("W|",     u"\u1FF3")
    t.add("W|/",    u"\u1FF4")
    t.add("W/|",    u"\u1FF4")

    t.add("A=|",    u"\u1FB7")
    t.add("H=|",    u"\u1FC7")
    t.add("W=|",    u"\u1FF7")

    t.add("W)=|",   u"\u1FA6") #PJB 20150401
    t.add("U=+",    u"\u1FE7") #PJB 20150401
    t.add("A\|",    u"\u1FB2") #PJB 20150401
    t.add("H\|",    u"\u1FC2") #PJB new, volgens mail 2015-03-23
    t.add("H(/|",   u"\u1F95") #PJB new, volgens mail 2015-03-23
    t.add("W\|",    u"\u1FF2") #PJB new, volgens mail 2015-03-23
    t.add("A)|",    u"\u1F80") #PJB new, volgens mail 2015-03-23
    t.add("A)=|",   u"\u1F86") #PJB new, volgens mail 2015-03-23

    
    t.add("R(",     u"\u1FE4")
    t.add("*R(",    u"\u1FEC")
    t.add("*(R",    u"\u1FEC")

#    t.add("~",      u"~")
#    t.add("-",      u"-")
    
#    t.add("(null)", u"(null)")
#    t.add("&", "&")
    
    t.add("0", u"0")
    t.add("1", u"1")
    t.add("2", u"2")
    t.add("3", u"3")
    t.add("4", u"4")
    t.add("5", u"5")
    t.add("6", u"6")
    t.add("7", u"7")
    t.add("8", u"8")
    t.add("9", u"9")
    
    t.add("@", u"@")
    t.add("$", u"$")
    
    t.add(" ", u" ")
    
    t.add(".", u".")
    t.add(",", u",")
    t.add("'", u"'")
    t.add(":", u":")
    t.add(";", u";")
    t.add("_", u"_")
    t.add("-", u"-") #PJB

    t.add("[", u"[")
    t.add("]", u"]")
    
    t.add("\n", u"")
    
    # edits by iris:
    # greek small letter omega with psili and oxia and ypogegrammeni U+1FA4
    t.add("W)/|",      u"\u1FA4")
    # *)W  -> greek capital letter omega with psili (U+1F68)
    t.add("*)W",      u"\u1F68")
    # *(/o -> greek capital letter omicron with dasia and oxia (U+1F4D)
    t.add("*(/O",      u"\u1F4D")

    # some HTML entities that occur in the XML text.	
    t.add("&RPAR;",      ")")
    t.add("&LPAR;",      "(")
    t.add("&DAGGER;",	u"\u2020")  

    t.add("&MDASH;",   "-")   #PJB
    t.add("&DASH;",    "-")   #PJB
    t.add("&LDQUO;",   '"')   #PJB
    t.add("&RDQUO;",   '"')   #PJB
    t.add("&LSQUO;",   "'")   #PJB
    t.add("&RSQUO;",   "'")   #PJB
    t.add("&LSQB;",    '[')   #PJB
    t.add("&RSQB;",    ']')   #PJB
    t.add("&LT;",      '<')   #PJB
    t.add("&GT;",      '>')   #PJB
    t.add("&AST;",     '*')   #PJB
    
    return t

t = beta2unicodeTrie()

import os, re, codecs, sys
inbody=0

'''
for f in ~/SURFdrive/Shared/GreekPerspectives/Data/Plato_perseus/Orig/*gk.xml;
do
echo $f
python2 Ancient-greek-master/mybeta2unicode.py $f
done

find  ~/SURFdrive/Shared/GreekPerspectives/Data/ -type f -iname "*gk.xml" -print0 | while IFS= read -r -d $'\0' line; do
    echo "$line"
    python2 Ancient-greek-master/mybeta2unicode.py "$line"
done

'''
    
fp = sys.argv[1] #full path
fn = os.path.basename(fp)  #filename

dbgfile = fn+".log"
dbgf = open(dbgfile, "w", 1)

dbg("START converting "+fn)

lc = 0 #line count
wc = 0 #word count
with open(fn+".txt", "w") as to: #only the converted greek text
    with open(fn+".uc.xml", "w") as uo: #unicode/converted xml out, all
        for line in file(sys.argv[1]):
            line = line.rstrip()
            lc += 1
            spans = []
            it = re.finditer(r"(<milestone.*?\>)", line)
            for match in it:
               #print match.group(), match.span()
               # match.span contains character indices
               spans.append(match.span())
            '''
            Example for a line with one <milestone...>:
            [(0, 36), [105, 0]]
            0 36 <milestone unit="section" n="337b"/>
            36 105 ka)/peita, au(/th dh/, e)/fh, h( *swkra/tous sofi/a: au)to\n me\n mh\
            '''
            if spans == []: #no milestones in line
                pass
            else:
                spans.append([len(line)-1,0]) #last character, end, leftover, etc
            '''
            <milestone unit="section" n="338c"/> (0, 36)
            <milestone ed="P" unit="para"/> (36, 67)
            <milestone ed="P" unit="para"/> (233, 264)
            [(0, 36), (36, 67), (233, 264), [593, 0]]

            Other:
            <milestone unit="page" n="281"/><milestone n="281a" unit="section"/><sp><speaker>*swkra/ths</speaker><p>
                                                                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            '''
            '''
            for chunk in range(0,len(spans)-1):
                bm = spans[chunk][0]   #start of milestone
                em = spans[chunk][1]   #end of milestone
                bt = spans[chunk][1]   #start of text after <milestone...>
                et = spans[chunk+1][0] #end of text
                print bm, em, line[bm:em]
                print bt, et, line[bt:et]
                print
            '''
            if spans:
                for chunk in range(0,len(spans)-1):
                    bm = spans[chunk][0]     #start of milestone
                    em = spans[chunk][1]     #end of milestone
                    bt = spans[chunk][1]     #start of text after <milestone...>
                    et = spans[chunk+1][0]+1 #end of text
                    #
                    # Look for speaker here?
                    #
                    milestonestr = line[bm:em]
                    betacodestr  = line[bt:et].upper()
                    #
                    bsl = munge(betacodestr)
                    #dbg(repr(bsl))
                    #
                    uo.write( milestonestr )
                    # maybe do conversion per word?
                    for betacodestr in bsl:
                        '''
                        # Test each word for possible conversion error
                        for bw in betacodestr.split():
                            a, b = t.convert(bw)
                            if b:
                                print bw, a, b
                        '''
                        wc += len(betacodestr.split())
                        a, b = t.convert(betacodestr)
                        if b: #b contains left over, is unconverted
                            ##print(a.encode("utf-8"), b)
                            # Assuming words are split with spaces, the last encoded word index
                            # is the index to the word that failed in the betacodestr.
                            wca = len(a.split())-1
                            print "ERROR in line", lc, "word", wca+1,":", betacodestr.split()[wca]
                            print milestonestr
                            dbg("ERROR in line "+str(lc)+", word "+str(wca+1)+": "+betacodestr.split()[wca])
                            #dbg(milestonestr)
                            dbg("beta="+betacodestr)
                            dbg("okay="+a)
                            dbg("rest="+b)
                            dbg("")
                        uo.write(a.encode("utf-8")+"\n")
                        to.write(a.encode("utf-8")+"\n")
            else:
                ##print line,
                uo.write(line)
dbg("END converting "+fn)
print "Logfile", dbgfile
#print fn+".uc.xml" #experimental
print fn+".txt"
