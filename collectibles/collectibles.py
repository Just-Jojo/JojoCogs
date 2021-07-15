# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import logging
from datetime import datetime
from typing import Literal, Optional, Union

import discord
from redbot.core import Config, bank, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_list, pagify

from .utils import Menu, Page, PositiveInt

log = logging.getLogger("red.JojoCogs.collectibles")
log.setLevel(logging.DEBUG)
_config_structure = {
    "user": {
        "collectibles": {},
        "total_count": 0,
    },
    "guild": {
        "collectibles": {},
    },
    "global": {"collectibles": {"Trophy": ["\N{TROPHY}\N{VARIATION SELECTOR-16}", 300]}},
}


class Collectibles(commands.Cog):
    """Collect trinkets and items!"""

    __authors__ = ["Jojo#7791"]
    __version__ = "1.0.2"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, 544974305445019651, True)
        self.config.register_guild(**_config_structure["guild"])
        self.config.register_global(**_config_structure["global"])
        self.config.register_user(**_config_structure["user"])

    def format_help_for_context(self, ctx: commands.Context):
        pre = super().format_help_for_context(ctx)
        plural = "s" if len(self.__authors__) > 1 else ""
        return (
            f"{pre}\n"
            f"Author{plural}: `{humanize_list(self.__authors__)}`\n"
            f"Version: `{self.__version__}`"
        )

    async def red_delete_data_for_user(
        self,
        *,
        requester: Literal["discord_deleted_user", "owner", "user", "user_strict"],
        user_id: int,
    ):
        await self.config.user_from_id(user_id).clear()

    @commands.group()
    async def collectible(
        self,
        ctx: commands.Context,
    ):
        """Buy and set collectibles"""
        pass

    @collectible.command(usage="[check_global=True] <collectible>")
    async def buy(
        self,
        ctx: commands.Context,
        _global: Optional[bool],
        *,
        collectible_name: str,
    ):
        """Buy a collectible"""
        _global = True if _global is None else _global
        maybe_collectible = await self._search_collectibles(
            ctx, _global, collectible_name  # type:ignore[arg-type]
        )
        if maybe_collectible is None:
            return await ctx.send("I could not find that Collectible")
        emoji, cost = maybe_collectible

        name = await bank.get_currency_name(ctx.guild)
        if not await bank.can_spend(ctx.author, cost):
            bal = await bank.get_balance(ctx.author)
            return await ctx.send(
                f"You can't buy that! {collectible_name} costs {cost} {name} but you only have {bal} {name}"
            )
        await bank.withdraw_credits(ctx.author, cost)
        coll_msg = f"You bought a {collectible_name} {emoji} for {cost} {name}"
        if await ctx.embed_requested():
            embed = discord.Embed(
                title="Collectible purchase",
                colour=await ctx.embed_colour(),
                description=coll_msg,
            )
            embed.timestamp = datetime.utcnow()
            kwargs = {"embed": embed}
        else:
            kwargs = {"content": coll_msg}
        await ctx.send(**kwargs)
        async with self.config.user(ctx.author).collectibles() as coll:
            try:
                msg = coll[collectible_name]
            except KeyError:
                coll[collectible_name] = f"{emoji} 1x"
            else:
                emoji, amount = msg.split()
                amount = int(amount.strip("x"))
                amount += 1
                coll[collectible_name] = f"{emoji} {amount}x"
        func = self.config.user(ctx.author).total_count
        await func.set(await func() + 1)

    @collectible.command(name="list")
    async def collectible_list(self, ctx: commands.Context):
        """List the collectibles available to purchase"""
        collectibles: dict = {"Global": await self.config.collectibles()}
        if ctx.guild:
            collectibles["Guild"] = await self.config.guild(ctx.guild).collectibles()
        log.debug(collectibles)
        msg: str = ""
        for key, value in collectibles.items():
            log.debug(value)
            if not value:
                msg += f"**{key}**\nNo Collectibles available"
                continue
            msg += (
                f"**{key}**\n"
                + "\n".join(
                    f"{name} {emoji}: {cost}" for name, (emoji, cost) in value.items()
                )
                + "\n\n"
            )
        msg = msg[:-2] if msg.endswith("\n") else msg
        await Menu(source=Page(list(pagify(msg)), "Collectibles")).start(ctx)

    @collectible.command(name="globaladd", aliases=["gadd"])
    @commands.is_owner()
    async def collectible_global_add(
        self,
        ctx: commands.Context,
        name: str,
        emoji: str,
        cost: PositiveInt,
    ):
        """Add a Collectible to the global list"""
        async with self.config.collectibles() as coll:
            if name in coll.keys():
                return await ctx.send(
                    f"A collectible with the name `{name}` already exists in the global cache"
                )
            coll[name] = [emoji, cost]
        await ctx.tick()

    @collectible.command(name="globalremove", aliases=["gdel", "gdelete"])
    async def collectible_global_remove(self, ctx: commands.Context, name: str):
        """Remove a Collectible from the global cache"""
        async with self.config.collectibles() as coll:
            if name not in coll.keys():
                return await ctx.send(
                    "I could not find a Collectible with that name in the global cache"
                )
            del coll[name]
        await ctx.tick()

    @collectible.command(name="add")
    @commands.admin()
    @commands.guild_only()
    async def collectible_guild_add(
        self,
        ctx: commands.Context,
        name: str,
        emoji: str,
        cost: PositiveInt,
    ):
        """Add a Collectible to your guild's cache"""
        async with self.config.guild(ctx.guild).collectibles() as coll:
            if name in coll.keys():
                return await ctx.send(
                    f"A Collectible with the name `{name}` already exists in this guild's cache"
                )
            coll[name] = [str(emoji), cost]
        await ctx.tick()

    @collectible.command(name="remove", aliases=["del", "delete"])
    @commands.admin()
    @commands.guild_only()
    async def collectible_guild_remove(self, ctx: commands.Context, name: str):
        """Remove a collectible from this guild's cache"""
        async with self.config.guild(ctx.guild).collectibles() as coll:
            if name not in coll.keys():
                return await ctx.send(
                    "There is no Collectible with that name in this guild's cache"
                )
            coll.pop(name)
        await ctx.tick()

    @collectible.command(name="owned")
    async def collectible_owned(self, ctx: commands.Context):
        """List your Collectibles"""
        collectibles, total_count = (await self.config.user(ctx.author).all()).values()
        if not collectibles:
            return await ctx.send("You do not have any collectibles")
        joined = "\n".join(f"{emoji} **{coll}**" for coll, emoji in collectibles.items())
        await Menu(Page(list(pagify(joined)), f"{ctx.author.name}'s Collectibles")).start(
            ctx
        )

    async def _search_collectibles(
        self, ctx: commands.Context, glob: bool, coll_name: str
    ) -> Optional[dict]:
        collectibles: dict = await self.config.collectibles()
        if coll_name in collectibles.keys() and glob:
            # This is an override bool as a global and
            # a guild collectible could co-exist in the settings
            return collectibles[coll_name]
        # If we can't find it in the global, we'll try in the guild
        if not ctx.guild:
            return None
        collectibles = await self.config.guild(ctx.guild).collectibles()
        if coll_name in collectibles.keys():
            return collectibles[coll_name]
        return None
