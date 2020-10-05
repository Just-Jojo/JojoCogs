from redbot.core import commands


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def coffee(self, ctx):
        await ctx.send("☕")
