# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import asyncio
import logging
from contextlib import suppress
from typing import Dict, List, Optional, Tuple, Union

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import escape, humanize_list, pagify, text_to_file
from redbot.core.utils.predicates import MessagePredicate

from .abc import MetaClass
from .commands import *
from .utils import (
    Cache,
    PositiveInt,
    TodoMenu,
    TodoPage,
    TodoPositiveInt,
    ViewTodo,
    formatting,
    timestamp_format,
)

_config_structure = {
    "todos": [],  # List[Dict[str, Any]] "task": str, "pinned": False
    "completed": [],  # List[str]
    "user_settings": {
        "autosorting": False,
        "colour": None,
        "combine_lists": False,
        "extra_details": False,
        "number_todos": False,
        "pretty_todos": False,
        "private": False,
        "reverse_sort": False,
        "use_embeds": True,
        "use_markdown": False,
        "use_timestamps": False,
    },
}


def attach_or_in_dm(ctx: commands.Context):
    if not ctx.guild:
        return True
    return ctx.channel.permissions_for(ctx.me).attach_files


class ToDo(
    Complete, Deleting, Settings, Miscellaneous, commands.Cog, metaclass=MetaClass
):
    """A todo list for keeping track of tasks you have to do

    This cog is my oldest, still standing cog and holds a special place in my heart even though it's a pain to work on lol

    I hope you have as much fun with it as I had designing it ❤
    - Jojo#7791"""

    __authors__ = [
        "Jojo#7791",
    ]
    __suggestors__ = ["Blackbird#0001"]
    __version__ = "3.0.0.dev1"
    _no_todo_message = (
        "You do not have any todos. You can add one with `{prefix}todo add <task>`"
    )

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, 19924714019, True)
        self.config.register_user(**_config_structure)
        self.cache = Cache(self.bot, self.config)
        self._startup_task = self.bot.loop.create_task(self._initialize())
        self.log = logging.getLogger("red.JojoCogs.todo")

    def cog_unload(self):
        with suppress(KeyError):
            self.bot.remove_dev_env_value("todo")

    def format_help_for_context(self, ctx: commands.Context):
        pre = super().format_help_for_context(ctx)
        plural = "s" if len(self.__authors__) > 1 else ""
        return (
            f"{pre}\n"
            f"Author{plural}: `{humanize_list(self.__authors__)}`\n"
            "Suggestors: Use `[p]todo suggestors`!"
            f"Version: `{self.__version__}`"
        )

    async def _initialize(self):
        """This is based off of Obi-Wan3's migration method in their github cog
        https://github.com/Obi-Wan3/OB13-Cogs/blob/main/github/github.py#L88"""

        with suppress(RuntimeError):
            self.bot.add_dev_env_value("todo", lambda x: self)
        for uid in (await self.config.all_users()).keys():
            async with self.config.user_from_id(uid).all() as data:
                if data.get("migrated"):
                    continue
                self.log.debug(data)

                new_data = {
                    "todos": None,
                    "user_settings": data["user_settings"],
                    "migrated": True,
                    "completed": data["completed"],
                }
                todos = []
                for todo in data["todos"]:
                    todos.append({"task": todo, "pinned": False})
                new_data["todos"] = todos
                self.log.debug(new_data)
                data.update(new_data)

    @commands.group(invoke_without_command=True)
    async def todo(self, ctx: commands.Context, index: TodoPositiveInt):
        """Your todo list inside Discord

        Arguments
            - `index` The todo you want to view. This is optional and if left out, it will show the help command instead
        """
        act_index = index - 1
        try:
            todo = await self.cache.get_todo_from_index(ctx.author, act_index)
        except IndexError:
            return await ctx.send("You do not have a todo at that index.")
        else:
            if todo is None:
                return await ctx.send(
                    self._no_todo_message.format(prefix=ctx.clean_prefix)
                )
        await ViewTodo(
            index,
            self.cache,
            todo,
            **await self.cache.get_user_item(ctx.author, "user_settings"),
        ).start(ctx)

    @todo.command(name="add")
    async def todo_add(self, ctx: commands.Context, pinned: Optional[bool], *, todo: str):
        """Add a todo task to your list

        Don't store sensitive information here for Pete's sake

        **Arguments**
            - `pinned` A boolean value that sets it to be pinned or not. Defaults to False
            - `todo` The todo task
        """
        data = await self.cache.get_user_data(ctx.author.id)
        pinned = pinned is not None and pinned is True
        payload = {"task": todo, "pinned": pinned}
        data["todos"].append(payload)
        await self.cache.set_user_item(ctx.author, "todos", data["todos"])

        data = data["user_settings"]
        msg = f"Added that as a todo."
        if data["extra_details"]:
            msg += f"\n'{todo}'"
        if data["use_timestamps"]:
            msg += f"\n{timestamp_format()}"
        if len(msg) > 2000:
            await ctx.send_interactive(pagify(msg))
        else:
            await ctx.send(msg)
        await self._maybe_autosort(ctx.author)

    @todo.command(name="list")
    async def todo_list(self, ctx: commands.Context):
        """List your todos

        This will list them with pinned todos first and then whatever sorting you have
        """
        data = await self.cache.get_user_data(ctx.author.id)
        todos = data["todos"]
        completed = data["completed"]
        user_settings = data["user_settings"]

        if not todos and not all([completed, user_settings["combine_lists"]]):
            return await ctx.send(self._no_todo_message.format(prefix=ctx.clean_prefix))
        elif not todos:
            return await self.__complete_list(completed, **user_settings)

        pinned, todos = await self._get_todos(todos)
        todos = await formatting._format_todos(pinned, todos, **user_settings)
        if completed and user_settings["combine_lists"]:
            completed = await formatting._format_completed(
                completed, combined=True, **user_settings
            )
            todos.extend(completed)

        await self.page_logic(ctx, todos, f"{ctx.author.name}'s Todos", **user_settings)

    @todo.command(name="multiadd")
    async def todo_multi_add(self, ctx: commands.Context, *, todos: str = None):
        """Add multiple todos in one command!"""
        if ctx.message.reference and not any(
            [todos is not None, ctx.message.attachments]
        ):
            # Message references get checked first
            msg = ctx.message.reference.resolved
            if not msg.attachments:
                return await ctx.send("That message does not have files!")
            maybe_file = msg.attachments[0]
            if not maybe_file.filename.endswith(".txt"):
                return await ctx.send("File format must be `.txt`")
            todos = await maybe_file.read()
            todos = todos.decode()
        elif ctx.message.attachments:
            maybe_file = ctx.message.attachments[0]
            if not maybe_file.filename.endswith(".txt"):
                return await ctx.send("File format must be `.txt`")
            todos = await maybe_file.read()
            todos = todos.decode()
        todos = [{"pinned": False, "task": t} for t in todos.split("\n")]
        current = await self.cache.get_user_item(ctx.author, "todos")
        current.extend(todos)
        await self.cache.set_user_item(ctx.author, "todos", current)
        await ctx.send("Done. Added those as todos")
        await self._maybe_autosort(ctx.author)

    @todo.command(name="gettodos", aliases=["todotofile"])
    @commands.check(attach_or_in_dm)
    async def todo_get_todos(self, ctx: commands.Context):
        """Grab your todos in a clean file format.

        This is handy for moving todos over from bot to bot
        """
        todos = await self.cache.get_user_item(ctx.author, "todos")
        if not todos:
            return await ctx.send(self._no_todo_message.format(prefix=ctx.clean_prefix))
        todos = "\n".join([t["task"] for t in todos])
        await ctx.send("Here are your todos", file=text_to_file(todos, "todo.txt"))

    @todo.command(name="reorder", aliases=["move"], usage="<from> <to>")
    async def todo_reorder(
        self, ctx: commands.Context, original: PositiveInt, new: PositiveInt
    ):
        """Move a todo from one index to another

        This will error if the index is larger than your todo list

        **Arguments**
            - `from` The index of the todo
            - `to` The new index of the todo
        """
        todos = await self.cache.get_user_item(ctx.author, "todos")
        if not todos:
            return await ctx.send(self._no_todo_message.format(ctx.clean_prefix))
        act_orig = original - 1
        act_new = new - 1
        try:
            task = todos.pop(act_orig)
        except IndexError:
            return await ctx.send(f"I could not find a todo at index `{original}`")
        todos.insert(act_new, task)
        await ctx.send(f"Moved a todo from index {original} to {new}")
        await self.cache.set_user_item(ctx.author, "todos", todos)

    @todo.command(name="sort")
    async def todo_sort(self, ctx: commands.Context, reverse: bool = None):
        """Sort your todos by alphabetical order

        You can optionally set it to sort in reverse

        **Arguments**
            - `reverse` Whether to set it to be reversed. Defaults to False
        """
        if reverse is None:
            msg = await ctx.send("Would you like to sort your todos in reverse? (y/N)")
            pred = MessagePredicate.yes_or_no(ctx)
            try:
                umsg = await self.bot.wait_for("message", check=pred)
            except asyncio.TimeoutError:
                pass
            with suppress(discord.NotFound, discord.Forbidden):
                await msg.delete()
                await umsg.add_reaction("\N{WHITE HEAVY CHECK MARK}")
            reverse = bool(
                pred.result
            )  # Calling bool because `pred.result` starts as `None`
        await self.cache.set_user_setting(ctx.author, "reverse_sort", reverse)
        await self.cache.set_user_setting(ctx.author, "autosorting", True)
        have_not = "have" if reverse else "have not"
        await ctx.send(
            f"Your todos are now sorted. They {have_not} been sorted in reverse"
        )
        await self._maybe_autosort(ctx.author)

    @staticmethod
    async def _get_todos(todos: List[dict]) -> Tuple[List[str], List[str]]:
        """An internal function to get todos sorted by pins"""
        pinned = []
        extra = []
        for todo in todos:
            if todo["pinned"]:
                pinned.append(todo["task"])
            else:
                extra.append(todo["task"])
        return pinned, extra

    async def page_logic(self, ctx: commands.Context, data: list, title: str, **settings):
        joined = "\n".join(data)
        pagified = list(pagify(joined, page_length=500))
        pages = TodoPage(pagified, title, **settings)
        await TodoMenu(pages).start(ctx)

    async def _maybe_autosort(self, user: Union[discord.Member, discord.User]):
        """An internal function to maybe autosort todos"""
        data = await self.cache.get_user_data(user.id)
        todos = data["todos"]
        completed = data["completed"]
        if not any([completed, todos]):
            return
        settings = data["user_settings"]
        if not settings["autosorting"]:
            return

        if todos:
            todos = sorted(
                todos, key=lambda x: x["task"], reverse=settings["reverse_sort"]
            )
            todos.extend(
                sorted(extra, key=lambda x: x["task"], reverse=settings["reverse_sort"])
            )
        if completed:
            completed.sort(reverse=settings["reverse_sort"])

        data["completed"] = completed
        data["todos"] = todos
        await self.cache.set_user_data(user, data)
