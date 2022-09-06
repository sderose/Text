#!/usr/bin/env python3
#
# json2xml.py: Convert JSON (or Python data) to XML or other syntax.
# 2012-12-04: Written by Steven J. DeRose.
#
import sys
import os
import re
import math
import json
import codecs
#import pyxser  # https://sourceforge.net/projects/pyxser/

from PowerWalk import PowerWalk, PWType
from alogging import ALogger
lg = ALogger(1)

__metadata__ = {
    "title"        : "json2xml",
    "description"  : "Convert JSON (or Python data) to XML or other syntax.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2012-12-04",
    "modified"     : "2022-09-06",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]

sampleJSON = """
    [{
        "atom01":        1,
        "atom03":        3.14,
        "atom04":        true,
        "atom05":        false,
        "atom06":        null,
        "atom07":        "",
        "atom09":        "token",
        "atom08":        "micro is \xB5, as in \xB5second.",
        "atom10":       " < & ]]> \\" \\n \\r \\t \\\\",
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
            { "sublist": [ [1,2,3], [4,5,6], [7,8,9] ] }
        ]
    }]
"""

descr = """
=Usage=

You can run this from the command line
to load and convert a JSON file(s):

json2xml.py [options] [files]

You can also use this from Python code
by calling `serialize2xml()` on most any Python object (whether it came from
JSON or not). In that case, you'll get fancier output, that tells you what the
classes were, handles complex numbers, tuples, etc.

By default, it converts (losslessly, I hope) from JSON to XML. But use the
`--oformat` option to choose other output formats (specifying `--oformat json`
will get you pretty-printing).


Simple but thorough conversion of JSON, or of pretty much any Python data,
to XML syntax. It's smart enough to represent not only the list vs. dict
distinction which comes naturally to JSON, but a variety of other Python types.

Or you can import this script and call `serialize2xml()` on most any Python
object, whether it came from JSON or not (in that case, not as much information
can be saved with JSON output as with XML output).

The basic goals are:

* To support a much larger range of types, round-trippably.
* To make the entire XML ecosystem (validation, transformation, rendering, databases,
digital signing, query languages and engines, etc. etc.) easy to apply to Python data.
* Support JSON entirely
* Support most Python types, such as collections; but not necessarily references,
and only the data, not code (for example, no functions, and only the data of objects)
* Enough information to round-trip correctly
* Fairly compact. but much mnore important, easy to read.

==The mapping==

Use `--sample` to generate an actual sample.

In short:
* collection become container elements of the appropriate type:
     <dict>, <list>, etc.
* collections that need keys (such as dict), contain <item> elements, whose 'key' attribute
holds the key, and whose content is the actual item. It may be preferable to just add
a 'key' attribute to all the items directly, which I plan to add as an option.
* numeric items become empty elements named for their type, with the value on an attribute:
    <i v="1"/>, <f v="-1.2"/>
* strings become the content of <u> (for Unicode) elements:
    <u>Hello, world.</u>
* The three special values True, False, and None become empty elements of the same names:
    <T/>, <F/>, <None/>

Scalar types generally are written as XML empty elements, with a single-character
tag name indicating the type, and a `v` attribute holding the value (you can set
format for each via options):
    int      i
    float    f (`inf`, `-inf`, and `nan` can occur)
    str      u
    complex  c (with @r for the real part, and @i for the imaginary part)

The singleton types are written as XML emtpty elements:
    True     <T/>
    False    <F/>
    None     <None/>

tuples and lists are named as such, and contain their members directly.

dicts are named as such, and contain a <ditem> element for each member,
with a `key` attribute, and the value as the content of the <ditem>.

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

Thus, these are the only Python types passed to the XML serializer when you parse
actual JSON. However, the XML output can identify any number of types. There are other
differences as well, such as that JSON object keys must be string, while Python
dict keys only need to be hashable.

==Additional types==

When exporting more general Python structures to XML, this script adds some detail.
For example, subclasses of dict and list are written similarly but include a `class`
attribute whose value is the class name. tuples, complex numbers, and
subclasses of object (if not already covered) also have information added.


=Example output=

""" + sampleJSON + """

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
bc   </u></ditem>
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

* '''--size'''

Add a "size" attribute on collecitons types, giving their length.

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
** JSON objects have no identifiers, so no built-in way to refer to each other.

* JSON objects are also unlike non-object dictionaries or hashes in many languages:

** You can ''only'' use strings, not ints, etc. as keys
** You have to quote the names.
** You can't tell hashes apart from actual objects, or from other things you'd have to
represent using them in JSON (Python namedtuple, C struct, etc.)

Of course a particular JSON user can add their own conventions on top.
But then JSON ends up more verbose and less portable than other languages
(all those quotes add up).


=To do=

* Fix -pad.
* Add specific support for namedtuples.
    if (isinstance(x, tuple) and hasattr(x, '_fields'))... seems to be enough.
* Test with non-string dict keys and other more complex Python data sources.
* At least as an option, drop <ditem> and just put the key on the items.
Or possibly, move scalar named items to parent attributes
* Finish support for changing the XML tags to use.
* Add more --oformat choices, such as Python and Perl dcls.
* Finish support for homogeneous collections.
* Add a loader for round-tripping straight into Python structures.
* Fix --pad.
* Option to number items in lists, put len on collections
* Option to optimize (numpy?) sparse lists (say, where item is same as prev, gen:
    <repeat n="200"/>
* Possibly an option to save the typename of each dict key (in JSON they're always
strings, but not in Python).


=History=

* 2012-12-04: Written by Steven J. DeRose.
* 2018-04-18: lint.
* 2020-03-04: line, POD to MarkDown. New layout.
* 2020-04-17: Various bugs. Fix output escaping. Start handling "objects" as
distinct from "dicts", even though JSON doesn't know. Write out subclasses
(even though they won't show up for data that was really JSON).
* 2020-12-09: Clean up. Add --oformat, integrate PowerWalk and alogging.
* 2021-03-08: Add `--jsonl`, `--sample`, `--oformat`, `--intFormat`,
`--floatFormat`, and `--keyFormat` options.
* 2021-08-12: Factor out tag names to enable options to set them. Type-hints.
Add --lengths.
* 2022-09-06: Big re-sync of divergent changes on copies in Text/ and XML/CONVERT/.
Then retire the former.


=Rights=

Copyright 2012 by Steven J. DeRose. This work is licensed under a Creative Commons
Attribution-Share Alike 3.0 Unported License. For further information on
this license, see [http://creativecommons.org/licenses/by-sa/3.0].

For the most recent version, see [http://www.derose.net/steve/utilities] or
[http://github.com/sderose].


=Options=
"""

def warning0(msg):
    sys.stderr.write(msg+"\n")
def warning1(msg):
    if (args.verbose >= 1): sys.stderr.write(msg+"\n")

# What to map various troublesome strings to, in XML.
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
def escapeAttribute(s:str):
    return re.sub(r'(["<&])', _escaper, s)
def escapeText(s:str):
    return re.sub(r'(<|&|]]>])', _escaper, s)
def escapePI(s:str):
    return re.sub(r'(\?>)', _escaper, s)
def escapeComment(s:str):
    return re.sub(r'(-->)', _escaper, s)

def startTag(x:str, attrs:dict=None):
    attlist = ""
    if (attrs):
        for k, v in attrs.items():
            attlist += ' %s="%s"' % (k, escapeAttribute(v))
    return "<%s%s>" % (x, attlist)

def emptyTag(x:str, attrs:dict=None):
    attlist = ""
    if (attrs):
        for k, v in attrs.items():
            attlist += ' %s="%s"' % (k, escapeAttribute(v))
    return "<%s/>" % (x)

def endTag(x:str):
    return "</%s>" % (x)


###############################################################################
# See http://stackoverflow.com/questions/1305532/convert-python-dict-to-object
# Promotes a dict to an Object.
#
class Str:
    def __init__(self, **entries):
        self.__dict__.update(entries)

def serialize2xml(pyObject, istring:str="    ", depth:int=0):
    """Return an XML serialization of the object (recursive).
    Typically we expect JSON, but it doesn't have to be.
    """

    # Define what names to use as tag for various types
    _DICT = "dict"
    _LIST = "list"
    _TUPLE = "tuple"
    _OBJECT = "object"
    _ITEM = "item"
    _TRUE = "True"
    _FALSE = "False"
    _NONE = "None"
    _int = "i"
    _float = "f"
    _complex = "c"
    _str = "u"
    # And attributes:
    _KEY = "key"
    _VALUE = "v"
    _REAL = "r"
    _IMAG = "i"
    _CLASS = "class"
    _LEN = "len"
    _GENEITY = "homogeneous"

    # Collection types
    #
    buf = ""
    if (isinstance(pyObject, tuple)):                   # TUPLE
        if (hasattr(pyObject, '_fields')):                  # NAMEDTUPLE
            assert False, "namedtuple not yet implemented, sorry" # TODO What *should* this do?
            # return buf
        if (istring): buf += "\n" + (istring * depth)
        attrs = {}
        if (type(pyObject).__name__ != "tuple"): attrs[_CLASS] = type(pyObject).__name__
        if (args.lengths): attrs[_LEN] = "%d" % (len(pyObject))
        buf += startTag(_TUPLE, attrs)
        depth += 1
        for k, v in pyObject.items():
            if (istring): buf += "\n" + (istring * depth)
            buf += (startTag(_ITEM) +
                serialize2xml(v, istring=istring,depth=depth) + endTag(_ITEM))
        depth -= 1
        buf += endTag(_TUPLE)
        return buf

    elif (isinstance(pyObject, dict)):                   # DICT
        if (istring): buf += "\n" + (istring * depth)
        attrs = {}
        if (type(pyObject).__name__ != "dict"): attrs[_CLASS] = type(pyObject).__name__
        if (args.lengths): attrs[_LEN] = "%d" % (len(pyObject))
        buf += startTag(_DICT, attrs)
        depth += 1
        theKeys = sorted(pyObject.keys()) if (args.sortkeys) else pyObject.keys()
        for k in theKeys:
            v = pyObject[k]
            if (istring): buf += "\n" + (istring * depth)
            buf += (startTag(_ITEM, { _KEY: k }) +
                serialize2xml(v, istring=istring,depth=depth+1) + endTag(_ITEM))
        depth -= 1
        if (istring): buf += "\n" + (istring * depth)
        buf += endTag(_DICT)
        return buf

    elif (isinstance(pyObject, list)):                   # LIST
        if (istring): buf += "\n" + (istring * depth)
        attrs = {}
        if (type(pyObject).__name__ != "list"): attrs[_CLASS]: type(pyObject).__name__
        if (args.lengths): attrs[_LEN] = "%d" % (len(pyObject))
        if (args.homogeneity):
            htype = homogeneousType(pyObject)
            if (htype): attrs[_GENEITY] = htype.__none__
        buf += startTag(_LIST, attrs)
        depth += 1
        for v in pyObject:
            if (istring): buf += "\n" + (istring * depth)
            #buf += "<item>%s</item>" % (serialize2xml(v, istring=istring, depth=depth))
            buf += serialize2xml(v, istring=istring, depth=depth)
        depth -= 1
        buf += endTag(_LIST)
        return buf

    # Scalar types (order of testing matters)
    # TODO: Support subclassing of scalar types
    #
    elif (isinstance(pyObject, int)):
        return startTag(_int, { _VALUE: "%d" % (pyObject) })

    elif (isinstance(pyObject, float)):
        return startTag(_float, { _VALUE: "%f" % (pyObject) })

    elif (isinstance(pyObject, complex)):
        return startTag(_complex, { _REAL: "%f" % (pyObject.real), _IMAG: "%f" % (pyObject.imag) })

    elif (isinstance(pyObject, str)):
        return startTag(_str) + escapeText(pyObject) + endTag(_str)

    elif (pyObject is True):
        return emptyTag(_TRUE)

    elif (pyObject is False):
        return emptyTag(_FALSE)

    elif (pyObject is None):
        return emptyTag(_NONE)

    elif (isinstance(pyObject, object)):
        if (istring): buf += "\n" + (istring * depth)
        attrs = None
        if (type(pyObject).__name__ != "object"):
            attrs = { _CLASS, type(pyObject).__name__ }
        buf += startTag(_OBJECT, attrs)
        depth += 1
        for k, v in pyObject.__dict__:
            if (callable(v)): continue
            if (k.startswith("__")): continue
            if (istring): buf += "\n" + (istring * depth)
            buf += (startTag(_ITEM, { _KEY: k }) +
                serialize2xml(v, istring=istring,depth=depth) + endTag(_ITEM))
        depth -= 1
        buf += endTag(_OBJECT)
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
def tuplesMatch(t1:tuple, t2:tuple, checkValueTypes:bool=True):
    assert (isinstance(t1, tuple))
    assert (isinstance(t2, tuple))
    if (len(t1) != len(t1)): return False
    if (not checkValueTypes): return True
    for i in range(len(t1)):
        if (type(t1[i]) != type(t2[i])): return False
    return True

def dictsMatch(d1:dict, d2:dict, checkValueTypes:bool=True):
    assert (isinstance(d1, dict))
    assert (isinstance(d2, dict))
    keySeq1 = sorted(d1.keys())
    keySeq2 = sorted(d2.keys())
    if (keySeq1 != keySeq2): return False
    if (checkValueTypes):
        for k in keySeq1:
            if (type(d1[k]) != type(d2[k])): return False
    return True

def listsMatch(l1:list, l2:list, checkValueTypes:bool=True, checkLengths:bool=True):
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

def objectsMatch(o1, o2, checkValueTypes:bool=True, checkExactClass:bool=True):
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


def dictKeysAreIdentifiers(pyObject, PythonKeyWordsOk:bool=True):
    """Check whether all the keys used in a dict, are legit Python identifiers.
    TODO: Integrate PEP589 'TypedDict'?
    """
    assert (isinstance(pyObject, dict))
    import keyword
    for k in pyObject.keys():
        if (type(k) != str): return False
        if (not str.isidentifier(k)): return False
        if (not PythonKeyWordsOk and keyword.iskeyword()): return False
    return True

def homogeneousType(l1:list):
    """See if thelist is homogeneous. If so, return the applicable type; else None.
    This doesn't do anything special for possibly-miscible subclasses.
    """
    assert (isinstance(l1, list))
    if (not l1): return None  # Empty list is inderterminate
    type0 = type(l1[0])
    if (len(l1) == 0): return type0
    for i in range(1, len(l1)):
        if (type(l1[i]) != type0): return None
    return type0


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
            "--homogeneity", action="store_true",
            help='Add a homogeneity attribute on collections, giving the type.')
        parser.add_argument(
            "--lengths", action="store_true",
            help='Add a cardinality attribute on collections.')
        parser.add_argument(
            "--iencoding", type=str, metavar="E", default="utf-8",
            help="Assume this character coding for input. Default: utf-8.")
        parser.add_argument(
            "--floatFormat", type=str, default="%8.4f",
            help="Use this %-format for float values.")
        parser.add_argument(
            "--intFormat", type=str, default="%d",
            help="Use this %-format for float values.")
        parser.add_argument(
            "--keyFormat", type=str, default="%-12s",
            help="Use this %-format for string values.")
        parser.add_argument(
            "--istring", type=str, default="    ",
            help="Repeat this string to indent the output.")
        parser.add_argument(
            "--jsonl", "--json-lines", action="store_true",
            help="Treat each input record as a separate object.")
        parser.add_argument(
            "--keydrop", type=str, action="append",
            help="Drop dict entries with this key. Repeatable.")
        parser.add_argument(
            "--maxl", "--max-lines", type=int, default=0,
            help="With --jsonl, stop after loading this many lines.")
        parser.add_argument(
            "--noprop", action="store_true",
            help='Untag the "pyxs:prop" element surrounding data atoms.')
        parser.add_argument(
            "--nonamespaces", action="store_true",
            help='Delete the "pyxs:" namespace prefix.')
        parser.add_argument(
            "--nosize", action="store_true",
            help='Delete the "size" attribute everywhere.')
        parser.add_argument(
            "--notype", action="store_true",
            help='Delete the "type" attribute everywhere.')
        parser.add_argument(
            "--oformat", type=str, default="xml",
            choices=[ "xml", "json", "report" ],
            help="Write the output to this form. Default: xml.")
        parser.add_argument(
            "--pad", type=int,
            help="Left-pad integers to this many columns.")
        parser.add_argument(
            "--quiet", "-q", action="store_true",
            help="Suppress most messages.")
        parser.add_argument(
            "--sample", action="store_true",
            help="Generate and display some sample output.")
        parser.add_argument(
            "--sortkeys", "--sort_keys", "--sort-keys", action="store_true",
            help='Delete the "type" attribute everywhere.')
        parser.add_argument(
            "--verbose", action="count", default=0,
            help="Add more messages (repeatable).")
        parser.add_argument(
            "--version", action="version", version="Version of "+__version__)

        parser.add_argument(
            "files", nargs=argparse.REMAINDER,
            help="Path(s) to input file(s).")

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
            pyObj = json.load(fh)
        except json.decoder.JSONDecodeError as e:
            lg.vMsg(0, "JSON load failed for %s:\n    %s" % (path, e))
            sys.exit()
        writeIt(pyObj)

    if (len(args.files) == 0):
        fh = sys.stdin
    elif (not os.path.isfile(args.files[0])):
        warning0("Can't find file '" + args.files[0] + "'.")
        sys.exit(0)
    else:
        fh = open(args.files[0], "r")

    def writeIt(pyObj):
        if (args.oformat == "xml"):
            buf = serialize2xml(pyObj, istring=args.istring)
        elif (args.oformat == "json"):
            buf = json.dumps(pyObj,
                sort_keys=args.sortkeys, indent=len(args.istring))
        elif (args.oformat == "report"):
            buf = lg.formatRec(pyObj)
        else:
            try:
                pyObject0 = json.load(fh)
            except json.decoder.JSONDecodeError as e:
                warning0("JSON load failed:\n    %s" % (e))
                sys.exit()
        print(buf)
        return


    ###########################################################################
    #
    args = processOptions()

    if (len(args.files) == 0):
        lg.vMsg(0, "json2xml.py: No files specified, using internal sample:\n%s" % (sampleJSON))
        try:
            pyObject0 = json.loads(sampleJSON)
        except json.decoder.JSONDecodeError as e:
            lg.vMsg(0, "JSON parse failed.\n    %s" % ( e))
            sys.exit()
        writeIt(pyObject0)

    else:
        pw = PowerWalk(args.files, open=False, close=False,
            encoding=args.iencoding)
        pw.setOptionsFromArgparse(args)
        for path0, fh0, what0 in pw.traverse():
            if (what0 != PWType.LEAF): continue
            doOneFile(path0)
