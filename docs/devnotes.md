# Notes

General notes on implementation and their positives/negatives.

Also touch on a bit of coding style.


## Forgive me PEP8 for I have sinned

The following are the settings used with flake8.  
Config is usually placed within `~/.config/flake8`
```
[flake8]
# https://pycodestyle.readthedocs.io/en/latest/intro.html#error-codes
# http://flake8.pycqa.org/en/latest/user/error-codes.html
# E128: continuation line under-indented for visual indent
# E501: line too long
# E731: do not assign a lambda expression
# W292: no newline at end of file
# W391: blank line at end of file
# W505: doc line too long
# F841: local variable name is assigned to but never used
ignore = E128, E501, E731, W292, W391, W505, F841
```


## Use of lambdas
Using lambdas in place of functions is bad style. But brevity of lambdas looks nice. I like things that look nice.  


## Extensions
The last extension is grabbed by default. This isn't bad, but it might not be what you want. Ideally this should be customizable.  

The simplest way to grab all extensions is using pathlib.suffixes. If I'm going to use pathlib for all suffixes of a filename, I might as well use it everywhere. Not a commitment I'm willing to make just yet.


## Regex replace nth
Replacing the nth value in regex is done by abusing re.sub, closures/decorators and attribute fields.  
#### Advantages
* Uses regex
* Can be easily extended to replace a range or set
* Simple

#### Disadvantages
* Uses regex
* Attribute field abuse
* **All** pattern matches are replaced, either by our choice or the match itself.
    * Optimisation: use the count field on re.sub so that we won't over-replace things


## Bracket remover
Bracket remover doesn't remove different types of brackets and doesn't work with nested brackets.  
If nested brackets aren't common and removing multiple bracket types at a time, then maybe I won't write anything for it. Could be an interesting exercise I guess.


## Exceptions
As it is ValueError and TypeError are raised and caught in seqObj. I could continue using this, or I could write a new exception for bad sequences.

I guess I'll leave it... for now.


## Sequences
Strings are joined from lists each time we want a sequence. This is nice and simple.  
We could be picky about when to join strings, but it could get a bit hairy.


## Packaging
After fighting with the package structure, I realised I was the problem.  
Tests should work from root directory. just run `pytest` (needs to be installed)