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

    @commands.command()
    async def hunger(self, ctx, pet_name: str):
        try:
            pet = await self.config.user(ctx.author).pets.get_raw(pet_name)
        except KeyError:
            await ctx.send("You don't own that pet!")
            return
        hunger = pet.get("hunger")
        await ctx.send("Your pet has {}/100 hunger".format(hunger))

    @commands.command()
    async def feed(self, ctx, pet_name: str, food: int):
        try:
            pet = await self.config.user(ctx.author).pets.get_raw(pet_name)
        except KeyError:
            await ctx.send("You don't own that pet!")
            return

        hunger = pet.get("hunger")
        new_hunger = max(hunger - food, 0)

        await self.config.user(ctx.author).pets.set_raw(
            pet_name, "hunger", value=new_hunger
        )
        await ctx.send("Your pet is now at {}/100 hunger!".format(new_hunger))
