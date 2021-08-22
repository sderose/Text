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
#import math
#import subprocess
from collections import namedtuple  # defaultdict, 
from enum import Enum
#from typing import Callable  # IO, Dict, List, Union
import uuid
import ast
import shlex

from xml.dom import minidom
from minidom import Node  #, Document, Element
    

#from strBuf import StrBuf
from DomExtensions import escapeXml  #, escapeCDATA, escapeComment, escapePI, escapeXmlAttribute

__metadata__ = {
    "title"        : "theScroll.py",
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
#META user.sjd="sderose@acm.org"
#META dc.type.mime="text/xml"
#
0_0_0, 1, sjd, 1629504349, chars:0:0, text:"<p>A new hope.</p>"
1,     2, sjd, 1629650250, END:, text:"<p>Document that resemble files &mdash; from a distance.</p>"
2,     3, sjd, 1629650251, match:\bfiles\b, text:"flies"
"""

descr = """
=Description=

This is a bare-bones implementation of a forking version space for documents or
other data expressible as text strings.

A document is represented as an append-only list of changes, one per record in
a readable file. The file can also have metadata records at the to (no provision for
changing them), and comment records anywhere.

The "real" records each represent a single change, which for now means replacing a
contiguous range of zero or more characters in the document, by some other characters.
Replacing an empty range is obviously an insertion; replacing a non-empty range with
an empty one is a deletion.

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
(at the moment I think this only replaces the start-tag; that's a bug).
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

The possible changes should add a mechanism for moves, and possibly for importing
from other documents and versions.

The document itself, never appears in the change-log file. Any particular version can
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

* Packaging a number of changes into a transaction?
* A userid+changenumber is a version; every change is based on some version.
* What verbs? insert; replace X with Y; add X vs. del Y; move? copy? annotate/makeRef?
* how to say what format the data is?
* multiple forks from a single user?
* markup is a separate layer -- just literal from this pov.
* Transclude/include/link (version-spec, or...)
* embed data (image etc)?
* merging

place reference?
    uuid, startoffset, endoffset

File format:

What if your change has to be acknowledged and assigned a sequence number by the server?

If characters are numbered by insertion, you have to thread them to get display order.

    H    e    l    l    o    ,    _    w    o    r    l    d    .
    0    1    2    3    4    5    6    7    8    9   10   12   13
    
But if numbered by display order, you have to change their number when they move, or have
a dense numbering space

==Version Identifiers==

A certain document version is identified as a file (URL or path) plus a change number 
in that file.  The file may start from scratch (empty), or by pointing to a "base"
document version (a change in another file).

A document file contains a list of numbered changes that are applied until the
requested change is reached. Since this is linear, identifying a version is easy:
just one int beyond the path.

When versions fork, the fork is a new document file, "based" like any other.
Every file points to its source/base file, and makes a linear sequence of changes
from there.

If two forks have no conflicts (and you should be able to *really* tell, because
of character haecceity), they can be merged (this seems to be a case where changes are
commutative, a la CRDTs). If they conflict, at least from that point forward thye have to 
be separate files, thus having their own change-numbering.

One way to do this is to send your changes back to the "base" document with a request
to incorporate. Then you're either rejected, or handed an ACK with enough info to 
reconcile: an int for you to add to all your changes might suffice, or an updated
change-list including others and your own; or permission to rebase onto a later version
that will get you all that.

The idea here is:
    * Trivial for single-user editing
    * Fairly easy for multi-user nonconflicting edits
    * You can work offline and reconcile (like git)
    * Characters can be identified despite their moving
        (actually, that depends on a separate MOV operation that adds traces).
    * Every conflict is a fork, so you immediately know.

==Moves==

If we only have ins/del, characters can't retain their identity after moving. But
if the MOV command itself is an edit operation, a character can be tracked through it
(if we're literally moving characters in a defined data format, the move might
break something (even if fixed soon after). Hmm, is there any case that necessarily 
breaks WF, not just validity? Hmm, how do you split a list into two?

==Forks and merges==

What if we really just log all the changes, but every one of them (logically) says
exactly what prior change (==version)/ it's based on? This can fork just fine, and
you know there's a fork any time you see the "BASE" change.

With that, you can add a special merge operation that:
    * picks a base
    * applies a set of specific changes, possibly including changes from the other stream
    * but how to co-identify places? by char ids again -- so, can we in fact map between
    things? yes, it every character inserted has an insertion serial number, and we can
    figure out that those fork at *the same time* the versions do. So each fork has it's
    own space, but all characters inserted before that have a common insertion-serial.
    
If every change knows its base, we can reconstruct any state. If every user/window has
its own space of change-numbers, they can all live in one append-only store, and not
get confused as long as there is a full ordering for each user -- there is no necessary ordering
across users. ahh, except you have to "re-base" in order to merge, and if you *really*
rebased, all your changes would have to be reconstructed. So we probably want a separate
"MERGE" operation, that takes two base versions (probably but not necessarily the tips
of two different users' chains), and applies enough edits to make them match. 

Any of this seems to require a very fast mutable string buffer. Hence StrBuf, below.


=Related Commands=

`strBuf.py`: a reasonably fast mutable buffer for very large strings.


=References=

[https://arxiv.org/pdf/0907.0929.pdf] TreeDoc


=Known bugs and Limitations=

* Need to pin down escaping rules for regexes.
* How do you add users, change metadata?
* Needs some notion of import.
* Need an XML-to-changes mechanism, at least to do thorough testing.
* Need a way to specify that a version should be cached?
    #CACHE-As: [tag]
* A way to record checksums
* A way to do and detect moves per se (is it enough to just have a source scheme "move:",
which by definition nukes the source from the original place? You could always track it
as an event, because, after all, it's say "move:".
* A tool to transcribe the build into git? Though git is not particularly adept for
append-only files.
* Way to guarantee uniqueness of change-ids for disconnected users (UUID1 was merely
a MAC address plus a 100ns timestamp, and a small serial number.
* Perhaps this could just use the record number in the changelog as the changeID.
But that means that disconnected users couldn't make their own changeIDs; they have to 
make temporary ones, and then the whole block would get shifted by a server-specified
amount when the checkin happened. But that would save a lot of space.

* How fast are replays??? With and without StrBuf?


=To do=

* Finalize changeId mechanism
* Add xptr support
* Add checksumming and caching of versions
* 

=History=

* 2021-08-03ff: Written by Steven J. DeRose.


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
def fatal(msg:str): log(0, msg); sys.exit()

def unescapeString(s:str) -> str:
    return ast.literal_eval(shlex.quote(s))
    
def unquoteString(s:str) -> str:
    if (not s): return ""
    assert s[0] in "'\"“‘" and s[-1] in "'\"”’"
    return s[1:-1]
    
def quoteSourceText(s:str) -> str:
    s = re.sub(r"\\", "\\\\", s)
    s = re.sub("r\"", "\\\"", s)
    return '"' + s + '"'
    
###############################################################################
# On this approach, there's only one state, constructed by a complete set of
# change events. So changes can always reliably refer to positions in the text
# as it existed after the previous change. You can also checksum at any point,
# or cache the version at any point.
#
# wait a sec... doc[x,y] = str   and    doc[x,y] = doc[x2,y2]
#     covers INS, DEL, MOV or CPY,
#
# Ops:
#     GET path
#     VER n
#     INS N "str"
#     DEL N, M
#     ...
#
point = int
span = namedtuple('span', [ 'fr', 'to' ])
change = namedtuple('cnum', [ 'ctype', 'oldLoc', 'source' ])  #:Union(None, str, span)

def makeQLit(s:str) -> str:
    s = re.sub(r"\\", "\\\\", s)
    s = re.sub(r'"', '\\"', s)
    return '"' + s + '"'
    
###############################################################################
#
class changeType(Enum):
    INS: 1  # point, str             # Can be s/
    DEL: 2  # span                  # Can be REP ""
    MOV: 3  # point, span
    PUL: 4  # span, span  # (translcude and/or link?)
    CHG: 5  # span, lhs, rhs, opts
    UNDO: 6 # changeId
    BASE: 7 # set the 'source' version for following edits

MimeType = Language = str
EpochTime = float

metaFields = {
    "title"        : str,
    "description"  : str,
    "rightsHolder" : str,
    "creator"      : str,
    "type"         : MimeType,
    "language"     : Language,
    "created"      : EpochTime,
    "license"      : str,
}


###############################################################################
#
class targetSpec:
    """Any of:
        chars:fromChar:toChar)
        match:regex
        xptr:...
        END
    """


###############################################################################
#
class sourceSpec:
    """Any of:
        new(qLit)
        move(targetSpec)
    Does transclude belong? If so, how is it repreented? Magically non-editable copy?
    Escaped #include? Just copied as the change happens?
    """
    
    
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
    def __init__(self, user:str=None, seq:int=None, subuser:int=0):
        if (not user): user = os.environ["USER"] + "@" + os.environ["HOST"]
        self.user = user
        if (seq is None): seq = uuid.uuid1()
        self.seq = seq
        if not(subuser): subuser = "0"
        self.subuser = subuser
    
    @classmethod
    def fromstring(cls, s:str):
        user, seq, subuser = s.split(sep="_")
        return cls(user, int(seq), int(subuser))
    
    def tostring(self) -> str:
        return ("%s_%x%s" % 
            (self.user, self.seq, '_%s' % (self.subuser) if self.subuser else "" ))

    def toxml(self) -> str:
        return ('<cId user="%s" seq="%x"%s/>' % 
            (self.user, self.seq, ' subuser="%s"' % (self.subuser) if self.subuser else "" ))

# Every document starts with this as the (unstored) baseChange:
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
        baseChange:str,      # uuid, user, etc so long as it's unique.
        thisChange:str,
        user:str,            # user id
        epochTime:int,       # *nix epoch time for the change
        target:str,          # where to insert/replace
        source:str,          # what to replace with
        loaded:bool=False    # Is it an old change loaded from a changeLog?
        ):
        if (not baseChange): baseChange = NULL_CHANGE_ID
        self.baseChange = baseChange
        if not thisChange: thisChange = ChangeId()
        self.thisChange = thisChange
        self.user = user
        if (isinstance(epochTime, str)): epochTime = int(epochTime)
        self.epochTime = epochTime
        self.target = target
        self.source = source
        self.loaded = loaded

    @classmethod
    def fromstring(cls, rec:str, loaded:bool=False):
        """Parse a record from a change-log file, like:
        """
        fields = rec.split(sep=ChangeEvent.FIELDSEP, maxsplit=5)
        if len(fields) != ChangeEvent.NFIELDS:
            raise ValueError("Got %d fields, not %d: %s" % 
                (len(fields), ChangeEvent.NFIELDS, repr(fields)))
        baseChange = fields[0].strip()
        thisChange = fields[1].strip()
        user = fields[2].strip()
        epochTime = fields[3].strip()
        try:
            if (not epochTime): epochTime = NULL_EPOCHTIME
            else: epochTime = float(epochTime)
        except ValueError as e:
            fatal("Bad epochTime '%s' in: %s\n    %s" % (epochTime, rec, e))
        target = fields[4].strip()
        source = fields[5].strip()
        return cls(baseChange=baseChange, thisChange=thisChange, user=user,
            epochTime=epochTime, target=target, source=source, loaded=loaded)
         
    def tostring(self):
        buf = ChangeEvent.FIELDSEP.join([
            self.baseChange,
            self.thisChange,
            "%d" % (self.epochTime),
            self.target,
            self.source
        ])
        return buf
        
    def toxml(self):
        buf = '<change id="%s" base="%s" time="%d" tgt="%s">%s</change>' % (
            self.baseChange,
            self.thisChange,
            self.epochTime,
            self.target,
            escapeXml(self.source)
        )
        return buf
        
    def apply(self, doc:str) -> str:
        """Modify the document by one changeEvent.
        TODO: For now, the only "source" is a literal string.
        """
        frChar, toChar = self.getTargetBounds(doc, self.target)
        return doc[0:frChar] + self.getSource(doc) + doc[toChar:]
     
    def getTargetBounds(self, doc:str, tgt:str) -> (int, int):
        """Interpret a 'target' specification, which says what contiguous span
        is to be replaced by the current change, into a (frChar, toChar) pair.
        Lots of ways you could specify, this just has a few. All use a scheme-prefix.
        """
        schemeEnd = tgt.index(":")
        assert schemeEnd > 0
        scheme = tgt[0:schemeEnd]
        rest = tgt[schemeEnd+1:]
        
        if (scheme == "END"):                    # very end of doc
            frChar = toChar = len(doc)
        elif (scheme == "chars:"):               # offset range (TODO: negatives?)
            frChar, toChar = tgt.split(sep=":", maxsplit=1)
            frChar = int(frChar)
            toChar = int(toChar)
            assert frChar >= 0 and frChar <= toChar and toChar <= len(doc)
        elif (scheme == "match:"):               # first match of regex
            targetExpr = re.compile(tgt[6:])
            mat = re.search(targetExpr, doc)
            assert mat
            frChar = mat.start()
            toChar = mat.end()
        elif (scheme == "attr:"):                # first element w/ attr (id?)
            # Get the attribute name and value, usual syntax
            mat = re.match(r"\s*(\w[-:.\w]*)\s*=\s*('[^']*'|\"[^\"]*\")", tgt[6:])
            assert mat
            aname = mat.group(1)
            aval = unquoteString(mat.group(2))
            targetExpr = re.compile(r"<\w*[^>]+\s%s\s*=\s*(['\"]%s['\"])" % (aname, aval))
            mat = re.search(targetExpr, doc)
            assert mat
            frChar = mat.start()
            toChar = mat.end()
        elif (scheme == "xptr:"):                # XPointer into XML
            raise KeyError("xptr not yet inmplemented")
        else:
            raise KeyError("unknown target scheme '%s' in '%s'." % (scheme, tgt))
        return frChar, toChar
        
    def getSource(self, doc):
        """Get the literal string that will replace a target. It can either be
        just a quoted string, or a reference to another place in the same
        document (as of the same baseChange), to be copied. Currently no trace
        of the copy is kept.
        Potential addition actions:
            move
            import doc@version@target
            pragma to cache baseChange
            xml mods: wrap, unwrap, rename
            globalchange?
        """
        
        if (self.source.startswith("text:")):           # quoted/escape literal
            mat = re.match(r"text:(['\"])(.*)\1\s*$", self.source[5:])
            assert mat
            return unescapeString(unquoteString(mat.group(2)))
        if (self.source.startswith("copy:")):           # nested target-spec
            frChar, toChar = self.getTargetBounds(doc, self.source[5:])
            return doc[frChar:toChar]
        else:
            raise KeyError("unknown source scheme in '%s'." % (self.target))
    
    
###############################################################################
#
class ChangeLing(dict):
    """A document, represented by a tree of ChangeEvent objects. They are
    stored in a plain dict, keyed by the ID of each ChangeEvent. Each ChangeEvent
    inclues the key of the ChangeEvent it is based on, so that leads to a tree.
    
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
        self.loadedFileSize = 0
        self.tips = {}
        self.meta = {}
        self.nChanges = 0
        
    def load(self, cfile):
        assert len(self) == 0  # For now
        cfh = codecs.open(cfile, "rb", encoding="utf-8")
        self.nChanges = 0
        for i, rec in enumerate(cfh.readlines()):
            self.loadOneRec(i, rec)
        self.loadedFileSize = cfh.ftell()
        cfh.close()
        
    def loadOneRec(self, i:int, rec:str) -> None:
        if (rec[0]=="#"):
            if (rec.startswith("#META")):
                assert self.nChanges==0, "#META at rec %d, not before all changes." % (i)
                self.storeMeta(rec)
            else:
                pass  # Comments allowed anywhere
            return
        ce = ChangeEvent.fromstring(rec.rstrip(), loaded=True)
        if not (ce.baseChange in self or ce.baseChange == NULL_CHANGE_ID):
            fatal("Unknown baseChange '%s' in record #%d: %s" % 
                (ce.baseChange, i, ce.tostring()))
        self[ce.thisChange] = ce
        if ce.baseChange in self.tips: del self.tips[ce.baseChange]
        self.tips[ce.thisChange] = True
    
    def storeMeta(self, rec:str) -> None:
        """Parse and record a #META entry in a dict keyed by field name. All META
        fields are repeatable, so the values are lists of strings.
        """
        mat = re.match(r"""#META\s+(\w[-.:\w]+)\s*=\s*"([^"]*)""", rec)
        assert mat, "Bad #META record: " + rec
        field = mat.group(1)
        val = mat.group(2).strip()
        if field not in self.meta: self.meta[field] = [ val ]
        else: self.meta[field].appen(val)
        
    def save(self, path:str) -> None:
        """Append all the changes we have, that are not flagged as having been loaded
        from the existing chagelog, to the changelog.
        """
        ofh = codecs.open(path, "ab", encoding="utf-8")
        for ch in self.getNewChanges():
            buf = ch.tostring()
            ofh.write(buf+"\n")
        ofh.close()
        
    def getNewChanges(self):
        """Extract just those changes that weren't in the loaded file.
        Mainly useful for appending them to the change-log file.
        """
        nc = []
        for k, v in self.items():
            if not v.loaded: nc.append(k)
        return sorted(nc)
        
    def getDocAsOfChangeId(self, cid:ChangeId) -> str:
        """Get the entire text of the document, as of a specific changeId.
        """
        cpath = self.getPathToChangeId(cid)
        warning1("Path to %s: %s." % (cid, repr(cpath)))
        doc = self.path2Document(cpath)
        return doc
        
    def getPathToChangeId(self, cid:ChangeId) -> list:
        """Trace backward from a given change, collecting all its ancestors.
        Until we introduce first-class merges, this is non-branching.
        """
        thePath = []
        cur = self[cid]
        while (cur != NULL_CHANGE_ID):
            thePath.insert(0, cur)
            if (cur.baseChange==NULL_CHANGE_ID): break
            try:
                cur = self[cur.baseChange]
            except KeyError:
                fatal("ChangeId %s not found, referenced from %s" %
                    (cur.baseChnge, cur))
        return thePath
        
    def path2Document(self, thePath:list) -> str:
        """Given a sequence of changes (such as extract by getPathTo), replay them
        to make a document.
        """
        doc = ""
        for chg in thePath:
            doc = chg.apply(doc)
        return doc
        
        
###############################################################################
#
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
            warning0("Cannot open '%s':\n    %s" % (path, e))
            return 0

    recnum = 0
    for rec in fh.readlines():
        recnum += 1
        if (args.tickInterval and (recnum % args.tickInterval == 0)):
            warning0("Processing record %s." % (recnum))
        if (rec == ""): continue  # Blank record
        rec = rec.rstrip()
        print(rec)
    if  (fh != sys.stdin): fh.close()
    return recnum

def doTest() -> None:
    """Run the internal smoke-test data.
    """
    warning0("Running smoke-test")
    changeling = ChangeLing()
    i = 0
    for rec in sampleData.splitlines():
        i += 1
        changeling.loadOneRec(i, rec)
    warning0("Loaded %d records." % (i))
    for i, cid in enumerate(changeling.tips):
        print("####### Tip version #%d:  %20s < %s" % (i, cid, changeling[cid].baseChange))
        doc = changeling.getDocAsOfChangeId(cid)
        print(doc)
    return i

def xml2ChangeLing(ipath:str, opath:str, user:str):
    """Build an XML document by adding (essentially) SAX events in order.
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
            "--iencoding", type=str, metavar="E", default="utf-8",
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
            "--verbose", "-v", action="count", default=0,
            help="Add more messages (repeatable).")
        parser.add_argument(
            "--version", action="version", version=__version__,
            help="Display version information, then exit.")

        parser.add_argument(
            "files", type=str, nargs=argparse.REMAINDER,
            help="Path(s) to input file(s)")

        args0 = parser.parse_args()
        return(args0)

    ###########################################################################
    #
    args = processOptions()
    
    if (args.test):
        doTest()
        
    if (len(args.files) == 0):
        fatal("theScroll.py: No files specified....")

    for path0, in args.files:
        doOneFile(path0)
    if (not args.quiet):
        warning0("theScroll.py: Done.")
