from redbot.core import commands, bank, Config, modlog
from redbot.core.utils import menus
import discord
from .embed_maker import Embed
import asyncio
import logging

log = logging.getLogger('red.jojo.fun')


class Fun(commands.Cog):
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
    async def add(self, ctx, item: str = None, cost: int = None):
        """Add an item to the store"""
        if item is None:
            return await ctx.send("Please name the item you would like to add")
        if cost is None:
            cost = 250
        await self.config.guild(ctx.guild).set_raw(item, value=cost)
        await ctx.send("{0} can now be bought with {1} credits".format(item, cost))

    @store.command(name="remove", aliases=["del", ])
    @commands.admin()
    async def _remove(self, ctx, *, item: str = None):
        """Remove an item from the store"""
        if item is None:
            return await ctx.send("You need to input an item for me to remove!")
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
            await self.page_logic(ctx, items)
        else:
            await ctx.send("Your guild does not have any purchasable items!\nTo get some items, have an admin run `[p]store add <item> [cost]`")

    @store.command(name="buy")
    async def _buy(self, ctx, item: str = None):
        """Purchase an item from the store"""
        if item is not None:
            try:
                cost = await self.config.guild(ctx.guild).items.get_raw(item)
            except KeyError:
                await ctx.send("I could not find that item!")
                return

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
            item_list = await self.config.guild(ctx.guild).items.get_raw()
            await self.page_logic(ctx, item_list)

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
            await self.page_logic(ctx, items_)

    @commands.command()
    async def items(self, ctx):
        """List all of your items in a clean embed"""
        items_ = await self.config.user(ctx.author).items.get_raw()
        if items_:
            await self.page_logic(ctx, items_, 10)
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
            await self.page_logic(ctx, roles)
        else:
            await ctx.send("This guild doesn't have any roles!\nTo add some buyable roles, please ask an admin to create one using `[p]role add`")

    @commands.command()
    @commands.is_owner()
    async def testing(self, ctx):
        embeds = []
        for i in range(10):
            emb = Embed.create(self, ctx, title="{} embed".format(i))
            embeds.append(emb)
        msg = await ctx.send(embed=embeds[0])
        c = menus.DEFAULT_CONTROLS if len(embeds) > 1 else {
            "\N{CROSS MARK}": menus.close_menu}
        asyncio.create_task(menus.menu(ctx, embeds, c, message=msg))
        menus.start_adding_reactions(msg, c.keys())

    def readable_dict(self, dictionary: dict, numbered: bool = False) -> str:
        """Convert a dictionary into something a regular person could read"""
        readable = []
        for num, (key, item) in enumerate(dictionary.items()):
            if numbered is True:
                string_version = "{0}. {1}: {2}".format(num, key, item)
            else:
                string_version = "{0}: {1}".format(key, item)
            readable.append(string_version)
        return "\n".join(readable)

    async def bank_utils(self, ctx: commands.Context, user: discord.Member = None) -> str:
        """Returns the name of the bank's currency and can optionally return the balance of a member"""
        name = await bank.get_currency_name(ctx.guild)
        if user is not None:
            balance = await bank.get_balance(ctx.author)
            return name, balance
        return name

    @commands.command()
    @commands.is_owner()
    async def pages(self, ctx):
        x = {"Test": 34, "Vanguards": 30, "Vanesrseguards": 30, "Vangersuards": 30, "Vanserguards": 30, "Vangdgesuards": 30, "Vanguargdds": 30, "Vangzuards": 30,
             "Vnguards": 30, "Vangusards": 30, "Vangfuards": 30, "Vandguards": 30, "Vangauards": 30, "Vangguards": 30, "Vangeuards": 30, "Vanguardsfds": 30, "Vansdfsdfguards": 30, "Vanguasdfsdfsrds": 30, "Vansefsdfweguards": 30, "Vanguardssdfsdf": 30,  "Vangsdfsdfsuards": 30, "Vanguarsdfsdfds": 30, "Vangdsfsuards": 30, }
        await self.page_logic(ctx, x)

    async def page_logic(self, ctx: commands.Context, dictionary: dict, field_num: int = 15) -> None:
        embeds = []
        count = 0
        title = "{}'s Collectables".format(ctx.guild.name)
        embed = self.embed.create(
            ctx, title=title, thumbnail=ctx.guild.icon_url)

        if len(dictionary.keys()) > field_num:
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
        else:
            for key, value in dictionary.items():
                embed.add_field(name=key, value=value, inline=True)
            embeds.append(embed)

        msg = await ctx.send(embed=embeds[0])
        control = menus.DEFAULT_CONTROLS if len(embeds) > 1 else {
            "\N{CROSS MARK}": menus.close_menu
        }
        asyncio.create_task(menus.menu(ctx, embeds, control, message=msg))
        menus.start_adding_reactions(msg, control.keys())
