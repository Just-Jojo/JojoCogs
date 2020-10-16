from redbot.core import commands, bank, Config
from typing import Literal
from redbot.core.utils import AsyncIter
import random
import discord


class JojoEconomy(commands.Cog):
    default_guild_settings = {
        "PAYDAY_TIME": 100,
        "REGISTER_CREDITS": 100,
        "PAYDAY_CREDITS": 120
    }
    default_global_settings = default_guild_settings
    default_member_settings = {"next_payday": 0}
    default_role_settings = {"PAYDAY_CREDITS": 0}
    default_user_settings = default_member_settings

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 6472514, force_registration=True)
        self.config.register_global(**self.default_global_settings)
        self.config.register_guild(**self.default_guild_settings)
        self.config.register_member(**self.default_member_settings)
        self.config.register_user(**self.default_user_settings)
        self.config.register_role(**self.default_role_settings)

    async def red_delete_data_for_user(
        self,
        *,
        requester: Literal["discord_deleted_user", "owner", "user", "user_strict"],
        user_id: int,
    ):
        if requester != "discord_deleted_user":
            return

        await self.config.user_from_id(user_id).clear()

        all_members = await self.config.all_members()

        async for guild_id, guild_data in AsyncIter(all_members.items(), steps=100):
            if user_id in guild_data:
                await self.config.member_from_ids(guild_id, user_id).clear()

    @commands.command()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def work(self, ctx):
        payday_amount = self.config.PAYDAY_CREDITS
        name = await bank.get_currency_name(ctx.guild)
        await bank.set_balance(ctx.author, payday_amount)
        await ctx.send("You got {0} {1}".format(payday_amount, name))

    @commands.command()
    async def steal(self, ctx, user: discord.Member):
        name = await bank.get_currency_name(ctx.guild)
        flip = random.choice([True, False])
        if flip is True:
            user_credits = await bank.get_balance(user)
            steal_amount = random.randint(100, user_credits)
            new_user_credits = user_credits - steal_amount
            await bank.set_balance(ctx.author, steal_amount)
            await bank.set_balance(user, new_user_credits)
            await ctx.send("You stole {0} {1} from {2.display_name}!".format(steal_amount, name, user))
        else:
            author_amount = await bank.get_balance(ctx.author)
            give_amount = random.randint(100, author_amount)
            new_author_amount = author_amount - give_amount
            await bank.set_balance(ctx.author, new_author_amount)
            await bank.set_balance(user, give_amount)
            await ctx.send("You were caught trying to steal from {0.mention}! You gave them {1} {2} as a fine".format(user, give_amount, name))
