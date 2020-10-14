from redbot.core import commands, Config, bank
import discord as dis


class EconomyTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 646613323, force_registration=True)

    async def get_currency(self, ctx: commands.Context, user: dis.Member):
        x = await bank.get_balance(user)
        y = await bank.get_currency_name(ctx.guild)
        return x, y

    @commands.command()
    # , account: bool = False):
    async def balance(self, ctx, user: dis.Member = None):
        if user is None:
            user = ctx.author
        user_bal, user_bank_cur_name = await self.get_currency(ctx, user)
        await ctx.send("{0.display_name} has {1} {2}".format(user, user_bal, user_bank_cur_name))

    @commands.command()
    async def account(self, ctx, user: dis.Member = None):
        if user is None:
            user = ctx.author
        acc = await bank.get_account(user)
        await ctx.send(acc)
