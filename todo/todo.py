import asyncio
import logging
from typing import Literal

import discord
from redbot.core import Config, checks, commands
from redbot.core.utils.chat_formatting import pagify
from . import menus

log = logging.getLogger("red.jojo.todo")


class ToDo(commands.Cog):
    """A simple todo list for discord"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, 19924714019, force_registration=True)
        self.config.register_user(
            todos=[]
        )

    async def red_delete_data_for_user(
        self,
        requester: Literal["discord", "owner", "user", "user_strict"],
        user_id: int
    ) -> None:
        await self.config.user_from_id(user_id).clear()

    @commands.group()
    async def todo(self, ctx):
        """Base todo reminder command"""

    @todo.command()
    async def add(self, ctx, *, todo: str):
        """Add a todo reminder

        Example:
        `[p]todo add Walk the dog soon`"""
        todos = await self.config.user(ctx.author).todos()
        todos.append(todo)
        await self.config.user(ctx.author).todos.set(todos)
        await ctx.send("Added that todo reminder!")

    @todo.command(aliases=["del", "delete"])
    async def remove(self, ctx, todo: int = None):
        """Remove a todo reminder

        Example:
        `[p]todo del <number>`"""
        todos: list = await self.config.user(ctx.author).todos()
        if not len(todos):
            await ctx.send(f"You don't have any todos yet!\nUse `{ctx.clean_prefix}todo add <todo>` to add one!")
            return
        if todo is None:  # can't use `not todo` since `0` is falsy
            sending = []
            for index, item in enumerate(todos, 1):
                sending.append(f"{index} {item}")
            await self.page_logic(ctx, sending)
            return
        else:
            todo -= 1
        try:
            del todos[todo]
        except IndexError:
            await ctx.send("That was an invalid todo index!")
        else:
            await ctx.send("Removed that todo!")
            await self.config.user(ctx.author).todos.set(todos)

    @todo.command(name="list")  # Fuck you reserved keywords >:|
    async def todo_list(self, ctx):
        """List your todo reminders"""
        todos = await self.config.user(ctx.author).todos()
        todos = [f"{num}. {item}" for num, item in enumerate(todos, 1)]
        if len(todos) >= 1:
            await self.page_logic(ctx, todos)
        else:
            await ctx.send(f"You don't have any ToDo reminders!\nYou can add one using `{ctx.clean_prefix}todo add <name> <ToDo>`")

    async def page_logic(self, ctx, things: list):
        things = "\n".join(things)
        menu = menus.TodoMenu(source=menus.TodoPages(
            list(pagify(things))), delete_message_after=False, clear_reactions_after=True)
        await menu.start(ctx=ctx, channel=ctx.channel)

    def create(
        self, ctx, title: str = "", color: discord.Colour = None, footer: str = None, footer_url: str = None
    ) -> discord.Embed:
        data = discord.Embed(title=title, color=color)
        if footer is None:
            footer = ctx.author.name
        if footer_url is None:
            footer_url = ctx.author.avatar_url
        data.set_footer(text=footer, icon_url=footer_url)
        return data
