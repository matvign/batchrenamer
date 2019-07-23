# Batchren

A script to rename files with various arguments. Supports Unix style file globbing.


## Requirements
1. Ubuntu 18.04
2. Python 3.6.7
3. pip
4. natsort (from pypa)
5. urwid (from pypa)


## Instructions
1. Download/clone this repo
2. cd into directory
3. run `pip install --user dist/batchren-0.6.1-py3-none-any.whl` (also downloads natsort & urwid)


## Usage
### Positional arguments:
path: specifies the file pattern to search for.  

Paths that are directories are automatically expanded.  
If there are special characters in your file, surround the path in quotes.  
See examples for more information.

Because some arguments take at *least n* arguments, place the `path` argument before optional arguments.  

### Optional arguments:  
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
--dryrun        run without renaming any files
-q/--quiet      skip output, but show confirmations  
-v/--verbose    show detailed output  
--version:      show version  
```


## Argument order
Arguments have an order that they are applied. The general idea is that 
characters are removed/replaced before adding characters.

Arguments are run in the following order:
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


## Examples
### Positional Arguments
By default batchren searches for all files in the current working directory.
If the file pattern is a directory batchren will expand into the directory.

batchren also supports wild characters **(`[], *, ?`)**. Surround file patterns in quotes when using pattern matching characters.

To escape pattern characters use `[]` or use the `--esc` option.

#### Examples
`batchren -pre file`: finds all files and prepends 'file'  
`batchren 'dir/' -pre file`: prepend 'file' to all files in `dir`  
`batchren 'lecture0*' -pre file`: finds all files starting with lecture0* and prepends 'file'  
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


### File Renaming Arguments
The following arguments are used to rename files. The absence of file renaming arguments terminates the program.


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
  
Second argument default is "".

##### Examples
Under construction...


#### Extension
`batchren -ext EXT`  
Change extension of files. Adds extension if it exists, otherwise replaces existing extension.

##### Examples
`batchren -ext mp4`: change file extension to `mp4`  
`batchren -ext ''`: remove all file extensions  


#### Sequences
The sequence option uses strings separated by slashes for formatting. Formatters begin with **%** and must be followed by **f**, **n**, **a**, **md**, or **mt** to be a valid formatter. Sequences reset with different directories.

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