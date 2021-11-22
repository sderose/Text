#!/usr/bin/env python
#
# any2xml.py: Convert anything to XML. Sort of.
# 2018-07-25: Written by Steven J. DeRose.
#
from __future__ import print_function
import sys
import argparse
import codecs

from sjdUtils import sjdUtils
su = sjdUtils()

__metadata__ = {
    'title'        : "any2xml.py",
    'description'  : "Convert anything to XML. Sort of.",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2018-07-25",
    'modified'     : "2020-12-08",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']

descr = """
=Description=

Convert anything to XML. Sort of.


=Known bugs and Limitations=

The point is not that this is useful, but that conversion requires ''thought''.
Syntax by itself is not enough.


=Rights=

Copyright 2018-07-25 by Steven J. DeRose. This script is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See http://creativecommons.org/licenses/by-sa/3.0/ for more information.

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
        "--iencoding", type=str, metavar='E', default="utf-8",
        help='Assume this character set for input files. Default: utf-8.')
    parser.add_argument(
        "--oencoding", type=str, metavar='E',
        help='Use this character set for output files.')
    parser.add_argument(
        "--quiet", "-q", action='store_true',
        help='Suppress most messages.')
    parser.add_argument(
        "--recursive", action='store_true',
        help='Descend into subdirectories.')
    parser.add_argument(
        "--unicode", action='store_const', const='utf8', dest='iencoding',
        help='Assume utf-8 for input files.')
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
    return(args0)


###############################################################################
#
def doOneFile(path, fh):
    """Read and deal with one individual file.
    """
    if (args.verbose):
        sys.stderr.write("Starting file '%s'." % (path))
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
# Main
#
args = processOptions()

if (len(args.files) == 0):
    sys.stderr.write("No files specified....\n")
    doOneFile("[STDIN]", sys.stdin)
else:
    for fArg in (args.files):
        fh0 = codecs.open(fArg, "rb", encoding=args.iencoding)
        doOneFile(fArg, fh0)
        fh0.close()
