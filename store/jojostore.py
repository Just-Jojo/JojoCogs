import asyncio
import logging
from typing import Literal

import discord
from redbot.core import Config, bank, commands, modlog
from redbot.core.utils import menus

from .embed_maker import Embed

log = logging.getLogger('red.jojo.fun')


class JojoStore(commands.Cog):
    """A Store designed by Jojo for Red.

    Have fun!"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 13814755994)
        self.config.register_guild(
            items={
                "coffee": 100,
                "scone": 150,
                "tea": 100
            },
            roles={}
        )
        self.config.register_user(items={})
        self.embed = Embed(self)

    __version__ = "1.0.0"

    async def red_delete_data_for_user(
        self,
        requester: Literal["discord", "owner", "user", "user_strict"],
        user_id: int
    ) -> None:
        await self.config.user_from_id(user_id).clear()

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        roles_list = await self.config.guild(role.guild).roles.get_raw()
        if role.name in roles_list.keys():
            await self.config.guild(role.guild).roles.clear_raw(role)

    @commands.group()
    @commands.guild_only()
    async def store(self, ctx):
        """Store commmands"""

    @store.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def add(self, ctx, item: str, cost: int = 250):
        """Add an item to the store"""
        await self.config.guild(ctx.guild).set_raw(item, value=cost)
        await ctx.send("{0} can now be bought with {1} credits".format(item, cost))

    @store.command(name="remove", aliases=["del", ])
    @commands.admin()
    async def _remove(self, ctx, *, item: str):
        """Remove an item from the store"""
        try:
            await self.config.guild(ctx.guild).items.clear_raw(item)
            await ctx.send("I removed {} from the store".format(item))
        except:
            await ctx.send("I could not remove that item!")

    @store.command(name="list")
    async def _list(self, ctx):
        """List all of the purchasable items in your guild's store"""
        items = await self.config.guild(ctx.guild).items.get_raw()
        if items:
            await self.page_logic(ctx, items, "{}'s Store".format(ctx.guild.name))
        else:
            await ctx.send("Your guild does not have any purchasable items!\nTo get some items, have an admin run `[p]store add <item> [cost]`")

    @store.command(name="buy")
    async def _buy(self, ctx, item: str = None):
        """Purchase an item from the store"""
        item_list = await self.config.guild(ctx.guild).items.get_raw()
        if item is not None:
            try:
                cost = await self.config.guild(ctx.guild).items.get_raw(item)
            except KeyError:
                await self.page_logic(ctx, item_list, "{}'s Store".format(ctx.guild.name))

            cur_name, old_bal = await self.bank_utils(ctx, ctx.author)
            if await bank.can_spend(ctx.author, cost):
                try:
                    item_lists = await self.config.user(ctx.author).items.get_raw(item)
                except KeyError:
                    item_lists = 0
                item_lists += 1
                await self.config.user(ctx.author).items.set_raw(item, value=item_lists)
                if item_lists != 1:
                    msg = "You bought a {0} for {1} {2}!\nYou have {3} {0}s!".format(
                        item, cost, cur_name, item_lists)
                else:
                    msg = "You bought a {0} for {1} {2}!\nYou have 1 {0}!".format(
                        item, cost, cur_name)

                await ctx.send(msg)
                await bank.set_balance(ctx.author, old_bal - cost)
            else:
                await ctx.send("You can't buy {0}! You don't have enough {1} to buy it!".format(item, cur_name))
        else:
            await self.page_logic(ctx, item_list, "{}'s Store".format(ctx.guild.name))

    @commands.command()
    async def use(self, ctx, item: str):
        """Use an item
        This only works if you have the item in your inventory
        """
        try:
            check_item = await self.config.user(ctx.author).items.get_raw(item)
            if check_item > 0:
                check_item -= 1
                await self.config.user(ctx.author).items.set_raw(item, value=check_item)
                await ctx.send("You used a {0}!\nYou have {1} remaining!".format(item, check_item))
            else:
                await ctx.send("You do not have that item!")
        except KeyError:
            items_ = await self.config.user(ctx.author).items.get_raw()
            await self.page_logic(ctx, items_, "{}'s Items".format(ctx.author.display_name))

    @commands.command()
    async def items(self, ctx):
        """List all of your items in a clean embed"""
        items_ = await self.config.user(ctx.author).items.get_raw()
        if items_:
            await self.page_logic(ctx, items_, "{}'s Store items".format(ctx.guild.name), 10)
        else:
            await ctx.send("You do not have any items!\nYou can buy some using `[p]store buy`")

    @commands.command(name="paidkick")
    @bank.cost(5000)
    async def kick_fun(self, ctx, user: discord.Member = None):
        """Ever been mad at a member but never could get them kicked?
        well now you don't have to wait for a mod!"""
        if user is None:
            raise bank.AbortPurchase
        if user is ctx.author:
            await ctx.send("I cannot let you do that. Self-harm is bad :pensive:")
            raise bank.AbortPurchase
        try:
            await ctx.guild.kick(user)
            _ = await modlog.create_case(
                ctx.bot, ctx.guild, ctx.message.created_at, action_type="kick",
                user=user, moderator=ctx.author, reason="{0.display_name} has redeemed a kick command and used it on {1}!".format(
                    ctx.author, user)
            )
            await ctx.send("Done. It was about time")
        except discord.Forbidden:
            await ctx.send("I could not kick that member!")
            raise bank.AbortPurchase

    @commands.group()
    @commands.guild_only()
    async def role(self, ctx):
        """Base role command

        This allows you to buy certain roles for credits"""

    @role.command(name="add")
    @commands.admin()
    async def _add(self, ctx, *, role: discord.Role, cost: int = 3000):
        """Add a purchasable role"""
        await self.config.guild(ctx.guild).roles.set_raw(role, value=cost)
        name = await bank.get_currency_name(ctx.guild)
        await ctx.send("{0} can now be bought for {1} {2}".format(role, cost, name))

    @role.command(aliases=["del", ])
    @commands.admin()
    async def remove(self, ctx, *, role):
        """Remove a buyable role"""
        try:
            await self.config.guild(ctx.guild).roles.clear_raw(role)
            await ctx.send("Removed {} from the store".format(role))
        except KeyError:
            await ctx.send("I couldn't find that role")

    @role.command()
    async def buy(self, ctx, *, role: discord.Role):
        """Buy a role with credits"""
        try:
            role_cost = await self.config.guild(ctx.guild).roles.get_raw(role)
        except KeyError:
            return await ctx.send("I could not find that role!")

        if await bank.can_spend(ctx.author, role_cost):
            try:
                await ctx.author.add_roles(role)
                await bank.withdraw_credits(ctx.author, role_cost)
                await ctx.send("You have sucessfully bought that role!")
            except discord.Forbidden:
                await ctx.send("I could not attach that role!")

    @role.command(name="list")
    async def rlist(self, ctx):
        """List all of the role that are purchasable in a guild"""
        roles = await self.config.guild(ctx.guild).roles.get_raw()
        if roles:
            await self.page_logic(ctx, roles, "{}'s Roles".format(ctx.guild.name))
        else:
            await ctx.send("This guild doesn't have any roles!\nTo add some buyable roles, please ask an admin to create one using `[p]role add`")

    @commands.command(aliases=["sinfo"])
    async def storeinfo(self, ctx):
        """Get the info on the Store cog"""
        app = await self.bot.application_info()
        msg = "Jojo's store, a cog designed for fun with the bank system.\nVersion: {}".format(
            self.__version__)
        emb = Embed.create(
            self, ctx, title="Jojo's Store Cog", description=msg, thumbnail=app.owner.avatar_url,
            footer="Cog designed by {}".format(app.owner.name), footer_url=app.owner.avatar_url
        )
        await ctx.send(embed=emb)

    async def bank_utils(self, ctx: commands.Context, user: discord.Member = None) -> str:
        """Returns the name of the bank's currency and can optionally return the balance of a member"""
        name = await bank.get_currency_name(ctx.guild)
        if user is not None:
            balance = await bank.get_balance(ctx.author)
            return name, balance
        return name

    # You don't know this but this single fucking function took me so long to make that I think my brain will never recover
    async def page_logic(self, ctx: commands.Context, dictionary: dict, item: str, field_num: int = 15) -> None:
        """Convert a dictionary into a pagified embed"""
        embeds = []
        count = 0
        title = item
        embed = self.embed.create(
            ctx, title=title, thumbnail=ctx.guild.icon_url)

        for key, value in dictionary.items():
            if count == field_num - 1:
                embed.add_field(name=key, value=value, inline=True)
                embeds.append(embed)

                embed = self.embed.create(
                    ctx, title=title, thumbnail=ctx.guild.icon_url)
                count = 0
            else:
                embed.add_field(name=key, value=value, inline=True)
                count += 1
        else:
            embeds.append(embed)

        msg = await ctx.send(embed=embeds[0])
        control = menus.DEFAULT_CONTROLS if len(embeds) > 1 else {
            "\N{CROSS MARK}": menus.close_menu
        }
        asyncio.create_task(menus.menu(ctx, embeds, control, message=msg))
        menus.start_adding_reactions(msg, control.keys())
