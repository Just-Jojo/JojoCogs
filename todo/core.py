# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_list, pagify

from .abc import MetaClass
from .utils import Cache, TodoPage, TodoMenu, TodoPositiveInt, ViewTodo, timestamp_format
import logging

from typing import Optional, Union, List, Dict, Tuple
from contextlib import suppress


_config_structure = {
    "todos": [],  # List[Dict[str, Any]] "task": str, "pinned": False
    "completed": [],  # List[str]
    "user_settings": {
        "autosorting": False,
        "colour": None,
        "combine_lists": False,
        "extra_details": False,
        "private": False,
        "reverse_sort": False,
        "use_embeds": True,
        "use_markdown": False,
        "use_timestamps": False,
    },
}


class ToDo(commands.Cog, metaclass=MetaClass):
    """A todo list for keeping track of tasks you have to do

    This cog is my oldest, still standing cog and holds a special place in my heart even though it's a pain to work on lol

    I hope you have as much fun with it as I had designing it ❤
    - Jojo#7791"""

    __authors__ = [
        "Jojo#7791",
    ]
    __version__ = "3.0.0.dev2"
    _no_todo_message = "You do not have any todos. You can add one with `{prefix}todo add`"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, 19924714019, True)
        self.config.register_user(**_config_structure)
        self.cache = Cache(self.bot, self.config)
        self._startup_task = self.bot.loop.create_task(self._initialize())
        self.log = logging.getLogger("red.JojoCogs.todo")
        with suppress(RuntimeError):
            self.bot.add_dev_env_value("todo", lambda x: self)

    def cog_unload(self):
        with suppress(Exception):
            self.bot.remove_dev_env_value("todo")

    def format_help_for_context(self, ctx: commands.Context):
        pre = super().format_help_for_context(ctx)
        plural = "s" if len(self.__authors__) > 1 else ""
        return (
            f"{pre}\n"
            f"Author{plural}: `{humanize_list(self.__authors__)}`\n"
            f"Version: `{self.__version__}`"
        )

    async def _initialize(self):
        """This is based off of Obi-Wan3's migration method in their github cog
        https://github.com/Obi-Wan3/OB13-Cogs/blob/main/github/github.py#L88"""

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
            todo,  # type:ignore
            **await self.cache.get_user_item(ctx.author, "user_settings"),
        ).start(ctx)

    @todo.command(name="add")
    async def todo_add(self, ctx: commands.Context, pinned: Optional[bool], *, todo: str):
        """Add a todo task to your list

        Don't store sensitive information here for Pete's sake

        Arguments
            - pinned: A boolean value that sets it to be pinned or not. Defaults to False
            - todo: The todo task
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
        todos = await self._get_todos(todos)
        if user_settings["combine_lists"]:
            completed.insert(0, "\N{WHITE HEAVY CHECK MARK} Completed todos")
            todos.extend(completed)
        await self.page_logic(ctx, todos, **user_settings)

    @staticmethod
    async def _get_todos(todos: List[dict], *, separate: bool = True) -> Union[List[str], Tuple[List[str], List[str]]]:
        """An internal function to get todos sorted by pins"""
        ret = []
        pinned = []
        if separate:
            pinned.append("\N{PUSHPIN} Pinned todos")
        for todo in todos:
            task = todo["task"]
            if todo["pinned"]:
                pinned.append(task)
                continue
            ret.append(task)
        if len(pinned) == 1:
            return ret
        if not separate:
            return pinned, ret
        ret.append("Other todos")
        pinned.extend(ret)
        return pinned

    async def page_logic(self, ctx: commands.Context, data: list, **settings):
        joined = "\n".join(data)
        pagified = list(pagify(joined))
        pages = TodoPage(pagified, **settings)
        await TodoMenu(pages).start(ctx)

    async def _maybe_autosort(self, user: Union[discord.Member, discord.User]):
        data = await self.cache.get_user_data(user.id)
        todos = data["todos"]
        completed = data["completed"]
        if not any([completed, todos]):
            return
        settings = data["user_settings"]
        if not settings["autosort"]:
            return
        if todos:
            todos = await self._get_todos(data["todos"], separate=False)
            todos.sort(reverse=settings["reverse_sort"])
        if completed:
            completed.sort(reverse=settings["reverse_sort"])
        data["completed"] = completed
        data["todos"] = todos
        await self.cache.set_user_data(user, data)
