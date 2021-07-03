# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from redbot.core import commands, Config
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_list, pagify

from .abc import MetaClass
from .utils import Cache, TodoPage, TodoMenu, TodoPositiveInt, ViewTodo, timestamp_format
import logging

from typing import Optional


_config_structure = {
    "todos": [],  # List[Dict[str, Any]] "task": str, "pinned": False
    "completed": [],  # List[str]
    "user_settings": {
        "autosorting": False,
        "colour": None,
        "combine_lists": False,
        "extra_details": False,
        "private": False,
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
    __version__ = "3.0.0.dev1"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, 19924714019, True)
        self.config.register_user(**_config_structure)
        self.cache = Cache(self.bot, self.config)
        self._startup_task = self.bot.loop.create_task(self._initialize())
        self.log = logging.getLogger("red.JojoCogs.todo")

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
            todo = await self.cache.get_todo_from_index(ctx.author, index)
        except IndexError:
            return await ctx.send("You do not have a todo at that index.")
        else:
            if todo is None:
                return await ctx.send(
                    f"You do not have any todos. Use `{ctx.clean_prefix}todo add <todo>` to add one."
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
        await self._maybe_autosort()

    async def page_logic(self, ctx: commands.Context, data: list, **settings):
        joined = "\n".join(data)
        pagified = list(pagify(joined))
        pages = TodoPage(pagified, **settings)
        await TodoMenu(pages).start(ctx)

    async def _maybe_autosort(self):
        ...
