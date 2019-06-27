#!/usr/bin/env python
#
# pod2md.py
#
# 2019-02-19: Written. Copyright by Steven J. DeRose.
# Creative Commons Attribution-Share-alike 3.0 unported license.
# See http://creativecommons.org/licenses/by-sa/3.0/.
#
# To do:
#     Let --extract-to default to same name but .md?
#     Option for MediaWiki and/or HTML output?
#
from __future__ import print_function
import sys
import argparse
import re
#import string
#import math
#import subprocess
import codecs
import PowerWalk

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
if PY2:
    string_types = basestring
    import htmlentitydefs as entities
else:
    string_types = str
    from html import entities
    def cmp(a, b): return  ((a > b) - (a < b))
    def unichr(n): return chr(n)
    def unicode(s, encoding='utf-8', errors='strict'): return str(s, encoding, errors)

#from sjdUtils import sjdUtils
from alogging import ALogger

__metadata__ = {
    'creator'      : "Steven J. DeRose",
    'cre_date'     : "2019-02-19",
    'language'     : "Python 3.7",
    'version_date' : "2019-02-19",
}
__version__ = __metadata__['version_date']

#su = sjdUtils()
lg = ALogger(1)
xfh = None

###############################################################################
#
def doOneFile(path, fh):
    """Read and deal with one individual file.
    """
    recnum = 0
    rec = ""

    if (args.all): inPOD = True
    else: inPOD = False
    depth = 0

    while (True):
        try:
            rec = fh.readline()
        except IOError as e:
            lg.error("Error (%s) reading record %d of '%s'." %
                (type(e), recnum, path), stat="readError")
            break
        if (len(rec) == 0): break # EOF
        recnum += 1

        rec = rec.strip()
        if (rec.startswith("=pod")):
            inPOD = True
            continue
        if (rec.startswith("=cut")):
            inPOD = False
            continue
        if (not inPOD):
            continue
        if (rec.startswith("=encoding")):
            #encoding = rec[9:].strip()
            continue

        if (rec.startswith("=head")):
            hLevel = int(rec[5]) + 0
            rec = ("#" * hLevel) + rec[6:].strip() + ("#" * hLevel)
        elif (rec.startswith("=over")):
            rec = ""
            depth += 1
        elif (rec.startswith("=back")):
            rec = ""
            depth += 1
        elif (rec.startswith("=item")):
            rec = ("*" * depth) + rec[5].strip()

        # Regex below doesn't yet support I<<xxx>>, etc.
        rec = re.sub(r'\b(\w)<([^>]*)>', fixInline, rec)

        print(rec, end="")
        if (xfh): xfh.write(rec)

    return(recnum)


# Define what string to issue to open and close inline font changes, etc.
#
codeMap = {
    #POD    MD+      MD-    MWiki+  MWiki-  HTML
    'B': [ "''",    "''",   "**",   "**",   "b",   ],   # bold
    'I': [ "'''",   "'''",  "*",    "*",    "i",   ],   # italic
    # 'U': [ "",      "",     "__",   "__",   "u",   ],   # underscore

    'C': [ "`",     "`",    "",     "",   "tt",  ],  # command
    'F': [ "`",     "`",    "",     "",   "tt",  ],  # filename

    #'E': [ "''",    "''",   "",     "",   "",    ],   # special ch

    'L': [ "[",     "]",    "",     "",   "a",   ],   # link           ??
    'S': [ "''",    "''",   "",     "",   "", ],   # no-break       special?
    'X': [ "''",    "''",   "",     "",   "idx", ],   # index entry    ???
    'Z': [ "",      "",     "",     "",   "",    ],   # No POD
}

def fixInline(mat):
    # Can POD nest inlines, like I<foo B<bar>>?
    code = mat.group(1)
    txt = mat.group(2)
    if (code == "E"):
        return decodeSpecialChar(txt)
    elif (code in codeMap):
        return codeMap[code][0] + txt + codeMap[code][1]
    else:
        lg.eMsg(0, "Bad inline POD code '%s' with text '%s'." % (code, txt))
        txt = mat.group()
    return txt

def decodeSpecialChar(text):
    text = text.strip()
    if   (text == "lt"):     return "<"
    if (text == "gt"):     return ">"
    if (text == "verbar"): return "|"
    if (text == "sol"):    return "/"
    if (text.startswith("0x")):  return chr(int(text[2:], 16))
    if (text.startswith("0")):   return chr(int(text[1:], 8))
    if (re.match(r'\d+$',text)): return chr(int(text[1:], 10))

    #from html import entities
    try:
        c = unichr(entities.name2codepoint[text])
    except KeyError:
        lg.eMsg(0, "Unrecognied value '%s' for E<> code." % (text))
        c = "<E%s>" % (text)
    return c


###############################################################################
###############################################################################
# Main
#
if __name__ == "__main__":
    def processOptions():
        descr = """
=head1 Description

Convert perldoc-sylte "POD" markup, to MarkDown.

=head2

Block codes: line-initial =xxx
    headN
    pod
    cut
    over
    back
    item

Inline codes:  X<text>, X<<text>>, etc.

    B<(.*?)>' bold
    C<(.*?)>' command
    E<(.*?)>' special characters
    F<(.*?)>' filename
    I<(.*?)>' italic
    L<(.*?)>' link
    S<(.*?)>' no-break
    X<(.*?)>' index entry
    Z<(.*?)>' No POD


=head1 Related Commands

=head1 Known bugs and Limitations

=head1 Licensing

Copyright 2019-02-19 by Steven J. DeRose. This script is licensed under a
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
            "--all",              action='store_true',
            help='Include whole file instead of scanning for =pod to start.')
        parser.add_argument(
            "--extract-to",       type=str, metavar='F', default="", dest="extract",
            help='Suppress most messages.')
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
        if (args0.verbose): lg.setVerbose(args0.verbose)
        return(args0)

    ###########################################################################
    #
    args = processOptions()

    if (args.extract):
        xfh = codecs.open(args.extract, "wb", encoding=args.oencoding)

    if (len(args.files) == 0):
        lg.error("No files specified....")
        doOneFile("[STDIN]", sys.stdin)
    else:
        fdepth = 0
        pw = PowerWalk.PowerWalk(args.files)
        pw.setOption('recursive', False)
        for path0, fh0 in pw.traverse():
            if (fh0 == "DIR_END"):
                fdepth -= 1
                continue
            print("    " * fdepth + path0)
            if (fh0 == "DIR_START"):
                fdepth += 1
                continue

            fileNum = pw.stats['itemsReturned']
            fh0 = codecs.open(path0, "rb", encoding=args.iencoding)
            doOneFile(path0, fh0)
            fh0.close()

    if (xfh): xfh.close()

    if (not args.quiet):
        lg.vMsg(0,"Done.")
        lg.showStats()
