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

        user_bal = await bank.get_balance(user)
        user_bank_currency_name = await bank.get_currency_name(ctx.guild)
        await ctx.send("{0.display_name} has {1} {2}".format(user, user_bal, user_bank_currency_name))
