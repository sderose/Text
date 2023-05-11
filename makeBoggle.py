#!/usr/bin/env python3
#
# makeBoggle.py: Generate and display a Boggle-like game board.
# 2022-07-20: Written by Steven J. DeRose.
#
import sys
import os
#import codecs
import string
import random
#import subprocess
#from typing import IO, Dict, List, Union

__metadata__ = {
    "title"        : "makeBoggle.py",
    "description"  : "Generate and display a Boggle-like game board.",
    "rightsHolder" : "Steven J. DeRose",
    "creator"      : "http://viaf.org/viaf/50334488",
    "type"         : "http://purl.org/dc/dcmitype/Software",
    "language"     : "Python 3.7",
    "created"      : "2022-07-20",
    "modified"     : "2022-07-20",
    "publisher"    : "http://github.com/sderose",
    "license"      : "https://creativecommons.org/licenses/by-sa/3.0/"
}
__version__ = __metadata__["modified"]

descr = """
=Name=
    """ +__metadata__["title"] + ": " + __metadata__["description"] + """


=Description=

Generate and display a word-finding game, one of several ways
(chosen with ''--method'').

* OLD: The old commercial Boggle(r) dice
* NEW: The new commercial Boggle(r) dice
* DENSEOLD: "ALESSTIDTERANAME" 842 words
* DENSENEW: "TLGNAEIASTRSDEHB" 906 words
* HIGHOLD: "DSLRETAIPRNTUDES" 2447 points
* HIGHNEW: "TSLNEIAENTRTBESO" 2447 points

* RANDOM: Random, unweighted by letter frequency
* WEIGHTED: a, weighted by letter frequency
* [any letters]: Specified by the user.

By default a 4x4 board is created. The last 3 --method types, however, allow you
to specify a different --size.

==Usage==

    makeBoggle.py [options] [files]


=See also=

[http://www.robertgamble.net/2016/01/a-programmers-analysis-of-boggle.html]


=Known bugs and Limitations=


=To do=

* Finish hooking up box-drawing chars.
* Option to colorize letters
* Add options to set width/height.
* Add other output formats, such as HTML.


=History=

* 2022-07-20: Written by Steven J. DeRose.


=Rights=

Copyright 2022-07-20 by Steven J. DeRose. This work is licensed under a
Creative Commons Attribution-Share-alike 3.0 unported license.
See [http://creativecommons.org/licenses/by-sa/3.0/] for more information.

For the most recent version, see [http://www.derose.net/steve/utilities]
or [https://github.com/sderose].


=Options=
"""

# Conceptual box-drawing characters (TODO: Support the real Unicode ones)
boxDraws = {
    # name     : ( ASCII  UHEAVY    ),
    "HBAR"     : ( "-"  , "\u2501", ),
    "TOP"      : ( "-"  , "\u2533", ),
    "BOT"      : ( "-"  , "\u253B", ),

    "VBAR"     : ( "|"  , "\u2501", ),
    "LEFT"     : ( "|"  , "\u2523", ),
    "RIGHT"    : ( "|"  , "\u252B", ),

    "CROSS"    : ( "+"  , "\u254B", ),

    "ULCORNER" : ( "/"  , "\u250F", ),
    "URCORNER" : ( "\\" , "\u2513", ),
    "LLCORNER" : ( "\\" , "\u2517", ),
    "LRCORNER" : ( "/"  , "\u251B", ),
}

"""See also Charsets/UnicodeLists/boxDrawing.py.

    /---------------\
    | T | O | L | B |
    |---+---+---+---|
    | E | N | U | T |
    |---+---+---+---|
    | W | S | J | H |
    |---+---+---+---|
    | I | T | N | O |
    \---------------/
"""

# name    ASCII    UHEAVY
HBAR     = "-"   # \u2501
TOP      = "-"   # \u2533
BOT      = "-"   # \u253B

VBAR     = "|"   # \u2501
LEFT     = "|"   # \u2523
RIGHT    = "|"   # \u252B

CROSS    = "+"   # \u254B

ULCORNER = "/"   # \u250F
URCORNER = "\\"  # \u2513
LLCORNER = "\\"  # \u2517
LRCORNER = "/"   # \u251B

oldDice = [
    "AACIOT", "AHMORS", "EGKLUY", "ABILTY",
    "ACDEMP", "EGINTV", "GILRUW", "ELPSTU",
    "DENOSW", "ACELRS", "ABJMOQ", "EEFHIY",
    "EHINPS", "DKNOTU", "ADENVZ", "BIFORX"
]

newDice = [
    "AAEEGN", "ELRTTY", "AOOTTW", "ABBJOO",
    "EHRTVW", "CIMOTU", "DISTTY", "EIOSST",
    "DELRVY", "ACHOPS", "HIMNQU", "EEINSU",
    "EEGHNW", "AFFKPS", "HLNNRZ", "DEILRX"
]

denseOldBoard = "ALESSTIDTERANAME"  # 842 words
denseNewBoard = "TLGNAEIASTRSDEHB"  # 906 words
highOldBoard = "DSLRETAIPRNTUDES"   # 2447 points
highNewBoard = "TSLNEIAENTRTBESO"   # 2447 points

def getBoard(size:int=4, method:str="RANDOM"):
    board = ""
    if (method == "OLD"):          # The old commercial Boggle(r) dice
        for d in oldDice:
            board += random.choice(d)
    elif (method == "NEW"):        # The new commercial Boggle(r) dice
        for d in newDice:
            board += random.choice(d)
    elif (method == "RANDOM"):     # Random, unweighted by letter frequency
        for _i in range(size*size):
            board += random.choice(string.ascii_uppercase)
    elif (method == "WEIGHTED"):   # Random, weighted by letter frequency
        assert False, "Weighted choice not finished."  # TODO
        for _i in range(size*size):
            board += random.choice(string.ascii_uppercase)
    elif (method == "DENSEOLD"):
        board = denseOldBoard
    elif (method == "DENSENEW"):
        board =  denseNewBoard
    elif (method == "HIGHOLD"):
        board = highOldBoard
    elif (method == "HIGHNEW"):
        board = highNewBoard
    else:
        if (len(method) != size*size or
            not method.isascii() or not method.isletter()):
            print("--method is not a named set or --size ** 2 Latin letters.")
            sys.exit()
        board = method
    return board

def showBoard(board:str, size:int=4, cellWidth:int=3, cellHeight:int=1, indent:int=4):
    assert len(board) == size*size

    # Make the printable parts
    # See also my 'align', which knows about Unicode box-drawing chars, too.
    iString = " " * indent
    vSpace = iString + VBAR
    topBar = iString + ULCORNER
    midBar = iString + LEFT
    botBar = iString + LLCORNER

    for _col in range(size):
        vSpace += " " * cellWidth + VBAR
        topBar += HBAR * cellWidth + TOP
        midBar += HBAR * cellWidth + CROSS
        botBar += HBAR * cellWidth + BOT
    vSpace = vSpace[0:-1] + VBAR
    topBar = topBar[0:-1] + URCORNER
    midBar = midBar[0:-1] + RIGHT
    botBar = botBar[0:-1] + LRCORNER

    cellPad = " " * (cellWidth>>1)
    cellFormat = cellPad + "%1s" + cellPad + VBAR

    for rowStart in range(0, size*size, size):
        print(topBar if rowStart == 0 else midBar)
        for _s in range(cellHeight>>1): print(vSpace)
        rowChars = board[rowStart:rowStart+size]
        buf = iString + VBAR
        for col in range(size):
            buf += cellFormat % (rowChars[col])
        print(buf)
        for _s in range(cellHeight>>1): print(vSpace)
    print(botBar)
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
            "--color",  # Don't default. See below.
            help="Colorize the output.")
        parser.add_argument(
            "--oformat", "--outputFormat", "--output-format",
            type=str, default="ASCII", choices=[ "ASCII", ],
            help="How to display the board.")
        parser.add_argument(
            "--method", type=str, default="OLD",
            help="How to generate the board (named method or specific letters).")
        parser.add_argument(
            "--quiet", "-q", action="store_true",
            help="Suppress most messages.")
        parser.add_argument(
            "--size", type=int, default=4,
            help="What size board to generate (only 4 for now).")
        parser.add_argument(
            "--verbose", "-v", action="count", default=0,
            help="Add more messages (repeatable).")
        parser.add_argument(
            "--version", action="version", version=__version__,
            help="Display version information, then exit.")

        args0 = parser.parse_args()

        args0.method = args0.method.upper()

        if (args0.color == None):
            args0.color = ("CLI_COLOR" in os.environ and sys.stderr.isatty())
        #lg.setColors(args0.color)
        #if (args0.verbose): lg.setVerbose(args0.verbose)
        return(args0)


    ###########################################################################
    #
    args = processOptions()

    board0 = getBoard(args.size, args.method)
    showBoard(board0, args.size)

    sys.exit()
