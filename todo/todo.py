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
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box, pagify
from redbot.core.utils.predicates import MessagePredicate

from .utils import *

log = logging.getLogger("red.JojoCogs.todo")


_new_lines = "\n"
_config_structure = {
    "todos": [],
    "completed": [],
    "detailed_pop": False,
    "use_md": True,
    "use_embeds": True,
    "autosort": False,
    "reverse_sort": False,
    "replies": False,
    "combined_lists": False,
    "private": False,
}
_about = (
    "ToDo is a cog designed by Jojo#7791 for keeping track"
    " of tasks for you to do. It provides a simple listing,"
    " adding, and completing for you to work with, and is highly"
    " customizable so you get the best out of it"
)
_comic_link = "https://raw.githubusercontent.com/Just-Jojo/JojoCog-Assets/main/data/todo_comic.jpg"
_no_todo_message = (
    "You don't have any todos!" " Add one using `{prefix}todo add <todo>`!"
)
_no_completed_message = (
    "You don't have any completed todos!"
    " You can complete a todo using `{prefix}todo complete <indexes...>`!"
)


class ToDo(commands.Cog):
    """A simple and highly customizable todo list for Discord"""

    __version__ = "1.1.0"
    __author__ = ["Jojo#7791"]

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            cog_instance=self, identifier=19924714019, force_registration=True
        )
        self.config.register_user(**_config_structure)

    def format_help_for_context(self, ctx: commands.Context):
        return (
            f"{super().format_help_for_context(ctx)}"
            f"\n\n**Current Version:** `{self.__version__}`"
            f"\n**Author:** `{', '.join(self.__author__)}`"
        )

    ### Setting commands ###

    @commands.group()
    async def todoset(self, ctx):
        """Base settings command for customizing your todo list"""
        pass

    @todoset.command()
    async def detailed(self, ctx, toggle: bool):
        """Have a more detailed adding, removing, and completing message"""
        if toggle:
            ed = "enabled"
        else:
            ed = "disabled"

        msg = f"Extra details are now {ed}!"
        await self._setting_toggle(
            ctx=ctx, toggle=toggle, setting="detailed_pop", msg=msg
        )

    @todoset.command(aliases=["md"])
    async def usemd(self, ctx, toggle: bool):
        """Have the lists use a markdown block"""
        ed = "enabled" if toggle else "disabled"
        msg = f"Markdown blocks are now {ed}!"
        await self._setting_toggle(ctx=ctx, toggle=toggle, setting="use_md", msg=msg)

    @todoset.command(aliases=["embed"])
    async def useembeds(self, ctx, toggle: bool):
        """Have the lists be embedded (this requires the bot to have embed links permissions in the channel)"""
        ed = "enabled" if toggle else "disabled"

        msg = f"Embedded lists are now {ed}!"
        await self._setting_toggle(
            ctx=ctx, toggle=toggle, setting="use_embeds", msg=msg
        )

    @todoset.command(aliases=["reply"])
    async def replies(self, ctx, toggle: bool):
        """Have the bot reply to you"""
        ed = "enabled" if toggle else "disabled"
        msg = f"Replies are now {ed}!"
        await self._setting_toggle(ctx=ctx, toggle=toggle, setting="replies", msg=msg)

    @todoset.command()
    async def autosort(self, ctx, toggle: bool):
        """Autosort your lists whenever you add or remove from it"""
        ed = "enabled" if toggle else "disabled"
        msg = f"Autosorting is now {ed}!"
        await self._setting_toggle(ctx=ctx, toggle=toggle, setting="autosort", msg=msg)

    @todoset.command()
    async def combine(self, ctx, toggle: bool):
        """Combine the todo and complete list"""
        ed = "enabled" if toggle else "disabled"
        msg = f"Combined lists are now {ed}!"
        await self._setting_toggle(
            ctx=ctx, toggle=toggle, setting="combined_lists", msg=msg
        )

    # @todoset.command()
    # async def private(self, ctx, toggle: bool):
    #     """Make the list private"""
    #     if toggle:
    #         if not isinstance(ctx.channel, discord.DMChannel):
    #             try:
    #                 await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
    #                 await ctx.author.send(
    #                     "Hey, I'm sending you a message to see if I can dm you!"
    #                 )
    #             except discord.Forbidden:
    #                 return await ctx.send("I can't dm you!")
    #     msg = f"Private lists are now {'enabled' if toggle else 'disabled'}!"
    #     await self._setting_toggle(ctx=ctx, toggle=toggle, setting="private", msg=msg)

    async def _setting_toggle(
        self, *, ctx: commands.Context, toggle: bool, setting: str, msg: str
    ):
        """Toggle logic for setting commands"""
        current = await self.config.user(ctx.author).get_raw(setting)
        if current == toggle:
            return await ctx.send(
                f"That setting is already {'enabled' if toggle else 'disabled'}!"
            )
        await ctx.send(content=msg)
        await self.config.user(ctx.author).set_raw(setting, value=toggle)

    @todoset.command()
    async def showsettings(self, ctx):
        """Show your todo settings"""
        conf = self.config.user(ctx.author)
        settings = {
            "Markdown": await conf.use_md(),
            "Embedded": await conf.use_embeds(),
            "Detailed": await conf.detailed_pop(),
            "Autosorting": await conf.autosort(),
            "Reverse Sort": await conf.reverse_sort(),
            "Replies": await conf.replies(),
            "Combined lists": await conf.combined_lists(),
            # "Private lists": await conf.private(),
        }
        if await ctx.embed_requested():
            embed = discord.Embed(
                title=f"{ctx.author.display_name}'s todo settings",
                colour=await ctx.embed_colour(),
            )
            for key, value in settings.items():
                embed.add_field(name=key, value=value, inline=True)
            kwargs = {"embed": embed}
        else:
            ret = f"{ctx.author.display_name}'s todo settings"
            for key, value in settings.items():
                ret += f"\n**{key}:** {value}"
            kwargs = {"content": ret}
        await self.maybe_reply(ctx, **kwargs)  # TODO maybe reply

    ### Listing commands ###

    @commands.group()
    async def todo(self, ctx):
        """Base command for adding, removing, and completing todos"""
        pass

    @todo.command(name="add")
    async def todo_add(self, ctx, *, todo: str):
        """Add a todo to your list"""
        async with self.config.user(ctx.author).todos() as todos:
            todos.append(todo)

        msg = "Added that as a todo!"
        details = await self.config.user(ctx.author).detailed_pop()
        if details:
            msg += f"\n'{discord.utils.escape_markdown(todo)}'"
        await ctx.send(content=msg)
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

    @todo.command()
    async def remove(self, ctx, *indexes: positive_int):
        """Delete todos"""
        if not indexes:
            return await ctx.send_help(ctx.command)
        todos = await self.config.user(ctx.author).todos()
        indexes = [x - 1 for x in indexes]
        if not todos:
            return await ctx.send(_no_todo_message.format(prefix=ctx.clean_prefix))
        else:
            removed, failed = 0, 0
            async with ctx.typing():
                async with self.config.user(ctx.author).todos() as todos:
                    for index in indexes:
                        try:
                            todos.pop(index)
                        except IndexError:
                            failed += 1
                        else:
                            removed += 1
            msg = "Done."
            detailed = await self.config.user(ctx.author).detailed_pop()
            if detailed:
                if removed:
                    msg += f"\nRemoved: {removed} {'todos' if removed > 1 else 'todo'}"
                if failed:
                    msg += f"\nFailed to remove: {failed} {'todos' if failed > 1 else 'todo'}"
            await ctx.send(msg)
            await self._maybe_autosort(ctx)

    @todo.command(aliases=["delall"])
    async def removeall(self, ctx):
        """Remove all of your todos"""
        await ctx.send(
            "WARNING, this will remove **ALL** of your todos. Would you like to remove your todos? (y/n)"
        )
        pred = MessagePredicate.yes_or_no(ctx)
        try:
            await self.bot.wait_for("message", check=pred)
        except asyncio.TimeoutError:
            await ctx.send("Okay, I won't delete your todos")
        else:
            if pred.result is False:
                await ctx.send("Okay, I won't delete your todos")
            else:
                await self.config.user(ctx.author).todos.clear()
                await ctx.send("Removed your todos.")

    @todo.command(name="list")
    async def todo_list(self, ctx):
        """List your current todos!"""
        todos = await self.config.user(ctx.author).todos()
        if not todos:
            await ctx.send(_no_todo_message.format(prefix=ctx.clean_prefix))
        else:
            todos = await self._number_lists(todos)
            if await self.config.user(ctx.author).combined_lists():
                if (c := await self.config.user(ctx.author).completed()) :
                    if not await self.config.user(ctx.author).use_md():
                        c = await self._cross_lists(c)
                    c = await self._number_lists(c)
                    c.insert(0, "\N{WHITE HEAVY CHECK MARK} Completed todos")
                    todos.extend(c)
            await self.page_logic(ctx, todos, "Todos")

    @todo.group(invoke_without_command=True)
    async def complete(self, ctx, *indexes: positive_int):
        """Complete some todos!"""
        if not indexes:
            return await ctx.send_help(ctx.command)
        indexes = [x - 1 for x in indexes]
        todos = await self.config.user(ctx.author).todos()
        if not todos:
            await ctx.send(_no_todo_message.format(prefix=ctx.clean_prefix))
        else:
            comp, failed = 0, 0
            async with ctx.typing():
                async with self.config.user(ctx.author).todos() as todos:
                    for index in indexes:
                        try:
                            todos.pop(index)
                        except IndexError:
                            failed += 1
                        else:
                            comp += 1
            msg = "Done."
            detail = await self.config.user(ctx.author).detailed_pop()
            if detail:
                if comp:
                    msg += f"\nCompleted: {comp} {'todos' if comp > 1 else 'todo'}"
                if failed:
                    msg += f"\nFailed to complete: {failed} {'todos' if failed > 1 else 'todo'}"
            await ctx.send(msg)
            await self._maybe_autosort(ctx)

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

    @complete.command(name="remove", aliases=["del", "rm"])
    async def complete_remove(self, ctx, *indexes: positive_int):
        """Remove compeleted todos"""
        if not indexes:
            return await ctx.send_help(ctx.command)
        indexes = [x - 1 for x in indexes]
        _ = await self.config.user(ctx.author).completed()
        if not _:
            return await ctx.send(_no_completed_message.format(prefix=ctx.clean_prefix))
        else:
            removed, failed = 0, 0
            async with ctx.typing():
                async with self.config.user(ctx.author).completed() as comp:
                    for index in indexes:
                        try:
                            comp.pop(index)
                        except IndexError:
                            failed += 1
                        else:
                            removed += 1
            msg = "Done."
            if await self.config.user(ctx.author).detailed_pop():
                if removed:
                    msg += f"\nRemoved: {removed} {'todos' if removed > 1 else 'todo'}"
                if failed:
                    msg += f"\nFailed to remove: {failed} {'todos' if failed > 1 else 'todo'}"
            await ctx.send(msg)
            await self._maybe_autosort(ctx)

    @complete.command(name="removeall", aliases=["delall", "rma"])
    async def complete_removeall(self, ctx):
        """Remove all of your completed todos"""
        await ctx.send(
            "WARNING, this will remove **ALL** of your completed todos. Would you like to remove them? (y/n)"
        )
        pred = MessagePredicate.yes_or_no(ctx)
        try:
            await self.bot.wait_for("message", check=pred)
        except asyncio.TimeoutError:
            await ctx.send("Okay, I won't delete your completed todos")
        else:
            if pred.result is False:
                await ctx.send("Okay, I won't delete your completed todos")
            else:
                await self.config.user(ctx.author).completed.clear()
                await ctx.send("Removed your completed todos.")

    ### Utility methods ###

    async def page_logic(self, ctx: commands.Context, data: list, title: str):
        """Page logic, because rewriting is boring"""
        data = self._pagified_list(data)
        use_md = await self.config.user(ctx.author).use_md()
        use_embeds = await self.config.user(ctx.author).use_embeds()
        reply = await self.config.user(ctx.author).replies()
        source = TodoPages(
            data=data,
            use_md=use_md,
            use_embeds=use_embeds,
            title=title,
        )
        await TodoMenu(
            source=source,
            reply=reply,
            delete_message_after=False,
            clear_reactions_after=True,
            timeout=15.0,
        ).start(ctx, channel=ctx.channel, wait=False)

    async def maybe_reply(self, ctx: commands.Context, **kwargs) -> discord.Message:
        """Maybe reply to a message"""
        if await self.config.user(ctx.author).replies():
            kwargs["mention_author"] = False
            return await ctx.reply(**kwargs)
        return await ctx.send(**kwargs)

    async def _number_lists(self, data: list):
        return [f"{num}. {x}" for num, x in enumerate(data, 1)]

    def _pagified_list(self, data: list):
        return list(pagify("\n".join(data), page_length=500))

    async def _maybe_autosort(self, ctx: commands.Context):
        if not await self.config.user(ctx.author).autosort():
            return
        reverse = await self.config.user(ctx.author).reverse_sort()
        async with self.config.user(ctx.author).todos() as todos:
            todos.sort(reverse=reverse)
        async with self.config.user(ctx.author).completed() as completed:
            completed.sort(reverse=reverse)

    # async def _get_destination(self, ctx: commands.Context):
    #     priv = await self.config.user(ctx.author).private()
    #     if priv:
    #         return ctx.author.dm_channel
    #     return ctx.channel

    async def _sort_indexes(self, index: typing.List[int]) -> typing.List[int]:
        index.sort(reverse=True)
        return index

    async def _cross_lists(self, data: list):
        return [f"~~{x}~~" for x in data]
