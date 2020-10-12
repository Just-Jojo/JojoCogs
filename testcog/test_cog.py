from redbot.core import commands, Config, bank


class TestCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 2958485)
        self.config.register_global(
            dog=30,
            cat=35,
            birb=40
        )
        self.config.register_user(
            pets={}
        )

    @commands.command()
    async def buy_pet(self, ctx, pet_type: str, pet_name: str):
        try:
            cost = await self.config.get_raw(pet_type)
        except KeyError:
            await ctx.send("I could not find that pet!")
            return

        if await bank.can_spend(ctx.author, cost):
            await self.config.user(ctx.author).pets.set_raw(
                pet_name, value={"cost": cost, "hunger": 0}
            )
            await ctx.send("You have purchased a {0} and called it {1}".format(pet_type, pet_name))
        else:
            await ctx.send("You do not have enough money to buy that pet!")
