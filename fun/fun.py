from redbot.core import commands
from discord import Member
from copy import copy


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def coffee(self, ctx):
        await ctx.send("☕")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def sudo(self, ctx, user: Member, *, command):
        """Sudo another user invoking a command.
        The prefix must not be entered.
        """
        msg = copy(ctx.message)
        msg.author = user
        msg.content = ctx.prefix + command

        ctx.bot.dispatch("message", msg)
