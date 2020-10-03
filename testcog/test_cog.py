from redbot.core import commands


class TestCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def read(self, ctx):
        with open("test.txt", "r") as f:
            await ctx.send(f.read())
