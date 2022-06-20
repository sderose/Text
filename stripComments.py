#!/usr/bin/env python3
#
# stripComments.py: Remove comments from a file, appropriate to its filetype.
# 2017-11-08: Written by Steven J. DeRose.
#
from __future__ import print_function
import sys
import os
import argparse
import re
import codecs
from subprocess import check_output
from collections import namedtuple

from alogging import ALogger
lg = ALogger(1)

__metadata__ = {
    'title'        : "stripComments",
    'description'  : "Remove comments from a file, appropriate to its filetype.",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2017-11-08",
    'modified'     : "2020-08-23",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']

descr = """
=Description=

Remove comments from the file, depending on the file's type.

Type is judged by file extension (see I<--ext> to choose an extension
to assume for files lacking one).

This knows about several common languages, but is based on regular expressions,
and is not smart enough
to allow for cases like comment-delimiters inside of quotes, etc.


=Related Commands=

For C, C++, and their kin, you might try:
    gcc -fpreprocessed -dD -E myFile.c

See [https://stackoverflow.com/questions/2394017].


=Known bugs and Limitations=

Do not pipe data in, because then we don't know its extension,
so cannot determine the right comment delimiters to look for.

It should try 'file' or similar to sniff. But it doesn't.

This doesn't use a real parser, so is totally confused by comment
delimiters that occur in special places. For example:

* Comment start obviated by one-liner:  // hello /*
* Quoted comment delimiters:  $ = "//eh?"
* The C preprocessor:   #ifdef 0... /*... #endif
* XML, HTML, etc. support doesn't handle '--' inside comments,
comments inside processing instructions, CDATA marked sections, etc.
* Python conventional comment at start of functions


=Licensing=

Copyright 2015 by Steven J. DeRose. This script is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See [http://creativecommons.org/licenses/by-sa/3.0/] for more information.


=Options=
"""


DelimSet = namedtuple('DelimSet', [ 'oneLine', 'start', 'end' ])

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
        "--color", # Don't default. See below.
        help='Colorize the output.')
    parser.add_argument(
        "--compact", "-c", action='store_true',
        help='Suppress blank lines.')
    parser.add_argument(
        "--extension", type=str, default='py',
        help='Choose the default extension to assume for files without one.')
    parser.add_argument(
        "--iencoding", type=str, metavar='E', default="utf-8",
        help='Assume this character set for input files. Default: utf-8.')
    parser.add_argument(
        "--oencoding", type=str, metavar='E',
        help='Use this character set for output files.')
    parser.add_argument(
        "--quiet", "-q", action='store_true',
        help='Suppress most messages.')
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
        "files", type=str, nargs=argparse.REMAINDER,
        help='Path(s) to input file(s)')

    args0 = parser.parse_args()
    lg.setVerbose(args0.verbose)
    if (args0.color is None):
        args0.color = ("CLI_COLOR" in os.environ and sys.stderr.isatty())
    lg.setColors(args0.color)
    return(args0)


###############################################################################
# Could add:
#   asp aspx java jsp rb json cgi r bat csh ksh vb vbe vbs scpt
#
def getDelimiters(ext):
    ext = ext.strip('.')
    if (ext in [ 'c', 'php', 'php3', 'php4', 'js', 'css', 'sass', 'scss', 'less', 'pcss', ]):
        ds = DelimSet('//', '/\\*', '\\*/')
    elif (ext in [ 'py', 'pl', 'sh' ]):
        ds = DelimSet('#',  None, None)
    elif (ext in [ 'html', 'htm', 'xml', 'xhtml', 'xhtml',
                   'xsl', 'xslt', 'svg', 'thml', 'rss', 'atom', ]):
        ds = DelimSet(None, '<!--', '-->')  # FIX REGEX FOR THIS
    elif (ext in [ 'el' ]):
        ds = DelimSet(';;', None, None)
    elif (ext in [ 'sql' ]):
        ds = DelimSet('--\\s', None, None)
    else:
        lg.error("Unsupported extension '%s'." % (ext))

        ds = DelimSet('#',  None, None)
    return ds


###############################################################################
#
def tryOneItem(path):
    """Try to open a file (or directory, if -r is set).
    """
    lg.info1("====Starting item '%s'" % (path))
    recnum = 0
    if (not os.path.exists(path)):
        lg.error("Couldn't find '%s'." % (path))
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
        fh = codecs.open(path, mode='r', encoding=args.iencoding)
    except IOError:
        lg.error("Can't open '%s'." % (path))
        return(0)
    lg.bumpStat("totalFiles")

    _root, ext = os.path.splitext(path)
    if (not ext):
        fileSniff = check_output([ 'file', path ])
        lg.error("No extension. 'file' says: %s" % (fileSniff))
        ext = args.extension
    ds = getDelimiters(ext)
    try:
        data = fh.read()
    except IOError as e:
        lg.error("Error (%s) reading file '%s'." % (type(e), path))
        return

    # This utterly fails for comment delims inside quotes, ifdefs, etc.
    # Could slightly improve via look-ahead/behind, but short of a complete
    # parse of the applicable language, forget it.
    #
    if (ds.oneLine):
        expr = ds.oneLine + r'.*?$'
        lg.vMsg(1, "oneLine expr: " + expr)
        data = re.sub(expr, ' ', data, 0, re.MULTILINE)  # re.DOTALL?
    if (ds.start):
        expr = ds.start + r'([^*]|\*[^/])*?' + ds.end
        lg.vMsg(1, "multi-line expr: " + expr)
        data = re.sub(expr, ' ', data, 0, re.MULTILINE)
    if (args.compact):
        data = re.sub(r'\n([ \t]*\n)+', "\n", data, 0, re.MULTILINE)

    print(data)
    fh.close()
    return


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
