#!/usr/bin/env python
#
# shortenContext.py: Trim long lines to just a limited around surrounding a
# given regex match.
#
# 2018-09-10: Written. Copyright by Steven J. DeRose.
# Creative Commons Attribution-Share-alike 3.0 unported license.
# See http://creativecommons.org/licenses/by-sa/3.0/.
#
# To do:
#
from __future__ import print_function
import sys, os
import argparse
import re
#import string
import codecs
import PowerWalk

from alogging import ALogger

__metadata__ = {
    'creator'      : "Steven J. DeRose",
    'cre_date'     : "2018-09-10",
    'language'     : "Python 2.7.6",
    'version_date' : "2018-09-10",
}
__version__ = __metadata__['version_date']

lg = ALogger(1)

def doOneFile(path, fh):
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
###############################################################################
# Main
#
if __name__ == "__main__":
    def processOptions():
        descr = """
=head1 Description

Trim long lines to just a limited around surrounding a
given regex match.

This is useful, for example, if you are getting C<grep> hits in files with
very long lines, and you want more than just the matched string, but less
then the entire lines.

=head1 Related Commands

C<grep>

=head1 Known bugs and Limitations

Unfinished....

=head1 Licensing

Copyright 2018-09-10 by Steven J. DeRose. This script is licensed under a
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
            "--color",  # Don't default. See below.
            help='Colorize the output.')
        parser.add_argument(
            "--iencoding",        type=str, metavar='E', default="utf-8",
            help='Assume this character set for input files. Default: utf-8.')
        parser.add_argument(
            "--ignoreCase", "-i", action='store_true',
            help='Disregard case distinctions.')
        parser.add_argument(
            "--maxLength",        type=int, metavar='N', default="79",
            help='Limit the returned length per match to this.')
        parser.add_argument(
            "--multi",            action='store_true',
            help='Show multiple hits per line.')
        parser.add_argument(
            "--oencoding",        type=str, metavar='E',
            help='Use this character set for output files.')
        parser.add_argument(
            "--quiet", "-q",      action='store_true',
            help='Suppress most messages.')
        parser.add_argument(
            "--regex", "-e",      type=str, metavar='R',
            help='Regex to identify the hits you want context for.')
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
        if (sys.stdin.isatty): lg.error("No files specified....")
        doOneFile("[STDIN]", sys.stdin)
    else:
        depth = 0
        pw = PowerWalk(args.files)
        pw.setOption('recursive', args.recursive)
        for path, fh in pw.traverse():
            if (fh == "DIR_END"):
                depth -= 1
                continue
            print("    " * depth + path)
            if (fh == "DIR_START"):
                depth += 1
                continue

            fileNum = pw.stats['itemsReturned']
            if (fileNum % args.tickInterval == 0):
                lg.vMsg(0, "At item #%d" % (fileNum))
            fh0 = codecs.open(fArg, "rb", encoding=args.iencoding)
            doOneFile(fArg, fh0)
            fh0.close()

    if (not args.quiet):
        lg.vMsg(0,"Done.")
        lg.showStats()
