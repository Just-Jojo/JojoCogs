from redbot.core import commands, Config, bank


class TestCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def _test(self, ctx):
        await ctx.send(ctx.bot.name)
