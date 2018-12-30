# Documentation - v0.5.1
batchren - a batch renamer  
batchren is a python script for batch renaming files. batchren uses unix style 
pattern matching to look for files and uses optional arguments to 
be applied to the set of files found.  
Files are placed into a set with glob, then renamed based on 
the optional arguments. 


# 1. Implementation detail
# 1.1.1 Batchren argument parsing
argparse is the module used to implement argument parsing from the
command line. The following is enabled:
* epilog: prints version after help
* prefix_chars: only accept dashes for optional arguments
* fromfile_prefix_char: accept arguments from file

### Arguments:
path: specifies the file pattern to search for. If using wildcards, surround the pattern in quotes.  
Expands pattern or those ending with a slash into directories.  
e.g. testdir/ -> testdir/\*

### Optional arguments:  
```
spaces:     replace whitespace with specified char. default character is underscore (_)  
translate:  replaces characters with opposing characters. argument lengths must be equal  
slice:      slices a portion of the file to keep. must follow 'start:end:step' format (can have missing values)  
shave:      shave some text from the top and/or the bottom of the text. must follow 'head:tail' format, must not be negative
case:       changes case of file to upper/lower/swap/capitalise word  
bracr:      remove curly/round/square brackets from filename. add an optional argument to remove the nth bracket instance.  
prepend:    prepend text to file  
postpend:   append text to file  
sequence:   apply a sequence to the file  
extension:  change extension of file (empty extensions are allowed)  
regex:      use regex to replace. a single argument removes that instance. add an optional argument to remove the nth instance.  
dryrun:     run without renaming any files
quiet:      skip output, but show confirmations (see section 1.5)  
verbose:    show detailed output (see section 1.5)  
version:    show version  
```


## 1.1.2 Considerations/issues
Arguments that require special characters should be encased in quotes.  
e.g. `python3 batchren.py 'testdir/*' -tr '[]' '()'`

Due to the way that argparse interpret hypens, arguments starting with a hypen 
should use an equal sign and quotes. This *should* work with most filters.  
e.g. `-arg='-val'`

The translate filter doesn't work with this method. Individual hypens can be
translated, but any extra characters will give an error.  
e.g. `-tr - +'` is ok, but `-tr '-a' '+b'` will give an error.


# 1.2 File and pattern matching
Unix style pattern matching is implmented using the python glob module.

glob.iglob()
* simplest with the most support
* doesn't include hidden files
* supports recursion (not that it should be used)


# 1.3 File renaming filters
## 1.3.1 Filters and order
Filters have a order that they are applied in. The general idea is that 
characters are removed/replaced before adding characters.

Filters are run in the following order:
1. regex
2. slice
3. shave
4. bracket remove
5. translate
6. spaces
7. case
8. sequence
9. prepend
10. postpend
11. extention (only applies to extension)
12. str.strip (always applied to basename and ext)


## 1.3.2 Filter implementation
Filenames are passed in from file pattern matching and split into directory, 
basename and ext.  
Each basename is run against a list of filters.  
Filters are implemented as classes, functions or lambda expressions in a list.  
The resulting filename is then recombined and processed to determine if it is
safe to rename.


## 1.3.3 Regex filter
Regex filter allows python regex to be used.  
There may be some untested oddities that occur from inputting python regex as
bash strings. If there was an issue with compiling
or executing regex replacement, the program (**should**) safely crash.  


## 1.3.4 Shave filter
The shave filter is a convenient variation of the slice filter that performs 
slicing on the ends of a file.  
Unlike the slice filter, shave only takes two slice values, one for head 
and one for tail.  
Values can be ommitted for head and/or tail slicing.  
Negative integers are not allowed in the shave values.

The slice filter can do everything the shave filter does. Shave exists purely for 
convenience.
```
e.g. 
-sh 4:2
removes 4 characters from the front and 2 characters from the back

-sh 4:2:0
invalid, only takes two values
```


## 1.3.5 Bracket remover
The bracket remover takes a certain bracket type: curly, round or square and
removes it from the filename.  
An optional argument can be specified to remove the nth bracket.  
Internally, it uses the same function from the regex filter.
```
e.g. 
-bracr square
removes all square brackets and their contents

-bracr square 1
remove only the first square bracket found.
```
Bracket remover doesn't work with nested brackets!!


## 1.3.6 Sequences
The sequence filter uses strings separated by slashes for formatting. Strings must belong with % and be either f, n or a to be a valid formatter. Sequences reset with different directories.

```
%f
represents the filename.

raw/%f
represents raw string to be placed before/after filename

%n/_/%f
represents a number sequence followed by filename.
Starts counting at 1 with 0 padded by default.

e.g. %n/_/%f
01_file
02_file
...
10_file
...
100_file

%n3:start:end:step
represents a number sequence with a depth of 3,  
starting at start, resetting to start when greater than end
and incrementing by step.  
* If depth is missing, default is 2 
* If start is missing, default is 1 
* If end is missing, keep counting up
* If step is missing, default is 1

e.g. %n3:2:9:2
002_file
004_file
006_file
008_file
002_file

%f/_/%a
represents a letter sequence starting at a and resetting when greater than z.

e.g. %f/_/%a
file_a
file_b
file_c
...
file_z
file_a

%a2:start:end
represents a letter sequence starting with a depth of 2,
starting at start, resetting to start when greater than end

e.g. %f/_/%a2:a:c
file_aa
file_ab
file_ac
file_ba
file_bb
file_bc
file_ca
file_cb
file_cc
file_aa
```

# 1.4 Processing rename information
## 1.4.1 Processing renamed strings
After filtering filenames, we categorise them into a nested dict:
```python
rentable = {
    'renames': { dest: src },
    'conflicts': {dest: {srcs: [srcs], err: {error codes}}}
    'unresolvable': set()
}
```
### Renames
The renames field contains dest to src mappings. These are files that
can and will be renamed.  
We can easily create a queue of (src, dest) for renaming.

### Conflicts
Filenames need to be checked for renaming conflicts since renaming can
potentially overwrite a file.  
The conflicts field contains detailed information about files that have
issues or cannot be renamed.
* dest: file name that caused an error
* srcs: list of file names attempting to rename to dest
* err: set of error codes explaining why the dest is erroneous

### Unresolvable
Unresolvable conflicts are files that will not be renamed.  
Unresolvable conflicts are srcs from conflicts. Anything that attempts
to rename to a file in this field is a conflict.


## 1.4.2 Conflict resolution
There are different renaming conflicts that can occur:
1. a file name has not changed
2. the base name is empty (e.g. parent/file -> parent/)
3. the base name begins with a dot (e.g. file -> .file)
4. the base name contains a slash (e.g. file -> fi/le)
5. file tries to rename to a file or directory that won't be renamed
6. two or more files are being renamed to the same name
7. file name is already in conflicts

To build the rename table, the following applies:
```
for every src, dest
    errset = set()
    if dest is in conflict
        add err to errset
        add dest into conflicts
        cascade(src)

    elif dest is in renames
        add err to errset
        add both entries to conflicts
        cascade(src)

    else
        if dest == src
            add err to errset
        if dest == ''
            add err to errset
        if dest[0] == '.'
            add err to errset
        if '/' in dest[0]
            add err to errset
        
        if dest not in files found and exists
            add err to errset

        if errors in errset
            add dest to conflicts
            cascade(src)

    if no errors
        move to renames

cascade(target)
'''
we need to mark srcs as unusable and invalidate entries in 'renames'  
that want to rename to our target.  
See 1.4.3 Cycle Resolution
'''
dest = target
while true
    add dest to unresolvable
    if dest in renames
        temp = renames[dest]
        move dest to conflicts
        dest = temp
        continue
    break
```
```
dir
  fileA   -> filea  
  fileB   -> filea (conflict with filea)  
  fileC   -> fileC (no change)
  fileD   -> fileC (conflict with fileC, unresolvable)
  fileE   -> fileE (not picked up by glob)
  fileF   -> fileE (conflict with fileE, unresolvable)
```


## 1.4.3 Cycle resolution
Cycles happen when each file wants to be renamed to the next.
```
dir
  filea -> fileb (cycle)
  fileb -> filec   ...
  filec -> filed   ...
  diled -> filea (cycle)
  filex -> filey (conflict with filey, resolvable)
  filey -> filez
```
filex -> filey will cause a conflict since filey already exists.
It is possible to delay filex and rename filey -> filez first. 
This way filex can rename to filey safely without conflict.  

However, a cycle will form for filea, fileb, filec and filed which cannot 
be resolved through reordering.  
The best way to resolve this is to use two pass renaming. 
Generate a random sequence followed by a number to break the cycle. 
If the generated sequence already exists, continue generating upwards.

For simplicity we apply two pass renaming for every conflict that we
encounter.
```
dir:
    filea           -> fileb (conflict with fileb, get random sequence)
    filea           -> filea_1
    fileb           -> filec (conflict with filec)
    filec           -> filed (conflict with filed)
    filed           -> filea (no conflict if filea -> filea_1)
    filea_1         -> fileb
```
There are also cases where invalid cycles need to invalidate members.
```
dir
    filea           -> fileb
    fileb           -> filec
    filec           -> filec (conflict)
```
Since filec won't be renamed, fileb can't be renamed to filec, 
and filea can't be renamed to fileb. So the entire cycle is invalid.  

To deal with this we use a cascade function, which removes names related
to the conflict. We also mark each conflicted src as unusable 
so that nothing else attempts to use it.
```
dir
    filea           -> fileb (removed by cascade)
    fileb           -> filec (removed by cascade)
    filec           -> filed (removed by cascade)
    filed           -> fil/ed (invalid name, cascade on filed)
    fileg           -> filea (conflict, filea is marked as unusable)
```

# 2. Displaying information
There are different behaviours depending on the arguments quiet, verbose and dryrun. 
Quiet and verbose cannot be set at the same time.

## 2.1 Parser level
The parser level is where arguments are read in.  
The following applies:
* If error with arguments, show error, quit
* If verbose, show arguments used
* If no optional arguments set, quit
* If no files found, quit
* If verbose, show files found
```
if argumenterror:
    show error with arguments
    quit
if verbose:
    show arguments used
if no optional arguments set
    show 'no optional arguments set for renaming'
    quit
else
    if no files found
        show 'no files found'
        quit
    if verbose
        show files found
```


## 2.2 Renamer level
The renamer level is showing the contents things that can be renamed or have errors.
For conflicts:
* If quiet, show no conflict information
* If verbose, show detailed errors
* If not quiet, not verbose, no errors, show nothing
* If not quiet, not verbose, errors exist, show files that won't be renamed
* If dryrun or verbose, show files as they are renamed
```
if quiet
    show nothing
elif verbose
    if conflicts
        show detailed errors
    else
        show 'no conflicts found'
elif not quiet and not verbose and conflicts
    show files that won't be renamed

if renames
    show files to be renamed
else
    show 'no files to rename'

if dryrun or verbose
    show files as they are renamed
```


# Changelog
## v0.3
* generate rentable in renamer
* use str.title over string.capwords
* use exclusive group for quiet and verbose, bracs and bracr
* use set and iglob to store files
* improve display for rentable
* implement conflict checking
* generate random names for cycle resolution 
* implement renaming
* general bugfixes

## v0.3.1
* more verbose display
* added filter for bracket remove
* bug fixes/code cleanup

## v0.3.2
* add translate filter
* remove separator filter in favor of translate filter
* rename .documentation (why was it hidden to begin with?)

## v0.3.3
* add slice filter
* add closure function for bracr filter
* add more conflict conditions (no empty, no . or ..)
* add dialog for added conflict conditions
* move slice and translate up in order

## v0.3.4
* quick fix for missing variable

## v0.3.5
* produce tuple from args.translate
* switch to lambda expression for bracr filter
* rename enumerate filter to sequence
* fix bug involving srcs.sort, should be sorted(srcs)
* make code smaller

## v0.3.6
* give help text about wild cards in --help
* change filter order
* remove bracket style in favor of tr

## v0.4.0
* change directory/file structure
* use natsort for sorting file names
* implement regex filter

## v0.4.1
* regex filter: one argument removes that word
* translate filter: better argument parsing

## v0.4.2
* proper package structure
* update __version variable in _version.py
* move code from batchren.py to renamer.py
* conflict condition: cannot rename to something starting with '/'
* conflict condition: cannot rename to something starting with '.'
* except all errors from os module
* new scheme for conflict printing
* bug fixes/code cleanup

## v0.5.0
* change help display for metavars
* better display for renames/conflicts
* cascade on cycle conflicts
* collapse adjacent dots, remove spaces and strip dots on right side of extension
* add dry run option
* implement sequence: add sequence to files (works over multiple directories)
* add tests
* bug fixes/code cleanup


## v0.5.1
* regex filter: except re.error in main.py and renamer.py
* regex filter: optional remove nth instance
* bracr filter: change to target specific bracket removal
* sequence filter: remove requirement for file formatter
* add help text for hyphens
* new: shave filter, remove text from head or/and tail
* bug fixes/code cleanup


# Planned updates
## v0.5.2
* new: interactive option for ordering of files
* bug fixes/code cleanup


# Documentation changelog
4/11/2018
* updated planned updates for v0.5

7/10/2018
* updated planned updates for v0.4.3

3/10/2018
* updated v0.4.2 and planned updates

3/9/2018
* changed planned updates for v0.4.2

1/9/2018
* changed planned updates for 0.3.6 - 0.4.1
* added proper category for 1.3 and 1.4

30/07/2018
* updated documentation to v0.3.5

29/07/2018
* added more conflict conditions
* updated documentation to v0.3.3

28/07/2018
* updated to markdown
* changed contents of planned updates
* updated missing version number

26/07/2018
* updated documentation to v0.3.1
* updated planned updates

25/07/2018
* updated documentation to include planned updates
* updated to reflect current code