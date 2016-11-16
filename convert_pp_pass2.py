#!/usr/bin/env python3
#
import getopt, sys, os
import re

# ----------------------------------------------------------------------------
#
# Takes output from convert_pp.py and makes the final BRAT version.
# Splits also in chapters/books
#  -a           :create (empty) .ann file
#  -b           :split files on "books"
#  -c           :split files on "chapters"
#  -i           :no IDs (not even ROOT), only text
#  -r           :output ROOT instead of "book1-chapter144-section2"
#                (implies .ann files)
#
# NB: overwrites existing files without warning.
#
# TODO: speaker ID annotation
#
# Conversie:
#  python convert_pp4.py -f thuc.hist_gk.xml
#  python convert_pp_pass2.py -f thuc.hist_gk.brat -b -c -r
#  tar and upload all *txt/*ann files to /scratch2/www/brat/data/ThucydidesP
#    fix permissions on all files.
#    copy annotation.conf, tools.conf, visual.conf
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


def toksplit(s):
    res = []
    curr_s = ""
    for c in s: #.decode("utf-8"):
        if c == ",":
            curr_s += " "+c 
            continue
        if c == ".":
            curr_s += " "+c 
            res.append(curr_s.strip())
            curr_s = ""
            continue
        curr_s += c
    if curr_s: #left over
        res.append(curr_s.strip())
    normalised_res = []
    for r in res:
        x = ' '.join( r.split() ) #make sure single spaces
        normalised_res.append( x )
    return normalised_res

        
afile    = None
do_ann   = False #create .ann file
split_c  = False
split_b  = False
no_id    = False #not even ROOT
do_root  = False
tokenise = False
verbose  = False

try:
    opts, args = getopt.getopt(sys.argv[1:], "abcf:irstv", [])
except getopt.GetoptError as err:
    print(str(err))
    sys.exit(1)
for o, a in opts:
    if o in ("-f"):
        afile = a
    elif o in ("-a"):
        do_ann = True
    elif o in ("-b"):
        split_b = True
    elif o in ("-c"):
        split_c = True
        split_b = True #implied
    elif o in ("-i"):
        no_id = True
    elif o in ("-r"):
        do_root = True
    elif o in ("-t"):
        tokenise = True
    elif o in ("-v"):
        verbose = True
    else:
        assert False, "unhandled option"

if not afile:
    print("Need a file ("+sys.argv[0]+" -f FILE).")
    sys.exit(1)

# Output
#file_n, file_e = os.path.splitext(afile)
bratfile = afile + ".tmp.txt" # .brat -> .brat2 WILL BE CHANGED LATER
annfile = afile + ".tmp.ann" # .brat -> .brat2 WILL BE CHANGED LATER
'''
<id>book1-chapter1</id>

<id>book1-chapter1-section1</id>
Θουκυδίδης Ἀθηναῖος ξυνέγραψε τὸν πόλεμον τῶν Πελοποννησίων καὶ Ἀθηναίων, ὡς ἐπολέμησαν πρὸς ἀλλήλους, ἀρξάμενος εὐθὺς καθισταμένου καὶ ἐλπίσας μέγαν τε ἔσεσθαι καὶ ἀξιολογώτατον τῶν προγεγενημένων, τεκμαιρόμενος ὅτι ἀκμάζοντές τε ᾖσαν ἐς αὐτὸν ἀμφότεροι παρασκευῇ τῇ πάσῃ καὶ τὸ ἄλλο Ἑλληνικὸν ὁρῶν ξυνιστάμενον πρὸς ἑκατέρους, τὸ μὲν εὐθύς, τὸ δὲ καὶ διανοούμενον.

<id>book1-chapter1-section2</id>
κίνησις γὰρ αὕτη μεγίστη δὴ τοῖς Ἕλλησιν ἐγένετο καὶ μέρει τινὶ τῶν βαρβάρων, ὡς δὲ εἰπεῖν καὶ ἐπὶ πλεῖστον ἀνθρώπων.
'''
current_id = None
speaker = ""
marker = "" #generalised "speaker" from <speaker>, <l> and other tags
opened_files = {}
curr_start_pos = 0
curr_text_ann = 1 #start at T1
curr_attr_ann = 1 #start at A1
#output = [] #gather text to output per section/...
with open(afile, "r") as f:
    for l in f:
        l = l.strip()
        #print( "{"+l+"}" )
        m = re.match( "<speaker>(.*?)</speaker>", l)
        if m:
            speaker = m.group(1)
            if speaker[-1] == '.':
                speaker = speaker[:-1]
            # note the character positions for .ann file?
            continue
        m = re.match( "<id>(.*?)</id>", l)
        if m:
            #print( m.group(1) )
            current_id = m.group(1)
            do_files = False
            # maybe get sections too, to be able to "ignore them"
            # glue section to ROOT
            #
            # NB, book ID only (<id>book1</id>) gets skipped.
            #
            bits = re.match( "book([0-9]+)\-chapter([0-9]+)\-section([0-9]+).*", current_id )
            if bits:
                sc = str(bits.group(3)) #section
            bits = re.match( "book([0-9]+)\-chapter([0-9]+).*", current_id )
            if bits:
                #print( bits.group(1), bits.group(2) )
                # split into different files per book/chapter...
                bk = str(bits.group(1))
                #ch = str(bits.group(2))
                ch = '{0:03n}'.format(int(bits.group(2))) #chapter, "008"
                if not split_b:
                    bratfile = afile + "2.txt"
                    annfile  = afile + "2.ann"
                if split_b and not split_c:
                    bratfile = afile + ".book" + bk +".txt"
                    annfile  = afile + ".book" + bk +".ann"
                if split_b and split_c:
                    bratfile = afile + ".book" + bk +".chap"+ ch +".txt"
                    annfile  = afile + ".book" + bk +".chap"+ ch +".ann"
            speaker = "" #reset speaker
            continue
        else: # handle normal utf-8 text
            if len(l) > 0:
                #if speaker:
                #    #check for . at end
                #    current_id += "_"+speaker
                #    ##speaker = "" #not yet
                #print( current_id, l )
                res = toksplit(l)
                if len(res) > 1:
                    if verbose:
                        print(repr(res))
                if bratfile in opened_files:
                    mode = "a"
                else:
                    mode = "w"
                    opened_files[bratfile] = 1
                    print( "CREATE: "+bratfile )
                    # reset positions and annotation counters?
                    # could be problem if numbers not monotoon stijgend
                    curr_start_pos = 0
                    curr_text_ann = 1 #start at T1
                    curr_attr_ann = 1 #start at A1
                    #
                    if do_ann:
                        with open(annfile, "w") as af:
                            #af.write("\n")
                            print( "CREATE: "+annfile )
                # write output files
                with open(bratfile, mode) as bf: #not the most efficient #NB APPENDING
                    for s in res: #the split sentences
                        # we want speaker and ROOT? clash?
                        if no_id:
                            current_id = ""
                            bf.write( s+"\n" )
                            curr_start_pos += len(s)
                            if speaker:
                                # also sentence nr? running total?
                                # this is just debug print
                                print( "SPEAKER: "+speaker )
                                print( s )
                            #no id is no annotation?
                        else:
                            if do_root:
                                '''
                                T1      ID 0 4  ROOT
                                A1      Section_0 T1
                                # or
                                T1      Section_1 0 4 ROOT
                                '''
                                current_id = "ROOT" #+str(sc) sc wordt annotatie
                                bf.write( current_id+" " )
                                with open(annfile, "a") as af:
                                    #af.write("T"+str(curr_text_ann)+"\tID "+str(curr_start_pos)+" "+str(curr_start_pos+len(current_id))+"\n" )
                                    #af.write("A"+str(curr_attr_ann)+"\tSection_"+str(sc)+" T"+str(curr_text_ann)+"\n")
                                    af.write("T"+str(curr_text_ann)+"\tS_"+str(sc)+" "+str(curr_start_pos)+" "+str(curr_start_pos+len(current_id))+"\tROOT\n" )
                                    curr_text_ann += 1
                                    curr_attr_ann += 1
                                    curr_start_pos += len(current_id) + 1
                            if speaker:
                                current_id = speaker
                                bf.write( current_id+" " )
                                with open(annfile, "a") as af:
                                    af.write("T"+str(curr_text_ann)+"\tSPEAKER "+str(curr_start_pos)+" "+str(curr_start_pos+len(current_id))+"\t"+speaker+"\n" )
                                    curr_text_ann += 1
                                    curr_start_pos += len(current_id) + 1
                                    #af.write("T"+str(curr_text_ann)+"\tDIRECT "+str(curr_start_pos))
                                    #af.write(" "+str(curr_start_pos+len(s))+"\n") #end pos
                                    #curr_text_ann += 1
                            bf.write( s+"\n" )
                            curr_start_pos += len(s) #up to end of sentence
                            curr_start_pos += 1 #according to test


'''

with open(afile, "r") as f:
    with open(bratfile, "w") as bf:
        for l in f:
            l = l.strip()
            #print( "{"+l+"}" )
            m = re.match( "<id>(.*?)</id>", l)
            if m:
                #print( m.group(1) )
                current_id = m.group(1)
                # maybe split different files per book/chapter...
                continue
            else:
                if len(l) > 0:
                    print( current_id, l )
                    bf.write( current_id+" "+l+"\n" )
'''
                            
print( "READY")
print( "OUTPUT:" )
for f in sorted(opened_files):
    print( f )
#print( "OUTPUT:", bratfile )
                    
