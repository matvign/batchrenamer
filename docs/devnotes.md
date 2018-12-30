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
Using lambdas in place of functions is frowned upon. But brevity of lambdas looks nicer.  
Forgive me PEP8 for I have sinned.


## Regex replace nth
Replacing the nth value in regex is done by abusing re.sub, closures and attribute fields.  
#### Advantages
* Uses regex
* Simple

#### Disadvantages
* Uses regex
* Attribute field abuse
* **All** pattern matches are replaced, either by our choice or the match itself.
    * Optimisation: use the count field on re.sub so that we won't over-replace things


## Bracket remover
Bracket remover doesn't work with nested brackets or multiple types of brackets.  
It **probably** isn't common to have nested brackets in filenames and **maybe** filenames
don't have to deal with multiple brackets at a time. **¯\\\_(ツ)_/¯**


## Sequences
Alphabetical sequences stores a static string and updates it when needed. It's a bit verbose however. Itertools might have something useful, like cycle, but not sure how to reset it cleanly.