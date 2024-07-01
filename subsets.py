#!/usr/bin/env python3
#
# subsets.py: Generate successive prefixes of some data.
# 2021-02-17: Written by Steven J. DeRose.
#
#pylint: disable=W0603
#
import sys
#import os
import codecs
import re
#import math
from subprocess import check_output
#from collections import defaultdict, namedtuple

__metadata__ = {
    "title"        : "subsets",
    "description"  : "Generate successive prefixes of some data.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2021-02-17",
    "modified"     : "2021-02-17",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]


descr = """
=Description=

Given an input stream, save a series of files, each containing a longer
part of the original.
This may be handy for testing performance of various tools.


=Usage=

    subsets.py --lines 100 --format "%04x" mySample.txt

copies:
    the first 100 lines of `mySample.txt` to subset_0001.txt
    the first 200 lines of `mySample.txt` to subset_0002.txt
    ...

The files are numbered sequentially (not by the starting file number),
and you can change `--format` to control padding, base, etc.


=Related Commands=

My `CSV/disaggregate`.


=Known bugs and Limitations=


=History=

* 2021-02-17: Written by Steven J. DeRose.


=To do=

* Option to do non-overlapping subsets
* Possibly integrate into `CSV/disaggregate`?
* Other ways to determine breaking points, such as XML elements,
regex matches, etc.


=Rights=

Copyright 2021-02-17 by Steven J. DeRose. This work is licensed under a
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

outFileCount = 0


###############################################################################
#
def doOneFile(path):
    """Read and deal with one individual file.
    """
    global outFileCount

    if (not path):
        if (sys.stdin.isatty()): print("Waiting on STDIN...")
        fh = sys.stdin
    else:
        try:
            fh = codecs.open(path, "rb", encoding=args.iencoding)
        except IOError as e:
            warning0("Cannot open '%s':\n    %s" % (e))
            return 0, 0

    recnum = 0
    outFileCount = 0
    ofh = None
    curOPath = generatePath(outFileCount)
    for rec in fh.readlines():
        if (recnum % args.lines == 0):
            if (ofh): ofh.close()
            outFileCount += 1
            if (outFileCount > args.maxFiles):
                warning0("--maxFiles limit reached.")
                break
            newOPath = generatePath(outFileCount)
            _rc = check_output("cp %s %s" % (curOPath, newOPath))
            curOPath = newOPath
            ofh = codecs.open(curOPath, "wb", encoding=args.oencoding)
        recnum += 1
        ofh.write(rec)
    if (ofh): ofh.close()
    return recnum, outFileCount

def generatePath(n):
    ns = args.format % format(n)
    path = re.sub("{}", ns, args.opath)
    return path


###############################################################################
# Main
#
if __name__ == "__main__":
    import argparse
    def processOptions():
        try:
            from BlockFormatter import BlockFormatter
            parser = argparse.ArgumentParser(
                description=descr, formatter_class=BlockFormatter)
        except ImportError:
            parser = argparse.ArgumentParser(description=descr)

        parser.add_argument(
            "--format", type=str, metavar="F", default="%04d",
            help="A format()-style spec for the numbers to insert.")
        parser.add_argument(
            "--iencoding", type=str, metavar="E", default="utf-8",
            help="Assume this character coding for input. Default: utf-8.")
        parser.add_argument(
            "--ignoreCase", "-i", action="store_true",
            help="Disregard case distinctions.")
        parser.add_argument(
            "--lines", type=int, default=1000,
            help="Increment by this many lines each time.")
        parser.add_argument(
            "--maxFiles", type=int, default=100,
            help="Don't write more than this many files.")
        parser.add_argument(
            "--oencoding", type=str, metavar="E", default="utf-8",
            help="Use this character coding for output. Default: iencoding.")
        parser.add_argument(
            "--opath", type=str, metavar="F", default="prefix_{}.txt",
            help="Template for generated filenames. Use '{}' for the number.")
        parser.add_argument(
            "--quiet", "-q", action="store_true",
            help="Suppress most messages.")
        parser.add_argument(
            "--unicode", action="store_const", dest="iencoding",
            const="utf8", help="Assume utf-8 for input files.")
        parser.add_argument(
            "--verbose", "-v", action="count", default=0,
            help="Add more messages (repeatable).")
        parser.add_argument(
            "--version", action="version", version=__version__,
            help="Display version information, then exit.")

        parser.add_argument(
            "files", type=str,
            nargs=argparse.REMAINDER,
            help="Path(s) to input file(s)")

        args0 = parser.parse_args()
        assert '%' in args.format
        assert '{}}' in args.format
        assert '%' not in args.opath
        return(args0)

    ###########################################################################
    #
    args = processOptions()
    if (args.iencoding and not args.oencoding):
        args.oencoding = args.iencoding
    if (args.oencoding):
        # https://stackoverflow.com/questions/4374455/
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
        # 3.7+ sys.stdout.reconfigure(encoding="utf-8")

    if (len(args.files) == 0):
        warning0("subsets.py: No files specified....")
        recs, ofiles = doOneFile(None)
    else:
        recs, ofiles = doOneFile(args.files[0])
    if (not args.quiet):
        warning0("subsets.py: Read, %d records, wrote %d files.\n" % (recs, ofiles))
