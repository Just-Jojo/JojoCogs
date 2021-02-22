import asyncio
import logging
import os
import random
import time
from operator import itemgetter
from typing import Literal, Optional

import aiohttp
import discord
from redbot.core import Config, commands
from redbot.core.utils import AsyncIter

log = logging.getLogger("red.mcoc-v3.brownies")
_config_structure = {
    "user": {"brownies": 0, "StealCD": 5, "BrownieCD": 5},
    "guild": {"StealCD": 300, "BrownieCD": 300},
}


def positive_int(arg: str) -> int:
    # From redbot.cogs.cleanup.converters
    """Returns a positive int"""
    try:
        ret = int(arg)
    except ValueError:
        raise commands.BadArgument(f"{arg} is not a integer.")
    if ret <= 0:
        raise commands.BadArgument(f"{arg} is not a positive integer.")
    return ret


class PluralDict(dict):
    """This class is used to plural strings
    You can plural strings based on the value input when using this class as a dictionary.
    """

    def __missing__(self, key):
        if "(" in key and key.endswith(")"):
            key, rest = key.split("(", 1)
            value = super().__getitem__(key)
            suffix = rest.rstrip(")").split(",")
            if len(suffix) == 1:
                suffix.insert(0, "")
            return suffix[0] if value <= 1 else suffix[1]
        raise KeyError(key)


class Brownies(commands.Cog):
    """Collector loves brownies, and will steal from others for you!"""

    __author__ = ["JJW", "Jojo#7791"]
    __version__ = "0.1.0"

    async def default_embed(
        self,
        ctx: commands.Context,
        title: str = None,
        description: str = None,
        thumbnail: str = None,
        image: str = None,
        footer: str = None,
        footer_url: str = None,
    ) -> discord.Embed:
        """Get a default embed from context"""
        session = aiohttp.ClientSession()
        data = discord.Embed()
        if title:
            data.title = title
        if description and len(description) < 2048:
            data.description = description
        elif description and len(description) > 2048:
            data.description = description[:2047]  # String splicing
            log.warning(
                f"Descriptions length ({len(description)}) was larger than the character limit"
            )

        if ctx.guild is not None:
            if str(ctx.author.colour) != "#000000":
                data.colour = ctx.author.colour
            else:
                data.colour = await ctx.embed_colour()
        else:
            data.colour = await ctx.embed_colour()
        if thumbnail is not None:
            try:
                async with session.get(str(thumbnail)) as response:
                    if response.status == 200:
                        data.set_thumbnail(thumbnail)
            except TypeError:
                pass
        if image is not None:
            try:
                async with session.get(str(image)) as response:
                    if response.status == 200:
                        data.set_image(image)
                    else:
                        log.warning(f"Image got a status code of {response.status}")
            except TypeError:
                pass
        if footer is None:
            footer = f"{ctx.bot.user.name} Embed"
        if footer_url is None:
            footer_url = ctx.bot.user.avatar_url
        else:
            async with session.get(footer_url) as response:
                if response.status != 200:
                    footer_url = ctx.bot.user.avatar_url
        data.set_footer(text=footer, icon_url=footer_url)
        await session.close()
        return data

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 2287042090, force_registration=True)
        self.config.register_member(**_config_structure["user"])
        self.config.register_guild(**_config_structure["guild"])

    async def format_help_for_context(self, ctx):
        return (
            f"{super().format_help_for_context(ctx)}"
            f"\n**__Version__**: {self.__version__}"
            f"\n**__Authors__**: {', '.join(self.__author__)}"
        )

    async def red_delete_data_for_user(
        self,
        *,
        user: Literal["discord_deleted_user", "owner", "owner", "user", "user_strict"],
        uid: int,
    ):
        """Delete brownie data for a user"""
        all_members = await self.config.all_members()
        async for guild_id, guild_data in AsyncIter(all_members.items(), steps=100):
            if uid in guild_data:
                await self.config.member_from_ids(guild_id, uid).clear()

    @commands.group()
    @commands.admin()
    async def setbrownie(self, ctx):
        """Change the Brownie settings for your guild"""

    @setbrownie.command()
    async def stealcd(self, ctx, seconds: positive_int):
        """Set the cooldown for stealing"""
        await self.config.guild(ctx.guild).StealCD.set(seconds)
        await ctx.send(f"Cooldown is now {seconds}")

    @setbrownie.command()
    async def browniecd(self, ctx, seconds: positive_int):
        """Set the cooldown for finding brownies"""
        await self.config.guild(ctx.guild).BrownieCD.set(seconds)
        await ctx.send(f"Cooldown is now {seconds}")

    @setbrownie.command()
    async def settings(self, ctx):
        """Get the settings for Brownie and Steal cooldown"""
        settings = await self.config.guild(ctx.guild).get_raw()
        settings.pop("Players")
        embed = await self.default_embed(
            ctx, title=f"{ctx.guild.name} Settings", thumbnail=ctx.guild.icon_url
        )
        for key, value in settings.items():
            embed.add_field(name=key, value=f"{value} seconds")
        await ctx.send(embed=embed)

    @commands.command()
    async def brownies(self, ctx):
        """See how many brownies you have!"""
        brownies = await self.config.member(ctx.author).brownies()
        if brownies == 0:
            msg = "You have 0 brownie points!"
        elif brownies == 1:
            msg = "You have 1 brownie point!"
        else:
            msg = f"You have {brownies} brownie points!"
        await ctx.send(msg)

    @commands.command()
    async def brownie(self, ctx):
        """Get a random amount of brownies"""
        action = "BrownieCD"
        cd = await self.check_cooldown(ctx=ctx, user=ctx.author, action=action)
        if not cd:
            return  # I don't like huge if statements
        weighted_sample = [1] * 152 + [x for x in range(49) if x > 1]
        brownies = random.choice(weighted_sample)
        user_brownies = await self.config.member(ctx.author).brownies()
        user_brownies += brownies
        await self.config.member(ctx.author).brownies.set(user_brownies)
        if brownies > 1:
            msg = f"{ctx.author.name} found {brownies} brownies!"
        else:
            msg = f"{ctx.author.name} found 1 brownie!"
        await ctx.send(msg)

    @commands.command()
    async def brownies(self, ctx):
        """Check your brownies!"""
        brownies = await self.config.member(ctx.author).brownies()
        if brownies > 1:
            msg = f"You have {brownies} brownies!"
        else:
            msg = "You have 1 brownie!"
        await ctx.send(msg)  # might at some point make it a user check...

    @commands.command(aliases=("giveb", "gib"))
    async def givebrownies(self, ctx, user: discord.Member, brownies: positive_int):
        """Give a user brownies!"""
        if user.id == ctx.author.id:
            return await ctx.send("You can't give yourself brownies")
        user_brownies = await self.config.member(user).brownies()
        author_brownies = await self.config.member(ctx.author).brownies()
        if brownies > author_brownies:
            return await ctx.send("You don't have enough brownies points")
        user_brownies += brownies
        author_brownies -= brownies
        await ctx.send(f"{ctx.author.name} gave {brownies} brownies to {user.name}")
        await self.config.member(user).brownies.set(user_brownies)
        await self.config.member(ctx.author).brownies.set(author_brownies)

    @commands.command()
    async def nom(self, ctx):
        """Nom nom nom..."""
        brownies = await self.config.member(ctx.author).brownies()
        if not brownies:
            return await ctx.send("There are no brownies to eat!")
        brownies -= 1
        if brownies == 0:
            msg = f"Nom nom nom.\n{ctx.author.name} has no more brownie points!"
        elif brownies == 1:
            msg = f"Nom nom nom.\n{ctx.author.name} has 1 brownie point!"
        else:
            msg = f"Nom nom nom.\n{ctx.author.name} has {brownies} brownie points!"
        await ctx.send(msg)
        await self.config.member(ctx.author).brownies.set(brownies)

    @commands.command()
    async def steal(self, ctx, user: Optional[discord.Member] = None):
        """Steal brownies!"""
        cd = await self.check_cooldown(ctx, ctx.author, "StealCD")
        if cd is False:
            return
        if user is None:
            user = self.random_user(ctx.guild, ctx.author)
        msg = await self.steal_logic(ctx, user, ctx.author)
        await ctx.send(f"{ctx.author.name} is on the prowl for brownies...")
        await asyncio.sleep(4)
        await ctx.send(msg)

    async def steal_logic(
        self, ctx: commands.Context, user: discord.Member, author: discord.Member
    ) -> str:
        """|coro|

        Logic for stealing brownies
        """
        user_brownies = await self.config.member(user).brownies()
        author_brownies = await self.config.member(author).brownies()

        if user_brownies == 0:
            return f"{user.name} has no brownies!"
        steal_chance = random.randint(1, 100)
        if steal_chance > 90:
            return "I could not find their brownie points"
        steal_b = int(user_brownies * 0.75)
        if steal_b < 1:
            stolen = 1
        else:
            # No need to generate a number between 1 and 1 LOL
            stolen = random.randint(1, steal_b)
        user_brownies -= stolen
        author_brownies += stolen
        await self.config.member(user).brownies.set(user_brownies)
        await self.config.member(author).brownies.set(author_brownies)
        return (
            f"{author.name} stole {stolen} brownies from {user.name}"
            if stolen > 1
            else f"{author.name} stole 1 brownie from {user.name}"
        )

    async def check_cooldown(
        self, ctx: commands.Context, user: discord.Member, action: str
    ) -> bool:
        """Check the cooldown for a member"""
        guild_cooldown = await self.config.guild(ctx.guild).get_raw(action)
        cooldown = await self.config.member(user).get_raw(action)
        if abs(cooldown - int(time.perf_counter())) >= guild_cooldown:
            # I have no idea how this works
            cooldown = int(time.perf_counter())
            await self.config.member(user).set_raw(action, value=cooldown)
            return True
        elif cooldown == 0:
            cooldown = int(time.perf_counter())
            await self.config.member(user).set_raw(action, value=cooldown)
            return True
        else:
            s = abs(cooldown - int(time.perf_counter()))
            seconds = abs(s - guild_cooldown)
            remaining = self.time_formatting(seconds)
            await ctx.send(f"This action has a cooldown. You still have:\n{remaining}")
            return False

    def random_user(
        self, guild: discord.Guild, author: discord.Member
    ) -> discord.Member:
        """Return a random, non-bot user"""
        clean_users = [
            member
            for member in guild.members
            if not member.bot and not member == author
        ]
        user = random.choice(clean_users)
        return user

    def time_formatting(self, seconds) -> str:
        """Format time for cooldown messages"""
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        data = PluralDict({"hour": h, "minute": m, "second": s})
        if h > 0:
            fmt = "{hour} hour{hour(s)}"
            if data["minute"] > 0 and data["second"] > 0:
                fmt += ", {minute} minute{minute(s)}, and {second} second{second(s)}"
            if data["second"] > 0 == data["minute"]:
                fmt += ", and {second} second{second(s)}"
            msg = fmt.format_map(data)
        elif h == 0 and m > 0:
            if data["second"] == 0:
                fmt = "{minute} minute{minute(s)}"
            else:
                fmt = "{minute} minute{minute(s)}, and {second} second{second(s)}"
            msg = fmt.format_map(data)
        elif m == 0 and h == 0 and s > 0:
            fmt = "{second} second{second(s)}"
            msg = fmt.format_map(data)
        elif m == 0 and h == 0 and s == 0:
            msg = "None"
        return msg

    async def cog_check(self, ctx: commands.Context):
        return ctx.guild is not None  # Guild only commands
