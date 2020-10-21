from redbot.core import commands, bank, Config, modlog
from redbot.core import checks
import discord


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 13814755994)
        self.config.register_guild(
            coffee=10,
            scone=15,
            doughnut=9
        )
        self.config.register_user(items={})

    def readable_dict(self, dictionary: dict) -> str:
        """Convert a dictionary into something a regular person could read"""
        x = []
        for key, item in dictionary.items():
            y = "{0}: {1}".format(key, item)
            x.append(y)
        return "\n".join(x)

    async def bank_utils(self, ctx: commands.Context, user: discord.Member = None):
        """Returns the name of the bank's currency and can optionally return the balance of a member

        Args:
            ctx (commands.Context): Needed for the guild to get the bank credit
            user (Member, optional): Optional to get the balance of a user. Defaults to None.

        Returns:
            str, int (optional)
        """
        name = await bank.get_currency_name(ctx.guild)
        if user is not None:
            balance = await bank.get_balance(ctx.author)
            return name, balance
        return name

    @commands.group()
    async def store(self, ctx):
        """Store commmands"""

    @store.command(name="buy")
    async def _buy(self, ctx, item: str):
        """Purchase an item from the store"""
        if item:
            try:
                cost = await self.config.guild(ctx.guild).get_raw(item)
            except KeyError:
                await ctx.send("I could not find that item!")
                return

            if await bank.can_spend(ctx.author, cost):
                cur_name, old_bal = await self.bank_utils(ctx, ctx.author)
                new_bal = old_bal - cost
                await self.config.user(ctx.author).items.set_raw(item, value=cost)
                await ctx.send("You bought a {0} for {1} {2}!".format(item, cost, cur_name))
                await bank.set_balance(ctx.author, new_bal)
            else:
                await ctx.send("You can't buy {0}! You don't have enough {1} to buy it!".format(item, cur_name))
        else:
            item_list = self.readable_dict(await self.config.guild(ctx.guild).get_raw())
            await ctx.send("Here are the items you can purchase in this guild: {0}".format(item_list))

    @commands.command(name="storeclear")
    @checks.is_owner()
    async def clear_store(self, ctx):
        """Clear out the store of items"""
        await self.config.clear()
        await ctx.send("Cleared the store")

    @commands.command(name="useitem", aliases=["use", "item"])
    async def use_item(self, ctx, item: str):
        try:
            check_item = await self.config.user(ctx.author).items.get_raw(item)
            if check_item:
                await self.config.user(ctx.author).items.clear_raw(item)
                await ctx.send("You used a {}!".format(item))
            else:
                await ctx.send("You do not have that item!")
        except:
            await ctx.send("You could not use that item!")

    @commands.command()
    async def items(self, ctx):
        items_ = await self.config.user(ctx.author).items.get_raw()
        if items_:
            await ctx.send("You have\n{0}".format(self.readable_dict(items_)))
        else:
            await ctx.send("You do not have any items!\nYou can buy some using `[p]store buy`")

    @commands.command(name="paidkick")
    @bank.cost(5000)
    async def kick_fun(self, ctx, user: discord.Member = None):
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
