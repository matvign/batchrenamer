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

Paths ending with '/' are automatically expanded.  
If there are special characters in your file, surround the path in quotes.  
See examples for more information.

Because some arguments take at *least n* arguments, place the path argument before optional arguments.  


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
-re             replace with regex. remove with one argument, replace with two. use three to replace nth pattern instance
-seq            apply a sequence to the file
-ext            change extension of file ('' removes the extension)

--sel           after finding files with a file pattern, manually select which files to rename
--sort          after finding files, sort by ascending, descending or manual. useful for sequences
-q/--quiet      skip output, but show confirmations (see docs)  
-v/--verbose    show detailed output (see docs)  
--version:      show version  
```


## Argument order
Arguments have an order that they are applied. The general idea is that 
characters are removed/replaced before adding characters.

Arguments are run in the following order:
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
11. strip (remove '._ ' chars from end of file)
12. extension


## Examples
### File searching
#### Pattern escaping
When using pattern matching characters **(`[], *, ?`)** surround 
the pattern in quotes.  
e.g. `'lecture0*'`

#### Directory expansion
Patterns that end in a slash are automatically expanded.  
e.g. `'testdir/'` -> `'testdir/*'`

#### Escaping pattern matching
To interpret pattern matching characters as literal use `[]`.  
`'[[]Funny[]] file.mkv'`: interpret text in brackets as literal. Matches `'[Funny] file.mkv'`.  
`'something[*]'`: interpret asterisk as literal. Matches `'something*'`.  
`'nothing[?]'`: interpret question mark as literal. Matches `'nothing?'`.


### Usage examples
`batchren -h`: show help  
`batchren -sp`: replace files with spaces in current directory with '_'  
`batchren -case lower`: convert files in current directory to lower case  
`batchren -tr a b`: replace character a with b  
`batchren -re a`: remove all 'a' characters from files  
`batchren -re a b`: replace 'a' with 'b'  
`batchren -re a b 2`: replace the second instance of 'a' with 'b'  
`batchren -bracr square`: remove all square brackets and their contents  
`batchren -bracr square 2`: remove second square bracket and its contents  
`batchren -sl 3`: slice first three characters from files  
`batchren -sl 3:-3`: slice slice first three and last three characters files  
`batchren -sh 3:3`: shave first three and last three characters from files  


## Sequences
The sequence filter uses strings separated by slashes for formatting. Formatters begin with **%** and must be followed by **f**, **n**, **a**, **md**, or **mt** to be a valid formatter. Sequences reset with different directories.

### File format
```
%f
represents the filename.

raw/%f
represents raw string to be placed before and after filename.
e.g. 'raw/%f'  
filename -> rawfilename
```

### Numerical sequence
```
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

### Alphabetical sequence
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

### Time format
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
18.00.37_file1
18.30.37_file2
19.30.37_file3

e.g. %md/./%mt/_/%f
2019-11-16.19.10.37_file
```