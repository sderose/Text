#!/usr/bin/env python
#
# text2html.py: Convert simple text layouts to HTML.
# Written 2018-07-21 by Steven J. DeRose
#
from __future__ import print_function
import sys
import argparse
import re
import codecs

import XmlOutput
from alogging import ALogger
lg = ALogger(1)

__metadata__ = {
    "title"        : "text2html.py",
    "description"  : "Convert simple text layouts to HTML.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2018-07-21",
    "modified"     : "2020-03-04",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/",
}
__version__ = __metadata__["modified"]


descr = """
=Description=

Convert simple text layouts to HTML.

==Basic logic==

    Anything with blank lines around it is a block.

   Should catch abutted but indented paras as breaks, too.

    The nominal indent of a block is than of its non-first lines (if any).
This is to avoid list-marker placement, and indented paragraphs

    Any block starting with a list-marker is a list item.

Unordered list markers (normally only one character)
    *  -  =  o  +
    \\u2022 2023 2043 204c 204d 2219 25d8 25e6 2619 29be 29bf
    all dingbats; rarely, any graphic

Ordered list markers (may be delimited, stacked, etc):
    Numbering types (see CSS list-style-type)
        1      2      3
        A      B      C
        a      b      c
        i      ii     iii    iv
        I      II     III    IV
        01     02     03     04
        001    002    003    004
        1st    2nd    3rd
        One    Two    Three
        First  Second Third
        greek, han, arabic-indic, armenian,...

    Delimited:
        1  1.  1)  1:  1-  [1]  (1)  -1-  =1=  /1/
        (maybe any punc + \\d+ + punc?)

    Hierarchy (see MS Word examples)
        1)     1)     1
        1)     a)     i)
        1.     1.1.   1.1.1.
        I.     A.     1.
        Article I     Section 1.01        (a)

Features of numbering:
    * Do headings successively indent?
    * Do headings show all, current, most recent n, or no numbers?
    * What separates each level from prev/next?
    * Any (leading only?) keyword per level?
        * What leading punctuation on the marker?
        * What final punctuation on the marker?
    * What numbering system at each level?

Layout:
    * Does content indent, too?
    * Is title run in to following text, or a new block?
    * Outset of marker from block
    * Left/right/center justification of marker
    * (formatting of the markers, font/size/color...)


=Related Commands=

`markdown2XML.py`, `pod2html`,....

`XmlOutput.py` (used for output generation).

`BlockFormatter.py`, and `MarkupHelpFormatter.py`.


=Known bugs and Limitations=


=Rights=

This program is Copyright 2018 by Steven J. DeRose.
It is hereby licensed under the Creative Commons
Attribution-Share-Alike 3.0 unported license.
For more information on this license, see [here|"https://creativecommons.org"].

For the most recent version, see [http://www.derose.net/steve/utilities] or
[http://github/com/sderose].


=History=

* 2018-07-21: Written by Steven J. DeRose.
* 2020-03-04: New layout. lint.


=Options=
"""


###############################################################################
#
class marker:
    """See https://developer.mozilla.org/en-US/docs/Web/CSS/list-style-type
    """
    bulletChars = u"""*-+=o""" + "".join([
        chr(0x2022),  # BULLET
        chr(0x2023),  # TRIANGULAR BULLET
        chr(0x2043),  # HYPHEN BULLET
        chr(0x204c),  # BLACK LEFTWARDS BULLET
        chr(0x204d),  # BLACK RIGHTWARDS BULLET
        chr(0x2219),  # BULLET OPERATOR
        chr(0x25d8),  # INVERSE BULLET
        chr(0x25e6),  # WHITE BULLET
        chr(0x2619),  # REVERSED ROTATED FLORAL HEART BULLET
        chr(0x2765),  # ROTATED HEAVY BLACK HEART BULLET
        chr(0x2767),  # ROTATED FLORAL HEART BULLET
        chr(0x29be),  # CIRCLED WHITE BULLET
        chr(0x29bf),  # CIRCLED BULLET
    ])
    for u in range(0x2701, 0x2753):
        bulletChars += chr(u)

    basicNameList = """decimal decimal-leading-zero
lower-alpha lower-greek lower-latin lower-roman
upper-alpha upper-greek upper-latin upper-roman"""

    fancyNameList = basicNameList + """ arabic-indic armenian bengali cambodian
cjk-decimal cjk-earthly-branch cjk-heavenly-stem cjk-ideographic devanagari
ethiopic-numeric georgian gujarati gurmukhi hebrew hiragana hiragana-iroha
japanese-formal japanese-informal kannada katakana katakana-iroha khmer
korean-hangul-formal korean-hanja-formal korean-hanja-informal lao
lower-armenian malayalam mongolian
myanmar oriya persian simp-chinese-formal simp-chinese-informal tamil
telugu thai tibetan trad-chinese-formal trad-chinese-informal upper-armenian"""

    markerTypes = {}
    for i, name in enumerate(re.split(r"\s+", basicNameList)):
        markerTypes[name] = i

    def __init__(self, text=""):
        self.text = text
        return

    def getMarkerType(self, s):
        """Identify what kind of bullet or number we've got (if any).
        There must be no punctuation or space, that should already be gone.
        """

        if (re.match(r"\d+", s)): return "decimal"
        if (re.match(r"[ivxlcm]{2,}$", s)): return "lower-roman"
        if (re.match(r"[IVXLCM]{2,}$", s)): return "upper-roman"
        if (re.match(r"[A-Z]", s)): return "upper-latin"  # But "I"
        if (re.match(r"[a-z]", s)): return "lower-latin"  # But "i"


###############################################################################
#
class blockify:
    def __init__(self):
        self.encoding = None
        self.path = None
        self.recs = []
        self.blocks = []

    def loadFile(self, path, encoding="utf-8"):
        fh = codecs.open(path, "rb", encoding=encoding)
        self.recs = fh.readlines()
        return len(self.recs)

    def loadString(self, s):
        self.recs = re.split(r"\r\n?|\n", s)
        return len(self.recs)

    def interpret(self):
        # Group at blank lines
        assert(False)


###############################################################################
#
def doOneFile(path, fh):
    """Read and deal with one individual file.
    """
    xo = XmlOutput.XmlOutput()
    xo.startHTML()

    try:
        recs = fh.readlines()
    except IOError as e:
        sys.stderr.write("Cannot read '%s':]n    %s" % (path, e))
        sys.exit()
    recnum = len(recs)

    nBlankLines = 0
    #lastRec = ""
    lastIndent = 0
    for i in range(recnum):
        # Normalize
        rec = recs[i].rstrip("\r\n")
        rec = rec.expandtabs(args.tabs)
        stripped = rec.strip()
        isBlank = (stripped == "")

        # Extract some basic characteristics
        indent = targetLen(r"^(\s+)", rec)
        allCaps = hasTarget(r"\w", rec) and hasTarget(r"^[^a-z]*$", rec)
        bulleted = hasTarget(r"^[*-=+]", stripped)
        numbered = hasTarget(r"^(\d+|[A-Z]|[IVXL]+)([):.])?\s", stripped)

        # Now decide what we're dealing with
        if (isBlank):
            xo.closeAllOfThese("p li")
            nBlankLines += 1
        elif (indent > lastIndent):
            if (numbered): xo.openElement("ol")
            elif (bulleted): xo.openElement("ul")
            else: xo.openElement("div")
            xo.openElement("li")
        elif (indent < lastIndent):
            if (numbered): xo.openElement("ol")
            elif (bulleted): xo.openElement("ul")
            else: xo.openElement("div")
            xo.closeElementIfOpen("li")
            if (xo.getCurrentElementName() in [ "ul", "ol", "div" ]):
                xo.closeElement()
        else:  # non-blank, same indent
            pass

        xo.makeText(rec)

        # Make new line "previous"
        lastIndent = indent
        if (not isBlank): nBlankLines = 0
        #lastRec = rec

    #print(recs)
    return(recnum)


def writeHeader():
    print(
"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
    "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta http-equiv="content-type" content="application/xhtml+xml; charset=utf-8" />
    <title></title>
</head>
<body>""")


def writeTrailer():
    print("</body>\n</html>")


def hasTarget(regex, s, groupNum=0):
    mat = re.search(regex, s)
    if (groupNum==0): return (mat is not None)
    else: return (mat.group(groupNum) is not None)

def getTarget(regex, s, groupNum=0):
    mat = re.search(regex, s)
    if (mat is None): return None
    return len(mat.group(groupNum))

def targetLen(regex, s, groupNum=0):
    mat = re.search(regex, s)
    if (mat is None): return None
    return len(mat.group(groupNum))


###############################################################################
# Main
#
if (__name__ == "_main_"):
    def processOptions():
        try:
            from BlockFormatter import BlockFormatter
            parser = argparse.ArgumentParser(
                description=descr, formatter_class=BlockFormatter)
        except ImportError:
            parser = argparse.ArgumentParser(description=descr)

        parser.add_argument(
            "--iencoding", type=str, default="utf8",
            help="Assume utf-8 for input files.")
        parser.add_argument(
            "--quiet", "-q", action="store_true",
            help="Suppress most messages.")
        parser.add_argument(
            "--tabs", type=int, default=4,
            help="Tab interval. Default 4.")
        parser.add_argument(
            "--unicode",          action="store_const", dest="iencoding",
            const="utf8", help="Assume utf-8 for input files.")
        parser.add_argument(
            "--verbose", "-v",    action="count", default=0,
            help="Add more messages (repeatable).")
        parser.add_argument(
            "--version", action="version", version=__version__,
            help="Display version information, then exit.")

        parser.add_argument(
            "files",             type=str,
            nargs=argparse.REMAINDER,
            help="Path(s) to input file(s)")

        args0 = parser.parse_args()
        if (args0.verbose): lg.setVerbose(args0.verbose)
        return(args0)


    ###########################################################################
    #
    args = processOptions()

    if (len(args.files) == 0):
        lg.error("No files specified....")
        doOneFile("[STDIN]", sys.stdin.readlines)
    else:
        for fArg in (args.files):
            lg.bumpStat("Total Args")
            fh0 = codecs.open(fArg, "rb", encoding=args.iencoding)
            doOneFile(fArg, fh0)
            fh0.close()

    if (not args.quiet):
        lg.vMsg(0,"Done.")
        lg.showStats()
