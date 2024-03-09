#!/usr/bin/env python3
#
# pastePP.py: Upgraded form of *nix 'paste'.
# 2021-06-09: Written by Steven J. DeRose.
#
import sys
import codecs

__metadata__ = {
    "title"        : "pastePP",
    "description"  : "Upgraded form of *nix 'paste'.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2021-06-09",
    "modified"     : "2021-06-09",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]


descr = """
=Description=

==Usage==

    pastePP.py [options] [files]

Like *nix `paste`, but (imho) better. Specifically:

* Encoding aware
* Allows multi-character delimiters
* Allows normal Python \\-codes for delimiters.
* Can skip blank lines (even if they vary across files)
* Can strip leading/trailing whitespace
* Can quote the parts
* Reports cases where delimiters were found in data.

If the files have differing numbers of records, empty records are generated
for the short ones. The actual number of records in each file is recorded, and
can be reported with -v.


=Related Commands=

Linux `paste`.


=Known bugs and Limitations=

* Haven't yet added escaping for delims found in data.
* Should support alternate output forms (via `fsplit.py`)


=History=

* 2021-06-09: Written by Steven J. DeRose.


=To do=


=Rights=

Copyright 2021-06-09 by Steven J. DeRose. This work is licensed under a
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
            "--blankIgnore", action="store_true",
            help="Discard blank lines.")
        parser.add_argument(
            "--cycleDelims", action="store_true",
            help="Rotate through single-char delimiters, like standard 'paste'.")
        parser.add_argument(
            "--delim", "-d", type=str, default=",",
            help="""Use this string as the delimiter between pasted records.
Supports \\xFF, \\uFFFF, \\UFFFFFFFF, \\x{FFF}, etc.
Default: ','. Note: if len > 1, the whole string is the delimiter, not each
character in rotation as with *nix 'paste'. To do that, set --cycleDelims.""")
        parser.add_argument(
            "--iencoding", type=str, metavar="E", default="utf-8",
            help="Assume this character coding for input. Default: utf-8.")
        parser.add_argument(
            "--lstrip", action="store_true",
            help="Remove whitespace from start of lines.")
        parser.add_argument(
            "--oencoding", type=str, metavar="E", default="utf-8",
            help="Use this character coding for output. Default: iencoding.")
        parser.add_argument(
            "--quiet", "-q", action="store_true",
            help="Suppress most messages.")
        parser.add_argument(
            "--quoteChar", type=str, default=None,
            help="Use this char to quote each (input) line.")
        parser.add_argument(
            "--rstrip", action="store_true",
            help="Remove whitespace from end of lines.")
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
        if ("\\" in args0.delim):
            args0.delim = args0.delim.decode('string_escape')

        return(args0)

    ###########################################################################
    #
    args = processOptions()
    if (args.iencoding and not args.oencoding):
        args.oencoding = args.iencoding
    if (args.oencoding):
        sys.stdout = codecs.getwriter(args.oencoding)(sys.stdout.detach())

    if (len(args.files) == 0):
        fatal("pastePP.py: No files specified....")

    fhs = []
    for path in args.files:
        fhs.append(codecs.open(path, "rb", encoding=args.iencoding))
    totRecsPerFile = [ 0 for x in range(len(fhs)) ]
    recnum = 0
    delimConflicts = 0
    while (True):
        recnum += 1
        buf = ""
        nWithData = 0
        for i, fh in enumerate(fhs):
            irec = fh.readline()
            if (irec != ""): nWithData += 1
            elif (totRecsPerFile[i] == 0): totRecsPerFile[i] = recnum
            irec = irec.rstrip("\n")
            if (args.rstrip): irec = irec.rstrip()
            if (args.lstrip): irec = irec.lstrip()
            if (args.quoteChar): irec = args.quoteChar + irec + args.quoteChar
            # TODO: Not clear what to check for with cycleDelims...
            curDelim = args.delim
            if (i>0):
                if (args.cycleDelims): curDelim = args.delim[(i-1) % len(args.delim)]
                buf += curDelim
            if (curDelim in irec):
                delimConflicts += 1
                if (not args.quiet):
                    warning0("Delim '%s' in data, file %d, record %d." %
                        (curDelim, i, recnum))
            buf += irec
        if (nWithData == 0): break
        print(buf)

    warning0("Finished, %d files, %d records, %d delimiter conflicts." %
        (len(fhs), recnum, delimConflicts))
    if (args.verbose):
        warning0("Number of records in each file:")
        for i, path in args.files:
            warning0("    %6d %s" % (totRecsPerFile[i], path))
