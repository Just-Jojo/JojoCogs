import asyncio
import logging
import typing

import discord
from redbot.core import Config, bank, commands, modlog
from redbot.core.bot import Red  # Type hinting
from redbot.core.utils import menus, predicates
from redbot.core.utils.chat_formatting import pagify
from .utils import JojoMenu, JojoPages

log = logging.getLogger('red.jojo.fun')


class JojoStore(commands.Cog):
    """A Store designed by Jojo for Red.

    Have fun!"""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, 13814755994)
        self.config.register_guild(
            items={
                "coffee": 100,
                "scone": 150,
                "tea": 100
            },
            default_cost=300
        )
        self.config.register_member(items={})

    __version__ = "1.1.0"

    async def red_delete_data_for_user(
        self,
        requester: typing.Literal["discord", "owner", "user", "user_strict"],
        user_id: int
    ) -> None:
        await self.config.user_from_id(user_id).clear()

    @commands.group()
    async def store(self, ctx):
        """Store commands!"""
        pass

    @store.command(name="list")
    async def store_list(self, ctx):
        """List all the purchasable items in the store"""
        items = await self.config.guild(ctx.guild).get_raw("items")
        if not items:
            return await ctx.send("Hm, looks like this guild doesn't have any items!")
        items = "\n".join([f"**{k}:** {v}" for k, v in items.items()])
        menu = JojoMenu(source=JojoPages(
            data=list(pagify(items, page_length=50))))
        await menu.start(ctx=ctx, channel=ctx.channel)

    @store.command()
    async def buy(self, ctx, item: str):
        """Buy an item from the store!"""
        item = item.lower()  # DON'T have case sensitive items
        guild_items = await self.config.guild(guild=ctx.guild).items()
        found = guild_items.get(item, False)
        if found is False:
            return await ctx.send("I could not find that item!")
        if await bank.can_spend(member=ctx.author, amount=found):
            user_items = await self.config.member(member=ctx.author).items()
            amount = user_items.get(item)
            if amount is None:
                user_items[item] = 1
            else:
                user_items[item] += 1
            await self.config.member(ctx.author).items.set(user_items)
            await ctx.send(f"You bought a {item.capitalize()} for {found}!")
            await bank.withdraw_credits(member=ctx.author, amount=found)
        else:
            await ctx.send("You did not have enough for that item!")

    @store.command()
    @commands.mod()
    async def stock(self, ctx, item: str, cost: int):
        """Add an item to the stockpile"""
        item = item.lower()  # DO NOT have case sensitive items
        default_cost = await self.config.guild(ctx.guild).default_cost()
        if cost < default_cost:
            cost = default_cost
        guild_items = await self.config.guild(ctx.guild).items()
        if item in guild_items.keys():
            await ctx.send("This item already exists! Would you like to edit it's cost? (y/n)")
            pred = predicates.MessagePredicate.yes_or_no(
                ctx=ctx, channel=ctx.channel, user=ctx.author)
            try:
                answer = await self.bot.wait_for("message", check=pred)
            except asyncio.TimeoutError:
                return await ctx.send("Alright, I won't edit the cost")
            if pred.result:
                guild_items[item] = cost
                await self.config.guild(ctx.guild).items.set(guild_items)
                return await ctx.send(f"`{item}` now has a cost of {cost}!")
            else:
                return await ctx.send("Alright, I won't edit the cost")
        guild_items[item] = cost
        await self.config.guild(ctx.guild).items.set(guild_items)
        await ctx.send(f"`{item}` has been added at a cost of {cost}!")

    @store.command()
    @commands.mod()
    async def remove(self, ctx, item: str):
        """Remove an item from the stockpile"""
        item = item.lower()
        items = await self.config.guild(ctx.guild).items()
        try:
            items.pop(item)
        except KeyError:
            return await ctx.send("Hm, that didn't seem to be an item")
        await self.config.guild(ctx.guild).items.set(items)
        await ctx.send(f"Removed `{item.capitalize()}` from the stockpile")

    @commands.group(invoke_without_command=True)
    async def item(self, ctx, item: str, user: discord.Member = None):
        """Commands working with user items!"""
        if user is None:
            user = ctx.author
        item = item.lower()
        items = await self.config.member(user).items()
        found = items.get(item, False)
        desc, state = self.desc_parser(
            amount=found, user=user, author=ctx.author)
        if state is False:
            return await ctx.send(desc)
        if item == 1:
            desc += f" {item}!"
        elif item > 0:
            desc += f" {item}s!"

        embed = self.create_embed(
            ctx=ctx, title=f"{ctx.author.name}'s Items!", description=desc)
        await ctx.send(embed=embed)

    def desc_parser(self, amount: typing.Union[bool, int], user: discord.Member, author: discord.Member) -> typing.Tuple[str, bool]:
        if amount is False or amount == 0:
            return f"Hm, {user.name} doesn't seem to have that item" if user != author else\
                "Hm, you don't seem to have that item", False
        else:
            return f"{user.name} has {amount}", True

    @item.command(name="list")
    async def item_list(self, ctx):
        items = await self.config.member(member=ctx.author).items()
        if not items:
            return await ctx.send("Hm, you don't seem to have any items")
        items = "\n".join([f"**{k}:** {v}" for k, v in items.items()])
        menu = JojoMenu(source=JojoPages(
            data=list(pagify(items))))
        await menu.start(ctx=ctx, channel=ctx.channel)

    @item.command()
    async def use(self, ctx, item: str):
        """Use an item. This will remove 1 of that item from your inventory"""
        item = item.lower()
        items = await self.config.member(member=ctx.author).items()
        found = items.get(item, False)
        if found is False or found == 0:
            return await ctx.send("Hm, you don't seem to have that item")
        found -= 1
        items[item] = found
        await ctx.send(f"*consuming noises* you used a {item.capitalize()}! You have {found} left!")
        await self.config.member(ctx.author).items.set(items)

    async def cog_check(self, ctx: commands.Context):
        """|coro|

        A check for the cog to make commands guild only as they can only be used in guilds
        """
        return ctx.guild is not None

    def create_embed(
        self, ctx: commands.Context, title: str = None, description: str = None,
        colour: discord.Colour = None, author: str = None, author_url: str = None,
        footer: str = None, footer_url: str = None
    ) -> discord.Embed:
        r"""Create a custom Discord embed

        Parameters
        ----------
        ctx: :class:`Context`
            Context for the embed giving colour, guild, and other details
        title: Optional[:class:`str`]
            The (optional) title for the embed
            If None the embed's title won't be set
        description: Optional[:class:`str`]
            The (optional) description for the embed
            As with the title, if not set the embed's description won't be set
        colour: Optional[:class:`Colour`]
            The colour of the embed
            If None there will be a check to see if the guild isn't None or the author doesn't have a 'blank' colour
        author: Optional[:class:`str`]
            The name for the author
            If None it will default to the Context's author's name
        author_url: Optional[:class:`str`]
            The url for the author icon
            If None it will default to the Context's author's icon url
        footer: Optional[:class:`str`]
            The footer of the embed
            If None it will default to the bot's name plus "Embed"
        footer_url: Optional[:class:`str`]
            The icon url for the footer
            If None it will default to the bot's icon url
        """
        ret = discord.Embed()
        if colour is None or not isinstance(colour, discord.Colour):
            if ctx.guild is None or str(ctx.author.colour) == "#000000":
                ret.colour = ctx.embed_color()
            else:
                ret.colour = ctx.author.colour
        else:
            ret.colour = colour
        if title is not None:
            ret.title = title
        if description is not None:
            ret.description = description

        if author is None:
            author = ctx.author.name
        if author_url is None:
            author_url = ctx.author.avatar_url

        if footer is None:
            footer = f"{self.bot.user.name} Embed"
        if footer_url is None:
            footer_url = self.bot.user.avatar_url
        ret.set_author(name=author, icon_url=author_url)
        ret.set_footer(text=footer, icon_url=footer_url)
        return ret
