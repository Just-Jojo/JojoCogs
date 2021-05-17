# Contributing

Firstly, thanks! I sometimes have no idea what I'm doing and I need help, so thanks! (:

### Linter

I use Flake8 for linting, and I have it set with the max line length to be 90.

If you don't have Flake8, in your venv (please work in a venv while doing dev stuff) type `pip install flake8`


### Formatting

I use Black for formatting. If you don't have it, again install it with `pip install black`

Formatting with Black should either be ran by an ide (I use vsc so it does it automatically), or from the command line

```py -m black -l 90 <path>```

### Type checking

I use Mypy for type checking. Again, if you do not have it install it with `pip install mypy`

```mypy --ignore-missing-imports --follow-imports=silent --show-column-numbers --show-error-codes <path>```

### Misc.

Make sure to respect the license and *please* try to keep be nice to other people working on this project :D