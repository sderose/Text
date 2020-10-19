#!/usr/bin/env python
#
# PdfStupidityFix.py: Make spacing, hyphenation, etc. better.
# 2020-09-25: Written by Steven J. DeRose.
#
from __future__ import print_function
import sys, os
import codecs
import re
from time import time

#import PowerWalk

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

__metadata__ = {
    'title'        : "PdfStupidityFix.py",
    'rightsHolder' : "Steven J. DeRose",
    'creator'      : "http://viaf.org/viaf/50334488",
    'type'         : "http://purl.org/dc/dcmitype/Software",
    'language'     : "Python 3.7",
    'created'      : "2020-09-25",
    'modified'     : "2020-09-30",
    'publisher'    : "http://github.com/sderose",
    'license'      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__['modified']


descr = """
=Description=

This does simple fixes to text copied out of representations like PDF, which
do not reliably represent word boundaries.
This is a pain to fix by hand, though difficult to fix automatically.
This script makes a valiant if imperfect effort.


==Examples==

The result varies depending on the PDF viewer in use.
[arxiv.org] has PDFs for many articles, where viewing the PDF and
selecting something often produces text such as shown below
(from Li and Jurafsky 2015 [DOI 10.18653/v1/D15-1200], as found at [https://arxiv.org/pdf/1511.06388.pdf]).


==="Raw" version===

This is edited to have line-breaks, hyphenation, and spacing comparable to
what you actually see:

  SENSE2VEC - A FAST AND ACCURATE METHOD
  FOR  WORD SENSE DISAMBIGUATION IN
  NEURAL WORD EMBEDDINGS.

  Andrew Trask & Phil Michalak & John Liu
  Digital Reasoning Systems, Inc.
  Nashville, TN 37212, USA
  {andrew.trask,phil.michalak,john.liu}@digitalreasoning.com

                                  ABSTRACT

  Neural word representations have proven useful in Natural Language Processing
  (NLP) tasks due to their ability to efficiently model complex semantic and syn-
  tactic word relationships.  However, most techniques model only one representa-
  tion per word, despite the fact that a single word can have multiple meanings or
  ”senses”.  Some techniques model words by using multiple vectors that are clus-
  tered based on context.  However, recent neural approaches rarely focus on the
  application to a consuming NLP algorithm.  Furthermore, the training process of
  recent word-sense models is expensive relative to single-sense embedding pro-
  cesses.  This paper presents a novel approach which addresses these concerns by
  modeling multiple embeddings for each word based on supervised disambigua-
  tion, which provides a fast and accurate way for a consuming NLP model to select
  a sense-disambiguated embedding.  We demonstrate that these embeddings can
  disambiguate both contrastive senses such as nominal and verbal senses as well
  as nuanced senses such as sarcasm.  We further evaluate Part-of-Speech disam-
  biguated embeddings on neural dependency parsing, yielding a greater than 8%
  average error reduction in unlabeled attachment scores across 6 languages.


===Firefox 81.0.1 with built-in PDF viewing===

This aggressively removes space, joining up words regardless of visual
line breaks and even large swathes of whitespace (e.g. around ABSTRACT). It
also turns soft hyphens hard, and keeps multiple spaces. It all ends up as a
single line.

SENSE2VEC-A FAST AND ACCURATE METHODFOR  WORD SENSE DISAMBIGUATION INNEURAL WORD EMBEDDINGS.Andrew Trask & Phil Michalak & John LiuDigital Reasoning Systems, Inc.Nashville, TN 37212, USA{andrew.trask,phil.michalak,john.liu}@digitalreasoning.comABSTRACTNeural word representations have proven useful in Natural Language Processing(NLP) tasks due to their ability to efficiently model complex semantic and syn-tactic word relationships.  However, most techniques model only one representa-tion per word, despite the fact that a single word can have multiple meanings or”senses”.  Some techniques model words by using multiple vectors that are clus-tered based on context.  However, recent neural approaches rarely focus on theapplication to a consuming NLP algorithm.  Furthermore, the training process ofrecent word-sense models is expensive relative to single-sense embedding pro-cesses.  This paper presents a novel approach which addresses these concerns bymodeling multiple embeddings for each word based on supervised disambigua-tion, which provides a fast and accurate way for a consuming NLP model to selecta sense-disambiguated embedding.  We demonstrate that these embeddings candisambiguate both contrastive senses such as nominal and verbal senses as wellas nuanced senses such as sarcasm.  We further evaluate Part-of-Speech disam-biguated embeddings on neural dependency parsing, yielding a greater than 8%average error reduction in unlabeled attachment scores across 6 languages.


===Safari 14.0===

Safari is thankfully less aggressive about cross-line join, but it doesn't take
out soft hyphens (and oddly leaves a space after "disambigua-").
Granted, not quite all line-final hyphens are soft -- but the odds
are good, especially if you use a dictionary (as this script does).

SENSE2VEC - A FAST AND ACCURATE METHOD FOR WORD SENSE DISAMBIGUATION IN NEURAL WORD EMBEDDINGS.
Andrew Trask & Phil Michalak & John Liu
Digital Reasoning Systems, Inc.
Nashville, TN 37212, USA {andrew.trask,phil.michalak,john.liu}@digitalreasoning.com
ABSTRACT
Neural word representations have proven useful in Natural Language Processing (NLP) tasks due to their ability to efficiently model complex semantic and syn- tactic word relationships. However, most techniques model only one representa- tion per word, despite the fact that a single word can have multiple meanings or ”senses”. Some techniques model words by using multiple vectors that are clus- tered based on context. However, recent neural approaches rarely focus on the application to a consuming NLP algorithm. Furthermore, the training process of recent word-sense models is expensive relative to single-sense embedding pro- cesses. This paper presents a novel approach which addresses these concerns by modeling multiple embeddings for each word based on supervised disambigua- tion, which provides a fast and accurate way for a consuming NLP model to select a sense-disambiguated embedding. We demonstrate that these embeddings can disambiguate both contrastive senses such as nominal and verbal senses as well as nuanced senses such as sarcasm. We further evaluate Part-of-Speech disam- biguated embeddings on neural dependency parsing, yielding a greater than 8% average error reduction in unlabeled attachment scores across 6 languages.


===Chrome 86.0.4240.75 ===

Chrome seems better at removing soft hyphens and excess space.
It keeps more line breaks that Safari, some of which seem odd (it seems to
think if the previous visual lines ends with a non-letter, or the next begins
with a non-letter, that's a paragraph break? For example, after "8%" and
before a quotation mark. But still, why not join up "the\\napplication"?

SENSE2VEC - A FAST AND ACCURATE METHOD
FOR WORD SENSE DISAMBIGUATION IN
NEURAL WORD EMBEDDINGS.
Andrew Trask & Phil Michalak & John Liu
Digital Reasoning Systems, Inc.
Nashville, TN 37212, USA
{andrew.trask,phil.michalak,john.liu}@digitalreasoning.com
ABSTRACT
Neural word representations have proven useful in Natural Language Processing
(NLP) tasks due to their ability to efficiently model complex semantic and syntactic word relationships. However, most techniques model only one representation per word, despite the fact that a single word can have multiple meanings or
”senses”. Some techniques model words by using multiple vectors that are clustered based on context. However, recent neural approaches rarely focus on the
application to a consuming NLP algorithm. Furthermore, the training process of
recent word-sense models is expensive relative to single-sense embedding processes. This paper presents a novel approach which addresses these concerns by
modeling multiple embeddings for each word based on supervised disambiguation, which provides a fast and accurate way for a consuming NLP model to select
a sense-disambiguated embedding. We demonstrate that these embeddings can
disambiguate both contrastive senses such as nominal and verbal senses as well
as nuanced senses such as sarcasm. We further evaluate Part-of-Speech disambiguated embeddings on neural dependency parsing, yielding a greater than 8%
average error reduction in unlabeled attachment scores across 6 languages.


===Opera===

Opera seems essentially the same as Chrome for this.

SENSE2VEC - A FAST AND ACCURATE METHOD
FOR WORD SENSE DISAMBIGUATION IN
NEURAL WORD EMBEDDINGS.
Andrew Trask & Phil Michalak & John Liu
Digital Reasoning Systems, Inc.
Nashville, TN 37212, USA
{andrew.trask,phil.michalak,john.liu}@digitalreasoning.com
ABSTRACT
Neural word representations have proven useful in Natural Language Processing
(NLP) tasks due to their ability to efficiently model complex semantic and syntactic word relationships. However, most techniques model only one representation per word, despite the fact that a single word can have multiple meanings or
”senses”. Some techniques model words by using multiple vectors that are clustered based on context. However, recent neural approaches rarely focus on the
application to a consuming NLP algorithm. Furthermore, the training process of
recent word-sense models is expensive relative to single-sense embedding processes. This paper presents a novel approach which addresses these concerns by
modeling multiple embeddings for each word based on supervised disambiguation, which provides a fast and accurate way for a consuming NLP model to select
a sense-disambiguated embedding. We demonstrate that these embeddings can
disambiguate both contrastive senses such as nominal and verbal senses as well
as nuanced senses such as sarcasm. We further evaluate Part-of-Speech disambiguated embeddings on neural dependency parsing, yielding a greater than 8%
average error reduction in unlabeled attachment scores across 6 languages.


===Acrobat Reader===

Similar to Chrome, but drops braces from author email address list, and
inserts 'g' before the @ (?). They also break lines quite differently

SENSE2VEC - A FAST AND ACCURATE METHOD
FOR WORD SENSE DISAMBIGUATION IN
NEURAL WORD EMBEDDINGS.
Andrew Trask & Phil Michalak & John Liu
Digital Reasoning Systems, Inc.
Nashville, TN 37212, USA
fandrew.trask,phil.michalak,john.liug@digitalreasoning.com
ABSTRACT
Neural word representations have proven useful in Natural Language Processing
(NLP) tasks due to their ability to efficiently model complex semantic and syntactic
word relationships. However, most techniques model only one representation
per word, despite the fact that a single word can have multiple meanings or
”senses”. Some techniques model words by using multiple vectors that are clustered
based on context. However, recent neural approaches rarely focus on the
application to a consuming NLP algorithm. Furthermore, the training process of
recent word-sense models is expensive relative to single-sense embedding processes.
This paper presents a novel approach which addresses these concerns by
modeling multiple embeddings for each word based on supervised disambiguation,
which provides a fast and accurate way for a consuming NLP model to select
a sense-disambiguated embedding. We demonstrate that these embeddings can
disambiguate both contrastive senses such as nominal and verbal senses as well
as nuanced senses such as sarcasm. We further evaluate Part-of-Speech disambiguated
embeddings on neural dependency parsing, yielding a greater than 8%
average error reduction in unlabeled attachment scores across 6 languages.


==Basic rules for this script==

* A bunch of alternating spaces and letters will be closed up, as in
"I N T R O D U C T I O N".

* Hyphens are removed when the strings they join are not both words, but the joined form is.

* A word is split up when it is not in the dictionary,
but it can be split at some point such that both resulting parts are.

* Line-breaks are inserted before various bullet characters.

* Whitespace is normalized.

* Lookups are done against a dictionary, and try rudimentary suffix-stripping, ignoring case, etc. See below re. the default word-list.


=The Lexicon=

Correctly joining and splitting requires checking whether you have
a legitimate word already, and whether you have one (or more) after adjusting.
Word lookup is handled by the "Lexicon" class, which can also be used independently.

It loads a rudimentary one-word-per-line
dictionary (default: the ubiquitous `/usr/share/dict/words`), and its
`isWord(s)` method tests
whether a given string is likely a word. It tries the word as-is, then in
lower case, then with a few common suffixes removed (mainly plural,
past, and progressive; including basic alternations like y/ies). It is not
nearly perfect, but it's pretty good, and reasonably fast.

The default dictionary file has these characteristics:

* It is all lowercase except for initial-capital proper names.
Thus no "1st", "M*A*S*H", "4x4", "100%", "it's", "3/4", etc.

* Only two entries ("Jean-Christophe" and "Jean-Pierre") have characters
other than [a-zA-Z].

* It lacks (most?) ''regular'' plurals, past and progressive verb
forms, etc., but has (e.g.):
    detect
    detectability
    detectable
    detectably
    detecter
    detectible
    detection
    detective
    detectivism
    detector
    indetectable
    predetect
    redetect
    undetectable
    undetected
    undetectible

(Note missing 'detects', 'detected', 'detecting'; and it counts dropping final
'e' as regular, since 'placing' is not included).

* It does, however, have 5540 -ing forms. Possibly these are ones that
the source dictionary considered significant enough to have main entries.
* It has many archaic terms.
* It lacks many recent terms.


=Known bugs and Limitations=

The rule that hyphens are removed if either side is not a word, is not
sufficient. For example, both 'mod' (or at least 'Mod') and 'els' are in `/usr/share/dict/words`, so 'mod-els' won't have the hyphen removed.

Tokens with multiple issues, like "incorporatingmulti-sense" are not fixed.

The usual *nix dictionary, and the workarounds for it here, are limited.

Why doesn't "ChineseRestaurant" get fixed?


=Related commands=

My `Text/wordPartTable.py`.


=History=

* 2020-09-25: Written by Steven J. DeRose.


=To do=

Add an option to disable some or all of the word-form handling, in case
people want to use this with alternative dictionaries that include forms.

Add code to degeminate double consonants before -ed or -ing, as in
'stopped' or 'referring' (this depends on syllable count, final stress,
having one but not two vowels before the doublet, etc.,
and still has exceptions.

Measure the coverage of `/usr/share/dict/words` against Google ngrams by era,
and use that to inform a replacement(s).

Recover correct inflections via Wiktionary or various other means, and make
a better word-list.

=Rights=

Copyright 2020-09-25 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See [http://creativecommons.org/licenses/by-sa/3.0/ for more information].

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""


###############################################################################
#
def warn(lvl, msg):
    if (args.verbose >= lvl): sys.stderr.write(msg + "\n")
    if (lvl < 0): sys.exit()

bullets = {
    # Bullets per se
    u"\u2022": 'BULLET',
    u"\u2023": 'TRIANGULAR BULLET',
    u"\u2043": 'HYPHEN BULLET',
    u"\u204c": 'BLACK LEFTWARDS BULLET',
    u"\u204d": 'BLACK RIGHTWARDS BULLET',
    u"\u2219": 'BULLET OPERATOR',
    u"\u25ce": 'BULLSEYE',
    u"\u25d8": 'INVERSE BULLET',
    u"\u25e6": 'WHITE BULLET',
    u"\u2619": 'REVERSED ROTATED FLORAL HEART BULLET',
    u"\u2765": 'ROTATED HEAVY BLACK HEART BULLET',
    u"\u2767": 'ROTATED FLORAL HEART BULLET',
    u"\u29be": 'CIRCLED WHITE BULLET',
    u"\u29bf": 'CIRCLED BULLET',
}

lex = {}
fileCount = dirCount = 0


###############################################################################
# Load and query a list of words, typically the usual *nix list.
#
class Lexicon(dict):
    def __init__(self, path, ignoreCase=True):
        startTime = time()
        with codecs.open(path, "rb", encoding="utf-8") as d:
            for w in d.readlines():
                w = w.strip()
                if (len(w) == 1): continue
                self[w] = 1
        warn(1, "Loaded %d words from '%s' in %6.4f seconds." %
            (len(self), path, time()-startTime))

    def isWord(self, w):
        """Check if the word, or a predictably-missing possible variant, is in
        the Lexicon. This over-accepts, because it tries regular endings even
        though they might not be correct. For example, "zebraing" counts.

        '' and single characters also count as True.
        """
        if (len(w)<=1):
            return True
        if (w in self):
            return True
        lw = w.lower()
        if (lw in self): return True
        if (lw.endswith('s')   and lw[0:-1] in self):
            return True
        if (lw.endswith('es')  and lw[0:-2] in self):
            return True
        if (lw.endswith('ies') and (lw[0:-3] + 'y') in self):
            return True
        if (lw.endswith('ed')  and lw[0:-2] in self):
            return True
        if (lw.endswith('ing') and
            (lw[0:-3] in self or lw[0:-3]+'e' in self)):
            return True
        return False


###############################################################################
#
def doAllFiles(pathlist):
    global dirCount, fileCount
    for path in pathlist:
        if (os.path.isdir(path)):
            dirCount += 1
            if (not args.recursive): continue
            children = os.listdir(path)
            for ch in children:
                doAllFiles(ch)
        else:
            fileCount += 1
            doOneFile(path)

def closeup(mat):
    return re.sub(' ', '', mat.group(1))

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
            sys.stderr.write("Cannot open '%s':\n    %s" %
                (e), stat="readError")
            return 0

    for rec in fh.readlines():
        buf = ""
        rec = re.sub(r'\b((\w ){4,})', closeUp, rec)  # Spaced-out titles
        tokens = re.split(r'([-\w]+)', rec)
        warn(2, "Tokens: %s" % ("|".join(tokens)))
        for token in tokens:
            if (not re.match(r'\w', token)):          # punct, space, etc.
                buf += token
                continue
            if (token.isupper()):                     # Acronym
                buf += token
                continue

            lToken = token.lower()
            if (token in bullets):                    # List item?
                token = "\n" + token
            elif ("-" in token):                      # Hyphenated
                warn(2, "hyphen: '%s'" % (token))
                mat = re.match(r'(.*)-(.*)', token)
                if (lex.isWord(mat.group(1)+mat.group(2))):
                    token = mat.group(1)+mat.group(2)
                elif (not lex.isWord(mat.group(1)) or
                    not lex.isWord(mat.group(2))):
                    token = mat.group(1) + ' ' + mat.group(2)
            elif (not lex.isWord(lToken)):            # Mystery word
                warn(2, "non-word: '%s'" % (lToken))
                for j in range(1, len(lToken)):
                    p1 = lToken[0:j]
                    p2 = lToken[j:]
                    if (lex.isWord(p1) and lex.isWord(p2)):
                        token = token[0:j] + ' ' + token[j:]
                        break
            buf += token
        print(re.sub(r'\s\s+', ' ', buf))

def closeUp(mat):
    return re.sub(r'(\S) ', "\\1", mat.group(1))


###############################################################################
# Main
#
if __name__ == "__main__":
    sample = """A  P A P E R  T I T L E  Learning a distinct representation for eachsense  of  an  ambiguous  word  could  leadto  more  powerful  and  fine-grained  mod-els  of  vector-space  representations.    Yetwhile  ‘multi-sense’  methods  have  beenproposed  and  tested  on  artificial  word-similarity tasks, we don’t know if they im-prove real natural language understandingtasks.  In this paper we introduce a multi-sense embedding model based on ChineseRestaurant Processes that achieves state ofthe  art  performance  on  matching  humanword  similarity  judgments,  and  proposea pipelined  architecture  for incorporatingmulti-sense embeddings into language un-derstanding."""

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
            "--dictionary",       type=str, metavar='D',
            default="/usr/share/dict/words",
            help='Dictionary to use.')
        parser.add_argument(
            "--iencoding",        type=str, metavar='E', default="utf-8",
            help='Assume this character set for input files. Default: utf-8.')
        parser.add_argument(
            "--ignoreCase", "-i", action='store_true',
            help='Disregard case distinctions.')
        parser.add_argument(
            "--quiet", "-q",      action='store_true',
            help='Suppress most messages.')
        parser.add_argument(
            "--test",             action='store_true',
            help='Run a demo/test on some fixed sample text.')
        parser.add_argument(
            "--unicode",          action='store_const',  dest='iencoding',
            const='utf8', help='Assume utf-8 for input files.')
        parser.add_argument(
            "--verbose", "-v",    action='count',       default=0,
            help='Add more messages (repeatable).')
        parser.add_argument(
            "--version", action='version', version=__version__,
            help='Display version information, then exit.')

        parser.add_argument(
            'files',             type=str,
            nargs=argparse.REMAINDER,
            help='Path(s) to input file(s)')

        args0 = parser.parse_args()
        return(args0)

    ###########################################################################
    #
    fileCount = 0
    args = processOptions()

    lex = Lexicon(args.dictionary)

    if (args.test):
        tfile = "/tmp/PdfStudpidityFix.tmp"
        with codecs.open(tfile, "wb", encoding="utf-8") as tf:
            tf.write(sample)
        warn(0, "Testing on:\n%s\n" % (sample))
        args.files.insert(0, tfile)

    if (len(args.files) == 0):
        warn(0, "No files specified....")
        doOneFile(None)
    else:
        doAllFiles(args.files)

    if (not args.quiet):
        warn(0, "Done, %d files.\n" % (fileCount))
