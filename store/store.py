"""
MIT License

Copyright (c) 2020-2021 Jojo#7711

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import logging

import discord
from redbot.core import bank, commands, Config
from redbot.core.bot import Red
from redbot.core.utils import AsyncIter
from redbot.core.utils.chat_formatting import pagify

import typing

from .utils import JojoMenu, JojoPages, lowercase_str, positive_int

log = logging.getLogger("red.JojoCogs.Store")
_config_structure = {
    "member": {
        # Items is a dict with the item name and
        # the amount of that item the user has
        "items": {}
    },
    "guild": {
        "items": {
            # Every item here should have a lowercase key
            # since the cog will find an item using `str.lower`
            "coffee": 200,
            "scone": 200,
            "tea": 200,
        },
        # `base_cost` is the lowest an item can cost
        # If an item being set has a cost lower than this
        # it will be replaced with `base_cost`
        "base_cost": 200,
    },
}
# Easier type hints lol
Context = commands.Context
Requester = typing.Literal["discord_deleted_user", "owner", "user", "user_strict"]


def pagified_list(items: str):
    return list(pagify(items))


class Store(commands.Cog):
    """A fun store with item buying and trading (soonish)"""

    __version__ = "0.1.0"
    __author__ = [
        "Jojo#7791",
    ]

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, 21654654231887, True)
        self.config.register_member(**_config_structure["member"])
        self.config.register_guild(**_config_structure["guild"])

    async def red_delete_data_for_user(
        self,
        *,
        requester: Requester,
        user_id: int,
    ):
        # Most of this is from Red's Economy cog
        # however I don't clear `user` since it's not registered
        if requester != "discord_deleted_user":
            return

        all_members = await self.config.all_members()

        async for guild_id, guild_data in AsyncIter(all_members.items(), steps=100):
            if user_id in guild_data:
                await self.config.member_from_ids(guild_id, user_id).clear()

    def format_help_for_context(self, ctx):
        return (
            f"{super().format_help_for_context(ctx)}\n"
            f"**__Version__**: {self.__version__}\n"
            f"**__Author__**: {', '.join(self.__author__)}"
        )

    @commands.group()
    @commands.mod()
    async def storeset(self, ctx):
        """Base command for the store's settings"""
        pass

    @storeset.command()
    async def additem(self, ctx, cost: positive_int, *, item: lowercase_str):
        """Add an item to the store"""
        if await self._check_item(ctx, item):
            await ctx.send("That item already exists!")
        else:
            cost = await self._check_cost(ctx, cost)
            name = await bank.get_currency_name(ctx.guild)
            msg = f"The item `{item}` has been added to the store for {cost} {name}"
            await ctx.send(content=msg)
            async with self.config.guild(ctx.guild).items() as items:
                items[item] = cost

    @storeset.command(aliases=["del", "removeitem", "remove"])
    async def delitem(self, ctx, *, item: lowercase_str):
        """Remove an item from the store"""
        if not await self._check_item(ctx, item):
            await ctx.send("Hm, that item doesn't seem to exist!")
        else:
            msg = f"Removed `{item}` from the store!"
            await ctx.send(content=msg)
            async with self.config.guild(ctx.guild).items() as items:
                del items[item]

    @storeset.command()
    async def default(self, ctx, cost: positive_int):
        """Set the default cost for items"""
        name = await bank.get_currency_name(ctx.guild)
        msg = f"The default cost for items is now {cost} {name}"
        await ctx.send(content=msg)
        await self.config.guild(ctx.guild).base_cost.set(cost)

    @commands.group(invoke_without_command=True)
    async def store(self, ctx):
        """Base command for the store!"""
        embed = discord.Embed(
            title=f"Welcome Ye Ol {ctx.guild.name} Store!",
            description=f"Welcome to my Store! What'll it be?",
            colour=await ctx.embed_colour(),
        )
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.set_author(name="Jojo")
        for key, value in {
            "Shop": "Buy some items from Ol' Jo",
            "List": "Browse the store for some items ye may want",
        }.items():
            embed.add_field(name=key, value=value, inline=False)
        embed.set_footer(text="Jojo's Store!")
        await ctx.send(embed=embed)

    @store.command()
    async def buy(self, ctx, *, item: lowercase_str):
        """Buy an item from the store!"""
        if not await self._check_item(ctx, item):
            await ctx.send("Hm, that doesn't seem to be an item!")
        else:
            cost = await self.config.guild(ctx.guild).items.get_raw(item)
            msg = await self.bank_logic(ctx, item, cost)
            await ctx.send(content=msg)

    @store.command(
        aliases=[
            "list",
        ]
    )
    async def itemlist(self, ctx):
        """List the avaiable items from the store"""
        embed = discord.Embed(
            title="Jojo's Store's stock",
            description="I have all these fine items for you",
            colour=await ctx.embed_colour(),
        )
        embed.set_author(name="Jojo")
        async with self.config.guild(ctx.guild).items() as items:
            for key, value in items.items():
                embed.add_field(
                    name=self._capitalize_all(key), value=value, inline=True
                )
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.set_footer(text="Jojo's Store!")
        await ctx.send(embed=embed)

    async def bank_logic(self, ctx: Context, item: str, cost: int) -> str:
        """Logistics for the bank stuff"""
        if await bank.can_spend(ctx.author, cost):
            member_conf = await self.config.member(ctx.author).items()
            am = member_conf.get(item, False)
            if am is False:
                await self.config.member(ctx.author).items.set_raw(item, value=1)
            else:
                await self.config.member(ctx.author).items.set_raw(item, value=am + 1)
            await bank.withdraw_credits(ctx.author, cost)
            return f"You bought a {item} for {cost} {await bank.get_currency_name(ctx.guild)}"
        else:
            name = await bank.get_currency_name(guild=ctx.guild)
            return f"Whoops! You don't have enough {name} to buy that item!"

    async def page_logic(self, ctx: Context, data: list):
        """Logic for menus"""
        data = "\n".join(data)
        menu = JojoMenu(
            source=JojoPages(pagified_list(data)),
            timeout=15.0,
            delete_message_after=False,
            clear_reactions_after=True,
            message=None,
            page_start=0,
        )
        await menu.start(ctx=ctx, channel=ctx.channel, wait=False)

    def _capitalize_all(self, data: str):
        return " ".join([x.capitalize() for x in data.split()])

    async def _check_item(self, ctx: Context, item: str) -> bool:
        items = await self.config.guild(ctx.guild).items()
        if items.get(item, None) is not None:
            return True
        return False

    async def _check_cost(self, ctx: Context, cost: int) -> int:
        default = await self.config.guild(ctx.guild).base_cost()
        if cost < default:
            return default
        return cost

    async def cog_check(self, ctx: Context):
        """Guild only cog check"""
        return ctx.guild is not None
