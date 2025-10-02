#!/usr/bin/env python3
#
# wcPP.py: An enhanced 'wc'.
# 2021-10-14: Written by Steven J. DeRose.
#
import sys
import re
#import codecs
from collections import namedtuple
#from typing import IO, Dict, List, Union

__metadata__ = {
    "title"        : "wcPP",
    "description"  : "An enhanced 'wc'.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2021-10-14",
    "modified"     : "2021-10-14",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]

descr = """
=Description=

==Usage==

    wcPP.py [options] [files]

Count the number of items in the input:
    * Bytes
    * Characters
    * Words
    * Sentences
    * Lines
    * Blocks

=Related Commands=

*nix `wc`. But this has full encoding support, can count several things `wc` can't
(such as line-final hyphens and blank-line-separated blocks),
can report in multiple formats, and has a selection of "word" definitions available.

My `countChars` -- counts characters by Unicode plane, block, script, etc., and makes
frequency-lists.

My `ord` and `CharDisplay.py` -- get lots of information about characters.


=Known bugs and Limitations=

Sentence counting is not yet implemented.


=To do=

* Tune `--wordDef historical` to exactly match *nix `wc`.
* Unicode canonical forms for character counting?


=History=

* 2021-10-14: Written by Steven J. DeRose.


=Rights=

Copyright 2021-10-14 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See [http://creativecommons.org/licenses/by-sa/3.0/] for more information.

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""

def log(lvl:int, msg:str) -> None:
    if (args.verbose >= lvl): sys.stderr.write(msg + "\n")
def warning(msg:str) -> None: log(0, msg)

dashes = {
    0x0002D:  "HYPHEN-MINUS",
    0x000AD:  "SOFT HYPHEN",                        ### SPECIAL
    0x0058A:  "ARMENIAN HYPHEN",
    0x01806:  "MONGOLIAN TODO SOFT HYPHEN",
    0x01B60:  "BALINESE PAMENENG (line-breaking hyphen)",
    0x02010:  "HYPHEN",
    0x02011:  "NON-BREAKING HYPHEN",                ### SPECIAL
    0x02012:  "FIGURE DASH",
    0x02013:  "EN DASH",
    0x02014:  "EM DASH",
    0x02027:  "HYPHENATION POINT",                  ### SPECIAL
    0x02043:  "HYPHEN BULLET",
    0x02053:  "SWUNG DASH",
    0x02212:  "MINUS",
    0x0229D:  "CIRCLED DASH",
    0x02448:  "OCR DASH",
    0x02E17:  "DOUBLE OBLIQUE HYPHEN",
    0x02E1A:  "HYPHEN WITH DIAERESIS",
    0x0301C:  "WAVE DASH",
    0x03030:  "WAVY DASH",
    0x030A0:  "KATAKANA-HIRAGANA DOUBLE HYPHEN",
    0x0FE58:  "SMALL EM DASH",
    0x0FE63:  "SMALL HYPHEN-MINUS",
    0x0FF0D:  "FULLWIDTH HYPHEN-MINUS",
}


###############################################################################
#
Stats = namedtuple('Stats',
    [ 'byts', 'chars', 'words', 'finalHypens',  'sents', 'lines', 'blocks', 'maxRec' ] )

dftSet = [ 'lines', 'words', 'byts' ]
printOrder = [ 'lines', 'words', 'byts', 'chars', 'finalHypens', 'sents', 'blocks', 'maxRec' ]

def pStats(st, path:str=""):
    buf = ""
    for i in range(len(st)):
        nam = st._fields[i]
        if (args.oformat == 'xml'):
            buf += "<%s>%8d</%s>" % (nam, st[i], nam)
        elif (args.oformat == 'csv'):
            buf += "%8d," % (st[i])
        elif (args.oformat == "posix"):
            buf += "%8d " % (st[i])
        else:
            raise KeyError
    if (args.oformat == 'xml'):
        buf += "<%s>%8d</%s>" % ("path", st[i], "path")
    else:
        buf += path
    print(buf)

def addStats(st1, st2):
    items = [ st1[i]+st2[i] for i in range(len(st1)) ]
    return Stats(*items)


###############################################################################
#
def doOneFile(path:str) -> int:
    """Read and deal with one individual file.
    """
    byts  = 0
    chars  = 0
    words  = 0
    finalHypens = 0
    sents  = 0        # TODO: Count these
    lines  = 0
    blocks = 0
    maxRec = 0

    if (not path):
        if (sys.stdin.isatty() and not args.quiet): print("Waiting on STDIN...")
        fh = sys.stdin
    else:
        try:
            fh = open(path, "rb")
        except IOError as e:
            warning("Cannot open '%s':\n    %s" % (path, e))
            return 0

    lines = 0
    interBlock = True
    for byteStr in fh.readlines():
        byteStr = bytes(byteStr)
        lines += 1
        byts += len(byteStr)
        rec = byteStr.decode(encoding=args.iencoding)
        recLen = len(rec)
        chars += recLen
        if recLen > maxRec: maxRec = recLen
        if (rec.strip() == ""):
            interBlock = True
            continue
        if (interBlock):
            blocks += 1
            interBlock = False
        cWords = tokenize(rec)
        words += len(cWords)
        if (rec.rstrip()[-1] in dashes): finalHypens += 1
    if (fh != sys.stdin): fh.close()
    stats = Stats(byts, chars, words, finalHypens, sents, lines, blocks, maxRec)
    return stats

def tokenize(s:str):
    """TODO: match to POSIX defn for wc.
    """
    if (args.wordDef == 'none'):
        return []
    elif (args.wordDef == "historical"):
        return re.split(r"[ \t\n]+", s)
    elif (args.wordDef == "asciiWS"):
        return re.split(r"[ \t\n\v\r\f]+", s)
    elif (args.wordDef == "unicodeWS"):
        return re.split(r"\s+", s, flags=re.UNICODE)
    elif (args.wordDef == "wordish"):
        return re.split(r"[-'.\w]+", s, flags=re.UNICODE)
    else:
        raise KeyError


###############################################################################
# Main
#
if __name__ == "__main__":
    import argparse

    def processOptions() -> argparse.Namespace:
        try:
            from BlockFormatter import BlockFormatter
            parser = argparse.ArgumentParser(
                description=descr, formatter_class=BlockFormatter)
        except ImportError:
            parser = argparse.ArgumentParser(description=descr)

        parser.add_argument(
            "-c", action="store_true",
            help="Count actual bytes.")
        parser.add_argument(
            "-l", action="store_true",
            help="Count lines.")
        parser.add_argument(
            "-m", action="store_true",
            help="Count characters (see also --iencoding).")
        parser.add_argument(
            "-w", action="store_true",
            help="Count words (not the exact Posix definition yet).")

        parser.add_argument(
            "--iencoding", "--input-encoding", type=str, metavar="E", default="utf-8",
            help="Assume this character coding for input. Default: utf-8.")
        parser.add_argument(
            "--oformat", "--output-format",
            type=str, default="posix", choices=[ "xml", "csv", "posix" ],
            help="Format to use for output.")
        parser.add_argument(
            "--quiet", "-q", action="store_true",
            help="Suppress most messages.")
        parser.add_argument(
            "--verbose", "-v", action="count", default=0,
            help="Add more messages (repeatable).")
        parser.add_argument(
            "--version", action="version", version=__version__,
            help="Display version information, then exit.")
        parser.add_argument(
            "--wordDef", type=str, default="historical",
            choices=[ "historical", "asciiWS", "unicodeWS", "wordish", "none", ],
            help="How to count 'words'.")

        parser.add_argument(
            "files", type=str, nargs=argparse.REMAINDER,
            help="Path(s) to input file(s)")

        args0 = parser.parse_args()
        return(args0)

    ###########################################################################
    #
    args = processOptions()
    totStats = Stats(0, 0, 0, 0, 0, 0, 0, 0)

    if (len(args.files) == 0):
        warning("wcPP.py: No files specified....")
        doOneFile(None)
    else:
        for path0 in args.files:
            theStats = doOneFile(path0)
            totStats = addStats(totStats, theStats)
            pStats(theStats, path0)
        if (not args.quiet):
            warning("wcPP.py: Done, %d files.\n" % (len(args.files)))
