from redbot.core import commands, bank, Config
from redbot.core import checks
from discord import Member


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 13814755994)

        self.config.register_member(
            items={
                "coffee": 0,
                "dougnut": 0,
                "scone": 0
            }
        )  # **_default_user)

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
                up = await self.config.user(ctx.author).items.get_raw(item.lower())
                upd = up + 1
                await self.config.user(ctx.author).items.set_raw(item.lower(), upd)
                await ctx.send("You bought a {0} for {1} {2}".format(item.lower(), stalk[item.lower()], cur_name))
        else:
            await ctx.send(self.readable_dict(stalk))

    @commands.command(name="storeclear")
    @checks.is_owner()
    async def clear_store(self, ctx):
        await self.config.clear()
        await ctx.send("Cleared the store")
