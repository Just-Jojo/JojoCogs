from redbot.core import commands, Config
import discord
import random
import logging

log = logging.getLogger('red.jojo.mjolnir')


class Mjolnir(commands.Cog):
    default_user = {
        "times_lifted": 0
    }
    default_guild = {
        "drop_rate": 100
    }

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 15034742, force_registration=True)
        self.config.register_user(**self.default_user)
        self.config.register_guild(**self.default_guild)

    @commands.command()
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def trylift(self, ctx):
        """Try to lift Thor's mighty hammer"""
        trylift_error = [
            "You tried your best but still lost. Fear not! There is still hope!",
            "If you wish for the power of a god, you better be worthy of it",
            "No luck just yet, try again!",
            "You'll get it! Just keep trying! I believe in you"
        ]
        rate = await self.config.guild(ctx.guild).get_raw("drop_rate")
        trylift_result = random.randint(1, rate)
        if trylift_result == rate:
            old = await self.config.user(ctx.author).get_raw('times_lifted')
            msg = "The sky opens up and a bolt of lightning strikes the ground\nYou are worthy. Hail, son of Odin"
            if rate >= 50:
                await self.config.user(ctx.author).set_raw("times_lifted", value=old + 1)
                log.info("{}({}) has lifted mjolnir".format(
                    ctx.author.name, ctx.author.id)
                )
            else:
                log.info(
                    "{} has lifted the hammer but because the drop rate was so low I will not be adding it to the leaderboard".format(
                        ctx.author.name)
                )
        else:
            msg = random.choice(trylift_error)
        await ctx.send(msg)

    @commands.command()
    @commands.mod_or_permissions(manage_guild=True)
    async def rates(self, ctx, number: int = None):
        """
        Adjust the chance for lifting Mjolnir

        *Note that if the chance for lifting it is below 50 anyone who lifts it will not be added to the leaderboard"""

        if number is not None:
            await self.config.guild(ctx.guild).set_raw("drop_rate", value=number)
            await ctx.send("The chance of lifting Mjolnir is now `{}`".format(number))
        else:
            rate = await self.config.guild(ctx.guild).get_raw("drop_rate")
            await ctx.send("The chance for lifting Mjolnir is `1/{}`".format(rate))

    @commands.command()
    async def liftedboard(self, ctx):
        """Get the leaderboard for the people who have lifted Thor's hammer"""

        board = await self.config.all_users()
        users = sorted(
            board.items(), key=lambda x: x[1]["times_lifted"], reverse=True
        )
        sen = []
        for user in users:
            name = ctx.guild.get_member(user[0]).name
            amount = user[1]["times_lifted"]
            sen.append("**{}** {}".format(name, amount))
        sending = "\n".join(sen)
        await ctx.send(sending)
