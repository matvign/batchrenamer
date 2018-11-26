# Documentation - v0.5.0
batchren - a batch renamer  
batchren is a python script for batch renaming files. batchren uses unix style 
pattern matching to look for files and uses optional arguments to 
be applied to the set of files found.  
Files are placed into a set with glob, then renamed based on 
the optional arguments. 


# 1. Implementation detail
## 1.1 batchren argument parsing
argparse is the module used to implement argument parsing from the
command line. The following is enabled:
* epilog: prints version after help
* prefix_chars: only accept dashes for optional arguments
* fromfile_prefix_char: accept arguments from file

### Arguments:
path: specifies the file pattern to search for. If using wildcards, surround the pattern in quotes. 
Expands pattern into directories or those ending with a slash. Doesn't apply to paths using special characters.  
e.g. testdir/ -> testdir/\*

### Optional arguments:  
```
spaces:     replace whitespace with specified char. default character is underscore (_)  
translate:  replaces characters with opposing characters. argument lengths must be equal  
slice:      slices a portion of the file to keep. must follow 'start:end:step' format (can have missing values)  
case:       changes case of file to upper/lower/swap/capitalise word  
bracr:      remove brackets and text.  
prepend:    prepend text to file  
postpend:     append text to file  
sequence:   apply a sequence to the file  
extension:  change extension of file (empty extensions are allowed)  
regex:      use regex to replace. a single argument removes that instance  
quiet:      suppress output. only shows what will be renamed and prompt  
verbose:    show what args were invoked and prompts for every file rename  
version:    show version  
```
note: arguments that require special characters should be encased in quotes  
e.g. `python3 batchren.py 'testdir/*' -tr '[]' '()'`


## 1.2 File and pattern matching
Unix style pattern matching can be implemented using a number of
different modules.

glob.iglob()
* simplest with the most support
* doesn't include hidden files
* supports recursion (not that it should be used)

pathlib
* complete directory management
* has its own implementation of glob
* hashable
* complex

At the moment we're using glob. pathlib is an option if we want less imports.


# 1.3 File renaming filters
## 1.3.1 Filters and order
Filters have a order that they are applied in. The general idea is that characters are removed/replaced before adding characters.

Filters are run in the following order:
1. regex
2. slice
3. bracket remove
4. translate
5. spaces
6. case
7. sequence
8. prepend
9. postpend
10. extention (only applies to extension)
11. str.strip (always applied to basename and ext)


## 1.3.2 Filter implementation
Filenames are passed in from file pattern matching and split into
directory, basename and ext. Each basename is run against a list 
of filters. Filters are implemented as lambda expressions in a list.  
A list of filters can be found above (1.3.1).

The resulting filename is then recombined and processed to determine if it is safe to rename.


# 1.4 Processing rename information
## 1.4.1 Processing renamed strings
After filtering filenames, we categorise them into a nested dict:
```python
rentable = {
    'renames': { 
        # dest: src 
    },
    'conflicts': {
        # dest: {
        #   srcs: [srcs]
        #   err: { error codes}
        # }
    }
}
```
The renames field contains dest to src mappings. These are the files 
that can be renamed safely. Using the sorted method, we can create a 
queue of (src, dest) files to rename.

The conflicts field contains dest to an object. 
The object contains a list of source names as well as a set of errors.
When printing the conflicts, we provide a few options.
1. If normal, show conflicts if they existed. Don't show reasons.
2. If verbose, always show conflict section. Show files and reason for conflict.
3. If quiet, don't show any information about conflicts


## 1.4.2 Conflict resolution
Filenames need to be checked for renaming conflicts. Renaming a file has the potential to overwrite an existing file.  
This is undesired behaviour so we need to ensure that it doesn't happen.

There are different renaming conflicts that can occur:
1. a file had no filters applied
2. new file name is empty
3. a file has a slash in it or a dot in front
4. two or more files are being renamed to the same name
5. file tries to rename itself to a file (or directory) that won't be renamed

note: the fifth conflict is a potential cycle (see 1.4.3)

Checking for a cycle is expensive and complicated. For this reason
we only consider conflict checking for the first two cases above and
handle cycles with another method.

The following applies:
```
for every src, dest
    if dest is in conflict
        add src into conflicts[dest]
    elif dest is in renames
        invalidate all dest in rentable
        add all dest to conflicts[dest]
    else
        if dest == src
            no filters applied, move to conflicts
        elif dest == ''
            empty string, move to conflicts
        elif dest[0] == '.'
            files should not start with ., move to conflicts
        elif '/' in dest[0]
            files should not start with /, move to conflicts
        else
            if dest exists and not in files found
                add to conflicts[dest]

    if no errors
        move to renames
'''
a file/dir not found by the file pattern will not be renamed, hence why it is immediately invalid. if a file exists and is in fileset, then we 
haven't encountered it yet and can be handled by our cases later.
'''
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

filex -> filey will cause an overwrite. However, it is possible to delay
filex and rename filey first. This way the conflict resolves itself.  
However, in the case of filea, fileb, filec and filed a cycle will be
formed and cannot be resolved.
The best way to resolve this is to use two pass renaming.
Create a random sequence whenever we get conflicts like this.

```
dir:
    filea           -> fileb (conflict, remove and get random sequence)
    filea           -> filea_1230
    fileb           -> filec (conflict)
    filec           -> filed (conflict)
    filed           -> filea (no conflict, if filea -> filea_1230)
    filea_1230      -> fileb
```

In this case, filea - filed is a cycle, so we have to use two pass for
every conflict we find.

For simplicity generate numbers instead of random strings. Files are
appended with an underscore and a number. If the file already exists 
then continue generating upwards.


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
* implement sequence: add a sequence to a file
* add tests
* bug fixes/code cleanup


# Planned updates



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