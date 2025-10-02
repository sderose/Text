#!/usr/bin/env python3
#
# theScroll.py: An append-only document version space.
# 2021-08-03: Written by Steven J. DeRose.
#
import sys
import os
import codecs
import re
import time
from datetime import datetime
#import math
#import subprocess
from collections import namedtuple, defaultdict
#from enum import Enum
#from typing import Callable  # IO, Dict, List, Union
import uuid
import ast
import shlex

from xml.dom import minidom
from xml.dom.minidom import Node

#from strBuf import StrBuf
from xmlstrings import XmlStrings as XStr

__metadata__ = {
    "title"        : "theScroll",
    "description"  : "An append-only document version space.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2021-08-03",
    "modified"     : "2021-08-03",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]

sampleData = """#META dc.author="sjd"
#META dc.title="Example document"
#META myId="0F994F86-1AF3-4F44-8D43-61EDF25F5E1C"
#META user.sjd="someonee@acm.org"
#META dc.type.mime="text/xml"
#
0_0_0, 1, sjd, 1629504349, chars:0:0, text:"<p>A new hope.</p>"
1,     2, sjd, 1629650250, END:, text:"<p>Documents that resemble files &mdash; from a distance.</p>"
2,     3, sjd, 1629650251, match:"\\bfiles\\b", text:"flies"
2,     4, ewk, 1630780160.00, match:"\\bfiles\\b", text:"the Philippines"
"""

sampleXml = """<?xml version="1.0"?>
<!DOCTYPE changeling PUBLIC "" "http://www.derose.net/namespace/changeling/V0.5">
<changeling>
<metadata>
    <meta name="dc.author" value="="sjd"" />
    <meta name="dc.title" value="="Example document"" />
    <meta name="myId" value="="0F994F86-1AF3-4F44-8D43-61EDF25F5E1C"" />
    <meta name="user.sjd" value="="sderose@acm.org"" />
    <meta name="dc.type.mime" value="="text/xml"
</meta>

<changes>
    <start chId="0_0_0" />
    <ch base="0_0_0" chId="1" user="sjd" date="1629504349">
        <tgt type="chars">0 0</tgt>
        <src type="text"><![CDATA[<p>A new hope.</p>]]></src>
    </ch>
    <ch base="1" chId="2" user="sjd" date="1629650250">
        <tgt type="END" />
        <src type="text">&lt;p>Document that resemble files &amp;mdash; from a distance.&lt;/p></src>
    </ch>
    <ch base="2" chId="3" user="sjd" date="1629650251">
        <tgt type="match">\\bfiles\\b</tgt>
        <src type="text">flies</src>
    </ch>
</changes>
</changeline>
"""

descr = """
=Description=

This is a bare-bones implementation of a forking version space for documents or
other data expressible as text strings.

A document is represented as an append-only list of changes, one per record in
a readable file. The file can also have metadata records at the top (no provision for
changing them yet, short of editing the raw file), and comment records anywhere.

The "real" records each represent a change and thus a version, which for now means replacing a
contiguous range of zero or more characters in the document, by some other characters.
Replacing an empty range is obviously an insertion; replacing a non-empty range with
an empty one is a deletion. Moves are desirable but not yet implemented.
As a side benefit, this enables a much more precise reconstruction of provenance.

A version of the document is identical with the change that created it.

Each change record includes:

* an ID for the prior version (=change) on which this change is based.

* an ID for this change, unique at least within the file.

* (not yet) a userid for the agent making the change.

* an optional *nix epoch time-stamp indicating when the change was made
(this is merely a convenience).

* a specification of the "target" range to be replaced (see below).

* a specification of the new "source" data to put there.

Because a new change can base itself on *any* prior existing change, the version space
is a tree. As with git, it may be useful to name particular versions; unlike git, this
does not provide a way to do that (at worst, you can paste change IDs somwhere along
with desired names.

Sources and targets consist of a scheme prefix, a colon, and then a scheme-specific
syntax. For the moment:

* Target schemes:
** END: The point at the very end (for appending to the document)
** chars: A pair of decimal integers, separated by a colon, giving the 0-based offset
to the first character to be replaced, and to the character past the last one to be
replaced (that is, Python-style). If the integers are equal, that's an empty span.
** match: A regex, the first match to which is the area to be replaced. This is matched
case-sensitively, with the default Python options.
** attr: Take an attribute name, '=', and quoted value, essentially the same as an
XML attribute in a start tag. The first element with that name and value is replaced
(at the moment I think this only replaces the start-tag; that's a bug). Probably it should
have a "locus" argument, to say whether to insert pre-start, post-start, pre-end, post-end,
or to replace inner or outer, or change the attribute itself?
** xptr: Reserved to support XPointers.
** xpath: Reserved to support XPaths.

Target specifications are highly dependent on the state of the document when applied.
For example 'chars:100:200' will typically refer to quite different text in every version
of a document.

* Source schemes:
** text: A de novo, quoted Unicode string to be inserted literally. The usual Python
special-character escapes may be used inside.
** copy: A target specification (including a target scheme prefix) giving a range of
characters to be copied. Giving the same target specification under source copy:, as
for the target itself, thus results in no net change.

The possible changes should perhaps add a mechanism for moves,
and probably for importing (copy vs. link vs. hot transclusion?)
from other documents and versions.

The document itself does not really appear in the change-log file. Any particular version can
be constructed by finding the change that created it, tracing back to find the linear
chain of prior changes that led there, and then re-playing those changes.

To avoid absurd amounts of string-copying during replay, this will use StrBuf, a related
package I wrote to handle large strings with frequent randomly-distributed changes.
For performance, the full document string corresponding to any change (or all of them)
can be cached, keyed by the change ID. Such caches benefit all subsequent versions,
because replay only needs to happen from the cached version forward.

Example file:
""" + sampleData + """

There is no assumption that the document is in a particular format. It is merely
treated as a big string.

==Usage==

    theScroll.py [options] [files]


=Design Notes=

This should work fine for disconnected or otherwise conflicting users, but not for
a single user who runs non-communicating processes doing simultaneous changes (though
their changes can be easily recorded as another forking path when they reconnect).
* A userid+changenumber identifies a change.
* Every change is based on (and explicitly chooses) one immediately-preceding change.
* Thus, a change is a version.
* Changes are recorded in an append-only change-log file, with a partial ordering
defined by change back-links (which is consistent with write -order, because you
can only append a change that is based on a change already present.
* At the moment, the only action is "replace", from which you can get insert and delete
by making either one be empty. The data to be replaced is called the "target", and
that to be inserted, the "source".
* Targets and sources specify a "scheme" (reminiscent of URL schemes). Targets exist
for character offset ranges, regex matches, and should be added for at least one
XML-aware pointing scheme (simplest being XPointer, imho). Sources can be any of those,
or a literal string.
* Move and copy can be detected by noting what a change does. Probably I'll add a
specific "move" action that does the copy and then delete as a unit.
* The change-log is in XML, but like XSLT, that's not the XML that is the document.
It should work fine to put any old non-XML text in the document and change-manage is
via offsets or regexes.
* Transclude, import, and link are potential semantics to add. All would require
a change id to be unambiguous.
* What about image data?
* There is no automated support for merging or even diffing yet.

File format:

==Version Identifiers==

A certain document version is identified as a file (URL or path) plus a change id
in that file. The change id, in turn, consists of a userid and a serial number assigned
local to that user.

A document file contains a list of changes, some of which comprise the ancestry of the
requested version. That back-chain is extracted, and then applied from "" until the
requested change is reached.

If two forks have no conflicts (and you should be able to *really* tell, because
of character haecceity can be (though is not yet) maintained by building two version at
once, with a warp table). This should mean they can be unambiguously merged.

*** This has a potential issue with target specifications other than offsets: if
there's a fork (created by 2 different changes basing themselves on the same prior),
later merges require mapping between:

    If this stream *had* included that earlier change, what would the corrected form of the subsequent changes be?

This seems to drop us into all the gory issues of git merges.... Addressing them somewhat
like git does, only at character rather than line level, could work but wouldn't be any
better than git for conflict cases (except that we'll be tracking actual moves as first-class
events, which should help some.

==Moves==

If we only have ins/del, can't in principle retain their identity after moving -- are
those inserted characters "the same ones" or not? If they match, or are close enough,
we can guess so (which is basically what git does). But
if the move is a unitary operation, characters can be tracked through it. However,
copies and multiple pastes are still an issue.

==Location reference==

I don't want to have to move a whole line or element just to change a character or phrase.
So I want character-level precision on changes. That means pointing to an element is not
enough. The simplest systems I know for specifying precise locations in XML are:

* a character offset, or a pair for a range
* an XPointer child-sequences, with a final component that can give an offset into
a text node (or potentially into an attributes, if you also allow an attribute selector
as an XPointer extension).


==Merges==

It should be possible to add a special merge operation that:
    * picks a base
    * applies a set of specific changes, possibly including changes from another stream

We probably want a separate
"MERGE" operation, that takes two base versions (probably but not necessarily the tips
of two different users' chains), and applies enough edits to make them match, while
simultaneously tracking the progress of warps between the two versions.


=Related Commands=

`strBuf.py`: a reasonably fast mutable buffer for very large strings.

`xml2Changeling.py`: convert XML documents to a changeling change-log that gradually
creates them. Mainly for testing.


=References=

[https://arxiv.org/pdf/0907.0929.pdf] TreeDoc


=Known bugs and Limitations=


=To do=

==High priority==

* Needs some notion of import.
* A way to do and detect moves per se (is it enough to just have a source scheme "move:",
which by definition nukes the source from the original place? You could always track it
as an event, because, after all, it says "move:".
* How fast are replays??? With and without StrBuf?
* Finish transactions / change bundling
* Finalize changeId mechanism
* Add xptr support
* Integrate with StrBuf
* ? Build offset-mapping / warp table between any two versions
* Devise a way to track offsets efficiently as a DOM changes, so changes can be
specified by either XPtr or by offset without getting messy.

==Lower priority==

* SHould there be a way to lock regions, tag versions, etc.?
* Way to specify that a version should be cached?
    #CACHE-As: [tag]
* Record checksums?
* How do you add users?
* A tool to transcribe the build into git? Though git is not particularly adept for
append-only files.
* ? Add explainer option on transaction, for user to express intent; maybe also
a status, so you can distinguish priority, review, etc.
* ? Something like a git fast-forward (or rebase?) to update one version to match another?
* Are there "operations", or just "replace"?
* ? Operation to discard/undo? a given change.

=History=

* 2021-08-03ff: Written by Steven J. DeRose, with lots of discussion with
C.M. Sperberg-McQueen and Patrick Durusau, and inspired by Balisage 2021 papers
by them as well as Joel Kalvasmaki and Michael Kay.


=Rights=

Copyright 2021-08-03 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See [http://creativecommons.org/licenses/by-sa/3.0/] for more information.

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""

def log(lvl:int, msg:str):
    if (args.verbose >= lvl): sys.stderr.write(msg + "\n")
def warning0(msg:str): log(0, msg)
def warning1(msg:str): log(1, msg)
def warning2(msg:str): log(2, msg)
def error(msg:str): log(0, msg)
def fatal(msg:str): log(0, msg); sys.exit()

def unescapeString(s:str) -> str:
    return ast.literal_eval(shlex.quote(s))

# From https://github.com/sderose/Charsets/blob/master/UnicodeLists/quote.py
quotePairs = [
    #(  "\u0060", "\u0060", 'back'     ),  # "GRAVE ACCENT",
    (  "\u0027", "\u0027", 'splain'   ),  # "APOSTROPHE",
    (  "\u0022", "\u0022", 'dplain'   ),  # "QUOTATION MARK",
    (  "\u2018", "\u2019", 'single'   ),  # "SINGLE QUOTATION MARK",
    (  "\u201C", "\u201D", 'double'   ),  # "DOUBLE QUOTATION MARK",
    (  "\u2039", "\u203A", 'sangle'   ),  # "SINGLE ANGLE QUOTATION MARK",
    (  "\u00AB", "\u00BB", 'dangle'   ),  # "DOUBLE ANGLE QUOTATION MARK *",
    (  "\u201A", "\u201B", 'slow9'    ),  # "SINGLE LOW-9 QUOTATION MARK",
    (  "\u201E", "\u201F", 'dlow9'    ),  # "DOUBLE LOW-9 QUOTATION MARK",
    (  "\u2032", "\u2035", 'sprime'   ),  # "PRIME",
    (  "\u301E", "\u301E", 'dprime'   ),  # "DOUBLE PRIME QUOTATION MARK",
    (  "\u2034", "\u2037", 'tprime'   ),  # "TRIPLE PRIME", "REVERSED TRIPLE PRIME",

    (  "\u2E02", "\u2E03", 'subst'    ),  # "SUBSTITUTION BRACKET",
    (  "\u2E04", "\u2E05", 'dotsubst' ),  # "DOTTED SUBSTITUTION BRACKET",
    (  "\u2E09", "\u2E0A", 'transp'   ),  # "TRANSPOSITION BRACKET",
    (  "\u2E0C", "\u2E0D", 'romission'),  # "RAISED OMISSION BRACKET",
    (  "\u2E1C", "\u2E1D", 'lpara'    ),  # "LOW PARAPHRASE BRACKET",
    #(  "\u2E20", "\u2E21", 'vbarq'    ),  # "VERTICAL BAR WITH QUILL",
    #(  "\u301D", "\u301F", 'rdprime'  ), # "DOUBLE PRIME QUOTATION MARK",
    (  "\u2057", "\u301D", 'rdprime'  ),  # "DOUBLE PRIME QUOTATION MARK",
    #      = "QUADRUPLE PRIME"

    (  "\uFF02", "\uFF02", 'fullwidth'),  # "FULLWIDTH QUOTATION MARK",
    #(  "\u275B", "\u275C", 'scommaO'  ),  # "HEAVY SINGLE TURNED COMMA QM ORNAMENT",
    #(  "\u275D", "\u275E", 'dcommaO'  ),  # "HEAVY DOUBLE TURNED COMMA QM ORNAMENT",
    #(  "\u276E", "\u276F", 'hangleO'  ),  # "HEAVY ANGLE QM ORNAMENT",
    #(  "\U0001F677", "\U0001F678", 'sshdcommonO' ),  # "SANS-SERIF HEAVY DOUBLE COMMA QM ORNAMENT",
]

def unquoteString(s:str) -> str:
    """Strip quotes off the ends of a string. Just one set, and they have to match.
    Internal escaped characters are not unescaped.
    If no known quote-pair is found, return s unchanged.
    """
    if (not s): return ""
    for lQuo, rQuo, _mnemonic in quotePairs:
        if (s.startswith(lQuo) and s.endswith(rQuo)):
            s = s[1:-1]
            return s
    return s

def quoteString(s:str, qtype:str="dangle") -> str:
    """Put quotes of chosen type around the string for display. No escaping done.
    """
    for lQuo, rQuo, mnemonic in quotePairs:
        if (mnemonic == qtype):
            return lQuo + s + rQuo
    raise KeyError("No such quote type as '%s'." % (qtype))

def quoteSourceText(s:str) -> str:
    """Quote with usual straight doubles, backslashing as needed.
    """
    s = re.sub(r"\\", "\\\\", s)
    s = re.sub("r\"", "\\\"", s)
    return '"' + s + '"'

def makeEpochTime(s:str, fail=False) -> float:
    """Parse one or more time formats into a *nix epoch timestamp.
    """
    try:
        return float(s)
    except ValueError:
        pass
    try:
        return time.mktime(datetime.fromisoformat(s).timetuple())
    except ValueError:
        pass
    if (fail):
        raise ValueError("Unrecognized time string: '%s'" % (s))
    return NULL_EPOCHTIME


###############################################################################
# On this approach, every change event is a version. So changes can reliably
# refer to positions in the text as it existed after the previous change.
# You can also checksum or cache at any point.
#
point = int
span = namedtuple('span', [ 'fr', 'to' ])
change = namedtuple('cnum', [ 'ctype', 'oldLoc', 'source' ])  #:Union(None, str, span)

MimeType = Language = str
EpochTime = float


###############################################################################
#
class ChangeId:
    """Generate a unique id for a new change.
    These are generally passed around as strings, so this object doesn't
    actually get used much.

    Consider:
        os.getpid()
        mac=uuid.getnode()
    """
    def __init__(self, user: str = None, seq: int = None, subuser: int = 0):
        if (not user): user = os.environ["USER"] + "@" + os.environ["HOST"]
        self.user = user
        if (seq is None): seq = uuid.uuid1()
        self.seq = seq
        if not(subuser): subuser = "0"
        self.subuser = subuser

    @classmethod
    def fromstring(cls, s: str):
        user, seq, subuser = s.split(sep="_")
        return cls(user, int(seq), int(subuser))

    def tostring(self) -> str:
        return ("%s_%x%s" %
            (self.user, self.seq, '_%s' % (self.subuser) if self.subuser else "" ))

    def toxml(self) -> str:
        return ('<cId user="%s" seq="%x"%s/>' %
            (self.user, self.seq, ' subuser="%s"' % (self.subuser) if self.subuser else "" ))

# Every document starts with this as the (unstored) baseId:
NULL_CHANGE_ID = ChangeId("0", 0, 0).tostring()
assert NULL_CHANGE_ID == "0_0_0"
NULL_EPOCHTIME = -307614600
#print("NULL_CHANGE_ID '%s', NULL_EPOCHTIME %d." % (NULL_CHANGE_ID, NULL_EPOCHTIME))


###############################################################################
#
class ChangeEvent:
    """A single change, made to a given prior version, and replacing one
    contiguous (possibly empty) span of it.
    ChangeEvents are partially-ordered overall, but fully-ordered for any one user
    (thus a single user shouldn't be acting on two version at once. Or can they?
    Each one says what it's based on, so do we even need a serial number?)

    Who makes the new ChangeID?
    """
    NFIELDS = 6
    FIELDSEP = ","

    def __init__(
        self,
        baseId:str,          # uuid, user, etc so long as it's unique.
        changeId:str,
        user:str,            # user id
        epochTime:int,       # *nix epoch time for the change
        target:str,          # where to insert/replace
        source:str,          # what to replace with
        loaded:bool=False    # Is it an old change loaded from a changeLog?
        ):
        if (not baseId): baseId = NULL_CHANGE_ID
        self.baseId = baseId
        if not changeId: changeId = ChangeId()
        self.changeId = changeId
        self.user = user
        if (isinstance(epochTime, str)): epochTime = int(epochTime)
        self.epochTime = epochTime
        self.target = target
        self.source = source
        self.loaded = loaded

    def toRecord(self):
        buf = ChangeEvent.FIELDSEP.join([
            self.baseId,
            self.changeId,
            "%d" % (self.epochTime),
            self.target,
            self.source
        ])
        return buf

    @staticmethod
    def toheader() -> str:
        return "%10s -> %10s %10s %10s: %s <- %s" % (
             "baseId", "changeId", "user", "timestamp", "target", "source")

    def tostring(self):
        buf = "%10s -> %10s %10s %10d: %s <- %s" % (
            self.baseId, self.changeId, self.user, self.epochTime,
            quoteString(self.target), quoteString(self.source))
        return buf

    def toxml(self):
        buf = '<change id="%s" base="%s" time="%d" tgt="%s">%s</change>' % (
            self.baseId,
            self.changeId,
            self.epochTime,
            self.target,
            XStr.escapeText(self.source)
        )
        return buf

    def apply(self, doc: str) -> str:
        """Modify a document string by this changeEvent.
        TODO: For now, the only "source" is a literal string.
        """
        try:
            frChar, toChar = self.getTargetBounds(doc, self.target)
            srcString = self.getSource(doc, self.source)
        except KeyError as e:
            error("Error applying ChangEvent\n    %s\n%s\n%s" % (self.tostring(), e, doc))
            return None
        return doc[0:frChar] + srcString + doc[toChar:]

    def getTargetBounds(self, doc: str, tgt: str) -> (int, int):
        """Interpret a 'target' specification, which says what contiguous span
        is to be replaced by the current change, into a (frChar, toChar) pair.
        Lots of ways you could specify, this just has a few. All use a scheme-prefix.
        """
        scheme, rest = tgt.split(sep=":", maxsplit=1)
        if (scheme == "END"):                                   # very end of doc
            frChar = toChar = len(doc)
        elif (scheme == "chars"):                               # offset range (TODO: negatives?)
            frChar, toChar = rest.split(sep=":", maxsplit=1)
            frChar = int(frChar)
            toChar = int(toChar)
            if frChar < 0 or frChar > toChar or toChar > len(doc):
                raise KeyError("Bad range [%d:%d]." % (frChar, toChar))
        elif (scheme == "match"):                               # first match of regex
            rest = unquoteString(rest)
            #warning1("Match expression #%s#" % (rest))
            targetExpr = re.compile(rest)
            mat = re.search(targetExpr, doc)
            if not mat:
                raise KeyError("No match for change to regex /%s/." % (rest))
            frChar = mat.start()
            toChar = mat.end()
        elif (scheme == "attr"):                                 # element w/ attr (id?)
            # Get the attribute name and value, usual syntax
            mat = re.match(r"\s*(\w[-:.\w]*)\s*=\s*('[^']*'|\"[^\"]*\")", rest)
            if not mat:
                raise KeyError("Invalid attr target: /%s/." % (rest))
            aname = mat.group(1)
            aval = unquoteString(mat.group(2))
            targetExpr = re.compile(r"<\w*[^>]+\s%s\s*=\s*(['\"]%s['\"])" % (aname, aval))
            mat = re.search(targetExpr, doc)
            if not mat:
                raise KeyError("No match for attr: change '%s'." % (rest))
            frChar = mat.start()
            toChar = mat.end()
        elif (scheme == "xptr"):                                # XPointer into XML
            raise KeyError("xptr not yet inmplemented")
        else:
            raise KeyError("unknown target scheme '%s' in '%s'." % (scheme, tgt))
        return frChar, toChar

    def getSource(self, doc: str, src: str) -> str:
        """Get the literal string that will replace a target. It can either be
        just a quoted string, or a reference to another place in the same
        document (as of the same baseId), to be copied. Currently no trace
        of the copy is kept.
        Potential addition actions:
            move
            import doc@version@target
            pragma to cache a given change
            xml mods: wrap, unwrap, rename
            globalchange?
        """
        scheme, rest = src.split(sep=":", maxsplit=1)
        if (scheme == "text"):                          # quoted/escape literal
            restu = unquoteString(unescapeString(rest))
            #warning0("literal comes out to: #%s#." % (restu))
            return restu
        if (scheme == "copy"):                          # nested target-spec
            frChar, toChar = self.getTargetBounds(doc, rest)
            return doc[frChar:toChar]
        else:
            raise KeyError("unknown source scheme '%s' in '%s'." % (scheme, src))


###############################################################################
#
class ChangeLing(dict):
    """A document, represented by a tree of ChangeEvent objects. They are
    stored in a plain dict, keyed by the ID of each ChangeEvent. Each ChangeEvent
    includes the key of the ChangeEvent it is based on, so that leads to a tree.

    At this time, there are no forward-pointers, so you can't actually traverse
    the tree forwards. That's because you normally start with a tip/head/current
    ChangeID, and only care about its priors in order to replay them to create
    the corresponding text, or to analyze the history in some way. For that,
    you can quickly traverse back to the start (stopping if you hit any prior
    version that's in a cache), and then play those changes forward. Easy enough
    to add the forward pointers during load if they seem useful.
    """
    # TODO Find all successors to a given version (even make git-log-ish display)
    # TODO Figure out how to do diffs and merges
    # TODO Implement moves (just another 'source' type, with a side-effect.
    # TODO Support having one doc pick up from some change in another?
    #
    def __init__(self):
        super(ChangeLing, self).__init__()
        self.tips = {}
        self.meta = {}
        self.nChanges = 0
        self.successors:dict = None

    def loadFromPlain(self, cfile):
        """Parse change records from a CSV-ish change-log file, as
        illustrated in 'sampleData'.
        """
        assert len(self) == 0  # For now
        cfh = codecs.open(cfile, "rb", encoding="utf-8")
        self.nChanges = 0
        for i, rec in enumerate(cfh.readlines()):
            if (rec[0]!="#"):
                self.addFromPlainRec(rec)
            else:
                if (rec.startswith("#META")):
                    assert self.nChanges==0, "#META at rec %d, not before all changes." % (i)
                    self.storeMeta(rec)
        cfh.close()
        self.tips = self.findAllTipVersions()

    def addFromPlainRec(self, rec: str):
        fields = rec.split(sep=ChangeEvent.FIELDSEP, maxsplit=5)
        if len(fields) != ChangeEvent.NFIELDS:
            raise ValueError("Got %d fields, not %d: %s" %
                (len(fields), ChangeEvent.NFIELDS, repr(fields)))
        # TODO unescapeString() all these?
        baseId = fields[0].strip()
        changeId = fields[1].strip()
        user = fields[2].strip()
        epochTime = makeEpochTime(fields[3].strip())
        target = fields[4].strip()
        source = fields[5].strip()
        ce = ChangeEvent(baseId=baseId, changeId=changeId, user=user,
            epochTime=epochTime, target=target, source=source, loaded=True)
        self.addChangeEvent(ce)
        if (args.verbose): warning0("Change: %s" % (ce.tostring()))

    def loadFromXml(self, path):
        """Parse change records from an XML change-log file, as
        illustrated in 'sampleXml'.
        """
        if (path.startswith("<?")):
            theDom = minidom.parseString(path)
        else:
            with codecs.open(path, "rb", encoding="utf-8") as ifh:
                theDom = minidom.parse(ifh)
        for i, node in enumerate(theDom.documentElement.getElementsByTagName("ch")):
            baseId = node.getAttribute("base")
            changeId = node.getAttribute("chId")
            user = node.getAttribute("user")
            epochTime = node.getAttribute("date")
            tgt = src = ""
            for cnode in node.childNodes:
                if (cnode.nodeType != Node.ELEMENT_NODE):
                    continue
                if (cnode.nodeName == 'tgt'):
                    if (tgt): raise ValueError("Extra target in <ch> with id '%s'." % (changeId))
                    tgt = cnode.innerXml()
                elif (cnode.nodeName == 'src'):
                    if (src): raise ValueError("Extra source in <ch> with id '%s'." % (changeId))
                    src = cnode.innerXml()
                else:
                    raise ValueError("Unexpected '%s' in <ch> with id '%s'." % (changeId))
                # TODO: Doesn't really support multiple tgt/src pairs in a single change.
                if (not tgt or not src):
                    raise ValueError("Did not get tgt and src in <ch> with id '%s'." % (changeId))
                ce = ChangeEvent(baseId=baseId, changeId=changeId, user=user,
                    epochTime=epochTime, target=tgt, source=src, loaded=True)
                tgt = src = ""
                self.addChangeEvent(ce)
                if (args.verbose): warning0("%4d: %s" % (i, ce.tostring()))
        self.tips = self.findAllTipVersions()

    def addChangeEvent(self, ce: ChangeEvent) -> None:
        if not (ce.baseId in self or ce.baseId == NULL_CHANGE_ID):
            fatal("Unknown baseId '%s' in: %s" %
                (ce.baseId, ce.tostring()))
        self[ce.changeId] = ce
        if ce.baseId in self.tips: del self.tips[ce.baseId]
        self.tips[ce.changeId] = True

    def storeMeta(self, rec: str) -> None:
        """Parse and record a #META entry in a dict keyed by field name. All META
        fields are repeatable, so the values are lists of strings.
        """
        mat = re.match(r"""#META\s+(\w[-.:\w]+)\s*=\s*"([^"]*)""", rec)
        assert mat, "Bad #META record: " + rec
        field = mat.group(1)
        val = mat.group(2).strip()
        if field not in self.meta: self.meta[field] = [ val ]
        else: self.meta[field].appen(val)

    def save(self, path: str) -> None:
        """Append all the changes we have, that are not flagged as having been loaded
        from the existing chagelog, to the changelog.
        """
        ofh = codecs.open(path, "ab", encoding="utf-8")
        for ch in self.getNewChanges():
            buf = ch.tostring()
            ofh.write(buf+"\n")
        ofh.close()

    def findAllTipVersions(self) -> dict:
        """Collect all versions that have no successor(s).
        Returns a dict keyed by changeID, with value baseId, containing all and only
        the changes that have no other changes based on them.
        """
        changeTips = {}
        for cid, ce in self.items():
            try:
                warning1("checking %s based on %s (%s)" % (ce.changeId, ce.baseId, type(ce.baseId)))
                changeTips[cid] = ce.baseId
            except AttributeError as e:
                error("Error on change %s:\n    %s" % (ce.tostring(), e))

        baseIds = list(changeTips.values())
        for baseId in baseIds:
            if (baseId in changeTips): del changeTips[baseId]
        return changeTips

    def mapSuccessors(self) -> dict:
        """For each version/change, make a list of its successor versions.
        """
        self.successors = defaultdict(list)
        for cid, ce in self.items():
            self.successors[ce.baseId].append(cid)

    def getNewChanges(self):
        """Extract just those changes that weren't in the loaded file.
        Mainly useful for appending them to the change-log file.
        """
        nc = []
        for k, ce in self.items():
            if not ce.loaded: nc.append(k)
        return sorted(nc)

    def getDocAsOfChangeId(self, cid: ChangeId) -> str:
        """Get the entire text of the document, as of a specific changeId.
        """
        cpath = self.getPathToChangeId(cid)
        warning1("Path to %s: %s." % (cid, repr(cpath)))
        doc = self.path2Document(cpath)
        return doc

    def getPathToChangeId(self, cid: ChangeId) -> list:
        """Trace backward from a given change, collecting all its ancestors.
        Until we introduce first-class merges, this is non-branching.
        """
        thePath = []
        cur = self[cid]
        while (cur != NULL_CHANGE_ID):
            thePath.insert(0, cur)
            if (cur.baseId==NULL_CHANGE_ID): break
            try:
                cur = self[cur.baseId]
            except KeyError:
                fatal("ChangeId %s not found, referenced from %s" %
                    (cur.baseChnge, cur))
        return thePath

    def path2Document(self, thePath: list) -> str:
        """Given a sequence of changes (such as extract by getPathTo), replay them
        to make a document.
        """
        doc = ""
        for chg in thePath:
            doc = chg.apply(doc)
            if (doc is None):
                error("Cannot reconstruct doc.")
        return doc


###############################################################################
#
def doOneFile(path:str) -> int:
    """Read and deal with one individual file.
    """
    changeling = ChangeLing()
    changeling.loadFromPlain(path)
    dump(changeling)

def doPlainTest() -> None:
    """Run the internal smoke-test data.
    """
    warning0("Running smoke-test from CSV-ish data.")
    changeling = ChangeLing()
    for rec in sampleData.splitlines():
        if (rec.startswith("#")): continue
        changeling.addFromPlainRec(rec)
    dump(changeling)

def doXmlTest() -> None:
    """Run the internal smoke-test data.
    """
    warning0("Running smoke-test from XML data.")
    changeling = ChangeLing()
    changeling.loadFromXml(sampleXml)
    dump(changeling)

def dump(theCL):
    print(ChangeEvent.toheader())
    cidOrder = sorted(theCL.keys())
    for cid in cidOrder:
        ce = theCL[cid]
        print(ce.tostring())

    print("\nTips (changes with no changes based on them):")
    theTips = theCL.findAllTipVersions()
    for tip in theTips:
        ce = theCL[tip]
        print("    Tip at change %10s" % (ce.changeId))

    for cid in cidOrder:
        doc = theCL.getDocAsOfChangeId(cid)
        print("******* Doc as of change id '%s':\n%s\n" % (cid, doc))

def xml2ChangeLing(ipath:str, opath:str, user:str):
    """Build an XML document by adding (essentially) SAX events in order.
    This gets a lot harder is you don't do it in order, if you still want to
    specify targets by offset. For which, see xml2Changeline.py.

    Hmm. What if you specified offsets as element number + offset? But you'd still
    need to update-to-root on total sizes every time something changed.
    Or, the changeEvent could record an explicit entry for the warp table:
        "From offset x onward, add/sub N"
        but how do we know which old pointers are/are not still meaningful?

    Aardvark basilisk cat dog emu fox gnu
    Now I refer to cat.*fox
    Now someone replaces (or inserts before) emu with horse.
    What *should* I now reference?
    """
    theDom = minidom.parse(ipath)
    cl = ChangeLing()
    trav(theDom.dom.documentElement, cl, lastCid=NULL_CHANGE_ID, user=user)
    cl.save(opath)

def trav(node:Node, changeling:ChangeLing, lastCid:str, user:str):
    if (node.nodeType == Node.ELEMENT_NODE):
        stag = quoteSourceText(node.getStartTag())
        ce = ChangeEvent(lastCid, None, user, time.time(), "END:", "text:%s" % (stag))
        newChangeId = changeling.add(ce)
        for childNode in node.childnodes:
            newChangeId = trav(childNode, changeling, newChangeId, user)
        etag = quoteSourceText(node.getEndTag())
        ce = ChangeEvent(lastCid, None, user, time.time(), "END:", "text:%s" % (etag))
    elif (node.nodeType == Node.TEXT_NODE):
        ce = ChangeEvent(lastCid, None, user, time.time(), "END:", "text:%s" % (node.data))
        newChangeId = changeling.add(ce)
    else:
        pass
    return newChangeId


###############################################################################
# Main
#
if __name__ == "__main__":
    import argparse

    def timer():
        print("Done")

    def processOptions() -> argparse.Namespace:
        try:
            from BlockFormatter import BlockFormatter
            parser = argparse.ArgumentParser(
                description=descr, formatter_class=BlockFormatter)
        except ImportError:
            parser = argparse.ArgumentParser(description=descr)

        parser.add_argument(
            "--iencoding", "--input-encoding", type=str, metavar="E", default="utf-8",
            help="Assume this character coding for input. Default: utf-8.")
        parser.add_argument(
            "--quiet", "-q", action="store_true",
            help="Suppress most messages.")
        parser.add_argument(
            "--test", action="store_true",
            help="Run a simple test on some internal data.")
        parser.add_argument(
            "--unicode", action="store_const", dest="iencoding",
            const="utf8", help="Assume utf-8 for input files.")
        parser.add_argument(
            "--user", type=str, metavar="U", default="theseus",
            help="Set user to this for changes generated with --xmlConvert.")
        parser.add_argument(
            "--verbose", "-v", action="count", default=0,
            help="Add more messages (repeatable).")
        parser.add_argument(
            "--version", action="version", version=__version__,
            help="Display version information, then exit.")
        parser.add_argument(
            "--xmlConvert", action="store_true",
            help="Convert an XML file into a changeling stepwise build of it.")

        parser.add_argument(
            "files", type=str, nargs=argparse.REMAINDER,
            help="Path(s) to input file(s)")

        args0 = parser.parse_args()
        return(args0)

    ###########################################################################
    #
    args = processOptions()

    if (args.test):
        doPlainTest()
        sys.exit()
    elif (args.xmlTest):
        doXmlTest()
        sys.exit()

    if (args.xmlConvert):
        for path0 in args.files:
            if (not path0.endswith(".xml")):
                error("must have extension .xml: '%s'." % (path0))
                continue
            opath0 = re.sub(r"\.xml$", ".chl", path0)
            if (os.path.exists(opath0)):
                error("Output file already exists: '%s'." % (opath0))
                continue
            xml2ChangeLing(path0, opath0, user=args.user)

    if (len(args.files) == 0):
        fatal("No files specified....")

    for path0, in args.files:
        doOneFile(path0)
    if (not args.quiet):
        warning0("Done.")
