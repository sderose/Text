#!/usr/bin/env python
#
# pod2md.py: Convert perldoc-style POD markup to MarkDown-ish.
# Written 2019-02-19 by Steven J. DeRose.
#
from __future__ import print_function
import sys
import argparse
import re
import codecs
import PowerWalk
from typing import IO

from alogging import ALogger
lg = ALogger(1)

PY3 = sys.version_info[0] == 3
if PY3:
    from html import entities
    def unichr(n): return chr(n)

__metadata__ = {
    "title"        : "pod2md",
    "description"  : "Convert perldoc-style POD markup to MarkDown-ish.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2019-02-19",
    "modified"     : "2020-10-01",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]

descr = """
=Description=

pod2md.py: Convert perldoc-tsyle "POD" markup (not including the more
complex POD 6 version), to MarkDown (mostly of the MediaWiki flavor).

==POD Summary==

POD is mostly for Perl Documenttion. See
[https://docs.perl6.org/language/pod].

===Line-level (must start at start of line)===
    =pod     Start POD when embedded in Perl
    =cut     End POD
    =head1   First-level heading
    ...
    =over    Indent one list level / start list
    =back    End list
    =item

===Inline===

    B<(.*?)> bold
    C<(.*?)> command
    E<(.*?)> special characters (quite a few, including HTML named entities)
    F<(.*?)> filename
    I<(.*?)> italic
    L<(.*?)> link
    S<(.*?)> no-break
    X<(.*?)> index entry
    Z<(.*?)> No POD

    Also B<<25<100>>, etc.

==Markdown summary==

(there are many variations)

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

Markdown isn't entirely standardized, so this is just one set of options.
It's fairly close to MediaWiki (used by wikipedia).

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


=Known bugs and limitations=

`--outputFormat` is unfinished. It mainly just does 'mediawiki', but 'html'
should work for inline markup and for headings.

Does not handle multi-<>  like I<<<foo>bar>>>.

Doesn't handle POD `=for`.

Leaves an extra blank line where `=over` and `=back` were.


=Related Commands=


=References=

* [https://www.mediawiki.org/wiki/Markup_spec] -- Obsolete, but one of
relatively few sites that enumerate MediaWiki markup constructs.
* [https://en.wikipedia.org/wiki/MediaWiki#Markup] -- MediaWiki or Markdown Extra
* [https://en.wikipedia.org/wiki/Markdown#Standardization]
* [https://tools.ietf.org/html/rfc7763] -- text/markdown media type
* [https://tools.ietf.org/html/rfc7764] -- Guidance on Markdown


=History=

* 2019-02-19: Written by Steven J. DeRose.
* 2020-01-02: Clean up.
* 2020-10-01: Add `--test`. Clean and lint. Fix bugs with lists.
Switch `--all` to opposite option `--justPOD` and fix. Get indent working.
Start support for alternate `--outputFormat` settings.


=To do=

* Let `--extract-to` default to same name but .md?
* Finish MediaWiki and/or HTML output?


=Rights=

Copyright 2019 by Steven J. DeRose. This script is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See http://creativecommons.org/licenses/by-sa/3.0/ for more information.

For the most recent version, see [http://www.derose.net/steve/utilities/]
or [http://github.com/sderose].


=Options=
"""

xfh = None

def escapeXmlContent(s):  # From sjdUtils.py
    """Turn ampersands, less-than signs, and greater-than signs that are
    preceded by two close square brackets, into XML entity references.
    Also delete any non-XML C0 control characters.
    This escaping is appropriate for XML text content.
    """
    if (s is None): return("")
    if (not isinstance(s, str)): s = str(s)
    s = s = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f]", "", s)
    s = re.sub(r"&",   "&amp;",  s)
    s = re.sub(r"<",   "&lt;",   s)
    s = re.sub(r"]]>", "]]&gt;", s)
    return(s)


###############################################################################
#
def doOneFile(path, fh:IO) -> int:
    """Read and deal with one individual file.
    """
    recnum = 0
    rec = ""

    if (args.justPOD): inPOD = False
    else: inPOD = True
    everSawPOD = False
    depth = 0
    skipped = 0

    while (True):
        try:
            rec = fh.readline()
        except IOError as e:
            lg.error("Error (%s) reading record %d of '%s'." %
                (type(e), recnum, path))
            break
        if (len(rec) == 0): break # EOF
        recnum += 1

        rec = rec.rstrip()
        mat = re.match(r"^(\s*)(.*)", rec)
        indentSpace = mat.group(1)
        rec = mat.group(2)

        if (not inPOD):
            skipped += 1
            continue
        elif (rec.startswith("=pod")):
            inPOD = True
            everSawPOD = True
            continue
        elif (rec.startswith("=cut")):
            inPOD = False
            continue
        elif (rec.startswith("=encoding")):
            encoding = rec[9:].strip()
            if (encoding != args.iencoding):
                lg.error("=encoding '%s' not supported." % (encoding))
            continue
        elif (rec.startswith("=head")):
            hLevel = int(rec[5]) + 0
            rec = makeHeading(rec[6:].strip(), hLevel)
        elif (rec.startswith("=over")):
            rec = ""
            depth += 1
            continue
        elif (rec.startswith("=back")):
            rec = ""
            depth -= 1
            continue
        elif (rec.startswith("=item")):
            rec = ("*" * depth) + re.sub(r"=item\s*[*+-o\d]*", "", rec)
        else:  # it's just text...
            #print("*** text line, indentSpace '%s'." % (indentSpace))
            rec = indentSpace + rec

        # Concert POD inline markup
        rec = re.sub(r"\b(\w)<([^>]*)>", fixInline, rec)

        if (args.verbose):
            print("%4d: %s" % (recnum, rec))
        else:
            print(rec, end="\n")
        if (xfh): xfh.write(rec)

    if (args.justPOD and not everSawPOD):
        print("Never saw '=pod'. Did you mistakenly set --justPOD?")
    return(recnum)

def makeHeading(txt:str, level:int=1) -> str:
    if (args.outputFormat=="md"):
        flag = "#" * level
        return (flag+txt+flag)
    elif (args.outputFormat=="mediawiki"):
        flag = "=" * level
        return (flag+txt+flag)
    elif (args.outputFormat=="html"):
        return "<h%d>%s</h%d>" % (level, txt, level)
    return txt

# Define what string to issue to open and close inline font changes, etc.
#
codeMap = {
    #POD    MD+      MD-    MWiki+  MWiki-  HTML
    "B": [ "''",    "''",   "**",   "**",   "b",   ],   # bold
    "I": [ "'''",   "'''",  "*",    "*",    "i",   ],   # italic
    # "U": [ "",      "",     "__",   "__",   "u",   ],   # underscore

    "C": [ "`",     "`",    "",     "",   "tt",  ],  # command
    "F": [ "`",     "`",    "",     "",   "tt",  ],  # filename

    #"E": [ "''",    "''",   "",     "",   "",    ],   # special ch

    "L": [ "[",     "]",    "",     "",   "a",   ],   # link           ??
    "S": [ "''",    "''",   "",     "",   "", ],   # no-break       special?
    "X": [ "''",    "''",   "",     "",   "idx", ],   # index entry    ???
    "Z": [ "",      "",     "",     "",   "",    ],   # No POD
}

def fixInline(mat:re.Match) -> str:
    # Can POD nest inlines, like I<foo B<bar>>?
    code = mat.group(1)
    txt = mat.group(2)
    if (code == "E"):
        return decodeSpecialChar(txt)
    elif (code in codeMap):
        if (args.outputFormat == "md"):
            return codeMap[code][0] + txt + codeMap[code][1]
        elif (args.outputFormat == "mediawiki"):
            return codeMap[code][2] + txt + codeMap[code][3]
        elif (args.outputFormat == "html"):
            return "<%s>%s</%s>" % (
                codeMap[code][4], escapeXmlContent(txt), codeMap[code][4])
    else:
        lg.error(0, "Bad inline POD code '%s' with text '%s'." % (code, txt))
        txt = mat.group()
    return txt

def decodeSpecialChar(text:str) -> str:
    text = text.strip()
    if (text == "lt"): return "<"
    if (text == "gt"): return ">"
    if (text == "verbar"): return "|"
    if (text == "sol"): return "/"
    if (text.startswith("0x")): return chr(int(text[2:], 16))
    if (text.startswith("0")): return chr(int(text[1:], 8))
    if (re.match(r"\d+$",text)): return chr(int(text[1:], 10))
    try:
        c = unichr(entities.name2codepoint[text])
    except KeyError:
        lg.error(0, "Unrecognized value '%s' for E<> code." % (text))
        c = "<E%s>" % (text)
    return c


###############################################################################
# Main
#
if __name__ == "__main__":
    def processOptions() -> argparse.Namespace:
        try:
            from BlockFormatter import BlockFormatter
            parser = argparse.ArgumentParser(
                description=descr, formatter_class=BlockFormatter)
        except ImportError:
            parser = argparse.ArgumentParser(description=descr)

        parser.add_argument(
            "--extract-to", "--extractTo", type=str, metavar="F", default="",
            dest="extractTo", help="Write a copy to this file.")
        parser.add_argument(
            "--iencoding", type=str, metavar="E", default="utf-8",
            help="Assume this character set for input files. Default: utf-8.")
        parser.add_argument(
            "--justPOD", action="store_true",
            help='Wait for "=pod" line to start.')
        parser.add_argument(
            "--oencoding", type=str, metavar="E", default="utf-8",
            help="Use this character set for output files.")
        parser.add_argument(
            "--outputFormat", "--output-format", "--oformat",
            type=str, metavar="F", default="mediawiki",
            choices=[ "md", "mediawiki", "html" ],
            help="Assume this character set for input files. Default: utf-8.")
        parser.add_argument(
            "--quiet", "-q", action="store_true",
            help="Suppress most messages.")
        parser.add_argument(
            "--test", action="store_true",
            help="Test on some fixed sample data.")
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
            "files", type=str,
            nargs=argparse.REMAINDER,
            help="Path(s) to input file(s)")

        args0 = parser.parse_args()
        if (args0.verbose): lg.setVerbose(args0.verbose)
        return(args0)

    sample = """
=pod

=Usage=

    pod2md.py [options] [files]

==The options==

=over

* Aardvark

* Basilisk

* Cats

=over

* Lions

* Tigers

=back

* And not Bears, oh my.

=back

And we also have inline markup, such as for
B<bold> and C<command> and E<bull> and
F<filename> and I<italic> and L<link> and
S<no-break> and X<index entry> and Z<No I<POD> in here>.

=cut
"""

    ###########################################################################
    #
    args = processOptions()

    if (args.test):
        tfile = "/tmp/pod2mdSample.pod"
        with codecs.open(tfile, "wb", encoding="utf-8") as tf:
            tf.write(sample)
        lg.vMsg(0, "Test data written to %s." % (tfile))
        args.files.insert(0, tfile)

    if (args.extractTo):
        xfh = codecs.open(args.extractTo, "wb", encoding=args.oencoding)

    if (len(args.files) == 0):
        lg.error("No files specified....")
        doOneFile("[STDIN]", sys.stdin)
    else:
        pw = PowerWalk.PowerWalk(
            args.files, open=True, close=True, encoding=args.oencoding)
        pw.setOption("recursive", False)
        for path0, fh0, typ in pw.traverse():
            if (typ != PowerWalk.PWType.LEAF): continue
            doOneFile(path0, fh0)

    if (xfh): xfh.close()
