import discord
import logging
import asyncio
import typing
import random

from . import menus

from redbot.core import commands, Config
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import pagify

log = logging.getLogger("red.JojoCogs.mjolnir")


class Mjolnir(commands.Cog):
    """Attempt to lift Thor's hammer!"""
    __version__ = "0.1.1"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, 1242351245243535476356, True)
        self.config.register_user(lifted=0)

    @commands.command()
    async def lifted(self, ctx):
        lifted = await self.config.user(ctx.author).lifted()
        if lifted == 1:
            sending = f"You have lifted Mjolnir 1 time."
        else:
            sending = f"You have lifted Mjolnir {lifted} times."
        await ctx.send(content=sending)

    @commands.command()
    async def trylift(self, ctx):
        lifted = random.randint(0, 100)
        if lifted >= 95:
            content = "The sky opens up and a bolt of lightning strikes the ground\nYou are worthy. Hail, son of Odin"
            lift = await self.config.user(ctx.author).lifted()
            lift += 1
            await self.config.user(ctx.author).lifted.set(lift)
        else:
            content = random.choice((
                "The hammer is strong, but so are you. Keep at it", "Mjolnir budges a bit but remains steadfast, as you should.",
                "You've got this!"))
        await ctx.send(content=content)

    @commands.command()
    async def liftedboard(self, ctx):
        all_users = await self.config.all_users()
        # log.info(all_users)
        # await ctx.tick()
        board = sorted(
            all_users.items(), key=lambda m: m[0], reverse=True
        )
        sending = []
        for user in board:
            _user = await self.bot.get_or_fetch_user(user[0])
            name = _user.display_name
            amount = user[1]["lifted"]
            sending.append(f"**{name}:** {amount}")
        sending = list(pagify("\n".join(sending)))
        if not len(sending):
            embed = discord.Embed(
                title="Mjolnir!",
                description=f"No one has lifted Mjolnir yet!\nWill you be the first? Try `{ctx.clean_prefix}`",
                colour=discord.Colour.blue()
            )
            return await ctx.send(embed=embed)
        menu = menus.MjolnirMenu(source=menus.MjolnirPages(sending))
        await menu.start(ctx=ctx, channel=ctx.channel)

    async def cog_check(self, ctx: commands.Context):
        return ctx.guild is not None
