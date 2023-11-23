#!/usr/bin/env python3
#
# pdfUtil.py: Do various stuff with PDFs.
# 2021-03-26: Written by Steven J. DeRose.
#
from __future__ import print_function
import sys
#from math import ceil, floor
import PyPDF2


__metadata__ = {
    "title"        : "pdfUtil.py",
    "description"  : "Do various stuff with PDFs.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2021-03-26",
    "modified"     : "2021-03-26",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]


descr = """
=Description=

Extract or reconstruct data from PDFs.

Some basic tasks:
* Break a PDF into separate pages.
* Concatenate multiple PDFs into one.
* reverse the order of pages in a PDF.
* Collate 2 PDFS, one of even vs. one of odd pages (e.g., what you get
if you scan 2-sided documents with a 1-sided scanner.
* Collate, but reversing the order of the verso (even) pages, because
that's likely the order when you do this).
* Reorder for printing a signature of n pages (a multiple of 4).
For example, 8-page signature would shuffle things into order:
    2, 7, 8, 1, 4, 5, 6, 3
    10, 15, 16, 9, 12, 13, 14, 11
    ...
* Extract "the" text (just 'cuz I'm already in here).
* Extract the metadata (if any).


==Usage==

    pdfUtil.py -action [A] [options] [files]

The `action` must be one of:

    "getMeta",
    "getText",
    "split",
    "splitEvenOdd",
    "cat",
    "reverse",
    "collate",
    "signature"


=Related Commands=

Pip `PyPDF2` is used to get access to PDF data. It doesn't provide access to individual
drawing objects, so this script doesn't either.


=Known bugs and Limitations=


=History=

* 2021-03-26: Written by Steven J. DeRose.


=To do=


=Rights=

Copyright 2021-03-26 by Steven J. DeRose. This work is licensed under a
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
def getMetadata(pfr1):
    docInfo = pfr1.documentInfo
    infoDict = {
        "author"   : docInfo.author,
        "creator"  : docInfo.creator,
        "producer" : docInfo.producer,
        "subject"  : docInfo.subject,
        "title"    : docInfo.title,
    }
    return infoDict

def getText(pfr1, sep=chr(0x0C)):
    buf = ""
    n1 = pfr1.getNumPages()
    for pageNum in range(n1):
        thePage = pfr1.getPage(pageNum)
        buf += thePage.extractText() + sep
    return buf

def catPages(pfr1, pfr2):
    writer = PyPDF2.PdfFileWriter()
    n1 = pfr1.getNumPages()
    for pageNum in range(n1):
        thePage = pfr1.getPage(pageNum)
        writer.addPage(thePage)
    n2 = pfr2.getNumPages()
    for pageNum in range(n2):
        thePage = pfr2.getPage(pageNum)
        writer.addPage(thePage)
    writeFile(writer)
    return True

def splitPages(pfr1):
    n1 = pfr1.getNumPages()
    for pageNum in range(n1):
        writer = PyPDF2.PdfFileWriter()
        thePage = pfr1.getPage(pageNum)
        writer.addPage(thePage)
        writeFile(writer, serial=pageNum)
    return True

def splitEvenOdd(pfr1):
    n1 = pfr1.getNumPages()
    writer1 = PyPDF2.PdfFileWriter()
    writer2 = PyPDF2.PdfFileWriter()
    for pageNum in range(n1):
        thePage = pfr1.getPage(pageNum)
        if pageNum % 2: writer1.addPage(thePage)
        else: writer2.addPage(thePage)
    writeFile(writer1, serial="odd")
    writeFile(writer2, serial="even")
    return True

def reversePages(pfr1):
    writer = PyPDF2.PdfFileWriter()
    n1 = pfr1.getNumPages()
    for pageNum in reversed(range(n1)):
        thePage = pfr1.getPage(pageNum)
        writer.addPage(thePage)
    writeFile(writer)
    return True

def collatePages(pfr1, pfr2, reverse1=False, reverse2=False):
    """Do a faro shuffle of the pages in 2 PDFs. Mainly useful if
    you scanned 2-sided originals on a 1-sided scanner.
    `pfr1` should be the odd-numbered (recto) pages, and
    `pfr2` should be the even-numbered (verso) pages (which are commonly
        in reverse order, in which case set `reverse2`).
    """
    n1 = pfr1.getNumPages()
    n2 = pfr2.getNumPages()
    if (abs(n1-n2) > 1):
        print("Must have same number of even/odd pages (within one).")
        return False
    writer = PyPDF2.PdfFileWriter()
    for p in range(max(n1, n2)):
        if (reverse1): curPageNum1 = n1 - p
        else: curPageNum1 = p
        thePage = pfr1.getPage(curPageNum1)
        writer.addPage(thePage)

        if (reverse2): curPageNum2 = n2 - p
        else: curPageNum2 = p
        thePage = pfr2.getPage(curPageNum2)
        writer.addPage(thePage)
    writeFile(writer)
    return True

def makeSignature(pfr1, pagesPerSignature=16):
    """Example: For 2 sheets of 2-up size paper:
        Sheet 0 (outer):  front: 2, 7  back 8, 1
        Sheet 1 (inner):  front: 4, 5  back 6, 3
    """
    assert (pagesPerSignature % 4) == 0
    n1 = pfr1.getNumPages()

    writer = PyPDF2.PdfFileWriter()
    sigStart = 1
    while (sigStart<=n1):
        sheetLast = sigStart + pagesPerSignature - 1
        sheetFirst = sigStart
        while sheetFirst < sheetLast:
            # TODO: write blank pages to fill out last signature
            writer.addPage(pfr1.getPage(sheetFirst+1))
            writer.addPage(pfr1.getPage(sheetLast-1))
            writer.addPage(pfr1.getPage(sheetLast))
            writer.addPage(pfr1.getPage(sheetFirst))
            sheetLast -= 2
            sheetFirst += 2
    writeFile(writer)
    return True


def writeFile(pdfWriter, serial=1):
    opath = "%s_%04d.pdf" % (args.outfile, serial)
    with open(opath, "wb") as ofh:
        pdfWriter.write(ofh)
    return(opath)


###############################################################################
# Main
#
if __name__ == "__main__":
    import argparse
    def anyInt(x):
        return int(x, 0)

    def processOptions():
        try:
            from BlockFormatter import BlockFormatter
            parser = argparse.ArgumentParser(
                description=descr, formatter_class=BlockFormatter)
        except ImportError:
            parser = argparse.ArgumentParser(description=descr)

        parser.add_argument(
            "--action", type=str, metavar="A", default="split",
            choices=[ "getMeta", "getText", "split", "splitEvenOdd", "cat",
                "reverse", "collate", "signature" ],
            help="What to do. Default: split.")
        parser.add_argument(
            "--iencoding", type=str, metavar="E", default="utf-8",
            help="Assume this character coding for input. Default: utf-8.")
        parser.add_argument(
            "--oencoding", type=str, metavar="E", default="utf-8",
            help="Use this character coding for output. Default: iencoding.")
        parser.add_argument(
            "--outfile", type=str, metavar="P", default="result",
            help="Where to write the result. Default: iencoding.")
        parser.add_argument(
            "--quiet", "-q", action="store_true",
            help="Suppress most messages.")
        parser.add_argument(
            "--reverse1", action="store_true",
            help="Collate first PDF in reverse page order.")
        parser.add_argument(
            "--reverse2", action="store_true",
            help="Collate second PDF in reverse page order.")
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
        return(args0)

    ###########################################################################
    #
    args = processOptions()
    if (args.iencoding and not args.oencoding):
        args.oencoding = args.iencoding
    if (args.oencoding):
        # https://stackoverflow.com/questions/4374455/
        # sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
        #sys.stdout.reconfigure(encoding=args.oencoding)
        pass

    pfh1 = open(args.files[0], "rb")
    reader1 = PyPDF2.PdfFileReader(pfh1)
    pfh2 = reader2 = None
    if (args.files[1]):
        pfh2 = open(args.files[1], "rb")
        reader2 = PyPDF2.PdfFileReader(pfh2)

    if (args.action == 'getMeta'):
        getMetadata(reader1)
    elif (args.action == 'split'):
        splitPages(reader1)
    elif (args.action == 'splitEvenOdd'):
        splitEvenOdd(reader1)
    elif (args.action == 'cat'):
        catPages(reader1, reader2)
    elif (args.action == 'reverse'):
        reversePages(reader1)
    elif (args.action == 'collate'):
        collatePages(reader1, reader2)
    elif (args.action == 'signature'):
        makeSignature(reader1)
    else:
        fatal("Unknown action '%s'." % (args.action))

    pfh1.close()
    if (pfh2): pfh2.close()

    if (not args.quiet):
        warning0("pdfUtil.py: Done.\n")
