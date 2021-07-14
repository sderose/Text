#!/usr/bin/env python
#
# findUnbalancedQuotes.py: Report lines with odd quotation patterns.
# 2017-07-03: Written by Steven J. DeRose.
#
import sys, os, argparse
import re
import codecs

from alogging import ALogger
lg = ALogger()

__metadata__ = {
    'title'        : "findUnbalancedQuotes.py",
    "description"  : "Report lines with odd quotation patterns.",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2017-07-03",
    'modified'     : "2020-04-21",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/",
}
__version__ = __metadata__['modified']


descr = """
=Description=

Scan for lines with imbalanced quotes.

This script does not know about particular programming or other languages,
so does not (yet) deal with cases such as quotes backslashed within quotes,
multi-line quotations, here documents, etc.

With ''--unicode'', checks for various curly quote pairs, though not perfectly.


=Related Commands=


=Known bugs and Limitations=

* Does not know to ignore comments in programming langauges.
* Does not know about quoted quotes, or full backslashing (though ``--escaped`
handles simple cases) or doubling.
* Does not know about multi-line quotes.
* Does not know about Perl q/.../, Python ""..."", shell here documents, etc.


=To do=

* Colorize the quotes or quoted portions?
* Really count ins and outs and types (perhaps not worth it)
* Track {} brace vs. indentation, at least when braces are line-final.
Add expandTabs for that.
* Parenthesis balancing.


=History=

2017-07-03: Written by Steven J. DeRose (port from bash script).
2020-04-21: Start indentation-tracking.
2021-07-13: Add --contractions and --escaped options,
 `origiRec` for accurate reporting.


=Rights=

This program is Copyright 2017 by Steven J. DeRose.
It is hereby licensed under the Creative Commons
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
        fh = codecs.open(path, mode='r', encoding=args.iencoding)
    except IOError as e:
        lg.error("Can't open '%s'." % (path), stat="CantOpen")
        return(0)
    recnum = 0
    rec = ""
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
        if (re.match(r'\s*$',rec)):                    # Blank record
            continue

        newIndent = len(rec) - len(rec.lstrip())       # Not happy w/ tabs.
        if (newIndent < indentStack[-1]):
            if (newIndent not in indentStack):
                if (args.indents): report(
                    recnum, "Indent decreasing from %d to %d, not on stack %s." %
                    (indentStack[-1], newIndent, indentStack), rec)
            while (indentStack[-1] > newIndent):
                indentStack.pop()
        if (newIndent > indentStack[-1]):
            indentStack.append(newIndent)

        ###
        # Per-record processing goes here
        ###
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

        if (args.iencoding == 'utf8'):
            for pair in (pairedQuotes):
                nopen = countChar(rec, pair[0])
                nclos = countChar(rec, pair[1])
                if (nopen != nclos):
                    report(recnum, "Open/close counts mismatch", origRec)
    fh.close()
    return(recnum)

# Count how many times the character 'c' occurs in 's'.
#
def countChar(s, c):
    s2 = re.sub('[^' + c + ']+', '', s)
    return len(s2)

def report(recnum, msg, rec):
    print("%6d: %s\n    %s" % (recnum, msg, rec))


###############################################################################
# Main
#
def processOptions():
    try:
        from BlockFormatter import BlockFormatter
        parser = argparse.ArgumentParser(
            description=descr, formatter_class=BlockFormatter)
    except ImportError:
        parser = argparse.ArgumentParser(description=descr)

    parser.add_argument(
        "--contractions", action='store_true',
        help='Discard apostrophes and right singlequotes within words, like "can\t".')
    parser.add_argument(
        "--escaped", action='store_true',
        help='Discard quotes wafter non-doubled backslash like "see \\\" and \\\'.".')
    parser.add_argument(
        "--iencoding", type=str, metavar='E', default="utf-8",
        help='Assume this character set for input files. Default: utf-8.')
    parser.add_argument(
        "--indents", action='store_true',
        help='Also report indentation decreases not to stacked columns.')
    parser.add_argument(
        "--oencoding", type=str, metavar='E',
        help='Use this character set for output files.')
    parser.add_argument(
        "--quiet", "-q", action='store_true',
        help='Suppress most messages.')
    parser.add_argument(
        "--singlesok", action='store_true',
        help='Discard quotes that are alone inside others, like: "\'".')
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
        'files', type=str, nargs=argparse.REMAINDER,
        help='Path(s) to input file(s)')

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
