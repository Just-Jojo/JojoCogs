# type:ignore[attr-defined, operator, union-attr]

# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import asyncio
import logging
import typing
from datetime import datetime
from typing import Optional, Union

import discord
from discord.ext import tasks
from jojo_utils import Menu, version_info
if type(version_info[0], str):
    from jojo_utils import positive_int
else:
    from jojo_utils import PositiveInt as positive_int #type:ignore
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box, humanize_list, pagify
from redbot.core.utils.predicates import MessagePredicate

from .commands import CompositeMetaclass, Deleting, Examples, Search, Settings
from .utils import TodoPages, todo_positive_int

now = datetime.utcnow
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
    "colour": None,
}


class ToDo(
    Examples, Settings, Deleting, Search, commands.Cog, metaclass=CompositeMetaclass
):
    """A simple and highly customizable todo list for Discord"""

    _no_completed_message = (
        "You don't have any completed todos!"
        " You can complete a todo using `{prefix}todo complete <indexes...>`"
    )
    _no_todo_message = "You don't have any todos! Add one using `{prefix}todo add <todo>`"
    _failure_explanation = (
        "(The most common reason for "
        "a todo deletion to have failed "
        "is that the index given was greater "
        "than the length of your todo list)"
    )

    __version__ = "1.2.19"
    __author__ = ["Jojo#7791"]
    __suggesters__ = [
        "Blackbird#0001",
    ]

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            cog_instance=self, identifier=19924714019, force_registration=True
        )
        self.config.register_user(**_config_structure)
        self.settings_cache: typing.Dict[int, dict] = {}
        self.log = logging.getLogger("red.JojoCogs.todo")
        self.update_cache_task.start()

    def cog_unload(self):
        self.update_cache_task.cancel()

    def format_help_for_context(self, ctx: commands.Context):
        """Thankie thankie Sinbad"""
        plural = ""
        if len(self.__author__) > 1:
            plural = "s"
        return (
            f"{super().format_help_for_context(ctx)}"
            f"\n\nCurrent Version: `{self.__version__}`"
            f"\nAuthor{plural}: `{', '.join(self.__author__)}`"
            f"\nSuggesters: Use `[p]todo suggesters`!"
        )

    async def update_cache(self, *, user_id: int = None):
        """|coro|

        Updates the settings cache

        credits to phen for sharing this
        https://github.com/phenom4n4n/phen-cogs/blob/1e862ff1f429dfc1c56074f952b75056a79cd246/baron/baron.py#L91
        """
        if user_id:
            self.settings_cache[user_id] = await self.config.user_from_id(user_id).all()
        else:
            self.settings_cache = await self.config.all_users()

    ### Listing commands ###

    @commands.group(invoke_without_command=True)
    async def todo(self, ctx, index: todo_positive_int):  # type:ignore
        """Todo commands

        Add a todo to your list and manage your tasks
        """

        act_index = index - 1
        conf: dict = await self._get_user_config(ctx.author)
        todos = conf.get("todos", [])
        if act_index >= len(todos):
            return await ctx.send("You don't have a todo at that index")
        todo = f"{index}. {todos.pop(act_index)}"
        embed = conf.get("use_embeds", True)
        md = conf.get("use_md", True)
        title = f"{ctx.author.name}'s Todos | Todo #{index}"

        if md:
            todo = box(todo, "md")
        if embed and await ctx.embed_requested():
            embed = discord.Embed(
                colour=await ctx.embed_colour(), title=title, description=todo
            )
            embed.timestamp = now()
            kwargs = {"embed": embed}
        else:
            msg = f"{title}\n{todo}"
            kwargs = {"content": msg}
        await ctx.send(**kwargs)

    @todo.group(
        invoke_without_command=True, aliases=["c"], require_var_positional=True
    )  # `c` is easy to type
    async def complete(self, ctx, *indexes: todo_positive_int):  # type:ignore[valid-type]
        """Commands having to do with completed todos"""
        if not await self.config.user(ctx.author).todos():
            return await ctx.send(self._no_todo_message.format(prefix=ctx.clean_prefix))
        conf = await self._get_user_config(ctx.author)
        try:
            conf["completed"]
        except KeyError:
            conf["completed"] = []
        try:
            conf["todos"]
        except KeyError:
            conf["todos"] = []
        async with ctx.typing():
            async with self.config.user(ctx.author).todos() as todos:
                async with self.config.user(ctx.author).completed() as completed:
                    indexes = [x - 1 for x in indexes]  # type:ignore[assignment]
                    # Remove 1 from each item...
                    indexes.sort(reverse=True)  # and sort the list
                    fails, failed, comp, compled = 0, [], 0, []
                    for index in indexes:
                        try:
                            rmd = todos.pop(index)
                            conf["todos"].pop(index)
                        except IndexError:
                            fails += 1
                            failed.append(f"`{index}`")
                        else:
                            comp += 1
                            compled.append(f"`{rmd}`")
                            completed.append(rmd)
                            conf["completed"].append(rmd)
        msg = "Done."
        details = conf.get("detailed_pop", False)
        if comp:
            plural = "" if comp == 1 else "s"
            msg += f"\nCompleted {comp} todo{plural}"
            if details:
                msg += "\n" + "\n".join(compled)
        if fails:
            plural = "" if fails == 1 else "s"
            msg += (
                f"\nFailed to complete {fails} todo{plural} {self._failure_explanation}"
            )
            if details:
                msg += "\n" + "\n".join(failed)
        await self._maybe_autosort(ctx)
        if len(msg) > 2000:
            await ctx.send_interactive(pagify(msg))
        else:
            await ctx.send(msg)
        self.settings_cache[ctx.author.id] = conf

    @todo.command(name="suggesters")
    async def todo_suggesters(self, ctx):
        """These awesome people have suggested things for this cog!"""
        msg = (
            "Thanks for everyone who's suggested something for this cog!"
            f"\n{humanize_list(self.__suggesters__)}"
            "\n\nSpecial thanks to Kreusada for helping me a lot with this cog ❤"
        )
        kwargs = {"content": msg}
        if await ctx.embed_requested():
            em = discord.Embed(
                title="Suggesters!", colour=await ctx.embed_colour(), description=msg
            )
            em.timestamp = datetime.utcnow()
            kwargs = {"embed": em}
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
            "(here's the issue link <https://github.com/Just-Jojo/JojoCogs/issues/15> 😄)"
            f"\n~~You can also appear in the `{ctx.clean_prefix}todo suggesters` command :p~~"
        )
        kwargs = {"content": msg}
        if await ctx.embed_requested():
            embed = discord.Embed(
                title="Todo suggestions",
                description=msg,
                colour=await ctx.embed_colour(),
            )
            embed.timestamp = now()
            kwargs = {
                "embed": embed,
            }
        await ctx.send(**kwargs)

    @todo.command(name="add")
    async def todo_add(self, ctx, *, todo: str):
        """Add a todo to your list"""
        async with self.config.user(ctx.author).todos() as todos:
            todos.append(todo)
        conf = await self._get_user_config(ctx.author)
        try:
            conf["todos"].append(todo)
        except KeyError:
            conf["todos"] = [
                todo,
            ]
        self.settings_cache[ctx.author.id] = conf

        msg = "Added that as a todo"
        details = conf.get("detailed_pop", False)
        if details:
            msg += f"\n'{discord.utils.escape_markdown(todo)}'"
        await self._maybe_autosort(ctx)
        if len(msg) > 2000:
            await ctx.send_interactive(pagify(msg))
        else:
            await ctx.send(msg)

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

    @todo.command(aliases=["ro", "move"])
    async def reorder(self, ctx, index: positive_int, to_place: positive_int):
        """Move a todo from one index to another"""
        act_index, act_to_place = index - 1, to_place - 1

        conf = await self._get_user_config(ctx.author)
        async with self.config.user(ctx.author).todos() as tds:
            if not tds:
                return await ctx.send(
                    self._no_todo_message.format(prefix=ctx.clean_prefix)
                )
            todos = conf.get("todos")
            try:
                todo = tds.pop(act_index)
                tds.insert(act_to_place, todo)
                # todo = todos.pop(act_index)
                # todos.insert(act_to_place, todo)
            except IndexError:
                return await ctx.send("I could not find a todo at that index!")
        msg = f"Moved a todo from index {index} to {to_place}"
        if conf["detailed_pop"]:
            msg += f"\n`{todo}`"
        await ctx.send(msg)
        if conf.get("autosort", False):
            await self.config.user(ctx.author).autosort.set(False)
        await self.update_cache(user_id=ctx.author.id)

    @todo.command(name="list")
    async def todo_list(self, ctx):
        """List your current todos!"""
        conf = await self._get_user_config(ctx.author)
        todos = conf.get("todos", [])
        completed = conf.get("completed", [])

        comb = conf.get("combined_lists", False)
        use_md = conf.get("use_md", True)
        use_embeds = conf.get("use_embeds", True)
        private = conf.get("private", True)
        colour = conf.get("colour", None)

        if not todos:
            if comb and completed:
                return await self._complete_list(
                    ctx,
                    completed=completed,
                    use_md=use_md,
                    use_embeds=use_embeds,
                    private=private,
                    colour=colour,
                )
            return await ctx.send(self._no_todo_message.format(prefix=ctx.clean_prefix))

        todos = await self._number_lists(todos)
        if comb and completed:
            if not use_md:
                completed = await self._cross_lists(completed)
            completed = await self._number_lists(completed)
            completed.insert(0, "\N{WHITE HEAVY CHECK MARK} Completed todos")
            todos.extend(completed)
        await self.page_logic(
            ctx,
            todos,
            "Todos",
            use_md=use_md,
            use_embeds=use_embeds,
            private=private,
            colour=colour,
        )

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
        await self.update_cache(user_id=ctx.author.id)

    @complete.command(name="list")
    async def complete_list(self, ctx):
        """List your completed todos"""
        conf = await self._get_user_config(ctx.author)
        completed = conf.get("completed", [])
        use_md = conf.get("use_md", True)
        use_embeds = conf.get("use_embeds", True)
        colour = conf.get("colour", None)

        if not completed:
            await ctx.send(self._no_completed_message.format(prefix=ctx.clean_prefix))
        else:
            if not use_md:
                completed = await self._cross_lists(completed)
            completed = await self._number_lists(completed)
            await self.page_logic(
                ctx,
                completed,
                "Completed todos",
                use_md=use_md,
                use_embeds=use_embeds,
                private=conf.get("private", False),
                colour=colour,
            )

    @complete.command(name="reorder")
    async def complete_reorder(self, ctx, index: positive_int, to_place: positive_int):
        """Move a completed todo to a new index"""
        act_index, act_to_place = [i - 1 for i in (index, to_place)]
        conf = await self._get_user_config(ctx.author)
        completed = conf.get("completed")
        async with self.config.user(ctx.author).completed() as comp:
            if not completed:
                return await ctx.send(
                    self._no_completed_message.format(prefix=ctx.clean_prefix)
                )
            try:
                todo = comp.pop(act_index)
                comp.insert(act_to_place, todo)
            except KeyError:
                return await ctx.send("I could not find a todo at that index!")
        msg = f"Moved a todo from {index} to {to_place}."
        if conf.get("detailed_pop"):
            msg += f"\n`{todo}`"
        await ctx.send(msg)
        if conf.get("autosort"):
            await self.config.user(ctx.author).autosort.set(False)
        await self.update_cache(user_id=ctx.author.id)

    @todo.command()
    async def version(self, ctx):
        """Check the version of todo"""
        msg = f"ToDo version: `{self.__version__}`\nMade with ❤ by Jojo"
        await ctx.send(msg)

    @todo.command()
    async def explain(self, ctx):
        """Explain about this cog"""
        await ctx.send(
            "Hallo! Please read this to learn about todo\n"
            "<https://github.com/Just-Jojo/JojoCogs/blob/master/todo/README.md>"
        )

    @todo.command(name="edit")
    async def todo_edit(self, ctx, index: positive_int, *, new_todo: str):
        """Edit a todo at a certain index"""
        new_index = index - 1
        conf = await self._get_user_config(ctx.author)
        todos = conf.get("todos", [])
        if not todos:
            return await ctx.send(self._no_todo_message.format(prefix=ctx.clean_prefix))
        try:
            old = box(f"{index}. {todos.pop(new_index)}", "md")
        except IndexError:
            return await ctx.send("I could not find a todo at that index")
        else:
            todos.insert(index, new_todo)
            new = box(f"{index}. {new_todo}", "md")
        use_embeds = conf.get("use_embeds", True)
        colour = conf.get("colour", None) or await ctx.embed_colour()
        formatting = f"**Old**\n{old}**New**\n{new}"
        kwargs: dict = {"content": f"**Todo edit**\n\n{formatting}"}
        if await ctx.embed_requested() and use_embeds:
            embed = discord.Embed(
                title="Todo edit", colour=colour, description=formatting
            )
            embed.timestamp = datetime.utcnow()
            kwargs = {"embed": embed}
        await ctx.send(**kwargs)
        self.settings_cache["todos"] = todos
        await self.config.user(ctx.author).todos.set(todos)

    ### Utility methods ###

    async def _complete_list(
        self,
        ctx: commands.Context,
        *,
        completed: typing.List[str],
        use_md: bool,
        use_embeds: bool,
        private: bool,
        colour: Optional[Union[str, int]],
    ):
        if not use_md:
            completed = await self._cross_lists(completed)
        completed = await self._number_lists(completed)
        completed.insert(0, "\N{WHITE HEAVY CHECK MARK} Completed")
        await self.page_logic(
            ctx=ctx,
            data=completed,
            title="Todos",
            use_md=use_md,
            use_embeds=use_embeds,
            private=private,
            colour=colour,
        )

    async def page_logic(
        self,
        ctx: commands.Context,
        data: list,
        title: str,
        *,
        use_md: bool,
        use_embeds: bool,
        private: bool,
        colour: Optional[Union[str, int]],
    ):
        data = self._pagified_list(data)
        source = TodoPages(
            data=data,
            use_md=use_md,
            use_embeds=use_embeds,
            title=title,
            colour=colour,
        )
        await Menu(
            source=source,
            delete_message_after=False,
            clear_reactions_after=True,
            timeout=15.0,
        ).start(
            ctx, channel=await self._get_destination(ctx, private=private), wait=False
        )

    async def _number_lists(self, data: list):
        return [f"{num}. {x}" for num, x in enumerate(data, 1)]

    def _pagified_list(self, data: list) -> typing.List[str]:
        return list(pagify("\n".join(data), page_length=500))

    async def _maybe_autosort(self, ctx: commands.Context):
        if not await self.config.user(ctx.author).autosort():
            return
        reverse = await self.config.user(ctx.author).reverse_sort()
        async with self.config.user(ctx.author).todos() as todos:
            todos.sort(reverse=reverse)
        async with self.config.user(ctx.author).completed() as completed:
            completed.sort(reverse=reverse)

    async def _get_destination(
        self, ctx: commands.Context, *, private: bool
    ) -> discord.TextChannel:
        if private:
            if ctx.author.dm_channel is None:
                await ctx.author.create_dm()
            return ctx.author.dm_channel
        return ctx.channel

    async def _sort_indexes(self, index: typing.List[int]) -> typing.List[int]:
        index.sort(reverse=True)
        return index

    async def _cross_lists(self, data: list) -> typing.List[str]:
        return [f"~~{x}~~" for x in data]

    async def _get_user_config(
        self, user: typing.Union[int, discord.Member, discord.User]
    ) -> typing.Dict[str, typing.Any]:
        uid = user if isinstance(user, int) else user.id
        maybe_config = self.settings_cache.get(uid, None)
        if maybe_config is None:
            await self.update_cache(user_id=uid)
            maybe_config = self.settings_cache.get(uid, _config_structure)
        return maybe_config  # type:ignore[return-value]

    @tasks.loop(minutes=30.0)  # I'm guessing this needs to be a float?
    async def update_cache_task(self):
        await self.update_cache()

    @update_cache_task.before_loop
    async def before_updating(self):
        await self.bot.wait_until_red_ready()

    @update_cache_task.after_loop
    async def after_updating_cache(self):
        self.log.debug("Updated todo cache")
