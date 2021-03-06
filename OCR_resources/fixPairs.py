#!/usr/bin/env python
#
# fixPairs.py: Try to fix common OCR errors.
# 2015-08-25: Written by Steven J. DeRose.
#
from __future__ import print_function
import sys, os, argparse
import re
import codecs
from collections import defaultdict

from sjdUtils import sjdUtils
from alogging import ALogger
from MarkupHelpFormatter import MarkupHelpFormatter

__metadata__ = {
    "title"        : "fixPairs.py",
    "description"  : "Try to fix common OCR errors.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2015-08-25",
    "modified"     : "2021-03-03",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]

#global args, su, typesByPair, tokensByPair, pairExamples, totalFreq
typesByPair = defaultdict(int)
tokensByPair = defaultdict(int)
pairExamples = defaultdict(list)
totalFreq = 0

splitExpr = re.compile(r'\t')


descr = """
=Description=

Utility to help figure out what character-mappings to use for OCR correction.
Obvious cases include 0->O, c->e, rn->m, and f->s (for texts prior to ~1800).

But the more mappings, the more collisions may occur (where
a single erroneous (well, unknown) form, maps to more than one correct (known)
form.

This scans a file of found->fixed corrections, and see what the diffs.


=Known bugs and Limitations=

Should add a feature to scan a corpus, and see how many rule-collisions
come up with various maps (e.g., whether a rare case like 6->c introduces
a lot of cases where a given error could map to >1 real (fixed) word.

Hook up to C<SimplifyUnicode> to ascii-ize, strip accents, etc.
Cf. https://pypi.python.org/pypi/Unidecode.

    from unidecode import unidecode
    asc = unidecode(u)


=History=

  2015-08-25: Written by Steven J. DeRose.


=Rights=

Copyright %DATE% by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
For further information on this license, see
[https://creativecommons.org/licenses/by-sa/3.0].

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""


"""Table of corrections generated by this program
   running on BestLcOCRRules.txt (a dictionary, not a text).
   We only use pairs representing at least args.minvocab forms.
   'Types' here represents how many types (of ~50,000 in the file)
   represent a single-character change, from char 1 to char 2.
"""
pairMap = [
    #Found  Fixed     Types
    (u'f',   u's',    17104),
    (u'c',   u'e',    14945),
    (u'1',   u'i',     3116),
    (u'v',   u'y',     2791),
    (u'l',   u't',     1823),
    (u'b',   u'h',     1166),
    (u'1',   u'l',      943),
    (u'6',   u'e',      838),
    (u'l',   u's',      823),
    (u'f',   u'c',      646),
    (u'l',   u'i',      546),
    (u'0',   u'o',      442),
    (u'd',   u'c',      328),
    (u'6',   u'o',      290),
    (u'e',   u'c',      158),
    (u'c',   u'o',      147),
    (u'j',   u's',      141),
    (u'i',   u'l',      115),
    (u'j',   u'y',       67),
    (u'i',   u's',       46),
    (u'y',   u'v',       46),
    (u'3',   u's',       41),
    (u'8',   u's',       27),
    (u'5',   u's',       24),
    (u'f',   u'e',       22),
    (u'd',   u'e',       15),
    (u'o',   u'c',       10),
    (u'4',   u'e',        9),
    (u'7',   u'y',        7),
    (u'3',   u'e',        7),
    (u'c',   u'f',        7),
    (u'3',   u'd',        6),
    (u'9',   u'g',        6),
    (u'9',   u'a',        4),
    (u'2',   u'z',        3),
    (u'4',   u't',        3),
    (u'3',   u'o',        2),
    (u't',   u'l',        2),
    (u'i',   u't',        2),
    (u'y',   u'j',        1),
    (u'8',   u'g',        1),
    (u'6',   u'c',        1),
]


###############################################################################
#
def processOptions():
    "Parse command-line options and arguments."
    global args, su
    x = sys.argv[0]
    parser = argparse.ArgumentParser(
        description=descr, formatter_class=MarkupHelpFormatter)

    parser.add_argument(
        "--iencoding",        type=str, metavar='E', default="utf-8",
        help='Assume this character set for input files. Default: utf-8.')
    parser.add_argument(
        "--ignoreCase", "-i", action='store_true',
        help='Disregard case distinctions.')
    parser.add_argument(
        "--minvocab",         type=int, default=25,
        help='Trim list or single-char mappings to use, to ones that ' +
        'represent at least this many vocab items.')
    parser.add_argument(
        "--quiet", "-q",      action='store_true',
        help='Suppress most messages.')
    parser.add_argument(
        "--verbose", "-v",    action='count',       default=0,
        help='Add more messages (repeatable).')
    parser.add_argument(
        "--version",          action='version', version=__metadata__['__version__'],
        help='Display version information, then exit.')

    parser.add_argument(
        'files',             type=str,
        nargs=argparse.REMAINDER,
        help='Path(s) to input file(s)')

    args0 = parser.parse_args()
    su = sjdUtils()
    su.setVerbose(args0.verbose)

    if (len(args0.files)==0):
        args0.files.append("BestLcOCRRules.txt")

    return(args0)


###############################################################################
#
def doOneFile(path):
    global totalFreq
    recnum = 0
    rec = ""
    try:
        fh = codecs.open(path, mode='r', encoding=args.iencoding)
    except IOError as e:
        lg.error("Can't open '%s'." % (path), stat="CantOpen")
        return(0)
    while (True):
        try:
            rec = fh.readline()
        except Exception as e:
            lg.error("Error (%s) reading record %d of '%s'." %
                (type(e), recnum, path), stat="readError")
            break
        if (len(rec) == 0): break # EOF
        recnum += 1
        rec = rec.rstrip()
        tokens = re.split(splitExpr, rec)
        if (len(tokens)!=3):
            print("%d: Wrong number of fields (%d) in '%s'" %
                (recnum, len(tokens), rec))
            continue
        found, fixed, freq = tokens
        freq = int(freq)
        totalFreq += freq
        if (len(found) != len(fixed)):
            lg.vMsg(1, "%s\tLength mismatch" % (rec), stat='typesLengthDifference')
            su.bumpStat('tokensLengthDifference', amount=freq)
            continue

        d = 0
        while(found[d]==fixed[d]): d += 1
        w = found[d]
        c = fixed[d]

        # Now try to fix
        if (d==len(found)-1):
            typesByPair[(w,c)] += 1
            tokensByPair[(w,c)] += freq
            pairExamples[(w,c)].append(found)
        elif (found[d+1:]==fixed[d+1:]):
            typesByPair[(w,c)] += 1
            tokensByPair[(w,c)] += freq
            pairExamples[(w,c)].append(found)
        elif (re.sub(r'f', 's', found)==fixed):
            su.bumpStat('multiFS')
        elif (tryList(found, fixed)):
            su.bumpStat('byList')
        else:
            su.bumpStat('other')
    fh.close()
    report(recnum)
    return(recnum)


def tryList(found, fixed):
    """Try the corrections in the list, vs. a dictionary, and collect all
    the returns.
    """
    for i, pair in pairMap.enumerate():
        fr, to, freq = pair
        if (re.sub(fr,to,found) == fixed):
            return(true)
    return(False)


def report(recnum):
    sigma = u'\u03A3'
    print("Forms in list, that need one-character replacement:")
    print("      Err   Fix    Tokens     Tokens%       " + sigma +
        "tok%    Types      Types%       " + sigma + "typ%")
    fmt = "    %s %8d %10.4f%% %10.4f%% %8d %10.4f%% %10.4f%%"

    stokPct = 0.0
    stypPct = 0.0
    skey = sorted(tokensByPair.items(), key=lambda x: -x[1])
    for k in skey:
        pair, freq = k
        tokFreq = tokensByPair[pair]
        tokPct = tokFreq*100.0/totalFreq
        stokPct += tokPct
        typFreq = typesByPair[pair]
        typPct = typFreq*100.0/recnum
        stypPct += typPct
        msg = fmt % (pair, tokFreq, tokPct, stokPct, typFreq, typPct, stypPct)
        lim = min(5, len(pairExamples[k]))
        if (args.verbose): msg += `pairExamples[k][0:lim]`
        print(msg)


###############################################################################
# Main
#
args = processOptions()

if (len(args.files) == 0):
    lg.error("No files specified....")
    sys.exit()

for f in (args.files):
    su.bumpStat("totalFiles")
    recs = doOneFile(f)
    su.bumpStat("totalRecords", amount=recs)

if (not args.quiet):
    su.showStats()
