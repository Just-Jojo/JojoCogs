from redbot.core import commands, checks
import discord
from copy import copy


class Dev(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @checks.is_owner()
    async def mock(self, ctx, user: discord.Member, *, command):
        """Mock another user invoking a command.
        The prefix must not be entered.
        """
        print("This is working")
        msg = copy(ctx.message)
        msg.author = user
        msg.content = ctx.prefix + command

        ctx.bot.dispatch("message", msg)
