#!/usr/bin/env python
#
# text2html.py
#
# 2018-07-21: Written by Steven J. DeRose.
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

import XmlOutput
#from sjdUtils import sjdUtils
from alogging import ALogger

__metadata__ = {
    'creator'      : "Steven J. DeRose",
    'cre_date'     : "2018-07-21",
    'language'     : "Python 2.7.6",
    'version_date' : "2018-07-21",
}
__version__ = __metadata__['version_date']

lg = ALogger(1)

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
if PY2:
    string_types = basestring
else:
    string_types = str
    def unichr(n): return chr(n)

class marker:
    """See https://developer.mozilla.org/en-US/docs/Web/CSS/list-style-type
    """
    bulletChars = u"""*-+=o""" + "".join([
        unichr(0x2022),  # BULLET
        unichr(0x2023),  # TRIANGULAR BULLET
        unichr(0x2043),  # HYPHEN BULLET
        unichr(0x204c),  # BLACK LEFTWARDS BULLET
        unichr(0x204d),  # BLACK RIGHTWARDS BULLET
        unichr(0x2219),  # BULLET OPERATOR
        unichr(0x25d8),  # INVERSE BULLET
        unichr(0x25e6),  # WHITE BULLET
        unichr(0x2619),  # REVERSED ROTATED FLORAL HEART BULLET
        unichr(0x2765),  # ROTATED HEAVY BLACK HEART BULLET
        unichr(0x2767),  # ROTATED FLORAL HEART BULLET
        unichr(0x29be),  # CIRCLED WHITE BULLET
        unichr(0x29bf),  # CIRCLED BULLET
    ])
    for u in range(0x2701, 0x2753):
        bulletChars += unichr(u)

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
    for i, name in enumerate(re.split(r'\s+', basicNameList)):
        markerTypes[name] = i

    def __init__(self, text=""):
        return

    def getMarkerType(s):
        """Identify what kind of bullet or number we've got (if any).
        There must be no punctuation or space, that should already be gone.
        """

        if (re.match(r'\d+', s)): return 'decimal'
        if (re.match(r'[ivxlcm]{2,}$', s)): return 'lower-roman'
        if (re.match(r'[IVXLCM]{2,}$', s)): return 'upper-roman'
        if (re.match(r'[A-Z]', s)): return 'upper-latin'  # But 'I'
        if (re.match(r'[a-z]', s)): return 'lower-latin'  # But 'i'


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
        self.recs = re.split(r'\r\n?|\n', s)
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

    recs = fh.readlines()
    recnum = len(recs)

    nBlankLines = 0
    lastRec = ""
    lastIndent = 0
    for i in range(recnum):
        # Normalize
        rec = recs[i].rstrip("\r\n")
        rec = expandtabs(rec, args.tabs)
        stripped = rec.strip()
        isBlank = (stripped == '')

        # Extract some basic characteristics
        indent = targetLen(r'^(\s+)', rec)
        allCaps = hasTarget(r'\w', rec) and hasTarget(r'^[^a-z]*$', rec)
        bulleted = hasTarget(r'^[*-=+]', stripped)
        numbered = hasTarget(r'^(\d+|[A-Z]|[IVXL]+)([):.])?\s', stripped)

        # Now decide what we're dealing with
        if (isBlank):
            xo.closeAllOfThese('p li')
            nBlankLines += 1
        elif (indent > lastIndent):
            if (numbered): xo.openElement('ol')
            elif (bulleted): xo.openElement('ul')
            else: xo.openElement('div')
            xo.openElement('li')
        elif (indent < lastIndent):
            if (numbered): xo.openElement('ol')
            elif (bulleted): xo.openElement('ul')
            else: xo.openElement('div')
            xo.closeElementIfOpen('li')
            if (xo.getCurrentElementName() in [ 'ul', 'ol', 'div' ]):
                xo.closeElement()
        else:  # non-blank, same indent
            pass

        xo.makeText(rec)

        # Make new line 'previous'
        lastIndent = indent
        if (not isBlank): nBlankLines = 0
        lastRec = rec

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
###############################################################################
# Main
#
if (__name__ == '_main_'):
    def processOptions():
        descr = """
=head1 Description

Convert simple text layouts to HTML.

=head2 Basic logic

    Anything with blank lines around it is a block.

   Should catch abutted but indented paras as breaks, too.

    The nominal indent of a block is than of its non-first lines (if any).
This is to avoid list-marker placement, and indented paragraphs

    Any block starting with a list-marker is a list item.

Unordered list markers (normally only one character)
    *  -  =  o  +
    \u2022 2023 2043 204c 204d 2219 25d8 25e6 2619 29be 29bf
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
        (maybe any punc + \d+ + punc?)

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


=head1 Related Commands

C<markdown2XML.py>, C<pod2html>,...

C<XmlOutput.py> (used for output generation).

=head1 Known bugs and Limitations

=head1 Licensing

Copyright 2018 by Steven J. DeRose. This script is licensed under a
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
            "--iencoding",        type=str, default='utf8',
            help='Assume utf-8 for input files.')
        parser.add_argument(
            "--quiet", "-q",      action='store_true',
            help='Suppress most messages.')
        parser.add_argument(
            "--tabs",        type=int, default='4',
            help='Tab interval. Default 4.')
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
