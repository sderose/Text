#!/usr/bin/env python3
#
# shortenContext.py: Trim lines to just the surrounding of a regex match.
# 2018-09-10: Written. Copyright by Steven J. DeRose.
#
from __future__ import print_function
import sys
import argparse
import re
import codecs

from PowerWalk import PowerWalk

__metadata__ = {
    "title"        : "shortenContext",
    "description"  : "Trim lines to just the surrounding of a regex match.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2018-09-10",
    "modified"     : "2021-02-23",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]


descr = """
=Description=

Trim long lines to just a limited around surrounding a
given regex match.

This is useful, for example, if you are getting `grep` hits in files with
very long lines, and you want more than just the matched string, but less
then the entire lines.


=Related Commands=

C<grep>


=Known bugs and Limitations=

Unfinished....


=History=

  2018-09-10: Written by Steven J. DeRose.
  2021-02-23: New layout.


=Rights=

Copyright 2018-09-10 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
For further information on this license, see
[https://creativecommons.org/licenses/by-sa/3.0].

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""

def doOneFile(_path, fh):
    for rec in fh.readlines():
        if (len(rec) < args.maxLength):
            print(rec)
            continue
        for mat in re.finditer(args.regex, rec):
            print(getContext(rec, mat))
            if (not args.multi): break
    return

def getContext(rec, mat):
    matchLen = mat.start() - mat.end() + 1
    addPerSide = (args.maxLength - matchLen) / 2
    if (addPerSide<=0): return mat.group()
    start = mat.start() - addPerSide
    if (start < 0): start = 0
    end = mat.end() + addPerSide
    if (end > len(rec)): end = len(rec)
    return rec[start:end]


###############################################################################
# Main
#
if __name__ == "__main__":
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
            "--ignoreCase", "-i", action='store_true',
            help='Disregard case distinctions.')
        parser.add_argument(
            "--maxLength", type=int, metavar='N', default="79",
            help='Limit the returned length per match to this.')
        parser.add_argument(
            "--multi", action='store_true',
            help='Show multiple hits per line.')
        parser.add_argument(
            "--oencoding", type=str, metavar='E',
            help='Use this character set for output files.')
        parser.add_argument(
            "--quiet", "-q", action='store_true',
            help='Suppress most messages.')
        parser.add_argument(
            "--regex", "-e", type=str, metavar='R',
            help='Regex to identify the hits you want context for.')
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
            "files", type=str,
            nargs=argparse.REMAINDER,
            help='Path(s) to input file(s)')

        args0 = parser.parse_args()
        return(args0)


    ###########################################################################
    #
    args = processOptions()

    if (len(args.files) == 0):
        if (sys.stdin.isatty): sys.stderr.write("Waiting on stdin...\n")
        doOneFile("[STDIN]", sys.stdin)
    else:
        depth = 0
        pw = PowerWalk(args.files)
        pw.setOption('recursive', args.recursive)
        for path0, fhOrFlag in pw.traverse():
            if (fhOrFlag == "DIR_END"):
                depth -= 1
                continue
            print("    " * depth + path0)
            if (fhOrFlag == "DIR_START"):
                depth += 1
                continue

            fileNum = pw.travState.stats['itemsReturned']
            fh0 = codecs.open(path0, "rb", encoding=args.iencoding)
            doOneFile(path0, fh0)
            fh0.close()
