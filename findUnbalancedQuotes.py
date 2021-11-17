#!/usr/bin/env python
#
# findUnbalancedQuotes.py: Report lines with odd quotation or indentation patterns.
# 2017-07-03: Written by Steven J. DeRose.
#
import sys
import os
import re
import codecs

from alogging import ALogger
lg = ALogger()

__metadata__ = {
    "title"        : "findUnbalancedQuotes.py",
    "description"  : "Report lines with odd quotation or indentation patterns.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2017-07-03",
    "modified"     : "2020-10-01",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/",
}
__version__ = __metadata__["modified"]


descr = """
=Description=

Scan for lines with imbalanced quotes, and optionally for suspicious indentation.
This is mainly useful for tracking down where an imbalance originated, for programming
language implementations that are not kind enough to direct you to the location of
things like the last unmatched "{", a line with only one '"', etc.

This script knows little about particular programming or other languages,
so does not (yet) deal with cases such as quotes backslashed within quotes,
multi-line quotations, here documents, etc.

  With ''--unicode'', checks for various curly quote pairs, though not perfectly.
  With ''--contractions', ignores likely natural-languages contraction apostrophes.
  With ''--perl'', also reports things like "if...{ [...code...]" with no "}",
and indentation changes without a brace or command ending the previous line.
  With ''--triple'', suppresses reporting of triple-quotes a la Python.
  With ''--parens'', also reports lines with mismatched () [] {}.
  

=Related Commands=

pylint, tidy, Perl::Tidy, etc.


=Known bugs and Limitations=

* --perl reports potential problems when the indentation increases but the previous
line didn't end with '{', or the indentation decreases but the previous
line didn't end with '}' or ','.  This covers a lot of common cases, but will report
a number of false positives, such as continuation lines that didn't break at a comma.
Still, it seems more useful in this application, to over-report than under.
Oh, the '--perl' option only (so far) adds indentation and brace checks, so can be
used for other languages with similar syntax.
* Does not know to ignore comments in programming langauges (but see ''--comment'').
* Does not know about quoted quotes, or full backslashing (though ''--escaped''
handles simple cases) or doubling.
* Does not know about multi-line quotes.
* Does not know about Perl q/.../, Python ""..."", shell "here" documents, etc.


=To do=

* Colorize the quotes or quoted portions?
* Really count indentation vs. open/close.
* Parenthesis balancing should have a way to not consider program-structure {}.


=History=

2017-07-03: Written by Steven J. DeRose (port from bash script).
2020-04-21: Start indentation-tracking.
2021-07-13: Add --contractions and --escaped options, `origiRec` for accurate reporting.
2021-08-06: Add experimental --perl to find one-line 'if's that don't close.
2021-09-10: Handle tab expansion. Add --comment, --tabStops.
2020-10-01: Make --perl check indentation changes against end of preceding line.


=Rights=

Copyright 2017 by Steven J. DeRose.
This program is hereby licensed under the Creative Commons
Attribution-Share-Alike 3.0 unported license.
For more information on this license, see [here|"https://creativecommons.org"].

For the most recent version, see [http://www.derose.net/steve/utilities] or
[http://github/com/sderose].


=Options=
"""

# Quote-pairs
#
pairedQuotes = [
    [ "\u00AB",    # "LEFT-POINTING DOUBLE ANGLE QUOTATION MARK *",
      "\u00BB" ],  # "RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK *",

    [ "\u2018",    # "LEFT SINGLE QUOTATION MARK",
      "\u2019" ],  # "RIGHT SINGLE QUOTATION MARK",

    [ "\u201A",    # SINGLE LOW-9 QUOTATION MARK",
      "\u201B" ],  # "SINGLE HIGH-REVERSED-9 QUOTATION MARK",

    [ "\u201C",    # "LEFT DOUBLE QUOTATION MARK",
      "\u201D" ],  # "RIGHT DOUBLE QUOTATION MARK",

    [ "\u201E",    # "DOUBLE LOW-9 QUOTATION MARK",
      "\u201F" ],  # "DOUBLE HIGH-REVERSED-9 QUOTATION MARK",

    [ "\u2039",    # "SINGLE LEFT-POINTING ANGLE QUOTATION MARK",
      "\u203A" ],  # "SINGLE RIGHT-POINTING ANGLE QUOTATION MARK",

    [ "\u2E02",    # "LEFT SUBSTITUTION BRACKET",
      "\u2E03" ],  # "RIGHT SUBSTITUTION BRACKET",

    [ "\u2E04",    # "LEFT DOTTED SUBSTITUTION BRACKET",
      "\u2E05" ],  # "RIGHT DOTTED SUBSTITUTION BRACKET",

    [ "\u2E09",    # "LEFT TRANSPOSITION BRACKET",
      "\u2E0A" ],  # "RIGHT TRANSPOSITION BRACKET",

    [ "\u2E0C",    # "LEFT RAISED OMISSION BRACKET",
      "\u2E0D" ],  # "RIGHT RAISED OMISSION BRACKET",

    [ "\u2E1C",    # "LEFT LOW PARAPHRASE BRACKET",
      "\u2E1D" ],  # "RIGHT LOW PARAPHRASE BRACKET",

    [ "\u2E20",    # "LEFT VERTICAL BAR WITH QUILL",
      "\u2E21" ],  # "RIGHT VERTICAL BAR WITH QUILL",
]

allQuoteChars = "'\"`'"
for pq in pairedQuotes:
    allQuoteChars += pq[0] + pq[1]
escapedExpr = re.compile(r"""\\[%s]""" % (allQuoteChars))


###############################################################################
#
def tryOneItem(path):
    """Try to open a file (or directory, if -r is set).
    """
    lg.hMsg(1, "Starting item '%s'" % (path))
    recnum = 0
    if (not os.path.exists(path)):
        lg.error("Couldn't find '%s'." % (path), stat="cantOpen")
    elif (os.path.isdir(path)):
        lg.bumpStat("totalDirs")
        if (args.recursive):
            for child in os.listdir(path):
                recnum += tryOneItem(os.path.join(path,child))
        else:
            lg.vMsg(0, "Skipping directory '%s'." % (path))
    else:
        doOneFile(path)
    return(recnum)


###############################################################################
#
def doOneFile(path):
    """Read and deal with one individual file.
    """
    try:
        fh = open(path, mode="r")  # binary
    except IOError:
        lg.error("Couldn't open '%s'." % (path), stat="cantOpen")
        return(0)
    lg.bumpStat("totalFiles")

    try:
        fh = codecs.open(path, mode="r", encoding=args.iencoding)
    except IOError:
        lg.error("Can't open '%s'." % (path), stat="CantOpen")
        return(0)
    recnum = 0
    lastRealRec = rec = ""
    indentStack = [ 0 ]
    while (True):
        try:
            rec = fh.readline()
        except IOError as e:
            lg.error("Error (%s) reading record %d of '%s'." %
                (type(e), recnum, path), stat="readError")
            break
        origRec = rec
        if (len(rec) == 0): break # EOF
        recnum += 1
        rec = rec.rstrip()
        if (re.match(r"\s*$",rec)):                                     # Blank record
            continue
        if (args.comment and rec.lstrip().startswith(args.comment)):    # Comment
            continue
        newIndent = getIndentColumn(rec)                                # Indentation
        if (newIndent != indentStack[-1]):
            if (newIndent < indentStack[-1]):
                if (newIndent not in indentStack):
                    if (args.indents): report(
                        recnum, "Indent decreasing from %d to %d, not on stack %s." %
                        (indentStack[-1], newIndent, indentStack), rec)
                while (indentStack[-1] > newIndent):
                    indentStack.pop()
            if (args.perl):  # TODO: enable for C, Java, etc. too
                if (newIndent < indentStack[-1]):
                    if (not re.search(r"}\s*(#.*)?$", lastRealRec)):
                        report(recnum, "Indent decreasing but prev line does not end in '}'.", rec)
                if (newIndent > indentStack[-1]):
                    # TODO: Following check gets some false positives....
                    if (not re.search(r"[{,]\s*(#.*)?$", lastRealRec)):
                        report(recnum, "Indent increasing but prev line does not end in [{,].", rec)
            
        if (newIndent > indentStack[-1]):
            indentStack.append(newIndent)

        ###
        # Per-record processing goes here
        ###
        if (args.triplesok):
            rec = re.sub(r'"""', '', rec)
        if (args.singlesok):
            rec = re.sub(r"""('"'|"'"|'`'|"`")""", "", rec)
        if (args.contractions):
            rec = re.sub(r"""\w['‘]\w""", "", rec)
        if (args.escaped):
            rec = re.sub(escapedExpr, "", rec)

        n = countChar(rec, "'")
        if (n % 2):
            report(recnum, "Odd number of straight single quotes (%s)" % (n), origRec)
        n = countChar(rec, '"')
        if (n % 2):
            report(recnum, "Odd number of straight double quotes (%s)" % (n), origRec)
        n = countChar(rec, "`")
        if (n % 2):
            report(recnum, "Odd number of plain back quotes (%s)" % (n), origRec)

        if (args.iencoding == "utf8"):
            for pair in (pairedQuotes):
                nopen = countChar(rec, pair[0])
                nclos = countChar(rec, pair[1])
                if (nopen != nclos):
                    report(recnum, "Open/close counts mismatch", origRec)
        if (args.perl and re.search(r"\bif.*{.*;[^\s}]*$", rec)):
            report(recnum, "Perl-like 'if' then '{' then code, but no '}'.", origRec)
        elif (args.parentheses):
            msg = checkParens(origRec)
            if (msg): report(recnum, msg, origRec)
        
        lastRealRec = rec
        
    fh.close()
    return(recnum)

def getIndentColumn(s):
    s = s.expandtabs(args.tabStops)
    s = re.sub(r"\S.*$", "", s)
    return len(s)
    
# Count how many times the character "c" occurs in "s".
#
def countChar(s, c):
    s2 = re.sub("[^" + c + "]+", "", s)
    return len(s2)

def report(recnum, msg, rec):
    print("%6d: %s\n    %s" % (recnum, msg, rec))

def checkParens(s:str) -> str:
    """Check balance of parentheses, brackets, and braces.
    Does not yet worry about escaped or quoted ones, or groups that span lines.
    @return An error message, or None.
    """
    pStack = []
    for i, c in enumerate(s):
        if (c in "([{"):
            pStack.append(c)
        elif (c in ")]}"):
            if (not pStack or pStack[-1] != c):
                return "Expecting '%s' but found '%s' at column %d" % (pStack[-1], c, i)
            pStack.pop()
    if (pStack):
        return "Unclosed: %s" % (str(pStack))
    return None
    
        
###############################################################################
# Main
#
def processOptions():
    import argparse
    
    try:
        from BlockFormatter import BlockFormatter
        parser = argparse.ArgumentParser(
            description=descr, formatter_class=BlockFormatter)
    except ImportError:
        parser = argparse.ArgumentParser(description=descr)

    parser.add_argument(
        "--comment", type=str, default="",
        help="Ignore lines starting with (optional whitespace plus) this.")
    parser.add_argument(
        "--contractions", action="store_true",
        help='Discard apostrophes and right singlequotes within words, like "can\t".')
    parser.add_argument(
        "--escaped", action="store_true",
        help='Discard quotes wafter non-doubled backslash like "see \\\" and \\\'.".')
    parser.add_argument(
        "--iencoding", type=str, metavar="E", default="utf-8",
        help="Assume this character set for input files. Default: utf-8.")
    parser.add_argument(
        "--indents", action="store_true",
        help="Also report indentation decreases not to stacked columns.")
    parser.add_argument(
        "--oencoding", type=str, metavar="E",
        help="Use this character set for output files.")
    parser.add_argument(
        "--parentheses", "--parens", action="store_true",
        help="Also look for unbalanced () [] {}.")
    parser.add_argument(
        "--perl", action="store_true",
        help="Also look for Perl-ish if.*{.*;[^\\s}]*$, and for indent changes not after [{},]."
        " This gets some false positives.")
    parser.add_argument(
        "--quiet", "-q", action="store_true",
        help="Suppress most messages.")
    parser.add_argument(
        "--singlesok", action="store_true",
        help='Discard quotes that are alone inside others, like: "\'".')
    parser.add_argument(
        "--tabStops", type=int, default=4,
        help="Tab interval for calculating indentation.")
    parser.add_argument(
        "--triplesok", action="store_true",
        help="Do not report cases of 3 double-quotes in a row, like Python multi-line quotes.")
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
        "files", type=str, nargs=argparse.REMAINDER,
        help="Path(s) to input file(s)")

    args0 = parser.parse_args()
    lg.setVerbose(args0.verbose)
    return(args0)


args = processOptions()

if (len(args.files) == 0):
    lg.error("No files specified....")
    sys.exit()

for f in (args.files):
    lg.bumpStat("totalFiles")
    recs = doOneFile(f)
    lg.bumpStat("totalRecords", amount=recs)

if (not args.quiet):
    lg.vMsg(0,"Done.")
    lg.showStats()
