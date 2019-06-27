#!/usr/bin/env python
#
# findUnbalancedQuotes.py
#
# 2017-07-03: Written. Copyright by Steven J. DeRose (port from bash script).
# Creative Commons Attribution-Share-alike 3.0 unported license.
# See http://creativecommons.org/licenses/by-sa/3.0/.
#
# To do:
#     Really count ins and outs and types....
#
from __future__ import print_function
import sys, os, argparse
import re
#import string
#import math
#import subprocess
import codecs

#import pudb
#pudb.set_trace()

from sjdUtils import sjdUtils
from MarkupHelpFormatter import MarkupHelpFormatter

global args, su, lg

__version__ = "2017-07-03"
__metadata__ = {
    'creator'      : "Steven J. DeRose",
    'cre_date'     : "2017-07-03",
    'language'     : "Python 2.7.6",
    'version_date' : "2017-07-03",
}

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
    global args, su, lg
    parser = argparse.ArgumentParser(
        description="""

=head1 Description

Scan for lines with imbalanced quotes.

This script does not know about particular programming or other languages,
so does not (yet) deal with cases such as quotes backslashed within quotes,
multi-line quotations, here documents, etc.

With I<--unicode>, checks for various curly quote pairs, though not perfectly.


=head1 Related Commands

=head1 Known bugs and Limitations

Does not know to ignore comments in programming langauges.

Does not know about quoted quoted, or backslashing or doubling.

Does not know about multi-line quotes.

Does not know about Perl q/.../, Python ""..."", here documents, etc.

Could usefully add parenthesis balancing.

Should add option to colorize the quotes or quoted portions.


=head1 Licensing

Copyright 2015 by Steven J. DeRose. This script is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See http://creativecommons.org/licenses/by-sa/3.0/ for more information.

=head1 Options
        """,
        formatter_class=MarkupHelpFormatter
    )
    parser.add_argument(
        "--color",  # Don't default. See below.
        help='Colorize the output.')
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
    su = sjdUtils()
    lg = su.getLogger()
    lg.setVerbose(args0.verbose)
    if (args0.color == None):
        args0.color = ("USE_COLOR" in os.environ and sys.stderr.isatty())
    su.setColors(args0.color)
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
    except:
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
        except Exception as e:
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
            for pair in (quotePairs):
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
