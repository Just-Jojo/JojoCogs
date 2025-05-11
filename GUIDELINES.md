# Some general guidelines for writing code
Currently this is not added to the repo and maybe I won't add it but I want a little thing for myself


## Functions
If it does not have to be in a class it shouldn't be. Staticmethods shouldn't exist unless absolutely necessary.
Create utility files with utility functions if they do not require interacting with instance variables.

## Indentation
Only 1 or 2 levels of indentation. If you have more, break it into a new function
(TODO change to using 8 spaces for indentation)

## Variable names
Short and concise. Get the information across and nothing more.

## Cog methods
### Cogs should be layed out like this:
Cog Initalization: (\_\_init\_\_, format_help_for_context, cog_load, any tasks that will need to be ran)
Commands
Helper functions: (sending menus, different formatting or other methods *Note the above [Functions guideline](#functions))