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
        print( "DBG:", strs, file=sys.stderr ) # use *strs for nicer strings
        
'''
DESCRIPTION
-----------
Counts statistics on brat .txt and .ann files

USAGE
-----
specify the *txt files (wildcards are expanded):
 python3 bratstats.py -f "thuc.hist_gk.brat.book6*.txt"

For each .txt file, an .ann file is expected.

OUTPUT
------

Print info for each file to the screen, aggregated statistics
are printed at the end.

OPTIONS
-------
 -f: the file(s) to process
 -D: debug output
 -0: only print statistics which are > 0

EXAMPLE RUN AND OUTPUT
----------------------
python3 bratstats.py -f "thuc.hist_gk.brat.book6.chap008.txt" -0

---- FILE: thuc.hist_gk.brat.book6.chap008.txt
thuc.hist_gk.brat.book6.chap008.txt
Aantal zinnen                                          4
Aantal woorden                                       199
---- FILE: thuc.hist_gk.brat.book6.chap008.ann

STATISTICS
python bratstats.py -f thuc.hist_gk.brat.book6.chap008.txt -0
Aantal bestanden                                       1
Aantal zinnen                                          4
Aantal woorden                                       199
Aantal 'Complement' annotaties                         8
Aantal indirecte 'Complement' annotaties               5
Aantal NP 'Complement' annotaties                      2
Aantal preposedNP 'Complement' annotaties              1
Aantal woorden in Complementen (met overlap)          54   6.75
Aantal woorden in Complementen                        48   6.00
Aantal woorden in indirecte Complementen              37   4.62
Aantal woorden in NP Complementen                     13   1.62
Aantal woorden in preposedNP Complementen              4   0.50
Aantal Complements met speech entity                   1
Aantal Complements met attitude entity                 7
'''

class Complement:
    # T13	Complement 96 153	ἐν μέρει τινὶ τῆς χώρας Κύκλωπες καὶ Λαιστρυγόνες οἰκῆσαι
    def __init__(self, id):
        self.id   = id
        self.chunked = False
        self.type = "?"
        self.words = []
        self.head = None
        self.roots = 0
        self.spans = [] # pairs of [start, end]
        self.entities = [] # the speech/perception/attitude entities
        self.subchunk = False # if this is part of a larger chunk
        # Contains δὴ and δή etc
        self.contains = Counter()
    def __repr__(self):
        return "|"+self.id+"|"
    def __str__(self):
        subc = ""
        if self.subchunk:
            subc = "SC"
        contains_str = ""
        for c in self.contains:
            contains_str = contains_str + str(c)+":"+str(self.contains[c])+" "
        return "Complement:"+self.id+" head:"+repr(self.head)+" type:"+self.type+" words:"+str(len(self.words))+" "+contains_str+" "+subc+" "+"/".join(self.entities) #+" span:"+repr(self.span)


#Given two ranges [x1,x2], [y1,y2]
def overlap(x1,x2,y1,y2):
    return max(x1,y1) <= min(x2,y2)

# ----

filenames = [] # Should be the *.txt files, and we figure out the .ann names from these
filename  = None
nozeroes  = False # specify -0 to only print statistics which are > 0

try:
    opts, args = getopt.getopt(sys.argv[1:], "f:D0", [])
except getopt.GetoptError as err:
    print(str(err))
    sys.exit(1)
for o, a in opts:
    if o in ("-f"):
        filenames = sorted(glob.glob(a))
    elif o in ("-D"):
        debug = True
    elif o in ("-0"):
        nozeroes = True
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
stats["compl_pnp"] = 0
stats["compl_wc"] = 0 # complements, word count
stats["compl_wc_i"] = 0 # indirect complements, word count
stats["compl_wc_d"] = 0 # indirect complements, word count
stats["compl_wc_np"] = 0 # NP complements, word count
stats["compl_wc_pnp"] = 0 # preposedNP complements, word count
stats["compl_owc"] = 0 # complements, overlap word count

stats["compl_rc"] = 0 # complements spanning a ROOT element
stats["compl_ae"] = 0 # number of complements with a attitude entity
stats["compl_se"] = 0 # number of complements with a speech entity
stats["compl_pe"] = 0 # number of complements with a perception entity

stats["count_ae"] = 0 # number of attitude entity annotations
stats["count_se"] = 0 # number of speech entity annotations
stats["count_pe"] = 0 # number of perception entity annotations

long = {}
long["fc"] = "Aantal bestanden"
long["wc"] = "Aantal woorden"
long["sc"] = "Aantal zinnen"
#
long["compl"] = "Aantal 'Complement' annotaties"
long["compl_i"] = "Aantal indirecte 'Complement' annotaties"
long["compl_d"] = "Aantal directe 'Complement' annotaties"
long["compl_np"] = "Aantal NP 'Complement' annotaties"
long["compl_pnp"] = "Aantal preposedNP 'Complement' annotaties"
long["compl_wc"] = "Aantal woorden in Complementen"
long["compl_wc_i"] = "Aantal woorden in indirecte Complementen"
long["compl_wc_d"] = "Aantal woorden in directe Complementen"
long["compl_wc_np"] = "Aantal woorden in NP Complementen"
long["compl_wc_pnp"] = "Aantal woorden in preposedNP Complementen"
long["compl_owc"] = "Aantal woorden in Complementen (met overlap)"

long["compl_rc"] = "Aantal Complements met ROOT"
long["compl_ae"] = "Aantal Complements met attitude entity"
long["compl_se"] = "Aantal Complements met speech entity"
long["compl_pe"] = "Aantal Complements met perception entity"

long["count_ae"] = "Aantal attitude entities"
long["count_se"] = "Aantal speech entities"
long["count_pe"] = "Aantal perception entities"

long["contains_δὴ"] = "Aantal δὴ in complementen"
long["contains_δή"] = "Aantal δή in complementen"
long["contains_γάρ"] = "Aantal γάρ na ROOT in complementen"
long["contains_γὰρ"] = "Aantal γὰρ na ROOT in complementen"
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
            words = [w for w in words if w != 'ROOT']
            # We normalise all Greek we read nowadays, but here we only count.
            # words = [ normalize('NFC', w) for w in words ]
            wc += len(words)
            sc += 1
    # Info per file (do we want this?)
    print( filename )
    print( "{0:<50} {1:>5n} ".format("Aantal zinnen", sc) )
    print( "{0:<50} {1:>5n} ".format("Aantal woorden", wc) )
    stats["wc"] += wc
    stats["sc"] += sc
    
    # ----
    # Now we read the .ann file next
    # ----
    filename = filebase + ".ann"
    if not os.path.isfile( filename ):
        print( "ERROR: annotation file not found.", file=sys.stderr )
        sys.exit(1)
    print( "---- FILE:", filename, file=sys.stderr )
    complements = {} # Complements by id
    compl_heads = {} # Temp storage for before Complement is known
    compl_types = {} # Temp storage for before Complement is known
    attitudes   = {} # Temp storage for before Complement is known
    perceptions = {} # Temp storage for before Complement is known
    speechents  = {} # Temp storage for before Complement is known
    with open(filename, 'r') as f:
        for l in f:
            l = l.strip()
            bits = l.split("\t")
            if len(bits) < 2:
                DBG("SKIP", l)
                continue
            # T4      Complement 46 156       αὖθις μείζονι...
            ann_id   = bits[0]
            ann_info = bits[1].split()
            ann_type = ann_info[0]
            if len(bits) == 3:
                words = [ normalize('NFC', w) for w in bits[2].split() ]
            else:
                words = []
            DBG("WORDS", l, words)
            # Als een complement uit 1 chunk bestaat hebben we alleen het complement geannoteerd,
            # niet de chunk, omdat we dan, was het idee, later die chunks in die gevallen
            # automatisch zouden toevoegen (span dus zelfde als complement)
            if ann_type == "Complement": #compl-head compl-chunk ? how does chunk relate to Compl?
                # Write out/count the current complement
                # Or save all of them, because the order is random in the .ann files?
                complements[ann_id] = Complement(ann_id)
                DBG("COMPLEMENT ID", ann_id)
                # spans could look like this:
                '''
                T13 Complement 96 153
                T17 Complement 156 158;163 173
                '''
                spans = " ".join(ann_info[1:]) # The string after "Complement"
                DBG("SPANS", spans)
                for span in spans.split(";"): # spans are seperated by a ";"
                    xy = span.split() # and consist of a start and end position
                    if len(xy) == 2:
                        complements[ann_id].spans.append( [int(xy[0]),int(xy[1])] )
                        DBG("SPAN", [int(xy[0]),int(xy[1])])
                    else:
                        print( "ERROR in spans" )
                        sys.exit(2)
                stats["compl"] += 1
                complements[ann_id].words = words # this includes "," etc
                complements[ann_id].roots = words.count("ROOT")
                '''
                # words are counted later because we need to find the overlaps first
                stats["compl_wc"] += (len(words) - complements[ann_id].roots)
                '''
                # Count these, in all the words
                complements[ann_id].contains["δὴ"] += words.count("δὴ")
                complements[ann_id].contains["δή"] += words.count("δή")
                
                # γὰρ and γάρ occur in a complement after root
                if words.count("ROOT") > 0:
                    DBG("ROOTS > 0", ann_id)
                    root_idx = [i for i,x in enumerate(words) if x == "ROOT"]
                    DBG( "ROOT", root_idx )
                    # this could give [3] or [3,5,8] or something
                    # we take the text after the first ROOT
                    root_pos = root_idx[0]
                    after = words[root_pos:]
                    DBG( root_pos, after )
                    # And count these
                    complements[ann_id].contains["γὰρ"] += words.count("γὰρ")
                    complements[ann_id].contains["γάρ"] += words.count("γάρ")
                
            # We try to fill in the type. If the Complement is not known yet, we
            # save the type for later.
            if ann_type == "compl-type":
                # compl-type T6 indirect
                compl_id   = ann_info[1] # points to the Complement id (could be unused chunk)
                compl_type = ann_info[2]
                DBG("TYPE", compl_id, compl_type)
                try:
                    complements[compl_id].type = compl_type
                    DBG("TYPE ADDED TO", compl_id)
                except KeyError:
                    DBG("COMPLEMENT ID FOR TYPE NOT FOUND", compl_id)
                    compl_types[ann_id] = [ compl_type ] #save for later

            # head info, look slike:
            #  T20	Compl-head 197 204	ἐσῆλθον
            #  R5	compl-head Arg1:T20 Arg2:T18
            # Here we scan positions, using Arg1/Arg2 is maybe easier, but Compl-head
            # still needs to be processed to get the head-word itself.
            if ann_id[0] == "T" and ann_type == "Compl-head": # uppercase Compl is enough?
                # Scan the span, and see in which complement it occurs.
                span = ann_info[1:] # The numbers after "Compl-head"
                span0 = int(span[0])
                span1 = int(span[1])
                DBG( "HEAD", ann_info, span0, span1 )
                # Find the Complement (try them all as we don't know the order in the .ann file)
                for c_id in complements:
                    c = complements[c_id]
                    for c_span in c.spans:
                        if c_span[0] <= span0 <= c_span[1] and c_span[0] <= span1 <= c_span[1]:
                            complements[c_id].head = words[0] # assume head is one word
                            continue #continue with next line
                # If not found, we have compl-head before complement is known sometimes:
                # T6	Compl-head 287 292	εἶναι
                # T7	Complement 280 292	καιρὸς εἶναι
                # Keep them in a list, and check if we get a new complement, or assemble everything
                # at the end.
                compl_heads[ann_id] = [ span0, span1, words[0] ] # [ 287 292 εἶναι ]
                DBG( "HANGING HEAD", ann_id )

            #  E1    AttitudeEnt:T5 report:T7
            # These are saved and processed later
            # Note that they can be attached to more than one complement, so the
            # counts of entities in complements can be higher than the absolute
            # counts (e.g in thuc.hist_gk.brat.book6.chap006.ann).
            if ann_id[0] == "E" and ann_type[0:11] == "AttitudeEnt":
                attitudes[ann_id] = ann_info # ['AttitudeEnt:T20', 'report:T21']
                stats["count_ae"] += 1 # global count we do here
                DBG("ATTITUDE ENTITY", ann_id, ann_info )

            #  T7      PerceptionEnt 612 619   ὁρῶντες
            #  E2      PerceptionEnt:T7 report:T8
            # These are saved and processed later
            if ann_id[0] == "E" and ann_type[0:13] == "PerceptionEnt":
                perceptions[ann_id] = ann_info # ['PerceptionEnt:T20', 'report:T21']
                stats["count_pe"] += 1 # global count we do here
                DBG("PERCEPTION ENTITY", ann_id, ann_info )

            # T15     SpeechEnt 461 464       ἔφη
            # E3      SpeechEnt:T15 report:T16    
            # These are saved and processed later
            if ann_id[0] == "E" and ann_type[0:9] == "SpeechEnt":
                speechents[ann_id] = ann_info # ['SpeechEnt:T20', 'report:T21']
                stats["count_se"] += 1 # global count we do here
                DBG("SPEECH ENTITY", ann_id, ann_info )

    # Complements for this file, and add to the global statistics, check if we have a
    # hanging head.

    # See if we can add the AttitudeEnts to the complements.
    for att in attitudes:
        attitude = attitudes[att]
        # Can alse be:
        # E2	AttitudeEnt:T11 report:T8 report2:T9 report3:T10
        if len(attitude) > 1:
            att_id1 = attitude[0].split(":")[1] # T11
            for r in attitude[1:]:
                att_id2 = r.split(":")[1]
                DBG("CHECKING ATTITUDE", att_id1, att_id2)
                try:
                    complements[att_id2].entities.append("A") # or with ent_id1
                    DBG("ADDING ATTITUDE TO COMPLEMENT", att_id2 )
                except KeyError:
                    print( "ERROR: AttitudeEnt points to non-existing complement." )
                    #sys.exit(4)
        else:
            print( "ERROR: AttitudeEnt has no ID." )
            #sys.exit(5)

    # See if we can add the perception to the complements.
    for ent in perceptions:
        entity = perceptions[ent]
        # Can alse be:
        # E2	AttitudeEnt:T11 report:T8 report2:T9 report3:T10
        if len(entity) > 1:
            ent_id1 = entity[0].split(":")[1] # T11
            for r in entity[1:]:
                ent_id2 = r.split(":")[1]
                DBG("CHECKING PERCEPTION", ent_id1, ent_id2)
                try:
                    complements[ent_id2].entities.append("P") # or with ent_id1
                    DBG("ADDING PERCEPTION TO COMPLEMENT", ent_id2 )
                except KeyError:
                    print( "ERROR: Entity points to non-existing complement." )
                    #sys.exit(4)
        else:
            print( "ERROR: Entity has no ID." )
            #sys.exit(5)

    # See if we can add the speech entities to the complements.
    for ent in speechents:
        entity = speechents[ent]
        # Can alse be:
        # E2	AttitudeEnt:T11 report:T8 report2:T9 report3:T10
        if len(entity) > 1:
            ent_id1 = entity[0].split(":")[1] # T11
            for r in entity[1:]:
                ent_id2 = r.split(":")[1]
                DBG("CHECKING SPEECHENT", ent_id1, ent_id2)
                try:
                    complements[ent_id2].entities.append("S") # or with ent_id1
                    DBG("ADDING SPEECHENT TO COMPLEMENT", ent_id2 )
                except KeyError:
                    print( "ERROR: Entity points to non-existing complement." )
                    #sys.exit(4)
        else:
            print( "ERROR: Entity has no ID." )
            #sys.exit(5)

    # Loop over the complements, add the hanging heads and types, count overlap
    # overlap
    overlaps = [] # Keep track of what we have done
    for c in sorted(complements.keys()):
        the_complement = complements[c]
        curr_spans = the_complement.spans
        curr_id = c
        for c_span in curr_spans:
            # check in all other except myself
            for c1 in sorted(complements.keys()):
                the_complement1 = complements[c1]
                if c1 == curr_id:
                    continue
                this_set = set({curr_id, c1})
                if this_set in overlaps:
                    continue
                overlaps.append(this_set)
                curr_spans1 = the_complement1.spans
                for c_span1 in curr_spans1:
                    if overlap(*c_span, *c_span1):
                        DBG("OVERLAP", curr_id, c1)
                        if len(the_complement.words) < len(the_complement1.words):
                            the_complement.subchunk = True
                        else:
                            the_complement1.subchunk = True
                        #delta = min(len(the_complement.words), len(the_complement1.words))
                        #print( "!", curr_id, c1, c_span, c_span1 )
                        #print( len(the_complement.words), len(the_complement1.words), delta )
    #types
    for ct in compl_types.keys():
        if ct in complements:
            if not complements[ct].type:
                complements[ct].type = compl_types[ct][0]
                DBG("ADDING SAVED TYPE", ct)
    # compl_heads + word counts
    for c in sorted(complements.keys()):
        the_complement = complements[c]
        if not the_complement.head:
            for ch in compl_heads:
                #print(ch, compl_heads[ch])
                span0 = compl_heads[ch][0]
                span1 = compl_heads[ch][1]
                word  = compl_heads[ch][2]
                for c_span in the_complement.spans:
                    if c_span[0] <= span0 <= c_span[1] and c_span[0] <= span1 <= c_span[1]:
                        the_complement.head = word # assign it
        # Start counting the statistics.
        compl_words = [w for w in the_complement.words if w != 'ROOT']
        stats["compl_owc"] += len(compl_words) #with overlap
        if not the_complement.subchunk:
            stats["compl_wc"] += len(compl_words) #no overlap
        if the_complement.type == "indirect":
            stats["compl_i"] += 1
            stats["compl_wc_i"] += len(compl_words)
        elif the_complement.type == "direct":
            stats["compl_d"] += 1
            stats["compl_wc_d"] += len(compl_words)
        elif the_complement.type == "NP":
            stats["compl_np"] += 1
            stats["compl_wc_np"] += len(compl_words)
        elif the_complement.type == "preposedNP":
            stats["compl_pnp"] += 1
            stats["compl_wc_pnp"] += len(compl_words)
        if the_complement.roots > 0:
            stats["compl_rc"] += 1
        #if the_complement.attverb:
        #    stats["compl_av"] += 1
        if "A" in the_complement.entities:
            stats["compl_ae"] += 1
        if "S" in the_complement.entities:
            stats["compl_se"] += 1
        if "P" in the_complement.entities:
            stats["compl_pe"] += 1
        for contain in the_complement.contains:
            stats["contains_"+contain] += int(the_complement.contains[contain])            
        DBG( str(the_complement) )

print( "\nSTATISTICS" )
print("python", " ".join(sys.argv))
for stat in [ 'fc', 'sc', 'wc', "LF",
                  'compl', 'compl_d', 'compl_i', 'compl_np', 'compl_pnp', 'compl_rc', "LF", 
                  'compl_owc', 'compl_wc',
                  'compl_wc_d', 'compl_wc_i', 'compl_wc_np', 'compl_wc_pnp', "LF",
                  'count_se', 'count_pe', 'count_ae', "LF",
                  'compl_se', 'compl_pe', 'compl_ae', "LF",
                  'contains_δὴ', 'contains_δή', 'contains_γάρ', 'contains_γὰρ' ]:
    if stat == "LF":
        print( "#" )
        continue
    count = stats[stat]
    if count == 0 and nozeroes:
        continue
#for stat, count in sorted(stats.items()):
    if stat.startswith("compl_wc") or stat.startswith("compl_owc"):
        try:
            if stat == "compl_wc":
                average = float(count) / stats["compl"]
            elif stat == "compl_wc_d":
                    average = float(count) / stats["compl_d"]
            elif stat == "compl_wc_i":
                    average = float(count) / stats["compl_i"]
            elif stat == "compl_wc_np":
                    average = float(count) / stats["compl_np"]
            elif stat == "compl_wc_pnp":
                    average = float(count) / stats["compl_pnp"]
            else:
                average = float(count) / stats["compl"]
        except ZeroDivisionError:
            # stats[...] is 0
            average = 0
        try:
            print( "{0:<50} {1:>5n} {2:>6.2f}".format(long[stat], count, average) )
        except KeyError:
            print( "# {0:<48} {1:>5n} {2:>6.2f}".format(stat, count, average) )
    else:
        try:
            print( "{0:<50} {1:>5n} ".format(long[stat], count) )
        except KeyError:
            print( "# {0:<48} {1:>5n} ".format(stat, count) )
'''
# Show left overs.
for stat in [ 'fc', 'sc', 'wc',
                  'compl', 'compl_d', 'compl_i', 'compl_np', 'compl_pnp',
                  'compl_owc', 'compl_wc',
                  'compl_wc_d', 'compl_wc_i', 'compl_wc_np', 'compl_wc_pnp',
                  'compl_se', 'compl_pe', 
                  'compl_ae',
                  'compl_rc',
                  'contains_δὴ', 'contains_δή', 'contains_γάρ', 'contains_γὰρ']:
    del stats[stat]
print( stats.keys() )
'''
