#!/usr/bin/env python
#
# json2xml.py: Convert JSON to XML or other forms.
# Written 2012-12-04 by Steven J. DeRose.
#
from __future__ import print_function
import sys
import os
import re
import codecs
import json
#import pyxser  # https://sourceforge.net/projects/pyxser/

from PowerWalk import PowerWalk, PWType
from alogging import ALogger
lg = ALogger(1)

__metadata__ = {
    'title'        : "json2xml.py",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2012-12-04",
    'modified'     : "2020-20-09",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']


descr = """
=Usage=

json2xml.py [options] [files]

Simple but thorough conversion of JSON, or of pretty much any Python data,
to XML syntax. It's smart enough to represent not only the list vs. dict
distinction which comes naturally to JSON, but

You can run this from the command line
to load and convert a JSON file(s). Or you can use this from Python code
by calling `serialize2xml()` on most any Python object (whether it came from
JSON or not).

By default, it converts (losslessly, I hope) from JSON to XML. But use the
`--oformat` option to choose other output formats (specifying `--oformat json`
will get you pretty-printing).

==Notes==

There are 3 data models in play here: JSON, XML, and Python.
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

There are also differences such as that JSON dict keys can only be strings,
and JSON files can of course have multiple entries with the same key (the
result of which is not necessarily consistent across JSON tools).

Thus, these are the only Python types passed to the XML serializer for data
that was loaded by JSON. However, this package handles other Python types.


==Example==

    [{
        "atom01":        1,
        "atom03":        3.14,
        "atom04":        true,
        "atom06":        null,
        "atom07":        "",
        "atom09":        "token",
        "atom10":       "a\nbc\t ",
        "atom11":       " < & ]]> \" \n \r \t \\",
        "list1_Ints":   [ 1, 22, 3333 ],
        "list2":        [ 9.0, false, "aardvark", [ 2, 3 ], [] ],
        "list5_Hashes":  [
            { "h1a":"aardvark",  "h1b": "boar" },
            { "h2a" :"cat",      "h2b" : "dog" },
            { "h3a"
            :
            "elephant"
            ,
            "h3b"            :       4.2 },
            {}
        ]
    }]

becomes (by default) this:

    <list>
        <dict>
            <ditem key="atom01"><i v="1"/></ditem>
            <ditem key="atom03"><f v="3.140000"/></ditem>
            <ditem key="atom04"><i v="1"/></ditem>
            <ditem key="atom06"><None/></ditem>
            <ditem key="atom07"><u></u></ditem>
            <ditem key="atom09"><u>token</u></ditem>
            <ditem key="atom10"><u>a
bc	 </u></ditem>
            <ditem key="atom11"><u> &lt; &amp; ]]> "
         </u></ditem>
            <ditem key="list1_Ints">
                <list>
                    <i v="1"/>
                    <i v="22"/>
                    <i v="3333"/></list></ditem>
            <ditem key="list2">
                <list>
                    <f v="9.000000"/>
                    <i v="0"/>
                    <u>aardvark</u>

                    <list>
                        <i v="2"/>
                        <i v="3"/></list>

                    <list></list></list></ditem>
            <ditem key="list5_Hashes">
                <list>

                    <dict>
                        <ditem key="h1a"><u>aardvark</u></ditem>
                        <ditem key="h1b"><u>boar</u></ditem>
                    </dict>

                    <dict>
                        <ditem key="h2a"><u>cat</u></ditem>
                        <ditem key="h2b"><u>dog</u></ditem>
                    </dict>

                    <dict>
                        <ditem key="h3a"><u>elephant</u></ditem>
                        <ditem key="h3b"><f v="4.200000"/></ditem>
                    </dict>

                    <dict>
                    </dict></list></ditem>
        </dict></list>


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

* '''--oformat''' `f`

Choose what form to write out. Choices include:

** 'xml': the default, as described above.
** 'json': just gets pretty-printing)
** 'report': a summary report, as produced by my `alogging.ALogger.formatRec()`.
** ...more to be added, such as Python and Perl dcls, maybe HTML list layout.

* '''--pad''' `n`

Left-pad integers with spaces, to a minimum of `n` columns.
(incomplete -- presently just puts a tab on each side instead).

* '''--quiet''' OR '''-q'''
Suppress most messages.

* '''--verbose'''

Add more detailed messages (doesn't do much at the moment).

* '''--version'''

Display version info and exit.


=Related Commands=

My `xml2json.py` -- essentially the opposite. But these don't exactly
round-trip, because what they convert ''to'', is conditioned heavily by
the input language. There should be an exact round-tripping feature added to both.

`json` -- built-in Python package for JSON support.

`pyxser` -- Python library (written in C by Daniel Molina Wegener),
to serialize any Python object as XML. [https://github.com/dmw/pyxser].
I used this at first, but had some problems, so rolled my own.

`formatRec()` in my `alogging.py` formats fairly arbitrary Python structures for
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

Of course a JSON user can add invent conventions for anything on top, at
some cost in verbosity, effective portability, and/or clarity.


=To do=

* Test with non-string dict keys.
* Add support for changing the XML tags to use.
* Add more --oformat choices, such as Python and Perl dcls.
* Finish support for homogeneous collections.
* Add a loader for round-tripping straight into Python structures.


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
* 2020-12-09: Clean up. Add --oformat, integrate PowerWalk and alogging.


=To do=

* Fix --pad.
* Option to move scalar named items to parent attributes, or not to tag scalars.
* Option to number items in lists, put len on collections
* Option to optimize sparse lists (say, where item is same as prev, gen:
    <repeat n="200"/>


=Options=
"""


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

def serialize2xml(pyObject, istring='    ', depth=0):
    """Return an XML serialization of the object (recursive).
    Typically we expect JSON, but it doesn't have to be.
    """
    # Collection types
    #
    buf = ""
    if (isinstance(pyObject, tuple)):                   # TUPLE
        if (istring): buf += "\n" + (istring * depth)
        if (type(pyObject).__name__ != 'tuple'):
            buf += '<tuple class="%s">' % (type(pyObject).__name__)
        else:
            buf += "<tuple>"
        depth += 1
        for k, v in pyObject.items():
            if (istring): buf += "\n" + (istring * depth)
            buf += "<item>%s</item>" % (
                serialize2xml(v, istring=istring,depth=depth))
        depth -= 1
        buf += "</tuple>"
        return buf

    elif (isinstance(pyObject, dict)):                   # DICT
        if (istring): buf += "\n" + (istring * depth)
        if (type(pyObject).__name__ != 'dict'):
            buf += '<dict class="%s">' % (type(pyObject).__name__)
        else:
            buf += "<dict>"
        depth += 1
        for k, v in pyObject.items():
            if (istring): buf += "\n" + (istring * depth)
            buf += "<ditem key=\"%s\">%s</ditem>" % (
                k, serialize2xml(v, istring=istring,depth=depth+1))
        depth -= 1
        if (istring): buf += "\n" + (istring * depth)
        buf += "</dict>"
        return buf

    elif (isinstance(pyObject, list)):                   # LIST
        if (istring): buf += "\n" + (istring * depth)
        if (type(pyObject).__name__ != 'list'):
            buf += '<list class="%s">' % (type(pyObject).__name__)
        else:
            buf += "<list>"
        depth += 1
        for v in pyObject:
            if (istring): buf += "\n" + (istring * depth)
            #buf += "<item>%s</item>" % (serialize2xml(v, istring=istring, depth=depth))
            buf += serialize2xml(v, istring=istring, depth=depth)
        depth -= 1
        buf += "</list>"
        return buf

    # Scalar types (order of testing matters)
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
            buf += "<item>%s</item>" % (
                serialize2xml(v, istring=istring,depth=depth))
        depth -= 1
        buf += "</object>"
        return buf

    else:
        lg.vMsg(0, "Unknown type for export: %s." % (type(pyObject)))


###############################################################################
# Test whether two collections are miscible. The details differ by type,
# but generally they must have the same size, same named members (if any),
# and (optionally) same types for corresponding members.
#
# This gives a decent shot at telling actual dicts from objects -- objects
# should have a consistent set of items, and typically consistent datatypes.
# Similar for homogeneous lists.
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
    if (checkExactClass and type(o1).__name__ != type(o2).__name__):
        return False
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
            "--iencoding",        type=str, metavar='E', default="utf-8",
            help='Assume this character coding for input. Default: utf-8.')
        parser.add_argument(
            "--istring", type=str, default='    ',
            help='Repeat this string to indent the output.')
        parser.add_argument(
            "--noprop", action='store_true',
            help='Untag the "pyxs:prop" element surrounding data atoms.')
        parser.add_argument(
            "--nonamespaces", action='store_true',
            help='Delete the "pyxs:" namespace prefix.')
        parser.add_argument(
            "--nosize", action='store_true',
            help='Delete the "size" attribute everywhere.')
        parser.add_argument(
            "--notype", action='store_true',
            help='Delete the "type" attribute everywhere.')
        parser.add_argument(
            "--oformat", type=str, default='xml',
            choices=[ 'xml', 'json', 'report' ],
            help='Write the output to this form. Default: xml.')
        parser.add_argument(
            "--pad", type=int,
            help='Left-pad integers to this many columns.')
        parser.add_argument(
            "--quiet", "-q", action='store_true',
            help='Suppress most messages.')
        parser.add_argument(
            "--sortkeys", "--sort_keys", "--sort-keys", action='store_true',
            help='Delete the "type" attribute everywhere.')
        parser.add_argument(
            "--verbose", action='count', default=0,
            help='Add more messages (repeatable).')
        parser.add_argument(
            "--version", action='version', version='Version of '+__version__)

        parser.add_argument(
            'files', nargs=argparse.REMAINDER,
            help='Path(s) to input file(s).')

        args0 = parser.parse_args()

        lg.setVerbose(args0.verbose)
        if (os.environ["PYTHONIOENCODING"] != "utf_8"):
            lg.vMsg(0, "Warning: PYTHONIOENCODING is not utf_8.")
        return args0


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
                lg.vMsg(0, "Cannot open '%s':\n    %s" % (e))
                return 0

        try:
            pyObject0 = json.load(fh)
        except json.decoder.JSONDecodeError as e:
            lg.vMsg(0, "JSON load failed for %s:\n    %s" % (path, e))
            sys.exit()

        if (args.oformat == 'xml'):
            buf = serialize2xml(pyObject0, istring=args.istring)
        elif (args.oformat == 'json'):
            buf = json.dumps(pyObject0,
                sort_keys=args.sortkeys, indent=len(args.istring))
        elif (args.oformat == 'report'):
            buf = lg.formatRec(pyObject0)
        else:
            lg.vMsg(-1, "Unknown --oformat value '%s'." % (args.oformat))

        print(buf)
        return


    ###########################################################################
    #
    args = processOptions()

    if (len(args.files) == 0):
        lg.vMsg(0, "json2xml.py: No files specified....")
        doOneFile(None)
    else:
        pw = PowerWalk(args.files, open=False, close=False,
            encoding=args.iencoding)
        pw.setOptionsFromArgparse(args)
        for path0, fh0, what0 in pw.traverse():
            if (what0 != PWType.LEAF): continue
            doOneFile(path0)
