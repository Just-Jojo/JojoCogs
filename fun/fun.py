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
        self.config.register_user(
            pets={}
        )

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
        try:
            cost = await self.config.guild(ctx.guild).get_raw(item)
        except KeyError:
            await ctx.send("I could not find that item!")
            return
        if await bank.can_spend(ctx.author, cost):
            await self.config.user(ctx.author).pets.set_raw(
                item, value={"cost": cost, "hunger points": 0}
            )
            # await ctx.send("You have purchased a {0} and called it {1}".format(pet_type, pet_name))
            # await self.update_balance(ctx.author, cost)
        else:
            await ctx.send("You do not have enough money to buy that pet!")

    @commands.command(name="storeclear")
    @checks.is_owner()
    async def clear_store(self, ctx):
        await self.config.clear()
        await ctx.send("Cleared the store")
