#!/usr/bin/env python3
#
# unescpeString.py: Unbackslash stuff, as for a Python string.
# 2021-08-12: Written by Steven J. DeRose.
#
import sys
import codecs
import re
import html
import urllib
import logging
lg = logging.getLogger("unescapeString")

__metadata__ = {
    "title"        : "unescpeString",
    "description"  : "Unbackslash stuff, as for a Python string.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2021-08-12",
    "modified"     : "2022-10-14",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]

descr = """
=Description=

==Usage==

    unescpeString.py [options] [files]

Expand "escaped" character in the input to literal.
By default (equal to ''--form plain''), this does what Python does when
interpreting a string via

    codecs.decode(s, "unicode_escape")

This includes cases like:
* \\n, \\r, \\t, \\\\ etc. to literal characters.
* \\xFF, \\uFFFF, \\U0001BEEF}, etc.

With ''--form html'', this instead uses Python's ''html.unescape()'' to
expand named and numeric character references.

With ''--form uri'', this instead uses ''urllib.parse.unquote()'' to
interpret %xx escape such as used in URIs.

With ''--form cpic'', this instead turns Unicode "control pictures" (U+2400...)
into actual control characters.


=Related Commands=

* unescapeURI: similar but for URI-style %FF escapes.
* manClean.py: undoes backspace-and-overstrike as used in ''man'' pages.
* PdfStupidityFix.py: fixes several common word-level extraction issues, such
as letters alternating with spaces; hardened or lost soft-hyphens, etc.


=Known bugs and Limitations=


=To do=

* Option to remove quotes (either line-by-line, or just start and end)
* Possibly, add a way to undo iterated UTF encoding, such as
U+2022 -> \xe2\x80\xa2 -> \xc3\xa2\xc2\x80\xc2\xa2 -> ....
* Check what happens if UTF-8 was escaped byte-by-byte.
* Options for other decodings? URL, HTML, etc?


=History=

* 2021-08-12: Written by Steven J. DeRose.
* 2022-10-14: Drop PowerWalk. Add --form, for html, uri, and cpic.

=Rights=

Copyright 2021-08-12 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See [http://creativecommons.org/licenses/by-sa/3.0/] for more information.

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""


###############################################################################
#
def doOneFile(path:str) -> int:
    """Read and deal with one individual file.
    """
    if (not path):
        if (sys.stdin.isatty()): print("Waiting on STDIN...")
        fh = sys.stdin
    else:
        try:
            fh = codecs.open(path, "rb", encoding=args.iencoding)
        except IOError as e:
            lg.warning("Cannot open '%s':\n    %s", path, e)
            return 0

    recnum = 0
    for rec in fh.readlines():
        recnum += 1
        if (args.form=="html"):
            print(html.unescape(rec))
        elif (args.form=="uri"):
            print(urllib.parse.unquote(rec))
        elif (args.form=="cpics"):
            print(re.sub(r"([\u2400-\u2426])", unPic, rec))
        elif (args.form=="plain"):
            try:
                print(codecs.decode(rec, "unicode_escape"), end="")
            except UnicodeDecodeError as e:
                lg.warning("Cannot decode line %d: %s\n    %s", recnum, rec, e)
                if (args.keep): print(rec, end="")
        else:
            assert False, "Unknown --form choice '%s'." % (args.form)
    if (fh != sys.stdin): fh.close()
    return recnum

def unPic(mat):
    codePoint = ord(mat.group(1))
    if (codePoint <= 0x2420): return chr(codePoint - 0x2400)
    if (codePoint == 0x2421): return chr(0xFF)
    if (codePoint == 0x2422): return " "
    if (codePoint == 0x2423): return " "
    if (codePoint == 0x2424): return "\n"
    if (codePoint == 0x2425): return chr(0xFF)
    if (codePoint == 0x2426): return chr(0x1A)
    assert False, "Non-control-picture code point U+%04x." % (codePoint)


###############################################################################
# Main
#
if __name__ == "__main__":
    import argparse

    def processOptions() -> argparse.Namespace:
        try:
            from BlockFormatter import BlockFormatter
            parser = argparse.ArgumentParser(
                description=descr, formatter_class=BlockFormatter)
        except ImportError:
            parser = argparse.ArgumentParser(description=descr)

        parser.add_argument(
            "--form", type=str, default="backslash",
            choices=[ "backslash", "html", "uri", "cpics" ],
            help="What kind of escaping to undo.")
        parser.add_argument(
            "--iencoding", type=str, metavar="E", default="utf-8",
            help="Assume this character coding for input. Default: utf-8.")
        parser.add_argument(
            "--keep", action="store_true",
            help="If set, lines with decoding errors will be unchanged, not discarded.")
        parser.add_argument(
            "--quiet", "-q", action="store_true",
            help="Suppress most messages.")
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
            "files", type=str, nargs=argparse.REMAINDER,
            help="Path(s) to input file(s)")

        args0 = parser.parse_args()
        return(args0)


    ###########################################################################
    #
    args = processOptions()

    if (len(args.files) == 0):
        lg.warning("unescpeString.py: No files specified....")
        doOneFile(None)
    else:
        for path0 in args.files:
            doOneFile(path0)
