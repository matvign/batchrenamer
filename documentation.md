# Documentation
## v0.3.6
batchren - a batch renamer  
batchren is a command line batch renamer written in python. batchren 
uses unix style pattern matching to look for files and uses a number 
of optional arguments to be applied to the set of files found.  
Files are placed into a set with glob, then renamed based on 
the optional args. 

# 1. Implementation detail

## 1.1 batchren argument parsing
argparse is the module used to implement argument parsing from the
command line. The following is enabled:
* epilog: prints version after help
* prefix_chars: only accept dashes for optional arguments
* fromfile_prefix_char: accept arguments from file

### Arguments:
dir: specifies the file pattern to search for.  
Expands file pattern into directories. Only works for file patterns ending with a slash. Doesn't work if special characters present.  
e.g. testdir/ -> testdir/\*

### Optional arguments:  
```
spaces:     removes all whitespaces. replaces with underscores by default  
translate:  replaces specified characters with opposing characters. argument lengths must be equal  
slice:      slices a portion of the file. must follow 'start:end:step' format (can have missing values)  
case:       changes case of file to upper/lower/swap/capitalise word  
bracr:      remove brackets and text.  
append:     append text to file  
prepend:    prepend text to file  
sequence:   use numbers and append  
extension:  change extension of file  
regex:      use regex to replace  
quiet:      suppress output. only shows what will be renamed and prompt  
verbose:    show what args were invoked and prompts for every file rename   
version:    show version  
```
note: arguments that require special characters should be encased in quotes  
e.g. `python3 pyren.py 'testdir/*' -tr '[]' '()'`

## 1.2 File and pattern matching
Unix style pattern matching can be implemented using a number of
different modules.

glob.iglob()
* simplest with the most support
* treats hidden files as special
* supports recursion, not that it should ever be used

pathlib
* full blown directory management
* supports many os
* has its own implementation of glob
* hashable
* complex

At the moment we're using glob. pathlib is an option if we want less imports or want os compatability.


## 1.3.1 File renaming filters
Filters have an order used to preserve intent of the user. The 
general idea is that we want to change/remove before adding 
characters. It wouldn't make sense to change things that the user 
wants to add.

Filters are run in the following order:
1. regex
2. slice
3. sequence
4. translate
5. spaces
6. bracket remove
7. case
8. append
9. prepend
10. extention (only applies to extension)
11. str.strip (always applied to basename and ext)


## 1.3.2 Filter implementation
Filenames are passed in from file pattern matching and split into
directory, basename and ext. Each basename is run against a list 
of filters. Filters are implemented as lambda expressions in a list.  
A list of supported filters can be found above (1.3.1).

The resulting filename is then recombined and processed to determine
if it is safe to rename.


## 1.4.1 Processing rename information
After filtering filenames, we categorise them into a nested dict:
```python
rentable = {
    'renames': { 
        # dest: src 
    },
    'conflicts': {
        # dest: [srcs]
    }
}
```
The renames field contains dest to src mappings. These are the files 
that can be renamed safely. Using the sorted method, we can create a 
queue of (src, dest) files to rename.

The conflicts field contains dest to a list of srcs. The list of srcs
are files that should not be renamed because of an issue with dest.
The following is used to distinguish the conflicts:
```
if dest == ''
    cannot rename to empty file
if dest == '.' or '..'
    cannot rename to dot files
else
    if len(dest) == 1
        no filters applied
    else
        conflicting rename with multiple files
```

## 1.4.1.1 Conflict resolution
The final portion of processing filenames is checking for renaming conflicts.
Renaming a file to an existing filename will overwrite the existing file.  
This is undesired behaviour so we need to ensure that it doesn't happen.

There are three renaming conflicts that can occur:
1. two files are trying to rename itself to the same name
2. file tries to rename itself to a file (or dir) that won't be renamed
3. file tries to rename itself to a file that will be renamed

note: the third conflict is a potential cycle (see 1.4.1.2)

Checking for a cycle is expensive and complicated. For that reason,
we only consider conflict checking for the first two cases above and
handle cycles with another method.

The following applies:
```python
for every src, dest
    if dest is in conflict
        add src into conflicts[dest]
    elif dest is in renames
        invalidate all dest in rentable
        add all dest to conflicts[dest]
    else
        if src == dest
            no filters applied, move to conflicts
        elif dest == ''
            empty string, move to conflicts
        elif dest == '.' or dest == '..'
            cannot rename to dot files, move to conflicts
        else
            if dest exists and not in fileset
                add to conflicts[dest]
            else
                add src to renames[dest]
'''
a file/dir not found by the file pattern will not be renamed, hence why
it is immediately invalid. if a file exists and is in fileset, then we 
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

## 1.4.1.2 Cycle resolution
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

For simplicity we generate numbers instead of random strings. The idea
is to append an underscore and a number. If the file already exists, 
then we continue generating upwards.


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


# Planned updates
## v0.4.0
* change directory/file structure
* use natsort for sorting file names
* implement regex filter

## v0.4.1
* implement directory sensitive renaming
* implement complex sequence filter
* bug fixes/code cleanup


# Documentation changelog
1/9/2018
* changed planned updates for 0.3.6 - 0.4.1

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