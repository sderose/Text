#!/usr/bin/env python3
#
# quoteLines.py: Escape input lines and/or put in quotes.
# 2021-03-24: Written by Steven J. DeRose.
#
import sys
import re
import codecs
#import string

from PowerWalk import PowerWalk, PWType

__metadata__ = {
    "title"        : "quoteLines",
    "description"  : "Escape input lines and put in quotes.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2021-03-24",
    "modified"     : "2021-04-13",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]


# https://github.com/sderose/Charsets/Unicode/asPython/blob/master/quote.py
qPairs = {
    "back":     [ 0x0060, 0x0060, "GRAVE ACCENT", ],
    "splain":   [ 0x0027, 0x0027, "APOSTROPHE", ],
    "dplain":   [ 0x0022, 0x0022, "QUOTATION MARK", ],
    "single":   [ 0x2018, 0x2019, "SINGLE QUOTATION MARK", ],
    "double":   [ 0x201C, 0x201D, "DOUBLE QUOTATION MARK", ],
    "sangle":   [ 0x2039, 0x203A, "SINGLE ANGLE QUOTATION MARK", ],
    "dangle":   [ 0x00AB, 0x00BB, "DOUBLE ANGLE QUOTATION MARK", ],
    "slow9":    [ 0x201A, 0x201B, "SINGLE LOW-9 QUOTATION MARK", ],
    "dlow9":    [ 0x201E, 0x201F, "DOUBLE LOW-9 QUOTATION MARK", ],
    "sprime":   [ 0x2032, 0x2035, "PRIME", ],
    "dprime":   [ 0x301E, 0x301E, "DOUBLE PRIME QUOTATION MARK", ],
    "tprime":   [ 0x2034, 0x2037, "TRIPLE PRIME and REVERSED TRIPLE PRIME", ],

    "subst":    [ 0x2E02, 0x2E03, "SUBSTITUTION BRACKET", ],
    "dotsubst": [ 0x2E04, 0x2E05, "DOTTED SUBSTITUTION BRACKET", ],
    "transp":   [ 0x2E09, 0x2E0A, "TRANSPOSITION BRACKET", ],
    "romission":[ 0x2E0C, 0x2E0D, "RAISED OMISSION BRACKET", ],
    "lpara":    [ 0x2E1C, 0x2E1D, "LOW PARAPHRASE BRACKET", ],
    "vbarq":    [ 0x2E20, 0x2E21, "VERTICAL BAR WITH QUILL", ],
    #'rdprime':  [ 0x301D, 0x301F, "DOUBLE PRIME QUOTATION MARK", ],
    "rdprime":  [ 0x2057, 0x301D, "DOUBLE PRIME QUOTATION MARK", ],
    # = "QUADRUPLE PRIME"

    "fullwidth":[ 0xFF02, 0xFF02, "FULLWIDTH QUOTATION MARK", ],
    "scommaO":  [ 0x275B, 0x275C, "HEAVY SINGLE TURNED COMMA QM ORNAMENT", ],
    "dcommaO":  [ 0x275D, 0x275E, "HEAVY DOUBLE TURNED COMMA QM ORNAMENT", ],
    "hangleO":  [ 0x276E, 0x276F, "HEAVY ANGLE QM ORNAMENT", ],
    "sshdcommonO": [ 0x1F677, 0x1F678, "SANS-SERIF HEAVY DOUBLE COMMA QM ORNAMENT", ],
}

descr = """
=Description=

Rewrite the input, each line having these changes applied
with respect to whatever kind of quotes you specify:
    * any \\, are escaped;
    * any occurrences of the chosen quote characters are escaped.
    * the chosen quote characters are added at start and end;
    * a separator is appended (default comma; set '' to suppress).

The quote types supported can be listed via `--help-quotes`.
"single" means the curly ones at U+2018, U+2019;
"double means the curly ones at U+201C, U+201D).

==Usage==

    quoteLines.py [options] [files]


=Related Commands=

Options are based on my `fsplit.py`, in turn based on Python `csv`.


=Known bugs and Limitations=

Seeing all the PowerWalk options in `-h` is annoying.


=History=

* 2021-03-24: Written by Steven J. DeRose.


=To do=

* Option to skip lines matching some regex (say, r"^#|^\\s*$").
* Option to just replace a kind(s) of quote with another.

=Rights=

Copyright 2021-03-24 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See [http://creativecommons.org/licenses/by-sa/3.0/ for more information].

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""

def log(lvl, msg):
    if (args.verbose >= lvl): sys.stderr.write(msg + "\n")
def warning0(msg): log(0, msg)
def warning1(msg): log(1, msg)
def warning2(msg): log(2, msg)
def fatal(msg): log(0, msg); sys.exit()
warn = log


###############################################################################
#
def doOneFile(path):
    """Read and deal with one individual file.
    """
    if (not path):
        if (sys.stdin.isatty()): print("Waiting on STDIN...")
        fh = sys.stdin
    else:
        try:
            fh = codecs.open(path, "rb", encoding=args.iencoding)
        except IOError as e:
            warning0("Cannot open '%s':\n    %s" % (e))
            return 0

    recnum = 0
    for rec in fh.readlines():
        recnum += 1
        op, cl, _desc = qPairs[args.quote]
        rec = quoteIt(rec, chr(op), chr(cl))
        rec += args.separator
        print(rec)
    if (fh != sys.stdin): fh.close()
    return recnum

def quoteIt(s, qp1, qp2):
    s = re.sub(r"\\", "\\\\", s)
    s = re.sub(qp1, "\\"+qp1, s)
    if (qp2 != qp1): s = re.sub(qp2, "\\"+qp2, s)
    return qp1 + s + qp2


###############################################################################
# Main
#
if __name__ == "__main__":
    import argparse

    def processOptions():
        try:
            from BlockFormatter import BlockFormatter
            parser = argparse.ArgumentParser(
                description=descr, formatter_class=BlockFormatter)
        except ImportError:
            parser = argparse.ArgumentParser(description=descr)

        parser.add_argument(
            "--help-quotes", action="store_true",
            help="Display the mnemonics for --quote, and their meanings.")
        parser.add_argument(
            "--iencoding", type=str, metavar="E", default="utf-8",
            help="Assume this character coding for input. Default: utf-8.")
        parser.add_argument(
            "--oencoding", type=str, metavar="E", default="utf-8",
            help="Use this character coding for output. Default: iencoding.")
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

        # Options based on fsplit.py
        parser.add_argument(
            "--quote", type=str, metavar="E", default="dplain",
            choices=qPairs.keys(),
            help="Name for type of quotes to use.")
        parser.add_argument(
            "--separator", type=str, metavar="E", default="utf-8",
            help="Append this character after the closing quote.")

        PowerWalk.addOptionsToArgparse(parser)

        parser.add_argument(
            "files", type=str,
            nargs=argparse.REMAINDER,
            help="Path(s) to input file(s)")

        args0 = parser.parse_args()

        if (args0.help_quotes):
            print("Quote types:")
            for qtype in sorted(qPairs.keys()):
                assert len(qPairs[qtype])==3, "Bad tuple: %s" % (qPairs[qtype])
                op, cl, desc = qPairs[qtype]
                print("    %-12s %s...%s U+%04x...U+%04x %s" %
                    (qtype, chr(op), chr(cl), op, cl, desc))

        return(args0)

    ###########################################################################
    #
    args = processOptions()
    if (args.iencoding and not args.oencoding):
        args.oencoding = args.iencoding
    #if (args.oencoding):
    #    sys.stdout.reconfigure(encoding="utf-8")

    if (len(args.files) == 0):
        warning0("quoteLines.py: No files specified....")
        doOneFile(None)
    else:
        pw = PowerWalk(args.files, open=False, close=False,
            encoding=args.iencoding)
        pw.setOptionsFromArgparse(args)
        for path0, fh0, what0 in pw.traverse():
            if (what0 != PWType.LEAF): continue
            doOneFile(path0)
        if (not args.quiet):
            warning0("quoteLines.py: Done, %d files.\n" % (pw.getStat("regular")))
