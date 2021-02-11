import asyncio
import logging

import discord
from redbot.core import Config, checks, commands
from redbot.core.utils.predicates import MessagePredicate
from redbot.core.utils.chat_formatting import pagify, box
from . import menus
import typing

log = logging.getLogger("red.JojoCogs.todo")

# f-strings cannot contain backslashes...
_new_line = "\n"
_config_structure = {
    "todos": [],
    "assign": {},
    "use_md": True,
    "detailed_pop": False,
    "use_embeds": True,
    "autosort": False,
    "reverse_sort": False,
    "completed": [],
}


def positive_int(arg: str) -> int:
    """Returns a positive int"""
    try:
        ret = int(arg)
    except ValueError:
        raise commands.BadArgument(f"{arg} is not a integer.")
    if ret <= 0:
        raise commands.BadArgument(f"{arg} is not a positive integer.")
    return ret


class ToDo(commands.Cog):
    """A simple todo list for discord"""

    __version__ = "0.1.8"
    __author__ = [
        "Jojo",
    ]

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 19924714019, force_registration=True)
        self.config.register_user(**_config_structure)

    def format_help_for_context(self, ctx):
        """Thankie thankie Sinbad"""
        return (
            f"{super().format_help_for_context(ctx)}"
            f"\n\n__Version:__ `{self.__version__}`\n"
            f"__Author:__ `{', '.join(self.__author__)}`"
        )

    async def red_delete_data_for_user(
        self,
        requester: typing.Literal["discord", "owner", "user", "user_strict"],
        user_id: int,
    ) -> None:
        await self.config.user_from_id(user_id).clear()

    ### Setting commands ###

    @commands.group()
    async def todoset(self, ctx):
        """Base settings command for customizing todo lists"""

    @todoset.command()
    async def pop(self, ctx, toggle: bool):
        """Log popped todo reminders"""
        await self._toggler(
            ctx=ctx, item="Logging todos", key="detailed_pop", toggle=toggle
        )

    @todoset.command()
    async def md(self, ctx, toggle: bool):
        """Toggle whether or not the list should use markdown"""
        await self._toggler(
            ctx=ctx, item="Fancy todo listing", key="use_md", toggle=toggle
        )

    @todoset.command(name="embed")
    async def use_embeds(self, ctx, toggle: bool):
        """Toggle whether or not to use embeds for todo lists"""
        await self._toggler(
            ctx=ctx, item="Embedded todo listing", key="use_embeds", toggle=toggle
        )

    @todoset.command()
    async def autosort(self, ctx, toggle: bool):
        await self._toggler(ctx=ctx, item="Autosorting", key="autosort", toggle=toggle)

    async def _toggler(self, ctx: commands.Context, item: str, key: str, toggle: bool):
        toggled = "enabled!" if toggle else "disabled!"
        setting = await self.config.user(ctx.author).get_raw(key)
        if setting == toggle:
            await ctx.send(f"{item} is already {toggled}")
        else:
            await ctx.send(f"{item} is now {toggled}")
            await self.config.user(ctx.author).set_raw(key, value=toggle)

    ### Listing commands ###

    @commands.group()
    async def todo(self, ctx):
        """Base todo reminder command"""

    @todo.group(
        invoke_without_command=True
    )  # TODO: Move this up to the other subcommands
    async def complete(self, ctx, *indexes: positive_int):
        """Complete todo reminders"""
        # Thanks to Blackie#0001 on Red for the idea
        # :D
        if not len(indexes):
            todos = await self.config.user(ctx.author).todos()
            if len(todos):
                return await self.page_logic(ctx, self.number(todos))
            return await ctx.send("Hm, you don't have any todos!")
        indexes = self.sort_lists(items=indexes)
        passes = []
        fails = []
        completed = []
        async with self.config.user(ctx.author).todos() as todos:
            for index in indexes:
                try:
                    _ = todos.pop(index)
                except IndexError:
                    fails.append(f"`{index}`")
                else:
                    passes.append(f"`{index}`")
                    completed.append(_)
            msg = ""
            detailed = await self.config.user(ctx.author).detailed_pop()
            if len(passes):
                if detailed:
                    comp = [f"`{x}`" for x in completed]
                    msg += f"Completed {len(passes)} todos:\n{', '.join(comp)}\n"
                else:
                    msg += f"Passed {len(passes)} todos\n"
            if len(fails):
                if detailed:
                    msg += f"Failed to complete {len(fails)} times:\n{', '.join(fails)}"
                else:
                    msg += f"Failed to complete {len(fails)} times"
            if not msg:
                msg = "Hm, something went wrong"
            await ctx.send(msg)
        async with self.config.user(ctx.author).completed() as complete:
            for item in completed:
                complete.append(item)

    @complete.command(name="list")
    async def complete_list(self, ctx):
        """List your completed todos!"""
        if len((completed := await self.config.user(ctx.author).completed())):
            await self.page_logic(ctx, self.number(completed), "Completed Todo List")
            log.info(completed)
        else:
            await ctx.send("You don't have any completed todos yet!")

    @todo.command()
    async def add(self, ctx, *, todo: str):
        """Add a todo reminder

        Example:
        `[p]todo add Walk the dog soon`"""
        async with self.config.user(ctx.author).todos() as todos:
            todos.append(todo)
            if await self.config.user(ctx.author).detailed_pop():
                await ctx.send(f"Added this as a todo reminder!\n`{todo}`")
            else:
                await ctx.send("Added that todo reminder!")
        await self._maybe_auto_sort(author=ctx.author)

    async def _maybe_auto_sort(self, author: discord.Member):
        autosort = await self.config.user(author).autosort()
        if not autosort:
            return
        reversed = await self.config.user(author).reverse_sort()
        async with self.config.user(author).todos() as todos:
            todos.sort(reverse=reversed)  # Fairly simple

    # `pop` because you're basically using list.pop(index) :p
    @todo.command(aliases=["del", "delete", "pop"])
    async def remove(self, ctx, *todo: positive_int):
        """Remove a todo reminder

        Example:
        `[p]todo del <number>`"""
        async with self.config.user(ctx.author).todos() as todos:
            if not len(todos):
                return await ctx.send(
                    (
                        "You don't have any todos yet!"
                        f"\nUse `{ctx.clean_prefix}todo add <todo>` to add one!"
                    )
                )
            if not len(todo):
                sending = self.number(item=todos)
                await self.page_logic(ctx, sending)
                return
            else:
                todo = self.sort_lists(todo)
            popped_todos = []
            failed = []
            for to in todo:
                try:
                    popped_todos.append(f"`{todos.pop(to)}`")
                except IndexError:
                    await ctx.send("That was an invalid todo index!")
                    failed.append(f"`{to}`")
            msg = ""
            if await self.config.user(ctx.author).detailed_pop():
                if len(popped_todos) > 1:
                    popped_todos = "\n".join(popped_todos)
                    msg += f"Removed these todo reminders!\n{popped_todos}"
                # Since this is gonna be `1` I don't have to check for it
                elif len(popped_todos):
                    popped_todos = popped_todos[0]
                    msg += f"Removed this todo reminder!\n`{popped_todos}`"
                if len(failed) > 1:
                    failed = "\n".join(failed)
                    msg += f"\nCould not remove todos at these indexes\n{failed}"
                elif len(failed):
                    failed = failed[0]
                    msg += f"\nCould not remove a todo at this index\n{failed}"
            else:
                if len(popped_todos) > 1:
                    msg += "Removed those todos!"
                else:
                    msg += "Removed that todo!"
                if len(failed):
                    msg += "\nFailed to remove some todos!"
        if msg:
            await ctx.send(msg)
        else:
            await ctx.send("Hm, something went wrong")
        await self._maybe_auto_sort(author=ctx.author)

    @todo.command(name="list")  # Fuck you reserved keywords >:|
    async def todo_list(self, ctx):
        """List your todo reminders"""
        todos = await self.config.user(ctx.author).todos()
        if len(todos) >= 1:
            todos = self.number(item=todos)
            await self.page_logic(ctx, todos)
        else:
            await ctx.send(
                (
                    f"You don't have any ToDo reminders!"
                    f"\nYou can add one using "
                    f"`{ctx.clean_prefix}todo add <name> <ToDo>`"
                )
            )

    @todo.command()
    async def sort(self, ctx: commands.Context):
        """Sort your todos alphabetically"""
        msg = await ctx.send("Would you like to sort your todos in reverse?")
        try:
            pred = MessagePredicate.yes_or_no(ctx)
            result = await self.bot.wait_for("message", check=pred, timeout=15.0)
        except asyncio.TimeoutError:
            await ctx.send("Alright!")
            reverse = True
        else:
            reverse = pred.result
        await self.config.user(ctx.author).reverse_sort.set(reverse)
        async with self.config.user(ctx.author).todos() as items:
            if not len(items):
                await ctx.send("You don't have any todos!")
            else:
                items.sort(reverse=reverse)
                await ctx.send("Okay! I've sorted your todos!")
                await self.page_logic(
                    ctx=ctx, things=[f"{num}. {i}" for num, i in enumerate(items, 1)]
                )

    @todo.command(
        aliases=[
            "move",
        ]
    )
    async def rearrange(self, ctx, index: positive_int, new_index: positive_int):
        """Rearrange a todo!"""
        index -= 1
        new_index -= 1
        async with self.config.user(ctx.author).todos() as items:
            if new_index > (leng := len(items)):
                new_index = leng - 1
            try:
                item = items.pop(index)
            except IndexError:
                await ctx.send("Hm, there doesn't seem to be a todo there")
            else:
                items.insert(new_index, item)
                await ctx.send(f"Moved todo reminder `{item}`")

    @todo.command()
    async def show(self, ctx, index: positive_int):
        """Show a todo reminder by index!"""
        act_index = index - 1
        async with self.config.user(ctx.author).todos() as todos:
            try:
                todo = todos[act_index]
            except IndexError:
                return await ctx.send("Hm, that doesn't seem to be a todo!")
        todo = f"{index}. {todo}"
        md = await self.config.user(ctx.author).use_md()
        embedded = await self.config.user(ctx.author).use_embeds()
        if embedded:
            sending = discord.Embed(
                title=f"{ctx.author.name}'s ToDos", colour=await ctx.embed_colour()
            )
            sending.set_footer(text="ToDo list")
            if md:
                sending.description = box(todo, lang="md")
            else:
                sending.description = todo
            await ctx.send(embed=sending)
        else:
            if md:
                sending = box(todo, lang="md")
            else:
                sending = todo
            await ctx.send(sending)

    ### Utilities ###

    def number(self, item: list) -> list:
        return [f"{num}. {act}" for num, act in enumerate(item, 1)]

    async def page_logic(
        self, ctx: commands.Context, things: list, title: str = "Todo List"
    ):
        things = "\n".join(things)
        use_md = await self.config.user(ctx.author).use_md()
        use_embeds = await self.config.user(ctx.author).use_embeds()
        menu = menus.TodoMenu(
            source=menus.TodoPages(
                data=list(pagify(things)),
                use_md=use_md,
                use_embeds=use_embeds,
                title=title,
            ),
            delete_message_after=False,
            clear_reactions_after=True,
        )
        await menu.start(ctx=ctx, channel=ctx.channel)

    def sort_lists(self, items: typing.List[int]) -> list:
        items = [v - 1 for v in items]
        items.sort(reverse=True)
        return items
