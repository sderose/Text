#!/usr/bin/env python
#
# annotsToHTML.py
# 2018-07-16: Written by Steven J. DeRose.
#
from __future__ import print_function
import sys
import os
import argparse
import re
import codecs

__metadata__ = {
    "title"        : "annotsToHTML.py",
    "description"  : "Get rid of IOBxyz notation.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2018-07-16",
    "modified"     : "2021-03-03",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]


descr = """
=Description=

Recode a sometimes-used but endlessly-variable NLP / text annotation convention
know by similarly-varying names starting or permuting "IOB" , to be viewable in
HTML in whatever browser. The input is expected to be faintly like:

    One token per line
    A space and status flag is appended to each line:
        B-XX goes on the *first* token of an instance of XX ("begin")
        I-XX goes on any additionals token of an instance of XX ("in")
        O goes on any tokens that aren't part of instances of XX at all ("out")
    Blank lines become paragraph breaks.

For example:
    The O
    Fulton B-NE
    County I=NE
    Grand I=NE
    Jury I=NE
    said O
    in O

becomes:

    <html>
    <head>
        <style>
            span  { color:red; }
        </style>
        <link rel="stylesheet" href="" />
    </head>
    <body>
    <p>The <span class="NE">Fulton County Grand Jury </span>said in
    </p>
    </body>
    </html>

The "XX" value from B-XX goes on the class attribute. You can edit the output
to add styles for different categories of annotations, or use the
I<--cssURL> option to generate a link to a stylesheet that does so.


=Related Commands=


=To do=

  Switch to use PowerWalk.py.


=History=

  2018-07-16: Written by Steven J. DeRose.
  2021-03-03: New layout.


=Options=
"""


###############################################################################
#
def processOptions():
    try:
        from BlockFormatter import BlockFormatter
        parser = argparse.ArgumentParser(
            description=descr, formatter_class=BlockFormatter)
    except ImportError:
        parser = argparse.ArgumentParser(description=descr)

    parser.add_argument(
        "--beginMark", type=str, metavar='S', default="B-",
        help='The string that indicates starts of annotation.')
    parser.add_argument(
        "--inMark", type=str, metavar='S', default="I-",
        help='The string that indicates continuing of annotation.')
    parser.add_argument(
        "--outMark", type=str, metavar='S', default="O",
        help='The string that indicates tokens not in an annotation.')

    parser.add_argument(
        "--classPrefix", type=str, metavar='S', default='',
        help='Prefix this to the class attribute on tagged spans.')
    parser.add_argument(
        "--cssURL", type=str, metavar='S', default='',
        help='URL to a CSS file to reference from the header.')
    parser.add_argument(
        "--iencoding", type=str, metavar='E', default="utf-8",
        help='Assume this character set for input files. Default: utf-8.')
    parser.add_argument(
        "--oencoding", type=str, metavar='E',
        help='Use this character set for output files.')
    parser.add_argument(
        "--recursive", action='store_true',
        help='Descend into subdirectories.')
    parser.add_argument(
        "--unicode",          action='store_const', dest='iencoding',
        const='utf8', help='Assume utf-8 for input files.')
    parser.add_argument(
        "--version", action='version', version=__version__,
        help='Display version information, then exit.')

    parser.add_argument(
        "files", type=str, nargs=argparse.REMAINDER,
        help='Path(s) to input file(s)')

    args0 = parser.parse_args()
    return(args0)


###############################################################################
#
def traverseFiles(path):
    if (not os.path.isdir(path)):
        fh = codecs.open(path, "rb", encoding=args.iencoding)
        doOneFile(path, fh)
        fh.close()
        return

    for root, dirs, files in os.walk(path):
        for f in files:
            fh = codecs.open(
                os.path.join(root, f), "rb", encoding=args.iencoding)
            doOneFile(path, fh)
            fh.close()
        if (args.recursive):
            for d in dirs:
                traverseFiles(os.path.join(root, d))
    return



###############################################################################
#
def doOneFile(path, fh):
    """Read and deal with one individual file.
    """
    recnum = 0
    rec = ""
    inPara = True
    inScope = None
    buf = """<html>
<head>
    <style>
        span  { color:red; }
    </style>
    <link rel="stylesheet" href="%s" />
</head>
<body>
<p>""" % (args.cssURL)

    while (True):
        rec = fh.readline()
        if (len(rec) == 0): break # EOF
        recnum += 1
        rec = rec.rstrip()
        tok = ''
        if (rec == ''):
            if (inPara): tok += "</p>"
            tok += "<p>"
        else:
            mat = re.search(r'\s(O|B-\w+|I-\w+)\s*$', rec)
            if (not mat):
                tok = rec
            else:
                m1 = mat.group(1)
                mainToken = rec[0: 0 - len(m1)]
                if (m1.startswith(args.beginMark)):
                    if (inScope): print("</span>")
                    tok += ('<span class="%s%s">%s' %
                        (args.classPrefix, m1[2:], mainToken))
                    inScope = True
                elif (m1.startswith(args.inMark)):
                    if (not inScope):
                        print("<b>inMark outside scope of beginMark</b>")
                    tok += mainToken
                elif (m1.startswith(args.outMark)):
                    data = mainToken
                    if (inScope):
                        tok += "</span>" + data
                        inScope = False
                    else:
                        tok += data

        if (len(buf) + len(tok) > 75):
            print(buf)
            buf = ""
        buf += tok

    print(buf)
    if (inScope): print("</span>")
    if (inPara): print("</p>")
    print("</body>\n</html>")
    fh.close()
    return(recnum)


###############################################################################
###############################################################################
# Main
#
args = processOptions()

if (len(args.files) == 0):
    print("No files specified....")
    sys.exit()
else:
    for fArg in (args.files):
        traverseFiles(fArg)
