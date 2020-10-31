from redbot.core import commands, Config
import discord
import random


class Mjolnir(commands.Cog):
    default_user = {
        "times_lifted": 0
    }

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 15034742, force_registration=True)
        self.config.register_user(**self.default_user)

    @commands.command()
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def trylift(self, ctx):
        trylift_error = [
            "You tried your best but still lost. Fear not! There is still hope!",
            "If you wish for the power of a god, you better be worthy of it",
            "No luck just yet, try again!",
            "You'll get it! Just keep trying! I believe in you"
        ]
        trylift_result = random.randint(1, 300)
        if trylift_result == 300:
            old = await self.config.user(ctx.author).get_raw('times_lifted')
            msg = "The sky opens up and a bolt of lightning strikes the ground\nYou are worthy. Hail, son of Odin"
            await self.config.user(ctx.author).set_raw("times_lifted", value=old + 1)
        else:
            msg = random.choice(trylift_error)
        await ctx.send(msg)

    @commands.command()
    async def liftedboard(self, ctx):
        """Get the leaderboard for the people who have lifted Thor's hammer"""
        lb = await self.config.all_users()
        list_leadered = []
        for item in sorted(lb.items(), key=lambda p: p[1]):
            list_leadered.append("**{0}**: {1}".format(*item))
        await ctx.send("\n".join(list_leadered))
