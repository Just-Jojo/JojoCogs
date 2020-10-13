from redbot.core import commands, bank
from discord import Member
from copy import copy


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def readable_dict(self, dictionary: dict):
        x = []
        for key, item in dictionary.items():
            y = "{0}: {1}".format(key, item)
            x.append(y)
        return "\n".join(x)

    @commands.group()
    async def store(self, ctx):
        """Store commmands"""

    @store.command(name="buy")
    async def _buy(self, ctx, item: str):
        stalk = {
            "coffee": 15,
            "doughnut": 10,
            "scone": 20
        }
        if item and item.lower() in stalk.keys():
            if await bank.can_spend(ctx.author, amount=stalk[item.lower()]):
                cur_name = await bank.get_currency_name(ctx.guild)
                await ctx.send("You bought a {0} for {1} {2}".format(item.lower(), stalk[item.lower()], cur_name))
        else:
            await ctx.send(self.readable_dict(stalk))
