#!/usr/bin/env python3
#
import re
import getopt, sys, os
import csv

'''
Workflow:
python3 convert_perseus_csv.py > hib_parses_uc.csv.wlp
python3 rewrite_perseus.py -f hib_parses_uc.csv.wlp > hib_parses_uc.csv.wlp.rwrt
cp hib_parses_uc.csv.wlp.rwrt ~/SurfdriveRadboud/Shared/PerspectiveProject/GreekPerspectives/Software/Lemmatizer/Scripts/perseus-wlt.txt

from /Users/pberck/Downloads/hib_parses_uc.csv
"ἅμα","ama","d--------","ἅμα^","ἅμα^"
"ἅμα","ama","d--------","ἁμαί","ἁμαί"
"ἅμα","ama","d--------","ἅμ’","ἅμ’"
"ἅμα","ama","d--------","χἄμα","χἄμα"

lemma_text, bare_headword, morph_code, form, expanded_form

Output:
form lemma morph_code
'''

afile = "/Users/pberck/Downloads/hib_parses_uc.csv"

try:
    opts, args = getopt.getopt(sys.argv[1:], "f:", [])
except getopt.GetoptError as err:
    print(str(err))
    sys.exit(1)
for o, a in opts:
    if o in ("-f"):
        afile = a
    else:
        assert False, "unhandled option"

with open(afile, newline='') as csvfile:
    csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
    for row in csvreader:
        print( row[3], row[0], row[2] )
