#!/usr/bin/env python
#
# unescpeString.py: Unbackslash stuff, as for a Python string.
# 2021-08-12: Written by Steven J. DeRose.
#
from __future__ import print_function
import sys
import codecs

from PowerWalk import PowerWalk, PWType

__metadata__ = {
    "title"        : "unescpeString.py",
    "description"  : "Unbackslash stuff, as for a Python string.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2021-08-12",
    "modified"     : "2021-08-12",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]

descr = """
=Description=

==Usage==

    unescpeString.py [options] [files]

Do what Python does when interpreting a string via

    codecs.decode(s, "unicode_escape")

This includes:
* \\n, \\r, \\t, \\\\ etc. to literal characters.
* \\xFF, \\uFFFF, \\U0001BEEF}, etc.


=Related Commands=


=Known bugs and Limitations=


=To do=

* Option to remove quotes (either line-by-line, or just start and end)
* Check what happens if UTF-8 was escaped byte-by-byte.

=History=

* 2021-08-12: Written by Steven J. DeRose.


=Rights=

Copyright 2021-08-12 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See [http://creativecommons.org/licenses/by-sa/3.0/] for more information.

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""

def log(lvl:int, msg:str) -> None:
    if (args.verbose >= lvl): sys.stderr.write(msg + "\n")
def warning0(msg:str) -> None: log(0, msg)


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
            warning0("Cannot open '%s':\n    %s" % (path, e))
            return 0

    recnum = 0
    for rec in fh.readlines():
        recnum += 1
        try:
            print(codecs.decode(rec, "unicode_escape"), end="")
        except UnicodeDecodeError as e:
            warning0("Cannot decode line %d: %s\n    %s" % (recnum, rec, e))
            if (args.keep): print(rec, end="")
    if (fh != sys.stdin): fh.close()
    return recnum


###############################################################################
# Main
#
if __name__ == "__main__":
    import argparse
    def anyInt(x:str) -> int:
        return int(x, 0)

    def processOptions() -> argparse.Namespace:
        try:
            from BlockFormatter import BlockFormatter
            parser = argparse.ArgumentParser(
                description=descr, formatter_class=BlockFormatter)
        except ImportError:
            parser = argparse.ArgumentParser(description=descr)

        parser.add_argument(
            "--iencoding", type=str, metavar="E", default="utf-8",
            help="Assume this character coding for input. Default: utf-8.")
        parser.add_argument(
            "--keep", action="store_true",
            help="If set, lines with decoding errors will be written out unchanged, not discarded.")
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

        PowerWalk.addOptionsToArgparse(parser)

        parser.add_argument(
            "files", type=str, nargs=argparse.REMAINDER,
            help="Path(s) to input file(s)")

        args0 = parser.parse_args()
        return(args0)


    ###########################################################################
    #
    args = processOptions()

    if (len(args.files) == 0):
        warning0("unescpeString.py: No files specified....")
        doOneFile(None)
    else:
        pw = PowerWalk(args.files, open=False, close=False, encoding=args.iencoding)
        pw.setOptionsFromArgparse(args)
        for path0, fh0, what0 in pw.traverse():
            if (what0 != PWType.LEAF): continue
            doOneFile(path0)
