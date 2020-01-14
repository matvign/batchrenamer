# Batchren
Batchren is a python script for batch renaming files.  
Batchren uses pattern matching to look for files and optional 
arguments to rename the set of files found.  

## Requirements
1. Ubuntu 18.04
2. Python 3.6.8
3. pip
4. natsort (from pypa)
5. urwid (from pypa)

## Instructions
1. Download/clone this repo
2. Change into directory for this repo
3. Run `make install`

## Developing
1. Download/clone this repo
2. Change into directory for this repo
3. `virtualenv venv -p python3.6`
4. `source venv/bin/activate`
5. `pip install -r requirements.txt`
6. Code...
7. `make build`
8. Deactivate `virtualenv`
9. `make remove && make install`

## Usage
### Positional arguments
path: specifies the file pattern to search for.  

Directory paths are automatically expanded.  
If there are special characters in your path, surround the path in quotes.  
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
-sl             rename files to character slice of file. follows 'start:end:step' format (can have missing values)
-sh             remove characters from head and/or tail of file. follows 'head:tail' format, must not be negative
-bracr          remove curly/round/square brackets and its contents. add optional argument to remove the nth bracket group
-re             remove/replace with regex. remove with one argument, replace with two. use three to replace nth pattern instance
-seq            apply a sequence to the file
-ext            change extension of file ('' removes the extension)

--esc           escape pattern matching characters
--raw           treat extension as part of filename and do not process whitespace

--sort          after finding files, sort by ascending, descending or manual. useful for sequences
--sel           after finding files with a file pattern, manually select which files to rename

--dryrun        run without renaming any files
-q/--quiet      skip output, but show confirmations (see **section 3**)  
-v/--verbose    show detailed output (see **section 3**)  
--version:      show version  
```


## Argument order
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
11. strip (remove whitespace from ends of file)
12. extension (remove whitespace and collapse dots)

## Examples
### Positional Arguments
By default batchren searches for all files in the current working directory.
If the file pattern is a directory batchren will expand into the directory.

batchren has support for wild characters **(`[], *, ?`)**. Surround file patterns in quotes if there are pattern matching characters.

To escape pattern characters use `[]` or the `--esc` option.

#### Examples
`batchren -pre f`: prepend 'f' to all files in the current working directory  
`batchren 'dir/' -pre f`: prepend 'f' to all files in `dir`  
`batchren 'lecture0*' -pre f`: prepend 'f' to all files matching 'lecture0*'  
`batchren 'file[*] -pre f`: prepend 'f' to the file with name 'file*'  
`batchren 'file[?] -pre f`: prepend 'f' to the file with name 'file?'  
`batchren '[[]720p] file.mp4' -pre f`: prepend 'f' to the file with name '[720p] file.mp4'  


### Optional Arguments
There are some optional arguments that influence the results, but do not rename files.

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


#### Raw
`batchren --raw`  
Treat extension as part of filename and do not process whitespace.
Use if you want to ignore extensions or preserve whitespace.

##### Examples
```
# Treat extension as part of filename
batchren file.txt -post bla: filebla.txt
batchren file.txt -post bla --raw`: file.txtbla
```
```
# Preserve whitespace
batchren file.txt -post " ": file.txt
batchren file.txt -post " " --raw: "file.txt "
batchren file.txt -pre " " --raw: " file.txt"

batchren " " -pre "bla": bla
batchren " " -pre "bla": " bla"
```


### File Renaming Arguments
Arguments are applied in a fixed order. The general idea is that 
characters are removed/replaced before adding characters.

The program ends if no file renaming arguments were specified.

#### Prepend/Postpend
`batchren -pre TEXT -post TEXT`  
Prepend/postpend adds text before/after filenames.

##### Examples
`batchren -pre 'text'`: add `'text'` before filename  
`batchren -post 'text'`: add `'text'` after filename  
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
`batchren -c cap`: capitalise words in the file. Works with files separated by symbols `'._-'` separated files  


#### Slice
`batchren -sl start:end:step`  
Slice a portion of filenames. Accepts python slice format.

##### Examples
`batchren -sl 1:3`: take characters starting from 1st index to 3rd index  
`batchren -sl 1:10:2`: take characters starting from 1st index to 10th index, skipping every second index  
`batchren -sl 3:-3`: remove first and last three characters


#### Shave
`batchren -sh head:tail`  
Shave a portion of filenames. Convenient option that is the same as removing first and last n characters.

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

Default argument for REPL is `""`.

##### Examples
Under construction...


#### Extension
`batchren -ext EXT`  
Change extension of filenames. Add extension if it doesn't exist, otherwise replace the existing extension.

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

e.g. %n/_/file
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

e.g. %n3:2:9:2/_/file
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

#### Timestamps
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
