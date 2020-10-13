from redbot.core import commands, Config, bank
import discord as dis


class EconomyTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 646613323, force_registration=True)

    @commands.command()
    async def balance(self, ctx, user: dis.Member = None):
        if user is None:
            user = ctx.author
        await ctx.send(await bank.get_balance(user))
