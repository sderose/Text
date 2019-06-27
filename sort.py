#!/usr/bin/env python
#
# sort.py
#
# 2018-07-18: Written. Copyright by Steven J. DeRose.
# Creative Commons Attribution-Share-alike 3.0 unported license.
# See http://creativecommons.org/licenses/by-sa/3.0/.
#
# To do:
#
from __future__ import print_function
import sys, os
import argparse
import re
#import string
#import math
#import subprocess
import codecs
#import gzip
#from collections import defaultdict

#import pudb
#pudb.set_trace()

#from sjdUtils import sjdUtils
from alogging import ALogger

__version__ = "2018-07-18"
__metadata__ = {
    'creator'      : "Steven J. DeRose",
    'cre_date'     : "2018-07-18",
    'language'     : "Python 2.7.6",
    'version_date' : "2018-07-18",
}

#su = sjdUtils()
lg = ALogger(1)


###############################################################################
#
def processOptions():
    descr = """
=head1 Description

*nix C<sort> is too lame, so do something I can make work.

=head1 Related Commands

=head1 Known bugs and Limitations

Nothing special for locale.

Can't specify *parts* of fields or multiple fields.

Limited to memory size.


=head1 Licensing

Copyright 2015 by Steven J. DeRose. This script is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See http://creativecommons.org/licenses/by-sa/3.0/ for more information.

=head1 Options
"""

    try:
        from MarkupHelpFormatter import MarkupHelpFormatter
        formatter = MarkupHelpFormatter
    except ImportError:
        formatter = None
    parser = argparse.ArgumentParser(
        description=descr, formatter_class=formatter)

    parser.add_argument(
        "--color",  # Don't default. See below.
        help='Colorize the output.')
    parser.add_argument(
        "--delim", "-d", "-t", "--fieldSep", type=str, default="\t",
        help='Use this (regex) as the field delimiter.')
    parser.add_argument(
        "--field", "-f", "-k", type=int, default=None,
        help='Use this (regex) as the field delimiter.')
    parser.add_argument(
        "--iencoding",        type=str, metavar='E', default="utf-8",
        help='Assume this character set for input files. Default: utf-8.')
    parser.add_argument(
        "--ignoreCase", "-i", action='store_true',
        help='Disregard case distinctions.')
    parser.add_argument(
        "--numeric", "-n", "-g", action='store_true',
        help='Do numeric comparison (incl. floats), instead of string.')
    parser.add_argument(
        "--quiet", "-q",      action='store_true',
        help='Suppress most messages.')
    parser.add_argument(
        "--reverse", "-r",    action='store_true', default=False,
        help='Sort in descending order.')
    parser.add_argument(
        "--tickInterval",     type=int, metavar='N', default=10000,
        help='Report progress every n records.')
    parser.add_argument(
        "--unicode",          action='store_const',  dest='iencoding',
        const='utf8', help='Assume utf-8 for input files.')
    parser.add_argument(
        "--verbose", "-v",    action='count',       default=0,
        help='Add more messages (repeatable).')
    parser.add_argument(
        "--version", action='version', version=__version__,
        help='Display version information, then exit.')

    parser.add_argument(
        'files',             type=str,
        nargs=argparse.REMAINDER,
        help='Path(s) to input file(s)')

    args0 = parser.parse_args()
    if (args0.color == None):
        args0.color = ("USE_COLOR" in os.environ and sys.stderr.isatty())
    lg.setColors(args0.color)
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

if (not args.quiet):
    lg.vMsg(0,"Done.")
    lg.showStats()
