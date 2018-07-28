# Documentation
## v0.3.1
pyren - a batch renamer  
pyren is a command line batch renamer written in python. pyren uses 
unix style pattern matching to look for files and uses a number of 
optional arguments to be applied to the set of files found.  
Files are placed into a set with glob, then renamed based on 
the optional args. 

# 1. Implementation detail

## 1.1 pyren argument parsing
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
spaces:     removes all whitespaces. replaces with underscores by default.  
translate:  replaces specified characters with opposing characters. Argument lengths must be equal  
case:       changes case of file   upper/lower/swap/capitalise word  
bracs:      replace brackets with round or square exclusive with bracr  
bracr:      remove brackets and text. exclusive with bracs  
append:     append text to file  
prepend:    prepend text to file  
enumerate:  use numbers and append  
extension:  change extension of file  
regex:      use regex to replace  
quiet:      suppress output. only shows what will be renamed and prompt  
verbose:    show what args were invoked  
version:    show version  


## 1.2 File and pattern matching
Unix style pattern matching can be implemented using a number of
different modules.

glob.iglob()
* simplest with the most support
* treats hidden files as special
* supports recursion, not that it should ever be used

pathlib
* full blown directory management
* has its own implementation of glob
* hashable
* complex

At the moment we're using glob. pathlib is an option if we want less 
imports.


## 1.3.1 File renaming filters
Filters have an order used to preserve intent of the user. The 
general idea is that we want to change/remove before adding 
characters. It wouldn't make sense to change things that the user 
wants to add.

Low priority:
* spaces
* translate
* bracket remove (exclusive group)
* bracket style  (exclusive group)
* case

Normal priority:
* append
* prepend

High priority
* extension (only applies to extension)
* enumerate
* regex
* str.strip (always applied to basename and ext)


## 1.3.2 Filter implementation
Filters are implemented as lambda expressions in a list. The
exception to this is high priority filters which are applied
external to the list of filters.
Filenames are passed in from file pattern matching and split into
directory, basename and ext. Each basename is run against the list 
of filters. Final processing occurs with high priority filters. 
A list of supported filters can be found above (1.3.1).

The resulting filename is then recombined and processed to determine
if it is safe to rename.


## 1.4.1 Processing rename information
If we rename a file to an existing filename the existing file will be 
overwritten. This is undesired behaviour so we need to ensure that it 
doesn't happen.

There are three conflicts that can occur:
1. two files are trying to rename itself to the same name
2. file tries to rename itself to a file that won't be renamed
3. file tries to rename itself to a file that will be renamed

note: the third conflict is a potential cycle (see 1.4.1.2)


## 1.4.1.1 Conflict resolution
Checking for a cycle is expensive and complicated. For that reason,
we only consider conflict checking for the first two cases above and
handle cycles with another method.

After filtering filenames, we categorise them into a nested dict
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
are all in conflict over the filename dest.
For convenience we also place files that were found but unchanged by 
filters into conflicts. 
The following is used to distinguish the conflicts:
```
if length(dest) == 1
    no filters applied
else
    name conflict over multiple files
```
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
        else
            if dest isfile and not in fileset
                add to conflicts[dest]
            else
                add src to renames[dest]

# a file not found by the file pattern will not be renamed, hence why
# it is immediately invalid. if a file exists and is in fileset, then we 
# haven't encountered it yet and can be handled by our cases later.
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
is the same as the windows os system. We use a number and incase it in
brackets. If the file already exists, then we continue generating upwards.


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

# Planned updates
## v0.3.3
* add slice filter
* review filter priority

## v0.4
* implement regex based filters
* implement high priority filters
* implement a more complex enumerate filter

## v0.4.1
* bug fixes/code cleanup


# Documentation changelog
28/07/2018
* updated to markdown
* changed contents of planned updates

26/07/2018
* updated documentation to v0.3.1
* updated planned updates

25/07/2018
* updated documentation to include planned updates
* updated to reflect current code