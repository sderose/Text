#!/usr/bin/env python3
# From Claude 3.5, w/ sjd.
#
import codecs
import re
import logging

lg = logging.getLogger("%NAME%")

__metadata__ = {
    "title"        : "lincolnIndex",
    "description"  : "Calculate Lincoln Index.",
    "rightsHolder" : "Steven J. DeRose, and Claude 3.5",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.9",
    "created"      : "2024-07-05",
    "modified"     : "2024-07-05",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]

descr = """
Given two files with one item per line (ignoring comments post-#),
report their sizes and their Lincoln Index.
"""

def read_file(filename:str):
    lg.info("Reading file: %s", filename)
    items = []
    with codecs.open(filename, 'rb', encoding=args.iencoding) as file:
        for rec in file.readlines():
            rec = rec.strip()
            if (rec=="" or rec.startswith("#")): continue
            if ("#" in rec): rec = re.sub(r"\s*#.*", "", rec)
            if (args.ignoreCase): rec = rec.lower()
            items.append(rec)
    return items


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
            "--ignoreCase", "--ignore-case", "-i", action="store_true",
            help="Disregard case distinctions.")
        parser.add_argument(
            "--intersection", action="store_true",
            help="Display the intersection of the lists.")
        parser.add_argument(
            "--quiet", "-q", action="store_true",
            help="Suppress most messages.")
        parser.add_argument(
            "--union", action="store_true",
            help="Display the union of the lists.")
        parser.add_argument(
            "--verbose", "-v", action="count", default=0,
            help="Add more messages (repeatable).")
        parser.add_argument(
            "--version", action="version", version=__version__,
            help="Display version information, then exit.")

        parser.add_argument(
            "file1", type=str,
            help="Path to first input file")
        parser.add_argument(
            "file2", type=str,
            help="Path to second input file")

        args0 = parser.parse_args()
        if (lg and args0.verbose):
            logging.basicConfig(level=logging.INFO - args0.verbose)

        return(args0)


    ###########################################################################
    #
    args = processOptions()

    try:
        list1 = read_file(args.file1)
        n1 = len(list1)
        print("Number of items in first list: %d" % (n1))

        list2 = read_file(args.file2)
        n2 = len(list2)
        print("Number of items in second list: %d" % (n2))

        uset = set(list1).union(set(list2))
        usize = len(uset)

        iset = set(list1).intersection(set(list2))
        isize = len(iset)
        print("Union: %d, Intersection: %d" % (usize, isize))

        if (isize): lincoln = float(n1 * n2) / isize
        else: lincoln = float('inf')

        print("Lincoln Index: %f" % (lincoln))

        if (args.union):
            print("\n####### Union:\n    %s" %
                ("\n    ".join(sorted(list(uset)))))

        if (args.intersection):
            print("\n####### Intersection:\n    %s"
                % ("\n    ".join(sorted(list(iset)))))

    except FileNotFoundError:
        print("File(s) not found.")
