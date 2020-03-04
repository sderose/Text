#!/usr/bin/env python
#
# findUnbalancedQuotes.py
#
from __future__ import print_function
import sys, os, argparse
import re
import codecs

from alogging import ALogger
from MarkupHelpFormatter import MarkupHelpFormatter

lg = ALogger()

PY3 = sys.version_info[0] == 3
if PY3:
    def unichr(n): return chr(n)

__metadata__ = {
    'title'        : "findUnbalancedQuotes.py",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2017-07-03",
    'modified'     : "2020-03-04",
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

Does not know to ignore comments in programming langauges.

Does not know about quoted quoted, or backslashing or doubling.

Does not know about multi-line quotes.

Does not know about Perl q/.../, Python ""..."", here documents, etc.

Could usefully add parenthesis balancing.

Add option to colorize the quotes or quoted portions?

=History=

2017-07-03: Written by Steven J. DeRose (port from bash script).

=To do=

* Really count ins and outs and types....

=Rights=

This program is Copyright 2017 by Steven J. DeRose.
It is hereby licensed under the Creative Commons
Attribution-Share-Alike 3.0 unported license.
For more information on this license, see L<here|"https://creativecommons.org">.

For the most recent version, see L<http://www.derose.net/steve/utilities/> or
L<http://github/com/sderose>.

=Options=
"""

# Quote-pairs
#
pairedQuotes = [
    [ 0x00AB,    # "LEFT-POINTING DOUBLE ANGLE QUOTATION MARK *",
      0x00BB ],  # "RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK *",

    [ 0x2018,    # "LEFT SINGLE QUOTATION MARK",
      0x2019 ],  # "RIGHT SINGLE QUOTATION MARK",

    [ 0x201A,    # SINGLE LOW-9 QUOTATION MARK",
      0x201B ],  # "SINGLE HIGH-REVERSED-9 QUOTATION MARK",

    [ 0x201C,    # "LEFT DOUBLE QUOTATION MARK",
      0x201D ],  # "RIGHT DOUBLE QUOTATION MARK",

    [ 0x201E,    # "DOUBLE LOW-9 QUOTATION MARK",
      0x201F ],  # "DOUBLE HIGH-REVERSED-9 QUOTATION MARK",

    [ 0x2039,    # "SINGLE LEFT-POINTING ANGLE QUOTATION MARK",
      0x203A ],  # "SINGLE RIGHT-POINTING ANGLE QUOTATION MARK",

    [ 0x2E02,    # "LEFT SUBSTITUTION BRACKET",
      0x2E03 ],  # "RIGHT SUBSTITUTION BRACKET",

    [ 0x2E04,    # "LEFT DOTTED SUBSTITUTION BRACKET",
      0x2E05 ],  # "RIGHT DOTTED SUBSTITUTION BRACKET",

    [ 0x2E09,    # "LEFT TRANSPOSITION BRACKET",
      0x2E0A ],  # "RIGHT TRANSPOSITION BRACKET",

    [ 0x2E0C,    # "LEFT RAISED OMISSION BRACKET",
      0x2E0D ],  # "RIGHT RAISED OMISSION BRACKET",

    [ 0x2E1C,    # "LEFT LOW PARAPHRASE BRACKET",
      0x2E1D ],  # "RIGHT LOW PARAPHRASE BRACKET",

    [ 0x2E20,    # "LEFT VERTICAL BAR WITH QUILL",
      0x2E21 ],  # "RIGHT VERTICAL BAR WITH QUILL",
]


###############################################################################
#
def processOptions():
    parser = argparse.ArgumentParser(
        description=descr, formatter_class=MarkupHelpFormatter)

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
    lg.setVerbose(args0.verbose)
    return(args0)


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

    recnum = 0
    rec = ""
    try:
        fh = codecs.open(path, mode='r', encoding=args.iencoding)
    except IOError as e:
        lg.error("Can't open '%s'." % (path), stat="CantOpen")
        return(0)
    while (True):
        try:
            rec = fh.readline()
        except IOError as e:
            lg.error("Error (%s) reading record %d of '%s'." %
                (type(e), recnum, path), stat="readError")
            break
        if (len(rec) == 0): break # EOF
        recnum += 1
        rec = rec.rstrip()
        if (re.match(r'\s*$',rec)):                    # Blank record
            continue
        ###
        # Per-record processing goes here
        ###
        n = countChar(rec, "'")
        if (n % 2):
            report(recnum, "Odd number of single quotes (%s)" % (n), rec)
        n = countChar(rec, '"')
        if (n % 2):
            report(recnum, "Odd number of double quotes (%s)" % (n), rec)
        n = countChar(rec, "`")
        if (n % 2):
            report(recnum, "Odd number of back quotes (%s)" % (n), rec)

        if (args.iencoding == 'utf8'):
            for pair in (pairedQuotes):
                nopen = countChar(rec, unichr(pair[0]))
                nclos = countChar(rec, unichr(pair[1]))
                if (nopen != nclos):
                    report(recnum, "Open/close counts mismatch", rec)
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
###############################################################################
# Main
#
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
