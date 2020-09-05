#!/usr/bin/env python
#
# pod2md.py: Convert perldoc-tsyle "POD" markup, to MarkDown.
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

#from sjdUtils import sjdUtils
from alogging import ALogger

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

__metadata__ = {
    'title'        : "pod2md.py",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2019-02-19",
    'modified'     : "2020-01-02",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']

descr = """
=Description=

pod2md.py: Convert perldoc-tsyle "POD" markup (not including the more
complex POD 6 version), to MarkDown (mostly of the MediaWiki flavor).

==POD Summary==

POD is mostly for Perl Documenttion. See
[https://docs.perl6.org/language/pod].

===Line-level (must start at start of line)===
    =pod     Start POD when embedded in Perl
    =cut     En POD
    =head1   First-level heading
    ...
    =over    Indent one list level / start list
    =back    End list
    =item

===Inline===

    B<(.*?)>' bold
    C<(.*?)>' command
    E<(.*?)>' special characters
    F<(.*?)>' filename
    I<(.*?)>' italic
    L<(.*?)>' link
    S<(.*?)>' no-break
    X<(.*?)>' index entry
    Z<(.*?)>' No POD

==Markdown summary==

===Line-level (must start at start of line)===

    =heading1=
    ==heading2==
    ...

    ||cell|cell|cell...
    ---- [horizontal rule]

    * First-level bulleted list item
    # First-level numbered list item
    ** Second-level bulleted list item
    ...

    :term;definition text
        indented text

===Inline===

   '''bold'''
   ''italic''
   [general link]
   [[internal link]]
   ISBN xxxxxxxxxx, RFC dddd
   {{macro/include}}

=Similar regex changes=

Markdown isn't entirely standardized, so this is just one set of options....
Some variants use "#" in place of "=" for headings.

These regexes don't do anything to accumulate multiple levels of `=over` and
`=back` for nested lists, and don't do anything for inline S, X, or Z.

    s/^=head1 (.*)/=\\1=/
    s/^=head2 (.*)/==\\1==/
    s/^=head3 (.*)/===\\1===/
    s/^=head4 (.*)/====\\1====/
    s/^=head5 (.*)/=====\\1=====/
    s/^=head6 (.*)/======\\1======/

    s/^=(over|back|pod|cut *//
    s/^=item B<\\*?>/\\* /
    s/^=item B<\\d+>/\\# /
    s/^=item /:/    /

    s/B<(.*?)>/'''\1'''/
    s/C<(.*?)>/`\1`/
    s/E<(.*?)>/&\1;/
    s/F<(.*?)>/`\1`/
    s/I<(.*?)>/''\1''/
    s/L<(.*?)>/[\1]/

You can put these changes into a file and apply them all with my
`globalChange` script.

=head1 Known bugs and limitations

=Related Commands=

=References=

* [https://www.mediawiki.org/wiki/Markup_spec] -- Obsolete, but one of
relatively few sites that enumerate MediaWiki markup constructs.
* [https://en.wikipedia.org/wiki/MediaWiki#Markup] -- MediaWiki or Markdown Extra
* [https://en.wikipedia.org/wiki/Markdown#Standardization]
* [https://tools.ietf.org/html/rfc7763] -- text/markdown media type
* [https://tools.ietf.org/html/rfc7764] -- Guidance on Markdown
* []

=History=

* 2019-02-19: Written. Copyright by Steven J. DeRose.
* Creative Commons Attribution-Share-alike 3.0 unported license.
* See http://creativecommons.org/licenses/by-sa/3.0/.
* 2020-01-02: Clean up.

=To do=

* Let --extract-to default to same name but .md?
* Option for MediaWiki and/or HTML output?

=Rights=

Copyright 2019 by Steven J. DeRose. This script is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See http://creativecommons.org/licenses/by-sa/3.0/ for more information.

For the most recent version, see L<http://www.derose.net/steve/utilities/>
or L<http://github.com/sderose>.

=Options=
"""

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
        lg.eMsg(0, "Unrecognized value '%s' for E<> code." % (text))
        c = "<E%s>" % (text)
    return c


###############################################################################
###############################################################################
# Main
#
if __name__ == "__main__":
    def processOptions():
        try:
            from BlockFormatter import BlockFormatter
            parser = argparse.ArgumentParser(
                description=descr, formatter_class=BlockFormatter)
        except ImportError:
            parser = argparse.ArgumentParser(description=descr)

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
