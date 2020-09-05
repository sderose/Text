#!/usr/bin/env python
#
# any2xml.py
#
# 2018-07-25: Written. Copyright by Steven J. DeRose.
# Creative Commons Attribution-Share-alike 3.0 unported license.
# See http://creativecommons.org/licenses/by-sa/3.0/.
#
# To do:
#
from __future__ import print_function
import sys
import argparse
#import re
#import string
#import math
import codecs

from sjdUtils import sjdUtils
from alogging import ALogger

__version__ = "2018-07-25"
__metadata__ = {
    'creator'      : "Steven J. DeRose",
    'cre_date'     : "2018-07-25",
    'language'     : "Python 2.7.6",
    'version_date' : "2018-07-25",
}

su = sjdUtils()
lg = ALogger(1)


###############################################################################
#
def processOptions():
    descr = """
=head1 Description

Convert anything to XML. Sort of.

=head1 Related Commands

=head1 Known bugs and Limitations

=head1 Licensing

Copyright 2018-07-25 by Steven J. DeRose. This script is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See http://creativecommons.org/licenses/by-sa/3.0/ for more information.

=head1 Options
"""

    try:
        from BlockFormatter import BlockFormatter
        parser = argparse.ArgumentParser(
            description=descr, formatter_class=BlockFormatter)
    except ImportError:
        parser = argparse.ArgumentParser(description=descr)

    parser.add_argument(
        "--iencoding",        type=str, metavar='E', default="utf-8",
        help='Assume this character set for input files. Default: utf-8.')
    parser.add_argument(
        "--oencoding",        type=str, metavar='E',
        help='Use this character set for output files.')
    parser.add_argument(
        "--quiet", "-q",      action='store_true',
        help='Suppress most messages.')
    parser.add_argument(
        "--recursive",        action='store_true',
        help='Descend into subdirectories.')
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
    lg.setColors(args0.color)
    if (args0.verbose): lg.setVerbose(args0.verbose)
    return(args0)



###############################################################################
#
def doOneFile(path, fh):
    """Read and deal with one individual file.
    """
    lg.vMsg(1, "Starting file '%s'." % (path))
    rec = ""
    print("""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE lame [
    <!ELEMENT lame ANY>
]>
<lame>
""")
    while (True):
        rec = fh.readline()
        if (len(rec) == 0): break # EOF
        rec = su.escapeXmlContent(rec)
        print(rec, end="")
    print("</lame>")
    return


###############################################################################
###############################################################################
# Main
#
args = processOptions()

if (len(args.files) == 0):
    lg.error("No files specified....")
    doOneFile("[STDIN]", sys.stdin)
else:
    for fArg in (args.files):
        lg.bumpStat("Total Args")
        fh0 = codecs.open(fArg, "rb", encoding=args.iencoding)
        doOneFile(fArg, fh0)
        fh0.close()

if (not args.quiet):
    lg.vMsg(0,"Done.")
    lg.showStats()
