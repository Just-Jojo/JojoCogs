from redbot.core import commands
from discord import Member
from copy import copy


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def coffee(self, ctx):
        await ctx.send("☕")
