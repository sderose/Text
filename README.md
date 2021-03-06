#README for "Text" repo#

Utilities and data for working with text files (including Unicode, but little or
no markup -- the notion "plain text" is, imho, barely meaningful).
For utilities more closely involved with character set issues per se,
see the neighboring "Charsets" repo.

As with all my utilities, use "-h" to get help.


''OCR_resources/'' has some statistics and other information relevant to OCR
error correction.

''addup'' --  A simple adding machine. Can also add times (hh:mm), and calculate
hourly payments.

''annotsToHTML.py'' --

''any2xml.py'' --  (moved to XML/CONVERT/).

''anycat'' --  Like 'zcat', this cats files even if they're compress in various ways.
But it should handle more types.

''body'' --  Like 'head' and 'tail', but lets you specify a starting point and an
ending point, to retrieve everything between. It also has a lot more options
for locating those points by line/char/total offset, regex, etc.

''cleanURI'' --  Clean up "nested" URIs, such as some search engines hand you, that
point back to the engine, with the "real" destination embedded in the query
portion.

''dbDumpUtil'' --  Retrieve and pretty-print summaries of a MySQL database's structure,
such as able declarations, lists of tables, etc.

''dotFill'' --  Replacement long runs of spaces in a text file, by packed or
intermittent dot-fills. You can do just each n-th line, or all; control
spacing between the dots; etc.

''doubleSpace'' --  Change \n to \n\n. For output with lots of long lines (that your
terminal program will wrap), pipe through this before 'more', and they'll be
much more readable. Can also triple-space or whatever.

''dropBlankLines'' --  Delete blank lines from the input. You can choose either
truly blank (empty) lines, or line with just whitespace; and to normalize space
in remaining lines (see also normalizeSpace).

''dropLineBreaks'' --  Remove newlines before and/or after lines matching a given
regex. Or replace the line-end sequence by a specified string instead.

''dumpx'' --  An old hex-dump I wrote, that I like better than 'od'. Based partly on
one from Brown University's VM/CMS system, which I think was written by
Peter DiCamillo.

''findDates'' --  Locate date strings in the input. Covers a fair range of formats,
but doesn' include times, and doesn't do anything special for data ranges,
durations, periodic dates, etc.

''findLineLengths'' --  Make a chart of how many lines of the input there are, of
each given length, with %, cumulative %, average, etc. Can also be told to
just find and report the longest line, or just lines outside given min and/or max,
or give you the line number of all lines of each length.

''findLongLines'' --  report all lines over a given length.

''findUnbalancedQuotes.py'' --  Just what it says.

''globalChange'' --  A pretty powerful regex global change tool. You can specify any
number of changes, and there are zillions of options, including an (I think)
rather nice dry-run option, and decent interactive options similar to emacs
(except that you have entered the realm of streaming data; you cannot go back).

''insertAt'' --  Inserts a message or the content of a file, at a certain point in the
       input. The point can be a given line number and column, or the first
       line matching a given regex. See also 'splitAt'.

''iota'' --  Prints a series of numbers, characters, or times.  either as-is or
       filled in to a place(s) in a template.  This can be useful for making
       lists to use in code or documents. Supports bases, alphabetical and
       Roman numeral ranges, dates, intervals, padding, etc.

''joinAt'' --  Remove line breaks where a given regex is matched.

''json2xml.py'' --  (moved to XML/CONVERT/).

''list2htmlForm'' --  (PERL) take a list of items (one per line), and put in the markup
to make it into HTML form items, Your choice of checkboxes, radiobuttons, or
a popup menu.

''list2htmlForm.py'' --  Same, but in Python.

''makeComparisonFromLists'' --

''numberLines'' --  Insert line number at the start of each line. Your choise of base,
separator to put after, or you can add them at end of line, remove existing ones,
pad to a given width, etc.

''pad'' --  Add specified pad character (default space) to start or end of lines,
to get them to a given length. Or insert at a specified column instead.

''pod2markdown.py'' --  Rough conversion of POD (PERL help-file markup) to MarkDown.

''randomRecords'' --  Select random records from a file. YOu can pick a certain number
of records, or a percent, or even n-th record. Includes support for "reservoir"
sampling, which makes the choice random despite not knowing how many total
records there will be. Various options such as excluding blank or "comment" lines,
inserting the (original) record number on each chosen line, skipping the first
N records, etc.

''shiftLinesDown'' --  For each line that matches some (Perl-style) regex, shift that line
       later in the file by some number of lines.

''shortenContext.py'' --  (unfinished) Trim long lines to just a limited around surrounding a
given regex match.
This is useful, for example, if you are getting grep hits in files with
very long lines, and you want more than just the matched string, but less
then the entire lines.

''sort.py'' --   (unfinished) Really simple version of 'sort'. Doesn't do fancy locale
stuff

''splitAtMatches'' --  Insert a line-break before and/or after each match of regex. Previous line breaks
       can be kept or dropped. You can instead replace each match with something,
       insert an --indent after inserted line-breaks,....
       Includes most of the functionality of *nix "fold"\

''stripComments.py'' --  Remove "comment" lines (you specify the delimiter).

''text2html.py'' --  convert plain-ish text files to HTML, accounting for blank lines,
numbered and asterisked lists with various punctuation, indentation.

''text2strings.py'' --  Turn a text file into a Python array of strings.
Each line is escaped and then double-quoted, and a comma is added.
The whole file is enclosed in square brackets.
Lines beginning with '#' can be treated as comments.

''utr'' --  A version of 'tr' that knows about Unicode.

''wrap'' --  Accumulate fields from input lines, and re-wrap to make full lines,
       optionally padding for nice columns. This does pretty much what 'ls' does
       for filenames, thugh with many options to control widths, paddings,
       row vs. column-major order, whitespace treatment, etc.
