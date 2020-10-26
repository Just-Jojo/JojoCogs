from redbot.core import commands
import random


class Mjolnir(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def trylift(self, ctx):
        trylift_error = [
            "You tried your best but still lost. Fear not! There is still hope!",
            "If you wish for the power of a god, you better be worthy of it",
            "No luck just yet, try again!"
        ]
        trylift_result = random.randint(1, 300)
        if trylift_result == 300:
            msg = "The sky opens up and a bolt of lightning strikes the ground\nYou are worthy. Hail, son of Odin"
        else:
            msg = random.choice(trylift_error)
        await ctx.send(msg)
