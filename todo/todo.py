import asyncio
import logging
from typing import Literal

import discord
from redbot.core import Config, checks, commands
from redbot.core.utils.predicates import MessagePredicate
from redbot.core.utils.chat_formatting import pagify
from . import menus

log = logging.getLogger("red.jojo.todo")


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

    __version__ = "0.1.0"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, 19924714019, force_registration=True)
        self.config.register_user(
            todos=[], use_md=True, sort=False
        )

    async def red_delete_data_for_user(
        self,
        requester: Literal["discord", "owner", "user", "user_strict"],
        user_id: int
    ) -> None:
        await self.config.user_from_id(user_id).clear()

    @commands.command()
    async def mdtoggle(self, ctx, toggle: bool):
        """Toggle whether or not the list should use markdown"""
        md = await self.config.user(ctx.author).use_md()
        toggled = "disabled!" if toggle is False else "enabled!"
        if md == toggle:
            await ctx.send(f"Markdown is already {toggled}")
        else:
            await ctx.send(f"Markdown is now {toggled}")
            await self.config.user(ctx.author).use_md.set(toggle)

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

    # `pop` because you're basically using list.pop(index) :p
    @todo.command(aliases=["del", "delete", "pop"])
    async def remove(self, ctx, todo: int = None):
        """Remove a todo reminder

        Example:
        `[p]todo del <number>`"""
        todos: list = await self.config.user(ctx.author).todos()
        if not len(todos):
            return await ctx.send((
                "You don't have any todos yet!"
                f"\nUse `{ctx.clean_prefix}todo add <todo>` to add one!"
            ))
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
            await ctx.send(
                (
                    f"You don't have any ToDo reminders!"
                    f"\nYou can add one using "
                    f"`{ctx.clean_prefix}todo add <name> <ToDo>`"
                )
            )

    @todo.command()
    async def sort(self, ctx):
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
        items: list = await self.config.user(ctx.author).todos()
        items.sort(reverse=reverse)
        await ctx.send("Okay! I've sorted your todos!")
        await self.page_logic(
            ctx=ctx, things=[f"{num}. {i}" for num, i in enumerate(items, 1)]
        )
        await self.config.user(ctx.author).todos.set(items)

    @todo.command(aliases=["move", ])
    async def rearrange(self, ctx, index: positive_int, new_index: positive_int):
        """Rearrange a todo!"""
        index -= 1
        new_index -= 1
        items = await self.config.user(ctx.author).todos()
        if new_index > (leng := len(items)):
            new_index = leng - 1
        try:
            item = items.pop(index)
        except IndexError:
            await ctx.send("Hm, that doesn't seem to be a todo!")
        else:
            items.insert(new_index, item)
            await ctx.send("I moved that todo!")
            await self.config.user(ctx.author).todos.set(items)

    async def page_logic(self, ctx: commands.Context, things: list):
        things = "\n".join(things)
        use_md = await self.config.user(ctx.author).use_md()
        menu = menus.TodoMenu(
            source=menus.TodoPages(data=list(pagify(things)), use_md=use_md),
            delete_message_after=False, clear_reactions_after=True
        )
        await menu.start(ctx=ctx, channel=ctx.channel)

    def create(
        self, ctx: commands.Context, title: str = "",
        color: discord.Colour = None,
        footer: str = None, footer_url: str = None
    ) -> discord.Embed:
        data = discord.Embed(title=title, color=color)
        if footer is None:
            footer = ctx.author.name
        if footer_url is None:
            footer_url = ctx.author.avatar_url
        data.set_footer(text=footer, icon_url=footer_url)
        return data
