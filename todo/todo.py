"""
MIT License

Copyright (c) 2020-2021 Jojo#7711

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import asyncio
import logging
import typing

import discord
from abc import ABC
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box, pagify
from redbot.core.utils.predicates import MessagePredicate

from .utils import TodoMenu, TodoPages, positive_int
from .commands import Examples, Settings, Deleting, CompositeMetaclass


_config_structure = {
    "todos": [],
    "completed": [],
    "detailed_pop": False,
    "use_md": True,
    "use_embeds": True,
    "autosort": False,
    "reverse_sort": False,
    "combined_lists": False,
    "private": False,
}
_about = (
    "ToDo is a cog designed by Jojo#7791 for keeping track"
    " of tasks for you to do. It provides a simple listing,"
    " adding, and completing for you to work with, and is highly"
    " customizable so you get the best out of it"
)
_comic_link = (
    "https://raw.githubusercontent.com/Just-Jojo/JojoCog-Assets/main/data/todo_comic.jpg"
)


class ToDo(Examples, Settings, Deleting, commands.Cog, metaclass=CompositeMetaclass):
    """A simple and highly customizable todo list for Discord"""

    _no_completed_message = (
        "You don't have any completed todos!"
        " You can complete a todo using `{prefix}todo complete <indexes...>`!"
    )
    _no_todo_message = (
        "You don't have any todos! Add one using `{prefix}todo add <todo>`!"
    )
    __version__ = "1.2.0"
    __author__ = ["Jojo#7791"]

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            cog_instance=self, identifier=19924714019, force_registration=True
        )
        self.config.register_user(**_config_structure)
        self.log = logging.getLogger("red.JojoCogs.todo")

    def format_help_for_context(self, ctx: commands.Context):
        """Thankie thankie Sinbad"""
        plural = ""
        if len(self.__author__) > 1:
            plural = "s"
        return (
            f"{super().format_help_for_context(ctx)}"
            f"\n\nCurrent Version: `{self.__version__}`"
            f"\nAuthor{plural}: `{', '.join(self.__author__)}`"
        )

    ### Listing commands ###

    @commands.group()
    async def todo(self, ctx):
        """Todo commands

        Add a todo to your list and manage your tasks
        """
        pass

    @todo.group(
        invoke_without_command=True, aliases=["c"], require_var_positional=True
    )  # `c` is easy to type
    async def complete(self, ctx, *indexes: positive_int):
        """Commands having to do with completed todos!"""
        if not await self.config.user(ctx.author).todos():
            return await ctx.send(self._no_todo_message.format(prefix=ctx.clean_prefix))
        async with ctx.typing():
            async with self.config.user(ctx.author).todos() as todos:
                async with self.config.user(ctx.author).completed() as completed:
                    indexes = [x - 1 for x in indexes]  # Remove 1 from each item...
                    indexes.sort(reverse=True)  # and sort the list
                    fails, failed, comp, compled = 0, [], 0, []
                    for index in indexes:
                        try:
                            rmd = todos.pop(index)
                        except IndexError:
                            fails += 1
                            failed.append(f"`{index}`")
                        else:
                            comp += 1
                            compled.append(f"`{rmd}`")
                            completed.append(f"`{rmd}`")
        msg = "Done."
        details = await self.config.user(ctx.author).detailed_pop()
        if comp:
            plural = "" if comp == 1 else "s"
            msg += f"Completed {comp} todo{plural}"
            if details:
                msg += "\n" + "\n".join(compled)
        if fails:
            plural = "" if fails == 1 else "s"
            msg += f"Failed to complete {fails} todo{plural}"
            if details:
                msg += "\n" + "\n".join(failed)
        await ctx.send(msg)
        await self._maybe_autosort(ctx)

    @todo.command()
    async def explain(self, ctx, comic: bool = False):
        """Explain a bit about this cog"""
        if (em := await ctx.embed_requested()) :
            embed = discord.Embed(title="About Todo", colour=await ctx.embed_colour())
            kwargs = {"embed": embed}
        else:
            kwargs = {"content": None}
        if comic:
            if em:
                embed.set_image(url=_comic_link)
            else:
                kwargs["content"] = _comic_link
        else:
            if em:
                embed.description = _about
            else:
                kwargs["content"] = _about
        await ctx.send(**kwargs)

    @todo.command()
    async def suggestions(self, ctx):
        """See how you could add suggestions!"""
        msg = (
            "Thanks for reading this! I made this cog for managing my tasks, "
            "however I realised that this would be helpful for a lot of people "
            "and I added the ability to customize your todo list!\nHowever, "
            "I can add more things, I just don't know what I should add, "
            "you can help by going to my GitHub repo (<https://github.com/Just-Jojo/JojoCogs>), "
            "go to the `issues` tab, click on `Todo suggestions`, and leave a comment! "
            "(here's the issue link <https://github.com/Just-Jojo/JojoCogs/issues/15> :) )"
        )
        if await ctx.embed_requested():
            kwargs = {
                "embed": discord.Embed(
                    title="Todo suggestions",
                    description=msg,
                    colour=await ctx.embed_colour(),
                ),
            }
        else:
            kwargs = {"content": msg}
        await ctx.send(**kwargs)

    @todo.command(name="add")
    async def todo_add(self, ctx, *, todo: str):
        """Add a todo to your list"""
        async with self.config.user(ctx.author).todos() as todos:
            todos.append(todo)

        msg = "Added that as a todo!"
        details = await self.config.user(ctx.author).detailed_pop()
        if details:
            msg += f"\n'{discord.utils.escape_markdown(todo)}'"
        await ctx.send(msg)
        await self._maybe_autosort(ctx)

    @todo.command()
    async def sort(self, ctx):
        """Sort your todos"""
        await ctx.send("Would you like to sort your todos in reverse? (y/n)")
        pred = MessagePredicate.yes_or_no(ctx)
        try:
            await self.bot.wait_for("message", check=pred)
        except asyncio.TimeoutError:
            await ctx.send("Okay, I won't sort your todos in reverse")
            result = False
        else:
            result = pred.result
        await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
        await self.config.user(ctx.author).reverse_sort.set(result)
        async with self.config.user(ctx.author).todos() as todos:
            todos.sort(reverse=result)
        await self.config.user(ctx.author).autosort.set(True)

    @todo.command(name="list")
    async def todo_list(self, ctx):
        """List your current todos!"""
        todos = await self.config.user(ctx.author).todos()
        comb = await self.config.user(ctx.author).combined_lists()
        completed = await self.config.user(ctx.author).completed()
        if not todos and not comb or not todos and not completed:
            await ctx.send(_no_todo_message.format(prefix=ctx.clean_prefix))
        elif not todos and comb:
            await self._complete_list(ctx=ctx)
        else:
            todos = await self._number_lists(todos)
            if comb:
                if (c := await self.config.user(ctx.author).completed()) :
                    if not await self.config.user(ctx.author).use_md():
                        c = await self._cross_lists(c)
                    c = await self._number_lists(c)
                    c.insert(0, "\N{WHITE HEAVY CHECK MARK} Completed todos")
                    todos.extend(c)
            await self.page_logic(ctx, todos, "Todos")

    @complete.command(name="sort")
    async def complete_sort(self, ctx):
        """Sort your todos"""
        await ctx.send("Would you like to sort your completed todos in reverse? (y/n)")
        pred = MessagePredicate.yes_or_no(ctx)
        try:
            await self.bot.wait_for("message", check=pred)
        except asyncio.TimeoutError:
            await ctx.send("Okay, I won't sort them in reverse")
            result = False
        else:
            result = pred.result
        await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
        await self.config.user(ctx.author).reverse_sort.set(result)
        async with self.config.user(ctx.author).completed() as todos:
            todos.sort(reverse=result)

    @complete.command(name="list")
    async def complete_list(self, ctx):
        """List your completed todos"""
        completed = await self.config.user(ctx.author).completed()
        if not completed:
            await ctx.send(_no_completed_message.format(prefix=ctx.clean_prefix))
        else:
            if not await self.config.user(ctx.author).use_md():
                completed = await self._cross_lists(completed)
            completed = await self._number_lists(completed)
            await self.page_logic(ctx, completed, "Completed todos")

    ### Utility methods ###

    async def _complete_list(self, ctx: commands.Context):
        """|coro|

        Logic for complete list... for todo list?
        """
        user_conf = self.config.user(ctx.author)
        completed = await user_conf.completed()
        if not completed:
            return
        if not await user_conf.use_md():
            completed = await self._cross_lists(completed)
        completed = await self._number_lists(completed)
        completed.insert(0, "\N{WHITE HEAVY CHECK MARK} Completed")
        await self.page_logic(ctx=ctx, data=completed, title="Todos")

    async def page_logic(self, ctx: commands.Context, data: list, title: str):
        """|coro|

        Creates a menu with the given data.

        Parameters
        ----------
        ctx: :class:`Context`
            Command's context for sending the message and getting settings
        data: :class:`list`
            The data to send in a menu
        title: :class:`str`
            Title of the menu. If it can use embeds it will be the embed's title.
            Otherwise it will be combined with the page string
        """
        data = self._pagified_list(data)
        use_md = await self.config.user(ctx.author).use_md()
        use_embeds = await self.config.user(ctx.author).use_embeds()
        source = TodoPages(
            data=data,
            use_md=use_md,
            use_embeds=use_embeds,
            title=title,
        )
        await TodoMenu(
            source=source,
            delete_message_after=False,
            clear_reactions_after=True,
            timeout=15.0,
        ).start(ctx, channel=await self._get_destination(ctx), wait=False)

    async def _number_lists(self, data: list):
        """|coro|

        Number lists. Eg. a list with the value ["One", "Two", "Three"] would become
        ["1. One", "2. Two", "3. Three"].

        Parameters
        ----------
        data: :class:`list`
            List to iterate and number

        Returns
        -------
        :class:`list`
            Numbered list
        """
        return [f"{num}. {x}" for num, x in enumerate(data, 1)]

    def _pagified_list(self, data: list):
        """Pagifies a list using Red's :func:`pagify`

        Parameters
        ----------
        data: :class:`list`
            Data to pagify.

        Returns
        -------
        List[:class:`str`]
            The pagified items converted to a list
        """
        return list(pagify("\n".join(data), page_length=500))

    async def _maybe_autosort(self, ctx: commands.Context):
        """|coro|

        Checks if a user's todo list can be sorted, and attempts to do so

        Parameters
        ----------
        ctx: :class:`Context`
            Context of the command to get settings for
        """
        if not await self.config.user(ctx.author).autosort():
            return
        reverse = await self.config.user(ctx.author).reverse_sort()
        async with self.config.user(ctx.author).todos() as todos:
            todos.sort(reverse=reverse)
        async with self.config.user(ctx.author).completed() as completed:
            completed.sort(reverse=reverse)

    async def _get_destination(self, ctx: commands.Context):
        """|coro|

        Gets the channel for lists

        Parameters
        ----------
        ctx: :class:`Context`
            Context of the command for getting settings

        Returns
        -------
        Union[:class:`TextChannel`, :class:`DMChannel`]
            The channel to send messages to
        """
        if await self.config.user(ctx.author).private():
            return ctx.author.dm_channel
        return ctx.channel

    async def _sort_indexes(self, index: typing.List[int]) -> typing.List[int]:
        """|coro|

        Sorts a list of ints in descending order

        Parameters
        ----------
        index: List[:class:`int`]
            The list of integers to sort

        Returns
        -------
        List[:class:`int`]
            The sorted list
        """
        index.sort(reverse=True)
        return index

    async def _cross_lists(self, data: list):
        """|coro|

        Crosses out items in a list

        Parameters
        ----------
        data: :class:`list`
            List of items to cross out

        Returns
        -------
        :class:`list`
            The list with items crossed out
        """
        return [f"~~{x}~~" for x in data]
