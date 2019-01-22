# Batchren

A script to rename files with various arguments. Supports Unix style file globbing.

## Requirements
1. Ubuntu 18.04
2. Python 3.6.7
3. Pip
4. natsort (from pypa)

## Instructions
1. Download/clone this repo
2. cd into directory
3. run pip install --user dist/batchren-0.5.2-py3-none-any.whl (should also download natsort)


### Arguments:
path: specifies the file pattern to search for. If using wildcards, surround the pattern in quotes.  
Expands pattern or those ending with a slash into directories.  
e.g. testdir/ -> testdir/\*

### Optional arguments:  
```
prepend:    prepend text to file  
postpend:   append text to file  
spaces:     replace whitespace with specified char. default character is underscore (_)  
translate:  replaces characters with opposing characters. argument lengths must be equal  
case:       changes case of file to upper/lower/swap/capitalise word  
slice:      slices a portion of the file to keep. must follow 'start:end:step' format (can have missing values)  
shave:      shave some text from the top and/or the bottom of the text. must follow 'head:tail' format, must not be negative
bracr:      remove curly/round/square brackets from filename. add an optional argument to remove the nth bracket instance.  
regex:      use regex to replace. a single argument removes that instance. add an optional argument to remove the nth instance.  
sequence:   apply a sequence to the file  
extension:  change extension of file (empty extensions are allowed)  
sort:       after finding files, sort by ascending or descending order. useful for sequences.  
dryrun:     run without renaming any files
quiet:      skip output, but show confirmations (see section 1.5)  
verbose:    show detailed output (see section 1.5)  
version:    show version  
```


## Sequences
The sequence filter uses strings separated by slashes for formatting. Formatters begin with **%** and must be followed by **f**, **n**, **a**, **md**, or **mt** to be a valid formatter. Sequences reset with different directories.

### File format
```
%f
represents the filename.

raw/%f
represents raw string to be placed before/after filename.
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
%f/_/%a
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

Default characters for missing values are 'a' and 'z' 
(includes missing values due to multiplier).
e.g. %a:a: = %a:a:z
     %a2:a:z = %a:a:zz = %a:aa:zz

When start is longer than end, the missing values are filled with None
and not incremented.
e.g. %a:aa:z = %a:aa:z(None) -> aa, ba, ca, da, ea, ..., za, aa

When end is longer than start, the missing values are filled with 'a'
and is incremented as usual.
e.g. %a:a:zz = %a:aa:zz

Uppercase and lowercase sequencing is supported.
Note that lowercase goes to uppercase, but NOT vice versa.
i.e. %a:a:A -> a, b, c, ..., z, A
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