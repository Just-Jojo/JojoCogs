# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import logging
from datetime import datetime
from typing import Optional, Union

import discord
from jojo_utils import positive_int
from redbot.core import Config, bank, commands
from redbot.core.bot import Red

log = logging.getLogger("red.JojoCogs.collectibles")
_config_structure = {
    "user": {
        "collectibles": {},
        "total_count": 0,
    },
    "guild": {
        "collectibles": {},
    },
    "global": {"collectibles": {"Trophy": ["🏆", 300]}},
}


class Collectibles(commands.Cog):
    """Collect trinkets and items!"""

    __author__ = ["Jojo#7791"]
    __version__ = "1.0.0Dev"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, 544974305445019651, True)
        for key, value in _config_structure.items():
            getattr(self.config, f"register_{key}")(
                **value
            )  # am too lazy to type it all out :)

    @commands.group()
    async def collectible(
        self,
        ctx: commands.Context,
    ):
        """Buy and set collectibles"""
        pass

    @collectible.command(usage="[check_global] <collectible>")
    async def buy(
        self,
        ctx: commands.Context,
        _global: Optional[bool] = True,
        *,
        collectible_name: str = None,
    ):
        """Buy a collectible"""
        if collectible_name is None:
            return await self._send_collectible_list(ctx)
        maybe_collectible = await self._search_collectibles(
            ctx, _global, collectible_name  # type:ignore[arg-type]
        )
        if maybe_collectible is None:
            return await ctx.send("I could not find that Collectible")
        emoji, cost = maybe_collectible
        log.info(f"{cost} {emoji}\n{type(cost)} {type(emoji)}")

        name = await bank.get_currency_name(ctx.guild)
        if not await bank.can_spend(ctx.author, cost):
            bal = await bank.get_balance(ctx.author)
            return await ctx.send(
                f"You can't buy that! {collectible_name} costs {cost} {name} but you only have {bal} {name}"
            )
        await bank.withdraw_credits(ctx.author, cost)
        coll_msg = f"You bought a {collectible_name} for {cost} {name}"
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

    @collectible.command(
        name="globaladd",
        aliases=[
            "gadd",
        ],
    )
    @commands.is_owner()
    async def collectible_global_add(
        self,
        ctx: commands.Context,
        name: str,
        emoji: discord.PartialEmoji,
        cost: positive_int,
    ):
        """Add a Collectible to the global list"""
        async with self.config.collectibles() as coll:
            if name in coll.keys():
                return await ctx.send(
                    f"A collectible with the name `{name}` already exists in the global cache"
                )
            coll[name] = [str(emoji), cost]
        await ctx.tick()

    @collectible.command(name="add")
    @commands.admin()
    async def collectible_guild_add(
        self,
        ctx: commands.Context,
        name: str,
        emoji: str,
        cost: positive_int,
    ):
        """Add a Collectible to your guild's cache"""
        async with self.config.guild(ctx.guild).collectibles() as coll:
            if name in coll.keys():
                return await ctx.send(
                    f"A Collectible with the name `{name}` already exists in this guild's cache"
                )
            coll[name] = [str(emoji), cost]
        await ctx.tick()

    @collectible.command(name="list")
    async def collectible_list(self, ctx: commands.Context):
        """List your Collectibles"""
        collectibles, total_count = (await self.config.user(ctx.author).all()).values()
        joined = "\n".join(f"**{coll}** {emoji}" for coll, emoji in collectibles.items())
        if await ctx.embed_requested():
            embed = discord.Embed(
                title=f"{ctx.author.name}'s Collectibles", colour=await ctx.embed_colour()
            )
            embed.description = joined
            kwargs = {"embed": embed}
        else:
            msg = f"{ctx.author.name}'s Collectibles\n"
            msg += joined
            kwargs = {"content": msg}
        await ctx.send(**kwargs)

    async def _search_collectibles(
        self, ctx: commands.Context, glob: bool, coll_name: str
    ) -> Union[None, dict]:
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

    async def _send_collectible_list(self, ctx: commands.Context):
        collectibles = await self.config.collectibles()
        guild_collectibles = None
        if ctx.guild:
            guild_collectibles = await self.config.guild(ctx.guild).collectibles()
        c_dict = {
            "Global": ", ".join(
                f"{c_name}: {emoji} {cost}"
                for c_name, (emoji, cost) in collectibles.items()
            ),
        }
        if guild_collectibles is not None:
            c_dict["Guild Collectibles"] = ", ".join(
                f"{c_name}: {emoji} {cost}"
                for c_name, (emoji, cost) in guild_collectibles.items()
            )
        if await ctx.embed_requested():
            embed = discord.Embed(
                title="Available Collectibles",
                description=f"Type `{ctx.clean_prefix}collectible buy <collectible>` to buy a collectible",
                colour=await ctx.embed_colour(),
            )
            for key, value in c_dict.items():
                embed.add_field(name=key, value=value or "No collectibles", inline=False)
            return await ctx.send(embed=embed)
        msg = "\n".join(f"**{key}**\n{value}" for key, value in c_dict.items())
        await ctx.send(msg)
