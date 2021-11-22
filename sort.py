#!/usr/bin/env python
#
# sort.py: Do a really, really plain sort.
# 2018-07-18: Written by Steven J. DeRose.
#
from __future__ import print_function
import sys
import argparse
import re
import codecs

from alogging import ALogger
lg = ALogger(1)

__metadata__ = {
    "title"        : "sort.py",
    "description"  : "Do a really, really plain sort.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2018-07-18",
    "modified"     : "2021-03-03",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]


descr = """
=Description=

*nix C<sort> is a little weird, so do something straughtforward, without locale.


=Related Commands=

`msort`


=Known bugs and Limitations=

Can't specify *parts* of fields or multiple fields.

Limited to memory size.


=History=

  2018-07-18: Written by Steven J. DeRose.
  2021-03-03: New layout.


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
        "--iencoding", type=str, metavar='E', default="utf-8",
        help='Assume this character set for input files. Default: utf-8.')
    parser.add_argument(
        "--ignoreCase", "-i", action='store_true',
        help='Disregard case distinctions.')
    parser.add_argument(
        "--numeric", "-n", "-g", action='store_true',
        help='Do numeric comparison (incl. floats), instead of string.')
    parser.add_argument(
        "--quiet", "-q", action='store_true',
        help='Suppress most messages.')
    parser.add_argument(
        "--reverse", "-r", action='store_true', default=False,
        help='Sort in descending order.')
    parser.add_argument(
        "--unicode", action='store_const', dest='iencoding',
        const='utf8', help='Assume utf-8 for input files.')
    parser.add_argument(
        "--verbose", "-v", action='count', default=0,
        help='Add more messages (repeatable).')
    parser.add_argument(
        "--version", action='version', version=__version__,
        help='Display version information, then exit.')

    parser.add_argument(
        "files", type=str, nargs=argparse.REMAINDER,
        help='Path(s) to input file(s)')

    args0 = parser.parse_args()
    if (args0.verbose): lg.setVerbose(args0.verbose)
    return(args0)


###############################################################################
#
def doOneFile(path, fhp):
    """Read and deal with one individual file.
    """
    recs = fhp.readlines()
    lg.vMsg(1, "File read: %s" % (path))
    if (args.numeric):
        recs.sort(key=getKeyNumeric, reverse=args.reverse)
    elif (args.ignoreCase):
        recs.sort(key=getKeyLower, reverse=args.reverse)
    else:
        recs.sort(key=getKeyString, reverse=args.reverse)

    for r in recs:
        print(r, end=None)
    return

def getKeyNumeric(rec):
    fields = re.split(args.delim, rec)
    try:
        return float(fields[args.field])
    except IndexError:
        return 0.0

def getKeyString(rec):
    fields = re.split(args.delim, rec)
    try:
        return "_" + fields[args.field]
    except IndexError:
        return '_'

def getKeyLower(rec):
    fields = re.split(args.delim, rec)
    try:
        return "_" + fields[args.field].tolower()
    except IndexError:
        return '_'


###############################################################################
# Main
#
args = processOptions()

if (len(args.files) == 0):
    lg.error("No files specified....")
    doOneFile("[STDIN]", sys.stdin.readlines)
else:
    for fArg in (args.files):
        fh = codecs.open(fArg, 'rb', encoding=args.iencoding)
        doOneFile(fArg, fh)
        fh.close()
