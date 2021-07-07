#!/usr/bin/env python
#
# PSDF.py: An accessible PDF-like format, in PS.
# 2021-06-10: Written by Steven J. DeRose.
#
from __future__ import print_function
import sys
import os
import codecs
#import string
#import math
#import subprocess
#from collections import defaultdict, namedtuple

from PowerWalk import PowerWalk, PWType
#from sjdUtils import sjdUtils
#from alogging import ALogger
#su = sjdUtils()
#lg = ALogger(1)


__metadata__ = {
    "title"        : "PSDF.py",
    "description"  : "An accessible PDF-like format, in PS.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2021-06-10",
    "modified"     : "2021-06-10",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]


descr = """
=Description=

(just drafting this idea, way unfinished)

==Usage==

    PSDF.py [options] [files]

Tools to produce PSDF (Portable Structured Document Format ''or''
PostScript Document Format).

==Goals==

* Portability (hence, it's just PostScript)
* Trivial to get the text out
** in a reasonable reading order
** distinguishing real text, generated bits like page headers, and original
but invisible/suppressed text
* Encourages keeping (for example) soft hyphens soft.
* Possible but not required, to include markup
* Ability to include arbitrary PS, but segragated from main content.
* Minimum difficulty to write.
* preserve ability to extract block, inline, table, fig, list, item, head
* distinguish logical vs. physical vs. display pagenums

==General architecture==

* The text goes in a block or array
* Pages mainly consist of:
** set font
** set position
** display item N of text, range [i:j]

functions
    newpage(userNum:str)
    moveTo(x, y, why)
        why: (adjust, inline, softBreak, hardbreak, secN, listN, tableN, cellN, rowN, image)
    setFont(enc, cat, fam, size, weight, sty, color, expand, rotate)
    showText(textNum, st, en)
    generateText(literal, st, en)
    drawImage, drawLine, etc.



=Related Commands=


=Known bugs and Limitations=


=History=

* 2021-06-10: Written by Steven J. DeRose.


=To do=


=Rights=

Copyright 2021-06-10 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See [http://creativecommons.org/licenses/by-sa/3.0/ for more information].

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""

def log(lvl, msg):
    if (args.verbose >= lvl): sys.stderr.write(msg + "\n")
def warning0(msg): log(0, msg)
def warning1(msg): log(1, msg)
def warning2(msg): log(2, msg)
def fatal(msg): log(0, msg); sys.exit()
warn = log


###############################################################################
#
def doOneFile(path):
    """Read and deal with one individual file.
    """
    if (not path):
        if (sys.stdin.isatty()): print("Waiting on STDIN...")
        fh = sys.stdin
    else:
        try:
            fh = codecs.open(path, "rb", encoding=args.iencoding)
        except IOError as e:
            warning0("Cannot open '%s':\n    %s" % (e))
            return 0

    recnum = 0
    for rec in fh.readlines():
        recnum += 1
        if (args.tickInterval and (recnum % args.tickInterval == 0)):
            warning0("Processing record %s." % (recnum))
        rec = rec.rstrip()
        if (rec == ""): continue  # Blank record
        print(rec)
    if  (fh != sys.stdin): fh.close()
    return recnum

def doOneXmlFile(path):
    """Parse and load
    """
    from xml.dom import minidom
    from DomExtensions import DomExtensions
    DomExtensions.patchDom(minidom)
    xdoc = minidom.parse(path)
    docEl = xdoc.documentElement
    paras = docEl.getElementsByTagName("P")
    for para in paras:
        print(para.textValue)
    return 0


###############################################################################
# Main
#
if __name__ == "__main__":
    import argparse
    def anyInt(x):
        return int(x, 0)

    def processOptions():
        try:
            from BlockFormatter import BlockFormatter
            parser = argparse.ArgumentParser(
                description=descr, formatter_class=BlockFormatter)
        except ImportError:
            parser = argparse.ArgumentParser(description=descr)

        parser.add_argument(
            "--color",  # Don't default. See below.
            help="Colorize the output.")
        parser.add_argument(
            "--iencoding", type=str, metavar="E", default="utf-8",
            help="Assume this character coding for input. Default: utf-8.")
        parser.add_argument(
            "--ignoreCase", "-i", action="store_true",
            help="Disregard case distinctions.")
        parser.add_argument(
            "--oencoding", type=str, metavar="E", default="utf-8",
            help="Use this character coding for output. Default: iencoding.")
        parser.add_argument(
            "--quiet", "-q", action="store_true",
            help="Suppress most messages.")
        if (0): parser.add_argument(
            "--recursive", action="store_true",
            help="Descend into subdirectories.")
        parser.add_argument(
            "--tickInterval", type=anyInt, metavar="N", default=10000,
            help="Report progress every n records.")
        parser.add_argument(
            "--unicode", action="store_const", dest="iencoding",
            const="utf8", help="Assume utf-8 for input files.")
        parser.add_argument(
            "--verbose", "-v", action="count", default=0,
            help="Add more messages (repeatable).")
        parser.add_argument(
            "--version", action="version", version=__version__,
            help="Display version information, then exit.")

        PowerWalk.addOptionsToArgparse(parser)

        parser.add_argument(
            "files", type=str,
            nargs=argparse.REMAINDER,
            help="Path(s) to input file(s)")

        args0 = parser.parse_args()
        if (args0.color == None):
            args0.color = ("USE_COLOR" in os.environ and sys.stderr.isatty())
        #lg.setColors(args0.color)
        #if (args0.verbose): lg.setVerbose(args0.verbose)
        return(args0)

    ###########################################################################
    #
    args = processOptions()
    if (args.iencoding and not args.oencoding):
        args.oencoding = args.iencoding
    if (args.oencoding):
        sys.stdout.reconfigure(encoding="utf-8")

    if (len(args.files) == 0):
        warning0("PSDF.py: No files specified....")
        doOneFile(None)
    else:
        pw = PowerWalk(args.files, open=False, close=False,
            encoding=args.iencoding)
        pw.setOptionsFromArgparse(args)
        for path0, fh0, what0 in pw.traverse():
            if (what0 != PWType.LEAF): continue
            if (path0.endswith(".xml")): doOneXmlFile(path0)
            else: doOneFile(path0)
        if (not args.quiet):
            warning0("PSDF.py: Done, %d files.\n" % (pw.getStat("regular")))
