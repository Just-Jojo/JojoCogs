import asyncio
import logging
from typing import Literal

import discord
from redbot.core import Config, checks, commands
from redbot.core.utils.chat_formatting import pagify
from redbot.core.utils import menus

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
        """Base To do reminder command"""

    @todo.command()
    async def add(self, ctx, *, todo: str):
        """Add a to do reminder

        Example:
        `[p]todo add Walk the dog soon`"""
        await self.config.user(ctx.author).set_raw("todos", value=todo)
        await ctx.send("Added the reminder `{}`".format(todo))

    @todo.command(aliases=["del", "delete"])
    async def remove(self, ctx, todo: str):
        """Remove a to do reminder

        Example:
        `[p]todo remove|del|delete ToDo`

        Note this *is* case sensitive"""
        try:
            await self.config.user(ctx.author).clear_raw("todos", todo)
        except KeyError:
            return await ctx.send("I could not find that ToDo reminder. Please use `{}todo list`".format(
                ctx.clean_prefix
            ))
        await ctx.send("Removed `{}` from your to do list!".format(todo))

    @todo.command(name="list")  # Fuck you, reserved keywords >:|
    async def todo_list(self, ctx):
        """List your ToDo reminders"""
        todos = await self.config.user(ctx.author).get_raw("todos")
        if len(todos) >= 1:
            await self.page_logic(ctx, todos)
        else:
            await ctx.send(f"You don't have any ToDo reminders!\nYou can add one using `{ctx.clean_prefix}todo add <name> <ToDO>`")

    async def page_logic(self, ctx: commands.Context, object: list) -> None:
        embeds = []
        values = {
            "title": "{}'s ToDos".format(ctx.author.display_name),
            "color": ctx.author.color
        }
        paged = pagify(", ".join(object), page_length=500)
        for i in paged:
            embed = discord.Embed(**values)
            embed.set_author(name=ctx.author.name,
                             icon_url=ctx.author.avatar_url)
            embed.add_field(name="ToDo's", value=i)
            embeds.append(embed)

        msg = await ctx.send(embed=embeds[0])
        controls = menus.DEFAULT_CONTROLS if len(embeds) > 1 else {
            "\N{CROSS MARK}": menus.close_menu
        }
        asyncio.create_task(menus.menu(ctx, embeds, controls, msg, timeout=15))
        menus.start_adding_reactions(msg, controls.keys())

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
