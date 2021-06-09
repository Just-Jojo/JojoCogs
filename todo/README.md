# ToDo Cog
Hello! This is a hopefully in depth guide to my todo cog, the largest cog on this repo.

\*note, throughout this guide `[p]` is your prefix (so for example, if your prefix is `$` instead of typing `[p]todo` you would type `$todo`). For examples, arguments surrounded by `[]` are *optional* arguments, and arguments surrounded by `<>` are *required* (if you do not input a required argument the help menu will be shown)

#### Table of contents
- [Basic commands](#BasicCommands)

### Basic commands

##### Todo
First off we have `todo`, the base command of the cog, and also a way to see a specific todo easily

**Usage** `[p]todo <sub command or index>`
If you do not provide a sub command or an index, it will show you the help command.

##### Add
Next, we have the second most basic command, `add`.
This *adds* a todo to your list.

**Usage** `[p]todo add <todo>`

##### List
Now we have the listing command. This lists your todos in a clean fashion. If you have todo lists combined, this will also list your completed todos

**Usage** `[p]todo list`

##### Remove
Last of the core three commands, we have remove. This will remove todos via indexes (yes, you can remove multiple)

**Usage** `[p]todo remove <indexes...>`

##### Reorder
This command moves a todo from one index to another index

**Usage** `[p]todo reorder <index> <new index>`

##### Search
This will search through your todos trying to match words (or a regular expression) to a todo
You can use [regex101.com](https://regex101.com/) on Python to figure out a regular expression.

**Usage** `[p]todo search [regex=False] <pattern>`

### Setting commands

##### Todoset
The base command for the settings group. Nothing special here

##### Embed
This toggles the cog to use embeds (if the channel allows for it) instead of plain text, or turns off that setting

**Usage** `[p]todoset embed <toggle>`

##### Markdown
This toggles if the cog should put text into a markdown code block, or turns off that setting

**Usage** `[p]todoset md <toggle>`

##### Autosort
This will auto sort your todos after you add them, or turns off this setting

**Usage** `[p]todoset autosort <toggle>`

##### Colour
This will change the colour of the embeds used (if toggled), or resets it to the bot's main colour

**Usage** `[p]todoset colour <colour>`

##### Private
This will make the cog send you a dm with your lists instead of to the channel you typed the command in, or turns off that setting

**Usage** `[p]todoset private <toggle>`
*Note: you will need to not have the bot blocked or dms disabled for it otherwise it will not work

##### Combine
This will combine both your todo and completed todo lists, or turns off this setting

**Usage** `[p]todoset combine <toggle>`

##### Details
This will provide extra details when adding, removing, or completing todos, or turns off this setting

**Usage** `[p]todoset details <toggle>`

##### Show settings
This will show your settings and the values associated with it (toggles and values)

**Usage** `[p]todoset showsettings`

### Complete
This subcommand deals with completed todos (todos that you have done or do not wish to do anymore)
This subcommand can be invoked with indexes to complete todos in your list

**Usage** `[p]todo complete <sub command or indexes>`

##### List
As with the todo list command, this lists your completed todos.

**Usage** `[p]todo complete list`

##### Remove
As with the todo remove command, this will remove completed todos at the indexes you input.

**Usage** `[p]todo complete remove <indexes>`

##### Reorder
As with the todo reorder command, this will move a completed todo to a new index.

**Usage** `[p]todo reorder <index> <new index>`

### Misc commands


##### Example
This shows an example of what your todo and complete list would look like

**Usage** `[p]todo example`

##### Version
This displays the version of todo

**Usage** `[p]todo version`

##### Suggestion
This tells you what to do if you have a suggestion

**Usage** `[p]todo suggestion`

##### Suggestors
This lists the people who have suggested something for this cog

**Usage** `[p]todo suggestors`