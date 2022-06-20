#!/usr/bin/env python3
#
# text2strings.py Quote up a file to make Python string init.
# 2018-11-05: Written by Steven J. DeRose.
#
import sys
import argparse
import codecs
import PowerWalk
from collections import defaultdict

__metadata__ = {
    "title"        : "text2strings",
    "description"  : "Turn a text file into a Python array of strings",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2018-11-05",
    "modified"     : "2021-03-03",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]

descr = """
=Description=

Turn a text file into a Python array of strings.

Each line is escaped and then double-quoted, and a comma is added.
The whole file is enclosed in square brackets.

Lines beginning with "#" are treated as comments. You can change this
via the `--comment` option, for example setting it to "//" or "".


=Known bugs and Limitations=

Should add an option to set the indentation level, and/or to put the opening
quote after any leading space.


=History=

2018-11-05: Written by Steven J. DeRose.
2021-03-03: New layout.


=Rights=

Copyright 2018-11-05 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
For further information on this license, see
[https://creativecommons.org/licenses/by-sa/3.0].

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""


###############################################################################
#
stats = defaultdict(int)

def doOneFile(path, fh):
    """Read and deal with one individual file.
    """
    recnum = 0
    rec = ""
    print("[")
    while (True):
        try:
            rec = fh.readline()
        except IOError as e:
            sys.stderr.write("Error (%s) reading record %d of '%s'.\n" %
                (type(e), recnum, path))
            break
        if (len(rec) == 0): break # EOF
        recnum += 1
        if (args.strip): rec = rec.strip()
        if (args.comment!='' and rec.startswith(args.comment)):
            pass
        elif (rec.strip() == ''):
            rec = ''
        else:
            rec = rec.replace("\\", "\\\\").replace('"', "\\\"").replace("\n", "\\n").replace("\r", "\\r")
            if (args.ustrings): rec = 'u"' + rec + '",'
            else: rec = '"' + rec + '",'
        print(args.indent + rec)
    print("]")
    return(recnum)


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
            "--comment", type=str, metavar='S', default="#",
            help='Treat lines starting with this as comments. Default: "#".')
        parser.add_argument(
            "--iencoding", type=str, metavar='E', default="utf-8",
            help='Assume this character set for input files. Default: utf-8.')
        parser.add_argument(
            "--indent", type=str, metavar='I', default="",
            help='Put this before each output line.')
        parser.add_argument(
            "--quiet", "-q", action='store_true',
            help='Suppress most messages.')
        parser.add_argument(
            "--recursive", action='store_true',
            help='Descend into subdirectories.')
        parser.add_argument(
            "--strip", action='store_true',
            help='Strip leading and trailing whitespace from records.')
        parser.add_argument(
            "--unicode", action='store_const', dest='iencoding',
            const='utf8', help='Assume utf-8 for input files.')
        parser.add_argument(
            "--ustrings", action='store_true',
            help='Put "u"s before the opening quotes.')
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
        return(args0)


    ###########################################################################
    #
    args = processOptions()

    if (len(args.files) == 0):
        sys.stderr.write("No files specified....\n")
        doOneFile("[STDIN]", sys.stdin)
    else:
        depth = 0
        pw = PowerWalk.PowerWalk(args.files)
        pw.setOption('recursive', args.recursive)
        for path0, fh0 in pw.traverse():
            if (fh0 == "DIR_END"):
                depth -= 1
                continue
            print("    " * depth + path0)
            if (fh0 == "DIR_START"):
                depth += 1
                continue

            fileNum = pw.travState.stats['itemsReturned']
            fh0 = codecs.open(path0, "rb", encoding=args.iencoding)
            doOneFile(path0, fh0)
            fh0.close()
