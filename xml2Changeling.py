#!/usr/bin/env python3
#
# xml2Changeling.py: Make XML into test data for changeling.
# 2021-08: Written by Steven J. DeRose.
#
import sys
import re
import codecs
import xml.sax
from xml.dom import minidom
from xml.dom.minidom import Node
#import json
from typing import List
#from collections import namedtuple

#from PowerWalk import PowerWalk, PWType
from DomExtensions import DomExtensions

DomExtensions.patchDom(minidom.Element)

__metadata__ = {
    "title"        : "xml2Changeling",
    "description"  : "Make XML into test data for changeling.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2021-08",
    "modified"     : "2021-08-29",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]

descr = """
=Description=

Load a DOM, and record the sizes of all the nodes (as they would export to XML).
Then also go through and sum to get all the offsets.

At the moment this is entirely static. Ideally, we could have the DOM calls that
can affect size, so they update.

That would be:
    * assignments to .data of text and cdata nodes, target and data of PIs
    * assignment to element.id, node.value, node.data
    * renaming an element
    * element.append, .before, .prepend, remove, removeAttribute[Node|NS]
    * insertAdjacentElement, insertAdjacentHTML, insertAdjacentText
    * setAttribute[Node|NS|NodeNS], delete attribute, toggleAttribute
    * appendChild, removeChild, re3placeChild[ren],replaceWith, insertBefore
    * ??? what are the rules for export re. namespace prefixes and inheritance?
    * setting innerHTML/outerHTML etc
    * node.normalize()?


=Related Commands=


=Known bugs and Limitations=


=To do=


=History=

* 2021-08: Written by Steven J. DeRose.


=Rights=

Copyright 2021-08 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See [http://creativecommons.org/licenses/by-sa/3.0/] for more information.

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""

def log(lvl:int, msg:str) -> None:
    if (args.verbose >= lvl): sys.stderr.write(msg + "\n")
def warning0(msg:str) -> None: log(0, msg)
def warning1(msg:str) -> None: log(1, msg)
def warning2(msg:str) -> None: log(2, msg)
def fatal(msg:str) -> None: log(0, msg); sys.exit()


###############################################################################
#
XmlDecl = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n"
Doctype = "<!DOCTYPE foo []>"

class XmlMap:
    """Make a map of a DOM, that knows about representation sizes/offsets.
    """
    def __init__(self):
        self.path = None
        self.theDom = None
        self.nodeInfo = None
        self.eid2Node = None

    def load(self, path):
        """Parse and load
        """
        self.theDom = minidom.parse(path)
        self.makeNodeInfo()

    def makeNodeInfo(self):
        docEl = self.theDom.documentElement
        self.nodeInfo = {}
        self.eid2Node = []
        for eid, node in enumerate(docEl.eachNode(attributeNodes=False)):
            self.nodeInfo[node] = { 'eid': eid }
            self.eid2Node.append(node)
        self.collectNodeSizes(docEl)

    def collectNodeSizes(self, node, curPos:int=0):
        """Figure the sizes of all the tags, and save them on each node.
        Of course, if you change the document after this, the numbers break until
        you run it again.
        TODO: PI, comment, empty elements, entities if esported?
        """
        annots = self.nodeInfo[node]
        annots['startAt'] = curPos
        if (node.nodeType == Node.DOCUMENT_TYPE_NODE):
            annots['what'] = "#DOCTYPE"
            annots['starter'] = XmlDecl + Doctype
            annots['ender'] = ""
            annots['dataLen'] = len(node.target) + 1 + len(node.data)
        elif (node.nodeType == Node.DOCUMENT_NODE):
            annots['what'] = "#DOCUMENT"
            annots['starter'] = ""
            annots['ender'] = ""
            dataLen = 0
            for ch in node.childNodes:
                dataLen += self.collectNodeSizes(ch, curPos=curPos)
            annots['dataLen'] = len(node.target) + 1 + len(node.data)
        elif (node.nodeType == Node.ELEMENT_NODE):
            annots['what'] = "#TEXT"
            annots['starter'] = node.getStartTag()
            annots['ender'] = node.getEndTag()
            dataLen = 0
            chStart = curPos + len(annots['starter'])
            for ch in node.childNodes:
                chTotLen = self.collectNodeSizes(ch, curPos=chStart)
                dataLen += chTotLen
                chStart += dataLen
            annots['dataLen'] = dataLen
        elif (node.nodeType == Node.TEXT_NODE):
            annots['what'] = "#TEXT"
            annots['starter'] = ""
            annots['ender'] = ""
            annots['dataLen'] = len(node.data)
        elif (node.nodeType == Node.CDATA_SECTION_NODE):
            annots['what'] = "#CDATA"
            annots['starter'] = "<![CDATA["
            annots['ender'] = "]]>"
            annots['dataLen'] = len(node.data)
        elif (node.nodeType == Node.PROCESSING_INSTRUCTION_NODE):
            annots['what'] = "#PI"
            annots['starter'] = "<?"
            annots['ender'] = "?>"
            annots['dataLen'] = len(node.target) + 1 + len(node.data)
        else:  # No attributes, please.
            raise ValueError("Unexpected nodeType %d." % (node.nodeType))
        annots['totLen'] = len(annots['starter']) + annots['dataLen'] + len(annots['ender'])
        curPos += annots['totLen']
        warning1("%6d: %s" % (self.nodeInfo[node]['eid'], annots))
        return annots['totLen']

    def collectNodeOffsets(self, curPos:int=0) -> int:
        """Given the sizes are there already, run through and accumulate to add
        the start and end offsets to each nodeInfo dict.
            <a>hello<b>there, </b><c>world.</c></a>
            0----+----1----+----2----+----3----+----4----+----5----+----6
        Should end up with (ignoring XML dcl, etc):
            a: st  0, end 39, size 39
            b: st  8, end 22, size 14
            c: st 22, end 35, size 13
        """
        docEl = self.theDom.documentElement
        curPos = 0
        for eid, node in enumerate(docEl.eachNode(attributeNodes=False)):
            annots = self.nodeInfo[node]
            assert annots['eid'] == eid
            annots['startChar'] = curPos
            curPos += len(annots['starter'])
            annots['endChar'] = curPos
            curPos += len(annots['starter'])
            curPos += node.mySize
            node.endOffset = curPos


 ###############################################################################
# Make element map via SAX
#
lineStarts = []

def makeElementMap(path, encoding="utf-8") -> List:
    """Create a map of all the elements in the path, as a list of (type, offset) tuples.
    """
    global lineStarts
    lineStarts = makeLineMap(path, encoding=encoding)
    saxParseIt(path, lineStarts)

def makeLineMap(path, encoding="utf-8") -> List[int]:
    """Scan a file and make a map of the *character* offsets for the first
    character of each line.
    """
    global lineStarts
    lineStarts = []
    curOffset = 0
    with codecs.open(path, "rb", encoding=encoding) as ifh:
        for rec in ifh.readlines():
            lineStarts.append(curOffset)
            curOffset += len(rec)
        finalTell = ifh.tell()
    warning0("makeLineMap: curOffset at end is %d, ftell is %d." % (curOffset, finalTell))
    return lineStarts

def saxParseIt(path, lineStartsArg:list):
    """Read and deal with one individual file.
    """
    warning1("Starting file " + path)
    p = xml.sax.make_parser()
    saxHand = saxHandler()
    saxHand.setLineStarts(lineStartsArg)
    p.setContentHandler(saxHand)
    with codecs.open(path, 'rb', encoding="utf-8") as fh:
        p.parse(fh)
    return


###############################################################################
# Sax event handlers
#     len(saxHandler.tagStack)
#
class saxHandler(xml.sax.handler.ContentHandler):
    encoding      = 'utf-8'
    version       = '1.0'
    standalone    = 'Y'
    typeIndicator = '"#"'
    rootName      = "#ROOT"

    def __init__(self):
        super(saxHandler, self).__init__()
        self.tagStack = []
        self.cnum = []
        self.theLocator = None
        self.lineStarts = None
        self.theMap = []

    def setLineStarts(self, ls):
        self.lineStarts = ls

    def setDocumentLocator(self, locator):
        self.theLocator = locator

    def getDocumentOffset(self):
        """Return the absolute file offset to the present location, by looking
        up where the line starts, and adding the column.
        """
        lin = self.theLocator.getLineNumber()
        col = self.theLocator.getColumnNumber()
        #pub = self.theLocator.getPublicId()
        #sysid = self.theLocator.getSystemId()
        try:
            return self.lineStarts[lin] + col
        except IndexError as e:
            fatal("No lineStarts entry for line %d.\n    %s" % (lin, e))

    def recordLoc(self, eventType:str):
        lin = self.theLocator.getLineNumber()
        col = self.theLocator.getColumnNumber()
        eventTypeP = re.sub(r"\n", "\\n", eventType)
        offsset = self.getDocumentOffset()
        print("L%4d C%4d -> %5d: %s %s" %
            (lin, col, offsset, '  ' * len(self.tagStack), eventTypeP))

    def getXptr(self):
        return "/".join([ str(x) for x in self.cnum ])

    def getFqgi(self):
        return "/".join(self.tagStack)

    # Escape, quote, and print a string
    # Optionally, do special things to non-ASCII.
    def sprint(self, s):
        print(",\n" + (args.istring*len(self.tagStack)) + self.clean(s), end="")

    def clean(self, s:str):
        return re.sub(r"([^[:ascii:]])", self.cleanFunc, s)

    @staticmethod
    def cleanFunc(mat):
        return "&#x%04x;" % (ord(mat.group(1)))

    def attrs2dict(self, attrs):
        d = {}
        for (n) in attrs.getNames():
            d[n] = attrs.getValue(n)
        return(d)

    ###########################################################################
    ### THE ACTUAL SAX EVENT HANDLERS
    ###########################################################################

    def startDocument(self):
        self.recordLoc("startDocument")
        return
    def endDocument(self):
        self.recordLoc("endDocument")
        return
    def startElement(self, name, attrs):
        self.recordLoc("startElement %s" % (name))
        eloc = { 'elType':self.tagStack[-1], 'cSeq':selfgetXptr(),  # TODO FIX
            'outerStart':None, 'innerStart':self.getDocumentOffset(),
            'innerEnd':None, 'outerEnd':None }
        self.theMap.append(eloc)
        self.tagStack.append(eloc)
        return
    def endElement(self, name):
        self.recordLoc("endElement %s" % (name))
        self.tagStack.pop()
        return
    def characters(self, content):
        self.recordLoc("characters '%s'" % (content))
        return
    def ignorableWhitespace(self, whitespace):
        self.recordLoc("ignorableWhitespace")
        return
    def processingInstruction(self, target, data):
        self.recordLoc("processingInstruction")
        return
    def comment(self, data):
        self.recordLoc("comment")
        return
    def skippedEntity(self, name):
        self.recordLoc("skippedEntity")
        return



###############################################################################
#
def doOneFile(path:str) -> int:
    """Read and deal with one individual file.
    """
    xm = XmlMap()
    xm.load(path)
    xm.collectNodeSizes(xm.theDom.documentElement)
    xm.collectNodeOffsets()
    print(xm.theDom.toprettyxml())
    return


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
            "--quiet", "-q", action="store_true",
            help="Suppress most messages.")
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
    if (args.iencoding and not args.oencoding):
        args.oencoding = args.iencoding
    if (args.oencoding):
        # https://stackoverflow.com/questions/4374455/
        # sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
        sys.stdout.reconfigure(encoding="utf-8")

    if (len(args.files) == 0):
        warning0("%NAME%: No files specified....")
        sys.exit()

    for path0 in args.files:
        makeElementMap(path0)
