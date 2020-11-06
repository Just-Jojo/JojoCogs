from redbot.core import commands, checks, Config
from redbot.core.utils import menus
import discord
import logging
import asyncio

log = logging.getLogger("red.jojo.todo")


class ToDo(commands.Cog):
    """A simple todo list for discord"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, 19924714019, force_registration=True)
        self.config.register_user(
            todo={}
        )

    @commands.group()
    async def todo(self, ctx):
        """Base To do reminder command"""

    @todo.command()
    async def add(self, ctx, title: str, *, description: str):
        """Add a to do reminder"""
        await self.config.user(ctx.author).todo.set_raw(title, value=description)
        await ctx.send("I have added the reminder under the name `{}`".format(title))

    @todo.command(aliases=["del", "delete"])
    async def remove(self, ctx, todo: str):
        """Remove a to do reminder
        Note this *is* case sensitive"""
        try:
            await self.config.user(ctx.author).todo.clear_raw(todo)
        except KeyError:
            return await ctx.send("I could not find that ToDo reminder. Please use `{}todo list`".format(
                ctx.clean_prefix
            ))
        await ctx.send("Removed `{}` from your to do list!".format(todo))

    @todo.command(name="list")  # Fuck you, reserved keywords >:|
    async def todo_list(self, ctx):
        """List your ToDo reminders"""
        try:
            todos = await self.config.user(ctx.author).todo.get_raw()
        except KeyError:
            return await ctx.send(
                "You don't have any todos! To add a todo reminder use `{}todo add <name> <reminder>`".format(
                    ctx.clean_prefix)
            )
        log.info(todos)
        await self.page_logic(ctx, todos)

    async def page_logic(self, ctx: commands.Context, object: dict) -> None:
        count = 0
        embeds = []
        embed = self.create(
            ctx, title=f"{ctx.author}'s ToDo list", color=ctx.author.color,
            footer=f"{ctx.author.name}'s ToDos'"
        )
        for key, value in object.items():
            if count == 5:
                embed.add_field(name=key, value=value, inline=True)
                embeds.append(embed)
                count = 0
                embed = self.create(
                    ctx, title=f"{ctx.author}'s ToDo list", color=ctx.author.color,
                    footer=f"{ctx.author.name}'s ToDos'"
                )
            else:
                embed.add_field(name=key, value=value, inline=True)
                count += 1
        else:
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
