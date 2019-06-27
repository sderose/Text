#!/usr/bin/env python
#
# json2xml.py
#
# 2012-12-04: Written by Steven J. DeRose.
# 2018-04-18: lint.
#
# To do:
#     Fix -pad.
#     Option to move atomic named items to parent attributes?
#
from __future__ import print_function
import sys
import os
import re
import argparse
#import string
#import math

import json
import pyxser  # https://sourceforge.net/projects/pyxser/

#from sjdUtils import sjdUtils
from alogging import ALogger
#su = sjdUtils()
#su.setColors(args.color)
lg = ALogger(1)

__version__ = "2018-04-18"


###############################################################################
# Process options
#
def processOptions():
    try:
        from MarkupHelpFormatter import MarkupHelpFormatter
        formatter = MarkupHelpFormatter
    except ImportError:
        formatter = None
    parser = argparse.ArgumentParser(
        description=descr, formatter_class=formatter)

    parser.add_argument(
        "--noprop",       action='store_true',
        help='Untag the "pyxs:prop" element surrounding data atoms.')
    parser.add_argument(
        "--nonamespaces", action='store_true',
        help='Delete the "pyxs:" namespace prefix.')
    parser.add_argument(
        "--nosize",       action='store_true',
        help='Delete the "size" attribute everywhere.')
    parser.add_argument(
        "--notype",       action='store_true',
        help='Delete the "type" attribute everywhere.')
    parser.add_argument(
        "--pad",          type=int,
        help='Left-pad integers to this many columns.')
    parser.add_argument(
        "--quiet", "-q",  action='store_true',
        help='Suppress most messages.')
    parser.add_argument(
        "--verbose",      action='count', default=0,
        help='Add more messages (repeatable).')
    parser.add_argument(
        "--version",      action='version', version='Version of '+__version__)

    parser.add_argument(
        'files',         nargs=argparse.REMAINDER,
        help='Path(s) to input file(s).')

    args0 = parser.parse_args()

    if (os.environ["PYTHONIOENCODING"] != "utf_8"):
        print("Warning: PYTHONIOENCODING is not utf_8.")
    return args0


###############################################################################
###############################################################################
# From http://stackoverflow.com/questions/1305532/convert-python-dict-to-object
# Promotes a dict to an Object.
#
class Str:
    def __init__(self, **entries):
        self.__dict__.update(entries)


def serialize(pyObject):
    s = Str(**pyObject)
    theXml = pyxser.serialize(obj=s, enc="utf-8")

    # De-clutter
    #
    if (args.pad): # incomplete
        theXml = re.sub(r'(<pyxs:prop type="int"[^>]*>)(\d+)', r'\1\t\2\t', theXml)

    if (args.noprop):
        sys.stderr.write("Dropping prop elements\n")
        theXml = re.sub(r'<pyxs:prop.*?>',  '',   theXml)
        theXml = re.sub(r'</pyxs:prop>',    '',   theXml)

    if (args.nonamespace):
        sys.stderr.write("Dropping namespaces\n")
        theXml = re.sub(r'<pyxs:',          '<',  theXml)
        theXml = re.sub(r'</pyxs:',         '</', theXml)

    if (args.nosize):
        sys.stderr.write("Dropping size attributes\n")
        theXml = re.sub(r' size="\d+">',    '>',  theXml)

    if (args.notype):
        sys.stderr.write("Dropping type attributes\n")
        theXml = re.sub(r' type="\w+">',    '>',  theXml)

    return theXml

def mySerialize(pyObject, depth=0):

    if (isinstance(pyObject, dict)):
        buf = "<dict>"
        for k, v in pyObject.items:
            buf += "<ditem key=\"%s\">%s</ditem>\n" % (k, mySerialize(v, depth+1))
        buf += "</dict>\n"
        return buf
    elif (isinstance(pyObject, dict)):
        buf = "<list>"
        for k, v in pyObject.items:
            buf += "<item>%s</item>\n" % (mySerialize(v, depth+1))
        buf += "</list>\n"
        return buf
    elif (isinstance(pyObject, int)):
        return "<int>%d</int>" % (pyObject)
    elif (isinstance(pyObject, long)):
        return "<long>%d</long>" % (pyObject)
    elif (isinstance(pyObject, float)):
        return "<float>%f</float>" % (pyObject)
    elif (isinstance(pyObject, unicode)):
        return "<unicode>%f</unicode>" % (pyObject)
    elif (pyObject is True):
        return "<True/>"
    elif (pyObject is False):
        return "<False/>"
     elif (pyObject is None):
        return "<None/>"


###############################################################################
###############################################################################
# Main
#
args = processOptions()

if (len(args.files) == 0):
    fh = sys.stdin
elif (not os.path.isfile(args.files[0])):
    lg.vMsg(0,"Can't find file '" + args.files[0] + "'.")
    sys.exit(0)
else:
    fh = open(args.files[0], "r")

# Load the JSON and make a Python Object.
#
pyObject = json.load(fh)

if (args.pyxser): theXml = serialize(pyObject)
else: theXml = mySerialize(pyObject)

print(theXml)

sys.exit(0)



###############################################################################
###############################################################################
###############################################################################
#
perldoc = """

=pod

=head1 Usage

json2xml.py [options]

Simple but thorough conversion using off-the-shelf packages 'json' and 'pyxser'.


=head2 Notes

The C<json> decoder library produces exactly these Python types:

    JSON          -- Python
    --------------------------
    object        -- dict
    array         -- list
    string        -- unicode
    number (int)  -- int, long
    number (real) -- float
    true          -- True
    false         -- False
    null          -- None

Thus, these are the only Python types passed to the XML serialized library.
This makes some of the generality of C<pyxser> unnecessary here.



=head1 Options

=over

=item * B<--noprop>

Untag the "pyxs:prop" elements from the XML output. Where they have names,
the name is lost (should instead move these items onto the container element
as named attributes, or something like that).

=item * B<--nonamespace>

Delete the "pyxs:" namespace prefixes from all output XML elements.

=item * B<--nosize>

Delete the "size" attributes from the XML output.

=item * B<--notype>

Delete the "type" attributes from the XML output (this would mainly be
useful in environments that don't care, such as many scripting languages,
or JSON data such as this script deals with).

=item * B<--pad> I<n>

Left-pad integers with spaces, to a minimum of I<n> columns.
(incomplete -- presently just puts a tab on each side instead).

=item * B<--quiet> OR B<-q>
Suppress most messages.

=item * B<--verbose>

Add more detailed messages (doesn't do much at the moment).

=item * B<--version>

Display version info and exit.

=back



=head Related Commands

C<json> -- built-in Python package for JSON support.

C<pyxser> -- Python library (written in C by Daniel Molina Wegener),
to serialize any Python object as XML. L<https://github.com/dmw/pyxser>.



=head1 Known bugs and limitations



=head1 Ownership

This work by Steven J. DeRose is licensed under a Creative Commons
Attribution-Share Alike 3.0 Unported License. For further information on
this license, see L<http://creativecommons.org/licenses/by-sa/3.0/>.

For the most recent version, see L<http://www.derose.net/steve/utilities/>.

=cut
"""
