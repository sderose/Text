#!/usr/bin/env python3
#
# manClean.py: Undo 'man' formatting conventions like X^HX for bold.
# 2022-10-14: Written by Steven J. DeRose.
#
import sys
import codecs
import re
import html

gotMath = False
try:
    import mathAlphanumerics
    gotMath = True
except ImportError:
    pass

import logging
lg = logging.getLogger("manClean.py")

__metadata__ = {
    "title"        : "manClean",
    "description"  : "Undo 'man' formatting conventions like X^HX for bold.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.9",
    "created"      : "2022-10-14",
    "modified"     : "2022-10-14",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]

descr = """
=Name=
    """ +__metadata__["title"] + ": " + __metadata__["description"] + """


=Description=

Undo 'man' formatting conventions to make plain-ish text (or maybe markup or
'mathAlphanumerics' characters).

Typically, running "man" in the shell generates text with backspace-and-overstrike
conventions for formatting. This is great is your terminal uses physical paper and
ink (or emulates it) -- but that kind of retro at this point, and it means a lot
of simple searches don't work. So, this turns that into more modern formatting.

Specifically:

    char + backspace + char means bold
    _ + backspace + char means underscored / italics
   char + backspace + _ means underscored / italics

Use --oformat to choose what you want as a result:

* "plain": leaves just the "base" character.
* "html": also puts in tags like <u>, <b>, etc. These are placed once around any
contiguous group of such characters, but not crossing line boundaries. You can
change the tag for underscoring with --uTag (say, to "i").
The text is also HTML-escape (though the rest of the file isn't -- maybe will add).
* "markdown": Puts "*" around bold, and "_" around underscoring.
* "math": replaces the sequence with the Unicode "MATHEMATICAL" equivalent of the
base character (see my 'mathAlphanumerics.py' for details).

==Usage==

    manClean.py [options] [files]


=See also=


=Known bugs and Limitations=

So far, only supports underscoring where the underscore comes before its base
character. I don't know if some man setups generate things the other way around.
And the possibility of mixing the two exists.

If a series of these characters crosses line boundaries in the input, each line
is treated separately.

"math" variants may not be supported in all terminal programs or all font choices.

"math" variants are typically only available for basic Latin, Greek, and digits.
However, this program does a Unicode decomposition first, so accented Latin and
Greek characters should work.

"math" changes underscoring to italics, because there is no MATHEMATICAL UNDERSCORED
range in Unicode (afaik). We could instead insert some Unicode combining character
such as shown below, but that wouldn't fix the search feature. Then again, whether
your "find" program think mathematical variants of "A" count as equal to "A" varies;
grep probably doesn't, but sort probably does (depending on locale setting).

    U+00331  ̱  COMBINING MACRON BELOW
    U+00332  ̲  COMBINING LOW LINE
    U+00333  ̳  COMBINING DOUBLE LOW LINE


=To do=


=History=

* 2022-10-14: Written by Steven J. DeRose.


=Rights=

Copyright 2022-10-14 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See [http://creativecommons.org/licenses/by-sa/3.0/] for more information.

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""


###############################################################################
#
undersExpr = re.compile(r"((_\x08.)+)")
boldsExpr = re.compile(r"(((.)\x08\3)+)")

tst = "hello \x08world"
print("|%d| '%s'" % (len(tst), tst))
if (re.search(r"\x08", tst)): print("Found bsp")
tst2 = re.sub(r"\x08", "", tst)
print("|%d| '%s'" % (len(tst2), tst2))

print("undersExpr: (%s) /%s" % (type(undersExpr), undersExpr))
print("boldsExpr: (%s) /%s" % (type(boldsExpr), boldsExpr))

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
            lg.error("Cannot open '%s':\n    %s", path, e)
            return 0

    recnum = 0
    for rec in fh.readlines():
        recnum += 1
        rec = rec.rstrip()
        rec = re.sub(undersExpr, fixUnderscore, rec)
        #rec = re.sub(r"((.\x08_)+)", fixUnderscore, rec)
        rec2 = re.sub(boldsExpr, fixBold, rec)
        print(rec2)
    if  (fh != sys.stdin): fh.close()
    return recnum

def fixUnderscore(mat):
    clean = re.sub(r"_\x08(.)", "\\1", mat.group(0))
    if (args.oformat == "plain"):
        return clean
    if (args.oformat == "html"):
        return "%s%s%s>" % (args.uTag, html.escape(clean), args.uTag)
    if (args.oformat == "math"):
        return mathAlphanumerics.convert(clean,
            script="Latin", font="Mathematical Italic ", decompose=True)
    if (args.oformat == "markdown"):
        return "_%s_" % (clean)
    lg.critical("Unsupported output format '%s'.", args.oformat)

def fixBold(mat):
    clean = re.sub(r"(.)\x08\\1", "\\1", mat.group(0))
    if (args.oformat == "plain"):
        return clean
    if (args.oformat == "html"):
        return "<b>%s</b>" % (html.escape(clean))
    if (args.oformat == "math"):
        return mathAlphanumerics.convert(clean,
            script="Latin", font="Mathematical Bold ", decompose=True)
    if (args.oformat == "markdown"):
        return "*%s*" % (clean)
    lg.critical("Unsupported output format '%s'.", args.oformat)


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
            "--iencoding", type=str, metavar="E", default="utf-8",
            help="Assume this character coding for input. Default: utf-8.")
        parser.add_argument(
            "--oencoding", type=str, metavar="E", default="utf-8",
            help="Use this character coding for output. Default: iencoding.")
        parser.add_argument(
            "--oformat", "--outputFormat", "--output-format", type=str,
            choices=[ "plain", "html", "math", "markdown" ],
            metavar="F", default="plain",
            help="What to map format sequences to.")
        parser.add_argument(
            "--quiet", "-q", action="store_true",
            help="Suppress most messages.")
        parser.add_argument(
            "--unicode", action="store_const", dest="iencoding",
            const="utf8", help="Assume utf-8 for input files.")
        parser.add_argument(
            "--utag", type=str, default="u",
            help="What XML/HTML tag to map underlining to.")
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
        if (lg and args0.verbose):            logging.basicConfig(level=logging.INFO - args0.verbose)


        if (args0.outputFormat == "math" and not gotMath):
            lg.critical("Unable to load mathAlphanumerics for --outputFormat math.")
            sys.exit()
        return(args0)


    ###########################################################################
    #
    args = processOptions()
    if (args.iencoding and not args.oencoding):
        args.oencoding = args.iencoding
    if (args.oencoding):
        # https://stackoverflow.com/questions/4374455/
        # sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
        sys.stdout.reconfigure(encoding="utf-8")

    if (len(args.files) == 0):
        lg.warning("manClean.py: No files specified....")
        doOneFile(None)
    else:
        for path0 in args.files:
            doOneFile(path0)
