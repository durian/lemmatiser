# python3
#
# 2017-01-13 Version 1

import re, glob
import getopt, sys, os
from unicodedata import normalize
from collections import Counter

debug = False
def DBG(*strs):
    if debug:
        sys.stderr.write("DBG:"+"".join(str(strs))+"\n")

'''
Counts statistics on brat .txt and .ann files

USAGE: specify the *txt files (wildcards are expanded):
  python3 bratstats.py -f "thuc.hist_gk.brat.book6*.txt"

For each .txt file, an .ann file is expexted.

# ----

Dit is een lijstje met aantallen die ik graag zou willen weten:

number of words
number of sentences
number of complements

number of complements that contain a root
(like this inthuc.hist_gk.brat.book7.chap048.ann:
T32	Complement 843 846;851 873;874 972;973 1178	οὐκ ἀπάξειν τὴν στρατιάν . ROOT εὖ γὰρ εἰδέναι ὅτι Ἀθηναῖοι σφῶν ταῦτα οὐκ ἀποδέξονται , ὥστε μὴ αὐτῶν ψηφισαμένων ἀπελθεῖν . ROOT καὶ γὰρ οὐ τοὺς αὐτοὺς ψηφιεῖσθαί τε περὶ σφῶν καὶ τὰ πράγματα ὥσπερ καὶ αὐτοὶ ὁρῶντας καὶ οὐκ ἄλλων ἐπιτιμήσει ἀκούσαντας γνώσεσθαι , ἀλλ' ἐξ ὧν ἄν τις εὖ λέγων διαβάλλοι , ἐκ τούτων αὐτοὺς πείσεσθαι
)

average number of word of complements, in general and for direct vs indirect complements

number of direct complements
number of indirect complements
number of NP complements

number of mixed complements

do attitude verbs occur with direct complements?
(T5    AttitudeEnt 263 268    ἔδοξε
 E1    AttitudeEnt:T5 report:T7
)

do δὴ and δή occur in complements? (mogen samen genomen worden)
do γὰρ and γάρ occur in a complement after root (mogen samengenomen worden, hoeft niet per se meteen achter root, maar ergens daarna)

# -----

We should count both .txt and .ann files.

The .txt files for the general statistics, number of sentences/words, etc.

The .ann files to count the complements etc.
'''

class Complement:
    # T13	Complement 96 153	ἐν μέρει τινὶ τῆς χώρας Κύκλωπες καὶ Λαιστρυγόνες οἰκῆσαι
    def __init__(self, id):
        self.id   = id
        self.chunked = False
        self.attverb = None
        self.type = "?"
        self.words = []
        self.head = None
        self.roots = 0
        self.span = [] # pairs of [start, end]
        # Contains δὴ and δή etc
        self.contains = Counter()
    def __repr__(self):
        return "|"+self.id+"|"
    def __str__(self):
        attv = ""
        if self.attverb:
            attv = "AV"
        contains_str = ""
        for c in self.contains:
            contains_str = contains_str + str(c)+":"+str(self.contains[c])+" "
        return "Complement:"+self.id+" head:"+repr(self.head)+" type:"+self.type+" words:"+str(len(self.words))+" "+contains_str+attv #+" span:"+repr(self.span)
    
filenames = [] # Should be the *.txt files, and we figure out the .ann names from these
filename  = None

try:
    opts, args = getopt.getopt(sys.argv[1:], "f:", [])
except getopt.GetoptError as err:
    print(str(err))
    sys.exit(1)
for o, a in opts:
    if o in ("-f"):
        filenames = sorted(glob.glob(a))
    else:
        assert False, "unhandled option"

stats = Counter()
stats["fc"] = 0 # file count
stats["wc"] = 0 # word count
stats["sc"] = 0 # sentence count
#
stats["compl"] = 0 # number of complements
stats["compl_i"] = 0 # indirect
stats["compl_d"] = 0 # direct
stats["compl_np"] = 0
stats["compl_wc"] = 0 # complements, word count
stats["compl_wc_i"] = 0 # indirect complements, word count
stats["compl_wc_d"] = 0 # indirect complements, word count
stats["compl_wc_np"] = 0 # NP complements, word count
stats["compl_rc"] = 0 # complements spanning a ROOT element
stats["compl_av"] = 0 # number of complements with attitude verb

long = {}
long["fc"] = "Aantal bestanden"
long["wc"] = "Aantal woorden"
long["sc"] = "Aantal zinnen"
#
long["compl"] = "Aantal 'Complement' annotaties"
long["compl_i"] = "Aantal indirecte 'Complement' annotaties"
long["compl_d"] = "Aantal directe 'Complement' annotaties"
long["compl_np"] = "Aantal NP 'Complement' annotaties"
long["compl_wc"] = "Aantal woorden in Complementen"
long["compl_wc_i"] = "Aantal woorden in indirecte Complementen"
long["compl_wc_d"] = "Aantal woorden in directe Complementen"
long["compl_wc_np"] = "Aantal woorden in NP Complementen"
long["compl_rc"] = "Aantal Complements met ROOT"
long["compl_av"] = "Aantal Complements met attitude verb"

# ----
# Process
# ----

if not filenames:
    print( "Nothing to do..." )
    sys.exit(0)
    
for filename in filenames:
    filebase, fileext = os.path.splitext(filename)
    if not fileext == ".txt":
        continue
    # We read the .txt file first, which should be the plain filename we supplied.
    print( "---- FILE:", filename, file=sys.stderr )
    with open(filename, 'r') as f:
        stats["fc"] += 1
        wc = 0
        sc = 0
        for l in f:
            l = l.strip()
            words = l.split()
            if not words:
                continue
            if words[0] == "ROOT":
                words = words[1:]
            # We normalise all Greek we read nowadays.
            words = [ normalize('NFC', w) for w in words ]
            wc += len(words)
            sc += 1
    print( "{0:<50} {1:>5n} ".format("Aantal zinnen", sc) )
    print( "{0:<50} {1:>5n} ".format("Aantal woorden", wc) )
    stats["wc"] += wc
    stats["sc"] += sc
    
    # ----
    # We read the .ann file next
    # ----
    filename = filebase + ".ann"
    if not os.path.isfile( filename ):
        print( "ERROR: annotation file not found.", file=sys.stderr )
        sys.exit(1)
    print( "---- FILE:", filename, file=sys.stderr )
    complements = {} # Complements by id
    compl_heads = {} # Temp storage for before Complement is known
    attitudes   = {} # Temp storage for before Complement is known
    with open(filename, 'r') as f:
        for l in f:
            l = l.strip()
            bits = l.split("\t")
            if len(bits) < 2:
                continue
            # T4      Complement 46 156       αὖθις μείζονι...
            ann_id   = bits[0]
            ann_info = bits[1].split()
            ann_type = ann_info[0]
            if len(bits) == 3:
                words = [ normalize('NFC', w) for w in bits[2].split() ]
            else:
                words = []
            # Als een complement uit 1 chunk bestaat hebben we alleen het complement geannoteerd,
            # niet de chunk, omdat we dan, was het idee, later die chunks in die gevallen
            # automatisch zouden toevoegen (span dus zelfde als complement)
            if ann_type == "Complement": #compl-head compl-chunk ? how does chunk relate to Compl?
                # Write out/count the current complement
                # Or save all of them, because the order is random in the .ann files?
                complements[ann_id] = Complement(ann_id)
                # spans could look like this:
                '''
                T13 Complement 96 153
                T17 Complement 156 158;163 173
                '''
                spans = " ".join(ann_info[1:]) # The string after "Complement"
                for span in spans.split(";"): # spans are seperated by a ";"
                    xy = span.split() # and consist of a start and end position
                    if len(xy) == 2:
                        complements[ann_id].span.append( [int(xy[0]),int(xy[1])] )
                    else:
                        print( "ERROR in spans" )
                        sys.exit(2)
                stats["compl"] += 1
                complements[ann_id].words = words # this includes "," etc
                complements[ann_id].roots = words.count("ROOT")
                stats["compl_wc"] += (len(words) - complements[ann_id].roots)
                # Count these
                complements[ann_id].contains["δὴ"] += words.count("δὴ")
                complements[ann_id].contains["δή"] += words.count("δή")
                # γὰρ and γάρ occur in a complement after root
                if complements[ann_id].roots > 0:
                    root_idx = [i for i,x in enumerate(words) if x == "ROOT"]
                    DBG( root_idx )
                    # this could give [3] or [3,5,8] or something
                    # we take the text after the first ROOT
                    root_pos = root_idx[0]
                    after = words[root_pos:]
                    DBG( root_pos, after )
                    # And count these
                    complements[ann_id].contains["γὰρ"] += words.count("γὰρ")
                    complements[ann_id].contains["γάρ"] += words.count("γάρ")

            # Not necessary:
            if False and ann_id[0] == "T" and ann_type == "Compl-chunk":
                print( l )
                # should look it up if it already exists somehow?
                complements[ann_id] = Complement(ann_id)
                # spans could look like this:
                '''
                T13 Complement 96 153
                T17 Complement 156 158;163 173
                '''
                spans = " ".join(ann_info[1:]) # The string after "Complement"
                for span in spans.split(";"): # spans are seperated by a ";"
                    xy = span.split() # and consist of a start and end position
                    if len(xy) == 2:
                        complements[ann_id].span.append( [int(xy[0]),int(xy[1])] )
                    else:
                        print( "ERROR" )
                        sys.exit(2)
                stats["compl"] += 1
                complements[ann_id].words = words # this includes "," etc
                complements[ann_id].roots = words.count("ROOT")
                stats["compl_wc"] += (len(words) - complements[ann_id].roots)
                # Count these
                complements[ann_id].contains["δὴ"] += words.count("δὴ")
                complements[ann_id].contains["δή"] += words.count("δή")
                # γὰρ and γάρ occur in a complement after root
                if complements[ann_id].roots > 0:
                    root_idx = [i for i,x in enumerate(words) if x == "ROOT"]
                    DBG( root_idx )
                    # this could give [3] or [3,5,8] or something
                    # we take the text after the first ROOT
                    root_pos = root_idx[0]
                    after = words[root_pos:]
                    DBG( root_pos, after )
                    # And count these
                    complements[ann_id].contains["γὰρ"] += words.count("γὰρ")
                    complements[ann_id].contains["γάρ"] += words.count("γάρ")

            # for example:
            # R2	compl-chunk Arg1:T17 Arg2:T14
            # The Arg2 points to a Complement (does it always?)
            if False ann_id[0] == "R" and ann_type == "compl-chunk":
                print( l )
                print( ann_info ) # ['compl-chunk', 'Arg1:T7', 'Arg2:T9']
                arg2 = ann_info[2].split(":")
                arg2_c = arg2[1]
                # What if complements[argc_2] doesn't exist? Is that possible?
                if arg2_c in complements:
                    print( arg2_c, complements[arg2_c] )
                else:
                    print( arg2_c )
                    sys.exit(3) # never happens in book6 and book7
                
            # We build up the Complements first, count when file is done
            if ann_type == "compl-type":
                # compl-type T6 indirect
                # print( bits )
                compl_id   = ann_info[1] #points to the Complement id
                compl_type = ann_info[2]
                try:
                    complements[compl_id].type = compl_type                    
                except KeyError:
                    DBG("CHUNK")
                    pass # chunks are not saved yet
                    
            # head info
            # T20	Compl-head 197 204	ἐσῆλθον
            # R5	compl-head Arg1:T20 Arg2:T18
            # Here we scan positions, using Arg1/Arg2 is maybe easier, but Compl-head
            # still needs to be scanned to get the head-word itself.
            if ann_id[0] == "T" and ann_type == "Compl-head": # uppercase Compl is enough?
                # scan the span, and see in which complement it occurs.
                span = ann_info[1:] # The numbers after "Compl-head"
                span0 = int(span[0])
                span1 = int(span[1])
                #print( ann_info, span0, span1 )
                # Find the Complement (try them all as we don't know the order in the .ann file)
                for c_id in complements:
                    c = complements[c_id]
                    for c_span in c.span:
                        if c_span[0] <= span0 <= c_span[1] and c_span[0] <= span1 <= c_span[1]:
                            complements[c_id].head = words[0] # assume head is one word
                            continue #continue with next line
                # If not found, we have compl-head before complement is known sometimes:
                # T6	Compl-head 287 292	εἶναι
                # T7	Complement 280 292	καιρὸς εἶναι
                # Keep them in a list, and check if we get a new complement, or assemble everything
                # at the end.
                compl_heads[ann_id] = [ span0, span1, words[0] ] # [ 287 292 εἶναι ]
                DBG( "HANGING HEAD" )

            #  E1    AttitudeEnt:T5 report:T7
            # These are saved and processed later
            if ann_id[0] == "E" and ann_type[0:11] == "AttitudeEnt":
                attitudes[ann_id] = ann_info # ['AttitudeEnt:T20', 'report:T21']
                #print( attitudes[ann_id] )
                
    # Complements for this file, and add to the global statistics, check if we have a
    # hanging head.
    # See if we can add the AttitudeEnts to the complements.
    for att in attitudes:
        attitude = attitudes[att]
        if len(attitude) > 1:
            att_id1 = attitude[0].split(":")[1]
            att_id2 = attitude[1].split(":")[1]
            try:
                complements[att_id2].attverb = att_id1
            except KeyError:
                print( "ERROR: AttitudeEnt points to non-existing complement." )
                sys.exit(4)
        else:
            print( "ERROR: AttitudeEnt as no ID." )
            #sys.exit(5)
    # Loop over the complements, add the hanging heads.
    for c in sorted(complements.keys()):
        the_complement = complements[c]
        if not the_complement.head:
            for ch in compl_heads:
                #print(ch, compl_heads[ch])
                span0 = compl_heads[ch][0]
                span1 = compl_heads[ch][1]
                word  = compl_heads[ch][2]
                for c_span in the_complement.span:
                    if c_span[0] <= span0 <= c_span[1] and c_span[0] <= span1 <= c_span[1]:
                        the_complement.head = word # assign it
        # Start counting th statistics.
        stats["compl_wc"] += len(the_complement.words)
        if the_complement.type == "indirect":
            stats["compl_i"] += 1
            stats["compl_wc_i"] += len(the_complement.words)
        elif the_complement.type == "direct":
            stats["compl_d"] += 1
            stats["compl_wc_d"] += len(the_complement.words)
        elif the_complement.type == "NP":
            stats["compl_np"] += 1
            stats["compl_wc_np"] += len(the_complement.words)
        if the_complement.roots > 0:
            stats["compl_rc"] += 1
        if the_complement.attverb:
            stats["compl_av"] += 1
        for contain in the_complement.contains:
            stats["contains_"+contain] += int(the_complement.contains[contain])
        print( the_complement )

print( "\nSTATISTICS" )
for stat, count in sorted(stats.items()):
    if stat.startswith("compl_wc"):
        average = float(count) / stats["compl"]
        try:
            print( "{0:<50} {1:>5n} {2:>6.2f}".format(long[stat], count, average) )
        except KeyError:
            print( "# {0:<48} {1:>5n} {2:>6.2f}".format(stat, count, average) )
    else:
        try:
            print( "{0:<50} {1:>5n} ".format(long[stat], count) )
        except KeyError:
            print( "# {0:<48} {1:>5n} ".format(stat, count) )
