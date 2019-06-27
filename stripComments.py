#!/usr/bin/env python
#
# stripComments.py
#
# 2017-11-08: Written. Copyright by Steven J. DeRose.
# Creative Commons Attribution-Share-alike 3.0 unported license.
# See http://creativecommons.org/licenses/by-sa/3.0/.
#
# To do:
#
from __future__ import print_function
import sys, os, argparse
import re
#import string
#import math
from subprocess import check_output
import codecs
from collections import namedtuple

#import pudb
#pudb.set_trace()

from sjdUtils import sjdUtils
from MarkupHelpFormatter import MarkupHelpFormatter

global args, su, lg
args = su = lg = None

__version__ = "2017-11-08"
__metadata__ = {
    'creator'      : "Steven J. DeRose",
    'cre_date'     : "2017-11-08",
    'language'     : "Python 2.7.6",
    'version_date' : "2017-11-08",
    'src_date'     : "$LastChangedDate$",
    'src_version'  : "$Revision$",
}

DelimSet = namedtuple('DelimSet', [ 'oneLine', 'start', 'end' ])

###############################################################################
#
def processOptions():
    global args, su, lg
    parser = argparse.ArgumentParser(
        description="""

=head1 Description

Remove comments from the file, depending on the file's type.

Type is judged by file extension (see I<--ext> to choose an extension
to assume for files lacking one).

This knows about several common languages, but is based on regular expressions,
and is not smart enough
to allow for cases like comment-delimiters inside of quotes, etc.

=head1 Related Commands

For C, C++, and their kin, you might try:
    gcc -fpreprocessed -dD -E myFile.c

See L<https://stackoverflow.com/questions/2394017>.

=head1 Known bugs and Limitations

Do not pipe data in, because then we don't know its extension,
so cannot determine the right comment delimiters to look for.

It should try 'file' or similar to sniff. But it doesn't.

This doesn't use a real parser, so is totally confused by comment
delimiters that occur in special places. For example:

=over

=item * Comment start obviated by one-liner:  // hello /*

=item * Quoted comment delimiters:  $ = "//eh?"

=item * The C preprocessor:   #ifdef 0... /*... #endif

=item * XML, HTML, etc. support doesn't handle '--' inside comments,
comments inside processing instructions, CDATA marked sections, etc.

=item * Python conventional comment at start of functions

=back

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
        "--compact", "-c",    action='store_true',
        help='Suppress blank lines.')
    parser.add_argument(
        "--extension",        type=str, default='py',
        help='Choose the default extension to assume for files without one.')
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
# Could add:
#   asp aspx java jsp rb json cgi r bat csh ksh vb vbe vbs scpt
# 
def getDelimiters(ext):
    ext = ext.strip('.')
    if   (ext in [ 'c', 'php', 'php3', 'php4', 'js',
                   'css', 'sass', 'scss', 'less', 'pcss', ]):
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
        lg.eMsg(0, "Unsupported extension '%s'." % (ext))
        
        ds = DelimSet('#',  None, None)
    return ds


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
        fh = codecs.open(path, mode='r', encoding=args.iencoding)
    except IOError as e:
        lg.error("Can't open '%s'." % (path), stat="CantOpen")
        return(0)
    lg.bumpStat("totalFiles")

    root, ext = os.path.splitext(path)
    if (not ext):
        fileSniff = check_output([ 'file', path ])
        lg.eMsg(0, "No extension. 'file' says: %s" % (fileSniff))
        ext = args.extension
    ds = getDelimiters(ext)
    try:
        data = fh.read()
    except IOError as e:
        lg.error("Error (%s) reading file '%s'." %
                 (type(e), path), stat="readError")
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
