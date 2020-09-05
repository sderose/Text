#!/usr/bin/env python
#
# json2xml.py, by Steven J. DeRose.
#
from __future__ import print_function
import sys
import os
import re
import argparse

import json
#import pyxser  # https://sourceforge.net/projects/pyxser/

__metadata__ = {
    'title'        : "json2xml.py",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2012-12-04",
    'modified'     : "2020-04-17",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']

descr = """
=Usage=

json2xml.py [options] [files]

Simple but thorough conversion. Can load from JSON, or import this script
and call `mySerialize()` on most any Python object, whether it came from
JSON or not.

=head2 Notes

The `json` decoder library produces exactly these Python types:

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

Thus, these are the only Python types passed to the XML serializer.

=Options=

* '''--noprop'''

Untag the "pyxs:prop" elements from the XML output. Where they have names,
the name is lost (should instead move these items onto the container element
as named attributes, or something like that).

* '''--nonamespace'''

Delete the "pyxs:" namespace prefixes from all output XML elements.

* '''--nosize'''

Delete the "size" attributes from the XML output.

* '''--notype'''

Delete the "type" attributes from the XML output (this would mainly be
useful in environments that don't care, such as many scripting languages,
or JSON data such as this script deals with).

* '''--pad''' I<n>

Left-pad integers with spaces, to a minimum of I<n> columns.
(incomplete -- presently just puts a tab on each side instead).

* '''--quiet''' OR '''-q'''
Suppress most messages.

* '''--verbose'''

Add more detailed messages (doesn't do much at the moment).

* '''--version'''

Display version info and exit.

=Related Commands=

`xml2json.py` -- essentially the opposite. But these don't exactly round-trip,
because what they convert ''to'', is conditioned heavily by the input language.
There should be an exact round-tripping feature added to both.

`json` -- built-in Python package for JSON support.

`pyxser` -- Python library (written in C by Daniel Molina Wegener),
to serialize any Python object as XML. [https://github.com/dmw/pyxser].
I used this at first, but had some problems, so rolled my own.

`formatRec()` in my `alogging.py`, which formats fairly arbitrary Python structures for
nice debugging display, and will likey add HTML and XML output options.


=Known bugs and limitations=

* JSON "objects" differ substantially from objects in most languages:

** JSON allows arbitrary string names, not just identifiers
** "objects" have no class they are a member of
** there is no relationship between the names used in various instance
** you cannot (within JSON proper) constrain what names appear
** the behavior if names are duplicated is inconsistent across applications
** it isn't like JavaScript where a name like "03.0000000000000001" is the same
as "3".
** Particular properties in objects cannot be restricted to a certain
datatype, or even to be atomic or homogeneous or interconvertible.
** JSONM objects have no identifiers, so no built-in way to refer to each other.

* JSON objects are also unlike non-objects dictionaries or hashes in most languages:

** You can ''only'' use strings, not ints, etc.
** You have to quote the names.
** You can't tell hashes apart from actual objects, or from other things you'd have to
represent using them in JSON (Python namedtuple, C struct, etc.)

Of course a particular JSON user can add invent their own personal conventions
for anything on top.
But this all means that JSON ends up more verbose than other languages
(all those quotes add up), and less informative (if dicts and objects are "the same",
then you've lost the ability to reconstruct the right one on re-load).


=Rights=

Copyright 2012 by Steven J. DeRose. This work is licensed under a Creative Commons
Attribution-Share Alike 3.0 Unported License. For further information on
this license, see [http://creativecommons.org/licenses/by-sa/3.0].

For the most recent version, see [http://www.derose.net/steve/utilities] or
[http://github.com/sderose].

=History=

* 2012-12-04: Written by Steven J. DeRose.
* 2018-04-18: lint.
* 2020-03-04: line, POD to MarkDown. New layout.
* 2020-04-17: Various bugs. Fix output escaping. Start handling "objects" as
distinct from "dicts", even though JSON doesn't know. Write out subclasses
(even though they won't show up for data that was really JSON).


=To do=

* Fix -pad.
* Option to move scalar named items to parent attributes, or not to tag scalars.
* Option to number items in lists, put len on collections
* Option to optimize sparse lists (say, where item is same as prev, gen:
    <repeat n="200"/>

=Options=
"""

def warn(lvl, msg):
    if (args.verbose >= lvl): sys.stderr.write(msg+"\n")

# What to map various troublesome strings to.
#
escMap = {
    '"'       : '&quo;',
    "'"       : '&apos;',
    '<'       : '&lt;',
    '>'       : '&gt;',
    '?>'      : '?&gt;',
    '-->'     : '- - >',
    ']]>'     : '&rsqb;]>',
    '&'       : '&amp;',
}
def _escaper(mat):
    return escMap[mat.group(1)]
def escapeAttribute(s):
    return re.sub(r'(["<&])', _escaper, s)
def escapeText(s):
    return re.sub(r'(<|&|]]>])', _escaper, s)
def escapePI(s):
    return re.sub(r'(\?>)', _escaper, s)
def escapeComment(s):
    return re.sub(r'(-->)', _escaper, s)


###############################################################################
# See http://stackoverflow.com/questions/1305532/convert-python-dict-to-object
# Promotes a dict to an Object.
#
class Str:
    def __init__(self, **entries):
        self.__dict__.update(entries)

def mySerialize(pyObject, istring='    ', depth=0):
    """Return an XML serialization of the object (recursive).
    Typically we expect JSON, but it doesn't have to be.
    """
    # Collection types
    #
    buf = ""
    if (isinstance(pyObject, tuple)):
        if (istring): buf += "\n" + (istring * depth)
        if (type(pyObject).__name__ != 'tuple'):
            buf += '<tuple class="%s">' % (type(pyObject).__name__)
        else:
            buf += "<tuple>"
        depth += 1
        for k, v in pyObject.items():
            if (istring): buf += "\n" + (istring * depth)
            buf += "<item>%s</item>" % (mySerialize(v, istring=istring,depth=depth))
        depth -= 1
        buf += "</tuple>"
        return buf

    elif (isinstance(pyObject, dict)):
        if (istring): buf += "\n" + (istring * depth)
        if (type(pyObject).__name__ != 'dict'):
            buf += '<dict class="%s">' % (type(pyObject).__name__)
        else:
            buf += "<dict>"
        depth += 1
        for k, v in pyObject.items():
            if (istring): buf += "\n" + (istring * depth)
            buf += "<ditem key=\"%s\">%s</ditem>" % (
                k, mySerialize(v, istring=istring,depth=depth+1))
        depth -= 1
        if (istring): buf += "\n" + (istring * depth)
        buf += "</dict>"
        return buf

    elif (isinstance(pyObject, list)):
        if (istring): buf += "\n" + (istring * depth)
        if (type(pyObject).__name__ != 'list'):
            buf += '<list class="%s">' % (type(pyObject).__name__)
        else:
            buf += "<list>"
        depth += 1
        for v in pyObject:
            if (istring): buf += "\n" + (istring * depth)
            #buf += "<item>%s</item>" % (mySerialize(v, istring=istring, depth=depth))
            buf += mySerialize(v, istring=istring, depth=depth)
        depth -= 1
        buf += "</list>"
        return buf

    # Scalar types
    #
    elif (isinstance(pyObject, int)):
        return '<i v="%d"/>' % (pyObject)

    elif (isinstance(pyObject, float)):
        return '<f v="%f"/>' % (pyObject)

    elif (isinstance(pyObject, complex)):
        return '<c r="%f" i="%f"/>' % (pyObject.real, pyObject.imag)

    elif (isinstance(pyObject, str)):
        return '<u>%s</u>' % (escapeText(pyObject))

    elif (pyObject is True):
        return '<T/>'

    elif (pyObject is False):
        return '<F/>'

    elif (pyObject is None):
        return '<None/>'

    elif (isinstance(pyObject, object)):
        if (istring): buf += "\n" + (istring * depth)
        if (type(pyObject).__name__ != 'object'):
            buf += '<object class="%s">' % (type(pyObject).__name__)
        else:
            buf += "<object>"
        depth += 1
        for k, v in pyObject.__dict__:
            if (callable(v)): continue
            if (k.startswith('__')): continue
            if (istring): buf += "\n" + (istring * depth)
            buf += "<item>%s</item>" % (mySerialize(v, istring=istring,depth=depth))
        depth -= 1
        buf += "</object>"
        return buf

    else:
        warn(0, "Unknown type for export: %s." % (type(pyObject)))


###############################################################################
# Test whether two collections are miscible. The details differ by type,
# but generally the have to have the same size, same named members (if any),
# and (optionally) same types for corresponding members.
#
# This gives a decent shot at telling JSON actual, dicts from objects -- objects
# should have a consistent set of items, and typically their datatypes.
# Similarly, you probably only want to use sparse-array techniques for homogeneous
# lists.
#
# TODO: Should they also be the exact same (sub) class?
#
def tuplesMatch(t1, t2, checkValueTypes=True):
    assert (isinstance(t1, tuple))
    assert (isinstance(t2, tuple))
    if (len(t1) != len(t1)): return False
    if (not checkValueTypes): return True
    for i in range(len(t1)):
        if (type(t1[i]) != type(t2[i])): return False
    return True

def dictsMatch(d1, d2, checkValueTypes=True):
    assert (isinstance(d1, dict))
    assert (isinstance(d2, dict))
    keySeq1 = sorted(d1.keys())
    keySeq2 = sorted(d2.keys())
    if (keySeq1 != keySeq2): return False
    if (checkValueTypes):
        for k in keySeq1:
            if (type(d1[k]) != type(d2[k])): return False
    return True

def listsMatch(l1, l2, checkValueTypes=True, checkLengths=True):
    """Lists often get used as tuples, in which case we want them to be the
    same size and maybe types. But in other cases, two homogeneous lists
    of different lengths could count as matching, so we add that option.
    """
    assert (isinstance(l1, list))
    assert (isinstance(l2, list))
    if (checkLengths and len(l1) != len(l1)): return False
    if (checkValueTypes):
        for i in range(len(l1)):
            if (type(l1[i]) != type(l2[i])): return False
    return True

def objectsMatch(o1, o2, checkValueTypes=True, checkExactClass=True):
    assert (isinstance(o1, object))
    assert (isinstance(o2, object))
    if (checkExactClass and type(o1).__name__ != type(o2).__name__): return False
    keySeq1 = sorted(o1.__dict__.keys())
    keySeq2 = sorted(o2.__dict__.keys())
    if (keySeq1 != keySeq2): return False
    if (checkValueTypes):
        for k in keySeq1:
            if (type(o1.__dict__[k]) != type(o2.__dict__[k])): return False
    return True


def dictKeysAreIdentifiers(pyObject, PythonKeyWordsOk=True):
    """Check whether all the keys used in a dict, are legit Python identifiers.
    """
    assert (isinstance(pyObject, dict))
    import keyword
    for k in pyObject.keys():
        if (type(k) != str): return False
        if (not str.isidentifier(k)): return False
        if (not PythonKeyWordsOk and keyword.iskeyword()): return False
    return True

def isListHomogeneous(l1):
    assert (isinstance(l1, list))
    if (len(l1) == 0): return True
    type0 = type(l1[0])
    for i in range(1, len(l1)):
        if (type(l1[i]) != type0): return False
    return True


###############################################################################
###############################################################################
# Main
#
def processOptions():
    try:
        from BlockFormatter import BlockFormatter
        parser = argparse.ArgumentParser(
            description=descr, formatter_class=BlockFormatter)
    except ImportError:
        parser = argparse.ArgumentParser(description=descr)

    parser.add_argument(
        "--istring",      type=str, default='    ',
        help='Repeat this string to indent the output.')
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


args = processOptions()

if (len(args.files) == 0):
    fh = sys.stdin
elif (not os.path.isfile(args.files[0])):
    warn(0, "Can't find file '" + args.files[0] + "'.")
    sys.exit(0)
else:
    fh = open(args.files[0], "r")

# Load the JSON and make a Python Object.
#
try:
    pyObject0 = json.load(fh)
except json.decoder.JSONDecodeError as e:
    warn(0, "JSON load failed:\n    %s" % (e))
    sys.exit()

theXml0 = mySerialize(pyObject0, istring=args.istring)

print(theXml0)

sys.exit(0)
