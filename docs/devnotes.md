# Notes

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
Replacing the nth value in regex is done by abusing attribute fields. This... probably isn't good? There are other ways of finding and replacing things. Abusing attribute fields on the other hand is nice and convenient.

## Sequences
Alphabetical sequences stores a static string and updates it when needed. It's a bit verbose however. Itertools might have something useful, like cycle, but not sure how to reset it cleanly.

#### Advantages
* Uses built in regex
* Simple

#### Disadvantages
* Uses regex
* Still replaces every value, basically the same as normal re.sub
* Attribute field abuse