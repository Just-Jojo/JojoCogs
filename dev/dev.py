from redbot.core import commands
from discord import Member
from copy import copy


class Dev(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="sudo", aliases=["mock"])
    @commands.is_owner()
    async def _mock(self, ctx, user: Member, *, command):
        msg = copy(ctx.message)
        msg.author = user
        msg.content = ctx.prefix + command

        ctx.bot.dispatch("message", msg)
