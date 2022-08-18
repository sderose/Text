#!/usr/bin/env python3
#
# list2htmlForm: Make an HTML form from a list of items.
# 2012-04-26: Written by Steven J. DeRose.
#
import sys
import os
import re
import argparse

__metadata__ = {
    'title'        : "list2htmlForm",
    "description"  : "Make an HTML form from a list of items.",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2012-04-26",
    'modified'     : "2022-08-18",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/",
}
__version__ = __metadata__['modified']

descr = """
=Usage=

list2htmlForm [options]

Make each line of a file into an item in an XHTML form.
You can make radio buttons, checkboxes or a pop-up menu,
and lay them out in various ways.


=Options=

* B<--break>
Put an HTML C<< <br> >> in front of each item (not applicable to I<--type menu>).

* B<--group> I<g>
Use I<g> as the group name for buttons.

* B<--type>
Radio (default), checkbox, or menu?

* B<--verbose>
Add more detailed messages (doesn't do much at the moment).

* B<--version>
Display version info and exit.


=Related Commands=


=Known bugs and limitations=


=History=

* 2012-04-26: Written by Steven J. DeRose.
* 2018-04-18: lint.
* 2020-04-04: lint, new layout, POD to MarkDown.
* 2022-08-18: Layout, lint, etc.


=Rights=

This program is Copyright 2012 by Steven J. DeRose.
It is hereby licensed under the Creative Commons
Attribution-Share-Alike 3.0 unported license.
For more information on this license, see [here|"https://creativecommons.org"].

For the most recent version, see [http://www.derose.net/steve/utilities] or
[http://github/com/sderose].


=Options=
"""

def vMsg(level, msg):
    if (args.verbose < level): return
    if (msg.startswith("====")): sys.stderr.write("\n" + "*" * 79 + '\n')
    sys.stderr.write(msg+'\n')


###############################################################################
# Process options
#
try:
    from BlockFormatter import BlockFormatter
    parser = argparse.ArgumentParser(
        description=descr, formatter_class=BlockFormatter)
except ImportError:
    parser = argparse.ArgumentParser(description=descr)

parser.add_argument(
    "--verbose", action='count', default=0,
    help='Add more messages (repeatable).')
parser.add_argument(
    "--break", action='store_true', dest="breakEm",
    help='Put a <br> before each item.')
parser.add_argument(
    "--group", type=str, default="group_01",
    help='Group name for checkbox or radio button.')
parser.add_argument(
    "--type", type=str, default="radio",
    help='Kind of input control: radio or checkbox or menu.')
parser.add_argument(
    "--verbose", "-v", action='count', default=0,
    help='Add more messages (repeatable).')
parser.add_argument(
    "--version", action='version', version=__version__,
    help='Display version information, then exit.')

parser.add_argument(
    "files", nargs=argparse.REMAINDER,
    help='Path(s) to input file(s)')

args = parser.parse_args()

if (os.environ["PYTHONIOENCODING"] != "utf_8"):
    print("Warning: PYTHONIOENCODING is not utf_8.")


###############################################################################
#
def clean(s):
    s = re.sub(r'[^-:.\w]', '_', s)
    if (len(s) == 0 or s[0] in "-:."): s = "A_" + s
    return(s)

def doOneFile(someFH):
    rec = ""
    recnum = 0

    print('<form id="form_01">')
    if (args.type == "menu"): print("  <select>")
    while (1):
        rec = someFH.readline()
        if (not rec): break
        recnum += 1
        item = rec.rstrip()
        if (args.type == "checkbox"):
            inp = ('<input type="{0}" name="{1}" type="{2}"/>{3}'.
                   format(args.type, args.group,
                          clean(item), item.capitalize()))
        elif (args.type == "radio"):
            inp = ('<input type="{0}" name="{1}" type="{2}"/>{3}'.
                   format(args.type, args.group,
                          clean(item), item.capitalize()))
        elif (args.type == "menu"):
            inp = ('<option>{0}</option>'.format(item.capitalize()))
        else:
            vMsg(0, "Unknown -type: "+args.type)
            sys.exit()
        if (args.breakEm and args.type != "menu"):
            inp = "<br />" + inp
        print("    " + inp)
    # EOF
    if (args.type == "menu"): print("  </select>")
    print('</form>')
    return(recnum)


###############################################################################
# Main
#
totalRecords = 0
totalFiles = 0

if (len(args.files) == 0):
    fh = sys.stdin
for fnum in (range(len(args.files))):
    totalFiles += 1
    f = args.files[fnum]
    if (os.path.isfile(f)):
        fh = open(f, "r")
        totalRecords += doOneFile(fh)
        fh.close()
    else:
        vMsg(0,"Can't find file '" + f + "'.")

vMsg(0, "Done, %d files, %d records." % (totalFiles, totalRecords))
