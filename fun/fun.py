from redbot.core import commands, bank, Config
from redbot.core import checks
from discord import Member


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

    def readable_dict(self, dictionary: dict):
        x = []
        for key, item in dictionary.items():
            y = "{0}: {1}".format(key, item)
            x.append(y)
        return "\n".join(x)

    async def bank_utils(self, ctx: commands.Context, user: Member = None):
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

    @commands.command(name="storeclear")
    @checks.is_owner()
    async def clear_store(self, ctx):
        await self.config.clear()
        await ctx.send("Cleared the store")

    @commands.command(name="useitem", aliases=["use", "item"])
    async def use_item(self, ctx, item: str):
        # try:
        await self.config.user(ctx.author).items.clear_raw(item)
        await ctx.send("You used a {}!".format(item))
        # except:
        #     await ctx.send("You could not use that item!")
