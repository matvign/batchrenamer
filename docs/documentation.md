# Documentation - v0.6.1
batchren - a batch renamer  
batchren is a python script for batch renaming files. batchren 
uses unix style pattern matching to look for files and uses optional 
arguments to rename the set of files found.  


# 1. Usage
## 1.1 Positional arguments:
path: specifies the file pattern to search for.  

Paths ending with '/' are automatically expanded.  
If there are special characters in your file, surround the path in quotes.  
See examples for more information.

Because some arguments take at *least n* arguments, place the path argument before optional arguments.  
See **section 1.3** for examples.


## 1.2 Optional arguments:  
```
-h:             show help text
-pre            add text before file
-post           add text after file
-sp             replace whitespace with specified char. default: '_'
-tr             translate characters of first argument to second argument. argument lengths must be equal
-c              change case of file to upper/lower/swap/capitalise word
-sl             slice a portion of the file to keep. must follow 'start:end:step' format (can have missing values)
-sh             shave text from top and/or the bottom of file. must follow 'head:tail' format, must not be negative
-bracr          remove curly/round/square bracket groups from filename. add optional argument to remove the nth bracket group
-re             remove/replace with regex. remove with one argument, replace with two. use three to replace nth pattern instance
-seq            apply a sequence to the file
-ext            change extension of file ('' removes the extension)

--esc           escape pattern matching characters
--sel           after finding files with a file pattern, manually select which files to rename
--sort          after finding files, sort by ascending, descending or manual. useful for sequences
-q/--quiet      skip output, but show confirmations (see **section 3**)  
-v/--verbose    show detailed output (see **section 3**)  
--version:      show version  
```

## 1.3 Usage
### Positional Arguments
By default batchren searches for all files in the current working directory.
If the file pattern is a directory or ends with a `'/'`, batchren will expand into the directory.

batchren also supports wild characters **(`[], *, ?`)**. Surround file patterns in quotes when using pattern matching characters.

To escape pattern characters use [] or use the `--esc` option.

#### Examples
`batchren 'testdir/' -pre file`: equivalent to 'testdir/*'  
`batchren 'lecture0*' -pre file`: finds all files   starting with lecture0* and prepends 'file'  
`batchren 'file[*] -pre f`: looks for 'file*'  
`batchren 'file[?] -pre f`: looks for 'file?'  
`batchren '[[]720p] file.mp4'`: looks for '[720p] file.mp4'  


### Optional Arguments
There are optional arguments that do not rename files, but do influence the results.

#### Escape
`batchren --esc [CHARS]`  
Escape pattern matching characters from `path` positional argument.
Accepts characters from `'*?[]'`. Escapes characters from the string.

##### Examples
`batchren --esc`: escape all pattern matching characters `'*?[]'`  
`batchren --esc '*?'`: escape pattern matching characters `'*?'`  
`batchren --esc '[]'`: escape range brackets  
`batchren --esc '['`: escape range brackets (same as above)  
`batchren --esc ']'`: escape range brackets (same as above)  


#### Select
`batchren --sel`  
Manually select files to rename after pattern matching.


#### Sort
`batchren --sort {asc, desc, man}`  
Sort order of files found through file matching and the select option. Useful for sequences.

##### Examples
`batchren --sort asc`: sort files in ascending order  
`batchren --sort desc`: sort files in descending order  
`batchren --sort man`: sort files manually. Opens interactive text-user interface.  


### Renaming Arguments
Arguments have an order that they are applied. The general idea is that 
characters are removed/replaced before adding characters.

Renaming arguments are run in the following order:
1. regex
2. bracket remove
3. slice
4. shave
5. translate
6. spaces
7. case
8. sequence
9. prepend
10. postpend
11. strip (remove '._ ' chars from end of file)
12. extension


#### Prepend/Postpend
`batchren -pre TEXT -post TEXT`  
Prepend/postpend adds text before or after files.

##### Examples
`batchren -pre 'text'`: add `'text'` before files  
`batchren -post 'text'`: add `'text'` after files  
`batchren -pre 'text' -post 'text'`: add `'text'` before and after files  


#### Space
`batchren -sp [REPL]`  
Change whitespace to the specified character. Default is `'_'`.

##### Examples
`batchren -sp`: replace whitespace in files with `'_'`  
`batchren -sp '.'`: replace whitespace in files with `'.'`


#### Translate
`batchren -tr CHARS CHARS`  
Translate characters from one to another. Accepts two arguments. Both arguments must be equal in length.

##### Examples
`batchren -tr a b`: translate `'a's to 'b's`  
`batchren -tr ab cd`: translate `'a's to 'c's` and `'b's to 'd's`


#### Case
`batchren -c {upper, lower, swap, cap}`  
Change case of files. Accepts one of either upper, lower, cap or swap.

##### Examples
`batchren -c lower`: make all files lower case  
`batchren -c upper`: make all files upper case  
`batchren -c swap`: swap case of all files  
`batchren -c cap`: capitalise words in the file. Works with `'_-'` separated files  


#### Slice
`batchren -sl start:end:step`  
Slice a portion of files. Accepts python slice format.

##### Examples
`batchren -sl 1:3`: take characters starting from 1st index to 3rd index  
`batchren -sl 1:10:2`: take characters starting from 1st index to 10th index, skipping every second index  
`batchren -sl 3:-3`: remove first and last three characters


#### Shave
`batchren -sh head:tail`  
Shave a portion of files. Convenient option that is the same as removing first and last n characters.

##### Examples
`batchren -sh 3:3`: shave first and last three characters


#### Bracket Remove
`batchren -bracr {curly, round, square} [COUNT]`  
Remove brackets and their contents. Bracket remover accepts one of either curly, round or square.  
An optional argument can be specified to remove the nth bracket group.  

##### Examples
`batchren -bracr square`: removes all square brackets and their contents  
`batchren -bracr square 1`: remove first square bracket and its contents


#### Regex
`batchren -re PATTERN [REPL] [COUNT]`
Use regex to replace contents. Accepts up to three arguments.
* If one argument, remove instances of PATTERN
* If two arguments, replace all instances PATTERN by REPL
* If three arguments, replace COUNT'th instance of PATTERN by REPL
  
Second argument default is ''.

##### Examples
Under construction...


#### Sequences
The sequence options uses strings separated by slashes for formatting. Formatters begin with **%** and must be followed by **f**, **n**, **a**, **md**, or **mt** to be a valid formatter. Sequences reset with different directories.

#### File format
```
%f
represents the filename.

raw/%f/raw
represents raw string to be placed before and after filename.
e.g. raw/%f/raw
filename -> rawfilenameraw
```

#### Numerical sequence
```
%n
represents a number sequence starting at 1
with 0 padded by default.

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
and incrementing by a number >= 0.  
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
```

#### Alphabetical sequence
```
%a
represents a letter sequence starting at 'a' and resetting when greater than 'z'.

e.g. %f/_/%a
file_a
file_b
file_c
...
file_z
file_a

%a:start:end
represents a letter sequence starting at start, 
resetting to start when greater than end.  
alphabetical sequences are bound by position.

e.g. %a:aa:cb
aa
ab
ba
bb
ca
cb
aa (complete reset)

%a2:start:end
represents a letter sequence, but with a width multiplier of 2.
e.g. %a2:a:z = %a:aa:zz (z is multiplied by 2)

Missing values are filled with default characters 'a' or 'z' 
(includes missing values due to multiplier).
e.g. %a:a:   = %a:a:z
     %a2:a:z = %a:a:zz = %a:aa:zz

When start is longer than end, missing values are filled with the 
default character and not incremented.
e.g. %a:aa:z = %a:aa:z(a) 
     -> aa, ba, ca, ..., za, aa

When end is longer than start, missing values are filled with 'a'
and incremented as usual.
e.g. %a:a:zz = %a:aa:zz
     -> aa, ab, ac, ..., az, ba, ..., zz

Uppercase and lowercase sequencing is supported.
Note that lowercase goes to uppercase, but NOT vice versa.
e.g. %a:a:Z -> a, ..., z, A, ..., Z 
     %a:A:a -> A, A, A, ..., A, A
```

#### Time format
```
%md
represents the date that a file was last modified.

e.g. %md/_/%f
2019-11-14_file1
2019-11-15_file2
2019-11-16_file3

%mt
represents the time that a file was last modified. 

e.g. %mt/_/%f
18:00:37_file1
18:30:37_file2
19:30:37_file3

e.g. %md/./%mt/_/%f
2019-11-16.19:10:37_file
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
The renamer level shows filenames that can be renamed or have errors.
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


# 3. Implementation detail
## 3.1 Batchren argument parsing
argparse is the module used to implement argument parsing from the
command line. The following is enabled:
* epilog: prints notification and link to readme for examples.
* prefix_chars: only accept dashes for optional arguments
* fromfile_prefix_char: accept arguments from file


## 3.2 File and pattern matching
Unix style pattern matching is implmented using the python glob module.

glob.iglob()
* simplest with the most support
* doesn't include hidden files
* supports recursion (not that it should be used)


## 3.3 File renaming arguments
Filenames are passed in from file pattern matching and split into directory, 
basename and ext.  
Each basename is run against a list of the applicable arguments.  
Each argument places is implemented as a class, function or 
lambda expression in a list.  
The resulting filename is then recombined and processed to determine if it is
safe to rename.


# 3.4 Processing rename information
## 3.4.1 Processing renamed strings
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


## 3.4.2 Conflict resolution
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


## 3.4.3 Cycle resolution
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


# 4. Version History
## Changelog
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
* reorganise package structure (python packaging is confusing)
* regex filter: optional remove nth instance
* bracr filter: target specific bracket type for removal (+ optional nth bracket)
* sequence filter: remove requirement for file formatter
* sequence filter: positional sequence of all alphabetical characters
* add help text for hyphens
* exceptions: use re.error and oserror for better exception handling
* new: shave filter, remove text from head or/and tail
* bug fixes/code cleanup

## v0.5.2
* normalise and expand ('.', '..', '~')
* remove any '._' from right side of file name
* new: option for sorting by asc or desc
* new: sequence filter :: add modification time
* bug fixes/code cleanup

## v0.6.0
* new: interactive option for ordering files
* new: interactive option for choosing files
* bug fixes/code cleanup


# Planned updates
## v0.6.1
* new: interactive option to select/unselect all files
* new: literal argument to interpret filenames literally
* bug fixes