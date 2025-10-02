#!/usr/bin/env python3
#
# sort.py: Do a really, really plain sort.
# 2018-07-18: Written by Steven J. DeRose.
#
import sys
import argparse
import re
import codecs
from enum import Enum
from typing import List

import logging
lg = logging.getLogger()

__metadata__ = {
    "title"        : "sort",
    "description"  : "Do a really, really plain sort.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2018-07-18",
    "modified"     : "2024-08-18",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]

descr = """
=Description=

[unfinished]

*nix C<sort> tries to adjust for locate, this just does
something straughtforward, without locale. But allows more sophisticated key
specs, with normalization, etc.

But it has a few added features, too, such as sorting by
one or more regex captures (h/t BBEdit).


=Related Commands=

`msort`

`PYTHONLIBS/FieldChoices.py`


=Known bugs and Limitations=

Can't specify *parts* of fields or multiple fields.

Limited to memory size.


=History=

  2018-07-18: Written by Steven J. DeRose.
  2021-03-03: New layout.
  2024-08-18: Add way to sort by extracted regex matches. Support multiple keys.


=Rights=

Copyright 2018-07-18 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
For further information on this license, see
[https://creativecommons.org/licenses/by-sa/3.0].

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""


###############################################################################
#
class fieldParsingMethod(Enum):
    COLS    = 1
    CSV     = 2
    REGEX   = 4
    XATTRS  = 4

class fieldTreatment:
    STR     = 1
    NORMSTR = 2
    INT     = 3
    FLOAT   = 4


class KeyDef:
    def __init__(self, fieldNum0, fieldNum1=None, reverse:bool=False,
        parse:fieldParsingMethod=fieldParsingMethod.CSV, delim:str=",",
        unorm=None, caseNorm=None, spaceNorm=None, castTo:type=None
    ):
        # TODO: Adopt casenorm/spacenorm/unorm from Dominus.BaseDOM
        # Values to treat as non-associating, and where to sort
        # Support callback?
        self.fieldNum0 = fieldNum0
        self.fieldNum1 = fieldNum1
        self.reverse = reverse
        self.parse = parse
        self.delim = delim
        self.unorm = unorm
        self.caseNorm = caseNorm
        self.spaceNorm = spaceNorm
        self.castTo = castTo

    def getKeyNumeric(self, rec):
        fields = re.split(args.delim, rec)
        try:
            return float(fields[args.field])
        except IndexError:
            return 0.0

    def getKeyString(self, rec):
        fields = re.split(args.delim, rec)
        try:
            return "_" + fields[args.field]
        except IndexError:
            return '_'

    def getKeyLower(self, rec):
        fields = re.split(args.delim, rec)
        try:
            return "_" + fields[args.field].tolower()
        except IndexError:
            return '_'


###############################################################################
#
def parseKeySpec(argObj) -> List[KeyDef]:
    return KeyDef(1)


###############################################################################
#
def doOneFile(path, fhp, keys:List[KeyDef]):
    """Read and deal with one individual file.
    """
    recs = fhp.readlines()
    lg.info("File read, %d records: %s", len(recs), path)

    recs.sort(key=keys.keyMaker)
    for r in recs:
        print(r, end=None)
    return


###############################################################################
#
def processOptions():
    try:
        from BlockFormatter import BlockFormatter
        parser = argparse.ArgumentParser(
            description=descr, formatter_class=BlockFormatter)
    except ImportError:
        parser = argparse.ArgumentParser(description=descr)

    parser.add_argument(
        "--delim", "-d", "-t", "--fieldSep", type=str, default="\t",
        help='Use this (regex) as the field delimiter.')
    parser.add_argument(
        "--field", "-f", "-k", type=int, default=None,
        help='Use this (regex) as the field delimiter.')
    parser.add_argument(
        "--iencoding", "--input-encoding", type=str, metavar="E", default="utf-8",
        help='Assume this character set for input files. Default: utf-8.')
    parser.add_argument(
        "--caseNorm", type=str, choices=[ "NONE", "UPPER", "CASEFOLD" ],
        help='Whether/how to normalize case distinctions.')
    parser.add_argument(
        "--quiet", "-q", action="store_true",
        help='Suppress most messages.')
    parser.add_argument(
        "--spaceNorm", type=str,
        choices=[ "NONE", "XML", "LEFT", "RIGHT", "STRIP", "RUNS", "DROP" ],
        help='Whether/how to normalize whitespace.')
    parser.add_argument(
        "--reverse", "-r", action="store_true", default=False,
        help='Sort in descending order.')
    parser.add_argument(
        "--unicode", action="store_const", dest='iencoding',
        const='utf8', help='Assume utf-8 for input files.')
    parser.add_argument(
        "--uNorm", type=str, choices=[ "NONE", "NFKC", "NFKD", "NFC", "NFD" ],
        help='Whether/how to normalize Unicode.')
    parser.add_argument(
        "--verbose", "-v", action="count", default=0,
        help='Add more messages (repeatable).')
    parser.add_argument(
        "--version", action="version", version=__version__,
        help='Display version information, then exit.')

    parser.add_argument(
        "files", type=str, nargs=argparse.REMAINDER,
        help='Path(s) to input file(s)')

    args0 = parser.parse_args()
    if (lg and args0.verbose):
        logging.basicConfig(level=logging.INFO - args0.verbose,
            format="%(message)s")
    return(args0)


###############################################################################
# Main
#
args = processOptions()

keyList = parseKeySpec(args)

if (len(args.files) == 0):
    lg.error("No files specified....")
    doOneFile("[STDIN]", sys.stdin.readlines, keyList)
else:
    for fArg in (args.files):
        fh = codecs.open(fArg, 'rb', encoding=args.iencoding)
        doOneFile(fArg, fh, keyList)
        fh.close()
