from redbot.core import commands
from discord import Member
from copy import copy


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def coffee(self, ctx):
        await ctx.send("☕")

    @commands.command()
    async def read_from_file(self, ctx):
        with open("something.txt", "r") as f:
            something_txt = f.read()
        await ctx.send("Found this in the file: {0}".format(something_txt))
