# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import asyncio
import logging
from contextlib import suppress
from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional, Tuple, Union

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils import AsyncIter
from redbot.core.utils.chat_formatting import escape, humanize_list, pagify, text_to_file
from redbot.core.utils.predicates import MessagePredicate

from .abc import MetaClass
from .commands import *
from .consts import __authors__, __suggestors__, __version__, config_structure
from .utils import (PositiveInt, TimestampFormats, TodoApi, TodoMenu, TodoPages, ViewTodo,
                    TodoPrivateMenu, PrivateMenuStarter, formatting, timestamp_format)


def attach_or_in_dm(ctx: commands.Context) -> bool:
    if not ctx.guild:
        return True
    return ctx.channel.permissions_for(ctx.me).attach_files


class ToDo(
    Complete,
    Deleting,
    Edit,
    Importer,
    Managers,
    Miscellaneous,
    Settings,
    SharedTodos,
    commands.Cog,
    metaclass=MetaClass,
):
    """A todo list for keeping track of tasks you have to do

    This cog is my oldest, still standing cog and holds a special place in my heart even though it's a pain to work on lol

    I hope you have as much fun with it as I had designing it ❤
    - Jojo#7791"""

    _no_todo_message = "You do not have any todos. You can add one with `{prefix}todo add <task>`"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, 19924714019, True)
        self.config.register_user(**config_structure)
        self.cache = TodoApi(self.bot, self.config)
        self._startup_task = self.bot.loop.create_task(self._initialize())
        self.log = logging.getLogger("red.JojoCogs.todo")

    def cog_unload(self) -> None:
        with suppress(KeyError):
            self.bot.remove_dev_env_value("todo")
        self.cache._pool.close()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        pre = super().format_help_for_context(ctx)
        plural = "s" if len(__authors__) > 1 else ""
        return (
            f"{pre}\n\n"
            f"**Author{plural}:** {humanize_list([f'`{a}`' for a in __authors__])}\n"
            "**Suggestors:** Use `[p]todo suggestors`!\n"
            f"**Version:** `{__version__}`"
        )

    async def red_delete_data_for_user(
        self,
        *,
        requester: Literal["discord_deleted_user", "owner", "user", "user_strict"],
        user_id: int,
    ) -> None:
        await self.cache.delete_data(user_id)

    async def _initialize(self) -> None:
        """This is based off of Obi-Wan3's migration method in their github cog
        https://github.com/Obi-Wan3/OB13-Cogs/blob/main/github/github.py#L88"""

        with suppress(RuntimeError):
            self.bot.add_dev_env_value("todo", lambda x: self)
        for uid in (await self.config.all_users()).keys():
            data = await self.config.user_from_id(uid).all()
            if data.get("migrated_v2"):
                continue
            self.log.debug(data)
            if not (user_settings := data.get("user_settings")):  # Old system
                user_settings = {
                    "extra_details": data["detailed_pop"],
                    "autosorting": data["autosort"],
                    "use_markdown": data["use_md"],
                    "use_embeds": data["use_embeds"],
                    "use_timestamps": data["timestamp"],
                    "colour": data["colour"],
                    "combine_lists": data["combined_lists"],
                    "private": False,  # Private does nothing at this point
                    "reverse_sort": data["reverse_sort"],
                }

            new_data = {
                "todos": None,
                "user_settings": user_settings,
                "migrated_v2": True,
                "completed": data["completed"],
            }
            todos = []
            for todo in data["todos"]:
                if isinstance(todo, dict):
                    todos.append(todo)
                else:
                    todos.append({"task": todo, "pinned": False, "timestamp": None})
            new_data["todos"] = todos
            self.log.debug(new_data)
            await self.config.user_from_id(uid).clear()
            await self.config.user_from_id(uid).set(new_data)

    @commands.group(invoke_without_command=True)
    @commands.bot_has_permissions(add_reactions=True)
    async def todo(self, ctx: commands.Context, index: PositiveInt(False)):  # type:ignore
        """Your todo list inside Discord

        **Arguments**
            - `index` The todo you want to view.
            This is optional and if left out, it will show the help command instead
        """
        act_index = index - 1
        try:
            todo = await self.cache.get_todo_from_index(ctx.author, act_index)
        except IndexError:
            return await ctx.send("You do not have a todo at that index.")
        else:
            if todo is None:
                return await ctx.send(self._no_todo_message.format(prefix=ctx.clean_prefix))
        await ViewTodo(
            ctx,
            todo,
            index,
            **await self.cache.get_user_item(ctx.author, "user_settings"),
        ).start()

    @todo.command(name="add")
    async def todo_add(self, ctx: commands.Context, pinned: Optional[bool], *, todo: str):
        """Add a todo task to your list

        Don't store sensitive information here for Pete's sake

        **Arguments**
            - `pinned` A boolean value that sets it to be pinned or not. Defaults to False
            - `todo` The todo task
        """
        data = await self.cache.get_user_data(ctx.author.id)
        if not data["todos"]:
            data["todos"] = []
        pinned = bool(pinned)
        payload = {"task": todo, "pinned": pinned, "timestamp": self._gen_timestamp()}
        data["todos"].append(payload)
        await self.cache.set_user_item(ctx.author, "todos", data["todos"])

        data = data["user_settings"]
        msg = f"Added that as a todo."
        if data["extra_details"]:
            msg += f"\n'{discord.utils.escape_markdown(todo)}'"
        if data["use_timestamps"]:
            msg += f"\n{timestamp_format()}"
        if len(msg) > 2000:
            await ctx.send_interactive(pagify(msg))
        else:
            await ctx.send(msg)
        await self.cache._maybe_autosort(ctx.author)

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
            return await ctx.invoke(self.complete_list)

        pinned, todos = await self._get_todos(
            todos,
            timestamp=user_settings["use_timestamps"],
            md=user_settings["use_markdown"],
        )
        todos = await formatting._format_todos(pinned, todos, **user_settings)
        if completed and user_settings["combine_lists"]:
            completed = await formatting._format_completed(
                completed, combined=True, **user_settings
            )
            todos.extend(completed)

        await self.page_logic(ctx, todos, f"{ctx.author.name}'s Todos", **user_settings)

    @todo.command(name="multiadd")
    async def todo_multi_add(self, ctx: commands.Context, *, todos: str = None):
        """Add multiple todos in one command. These are split by a newline.

        You can upload a file instead of inputting the todos, or reply to a message that contains a file\

        **Examples**
        `[p]todo multiadd Todo number 1
        todo number 2
        todo number 3`

        **Arguments**
            - `todos` The todos you want to add.
            This is an optional argument and you can upload, or reply to a message with, a file instead
        """
        data: bytes
        if ctx.message.reference and not any([todos is not None, ctx.message.attachments]):
            # Message references get checked first
            msg = ctx.message.reference.resolved
            if not msg.attachments:
                return await ctx.send("That message does not have files!")
            maybe_file: discord.Attachment = msg.attachments[0]
            if not maybe_file.filename.endswith(".txt"):
                return await ctx.send("File format must be `.txt`")
            data = await maybe_file.read()
            todos = data.decode()
        elif ctx.message.attachments:
            maybe_file = ctx.message.attachments[0]
            if not maybe_file.filename.endswith(".txt"):
                return await ctx.send("File format must be `.txt`")
            data = await maybe_file.read()
            todos = data.decode()
        elif todos is None:  # No files or anything
            raise commands.UserInputError
        todos = [
            {
                "pinned": False,
                "task": t.replace("\\n", "\n"),
                "timestamp": self._gen_timestamp(),
            }
            for t in todos.split("\n")  # type:ignore
            if t
        ]
        current = await self.cache.get_user_item(ctx.author, "todos")
        if not current:
            current = []
        current.extend(todos)
        await self.cache.set_user_item(ctx.author, "todos", current)
        await ctx.send("Done. Added those as todos")
        await self.cache._maybe_autosort(ctx.author)

    @todo.command(name="gettodos", aliases=["todotofile"])
    @commands.check(attach_or_in_dm)
    async def todo_get_todos(self, ctx: commands.Context):
        """Grab your todos in a clean file format.

        This is handy for moving todos over from bot to bot
        """
        await self.cache._maybe_fix_todos(ctx.author.id)
        todos = await self.cache.get_user_item(ctx.author, "todos")
        if not todos:
            return await ctx.send(self._no_todo_message.format(prefix=ctx.clean_prefix))
        todos = "\n".join(t["task"].replace("\n", "\\n") for t in todos)
        await ctx.send("Here are your todos", file=text_to_file(todos, "todo.txt"))

    @todo.command(name="pin", aliases=["unpin"])
    async def todo_pin(self, ctx: commands.Context, index: PositiveInt):
        """Pin or unpin a todo

        This will stick it at the top of the list whenever you view it

        **Arguments**
            - `index` The index of the todo you want to pin/unpin
        """
        act_index = index - 1
        if not (todos := await self.cache.get_user_item(ctx.author, "todos")):
            return await ctx.send(self._no_todo_message.format(prefix=ctx.clean_prefix))
        try:
            todo = todos.pop(act_index)
        except IndexError:
            return await ctx.send("That index was bigger than your todo list!")
        if not isinstance(todo, dict):
            todo = {"task": str(todo), "pinned": False}
        todo["pinned"] = not todo["pinned"]
        pinned = "" if todo["pinned"] else "un"
        await ctx.send(f"Done. That todo is now {pinned}pinned")
        todos.insert(act_index, todo)
        await self.cache.set_user_item(ctx.author, "todos", todos)

    @todo.command(name="reorder", aliases=["move"], usage="<from> <to>")
    async def todo_reorder(self, ctx: commands.Context, original: PositiveInt, new: PositiveInt):
        """Move a todo from one index to another

        This will error if the index is larger than your todo list

        **Arguments**
            - `from` The index of the todo
            - `to` The new index of the todo
        """
        if original == new:
            return await ctx.send("You cannot move a todo from one index... to the same index")
        todos = await self.cache.get_user_item(ctx.author, "todos")
        if not todos:
            return await ctx.send(self._no_todo_message.format(prefix=ctx.clean_prefix))
        act_orig = original - 1
        act_new = new - 1
        try:
            task = todos.pop(act_orig)
        except IndexError:
            return await ctx.send(f"I could not find a todo at index `{original}`")
        todos.insert(act_new, task)
        await ctx.send(f"Moved a todo from index {original} to {new}")
        await self.cache.set_user_setting(ctx.author, "autosorting", False)
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
            reverse = bool(pred.result)  # Calling bool because `pred.result` starts as `None`
        await self.cache.set_user_setting(ctx.author, "reverse_sort", reverse)
        await self.cache.set_user_setting(ctx.author, "autosorting", True)
        have_not = "have" if reverse else "have not"
        await ctx.send(f"Your todos are now sorted. They {have_not} been sorted in reverse")
        await self.cache._maybe_autosort(ctx.author)

    @todo.command(name="search")
    async def todo_search(self, ctx: commands.Context, regex: Optional[bool], *, query: str):
        """Query your todo list for todos containing certain words

        **Arguments**
            - `query` The words to search for.
        """
        if not (todos := await self.cache.get_user_item(ctx.author, "todos")):
            return await ctx.send(self._no_todo_message.format(prefix=ctx.clean_prefix))
        await ctx.send("This might take a while...")
        async with ctx.typing():
            todos = await self.cache.query_list(ctx.author, regex=bool(regex), query=query)
        if not todos:
            return await ctx.send("I could not find any todos matching that query")
        user_settings = await self.cache.get_user_item(ctx.author, "user_settings")
        pinned, todos = await self._get_todos(
            todos, timestamp=user_settings["use_timestamps"], md=user_settings["use_markdown"]
        )
        todos = await formatting._format_todos(pinned, todos, **user_settings)
        await self.page_logic(ctx, todos, title="Todos matching that query", **user_settings)

    @staticmethod
    async def _get_todos(
        todos: List[dict], *, timestamp: bool = False, md: bool = False
    ) -> Tuple[List[str], List[str]]:
        """An internal function to get todos sorted by pins"""
        pinned = []
        extra = []
        for todo in todos:
            if not isinstance(todo, dict):
                extra.append(str(todo))
                continue
            task = todo["task"]
            if timestamp:
                task = (
                    f"{task} - {timestamp_format(ts, ts_format=TimestampFormats.RELATIVE_TIME)}"
                    if (ts := todo.get("timestamp")) and not md
                    else task
                )
            if todo["pinned"]:
                pinned.append(task)
            else:
                extra.append(task)
        return pinned, extra

    @staticmethod
    def _gen_timestamp():
        return int(datetime.now(tz=timezone.utc).timestamp())

    async def page_logic(self, ctx: commands.Context, data: list, title: str, **settings) -> None:
        joined = "\n".join(data)
        pagified = list(pagify(joined, page_length=300))
        pages = TodoPages(pagified, title, settings)
        if settings["private"]:
            await PrivateMenuStarter(ctx, pages).start()
            return
        await TodoMenu(pages, self.bot, ctx).start()

    async def _embed_requested(self, ctx: commands.Context, user: discord.User) -> bool:
        """An slightly rewritten method for checking if a command should embed or not"""
        if ctx.guild and not ctx.channel.permissions_for(ctx.me).embed_links:
            return False
        return await self.cache.get_user_setting(user, "use_embeds")

    async def _embed_colour(self, ctx: commands.Context) -> discord.Colour:
        colour = await self.cache.get_user_setting(ctx.author, "colour")
        return colour or await ctx.embed_colour()
