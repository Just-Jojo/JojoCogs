import asyncio
import os
import random
import time
from operator import itemgetter
from typing import Literal

from redbot.core import commands, Config, checks
from redbot.core.utils import AsyncIter
import discord


class PluralDict(dict):
    """This class is used to plural strings
    You can plural strings based on the value input when using this class as a dictionary.
    """

    def __missing__(self, key):
        if '(' in key and key.endswith(')'):
            key, rest = key.split('(', 1)
            value = super().__getitem__(key)
            suffix = rest.rstrip(')').split(',')
            if len(suffix) == 1:
                suffix.insert(0, '')
            return suffix[0] if value <= 1 else suffix[1]
        raise KeyError(key)


class Brownie(commands.Cog):
    """Collector loves brownies, and will steal from others for you!"""

    default_guild_settings = {
        "Players": {},
        "Config": {
            "Steal CD": 300,
            "brownie CD": 300
        }
    }

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, 2287042090, force_registration=True
        )
        self.config.register_guild(**self.default_guild_settings)

    async def red_delete_data_for_user(
        self,
        *,
        user: Literal["discord_deleted_user", "owner", "owner", "user", "user_strict"],
        id: int
    ):
        if user != "discord_deleted_user":
            return
        await self.config.user_from_id(id).clear()

        all_members = await self.config.all_members
        async for guild_id, guild_data in AsyncIter(all_members.items(), steps=500):
            if id in guild_data:
                await self.config.member_from_ids(guild_id, id).clear()

    @commands.command()
    @commands.is_owner()
    async def delete(self, ctx):
        for guild in self.bot.guilds:
            await self.config.guild(guild).clear_raw()
        await ctx.send("Cleared the brownie cache")
        for guild in self.bot.guilds:
            await self.config.guild(guild).set_raw(value=self.default_guild_settings)
        await ctx.send("Reregistered the guilds")
        x = await self.config.guild(ctx.guild).Players.get_raw()
        print(x)

    @commands.group()
    @commands.guild_only()
    async def setbrownie(self, ctx):
        """brownie settings group command"""

    @setbrownie.command(name="stealcd")
    @checks.admin()
    async def _stealcd_heist(self, ctx, cooldown: int):
        """Set the cooldown for stealing brownies"""
        if cooldown >= 0:
            await self.config.guild(ctx.guild).Config.set_raw("Steal CD", value=cooldown*60)
            msg = "Cooldown for steal set to {0}".format(cooldown)
        else:
            msg = "Cooldown needs to be higher than 0."
        await ctx.send(msg)

    @setbrownie.command(name="browniecd")
    @checks.admin()
    async def _browniecd_heist(self, ctx, cooldown: int):
        """Set the cooldown for brownie command"""
        if cooldown >= 0:
            await self.config.guild(ctx.guild).Config.set_raw("brownie CD", value=cooldown*60)
            msg = "Cooldown for brownie set to {0}".format(cooldown)
        else:
            msg = "Cooldown needs to be higher than 0."
        await ctx.send(msg)

    @commands.command()
    async def brownie(self, ctx):
        """Obtain a random number of brownies. 12h cooldown"""
        await self.account_check(ctx.author)

        action = "brownie CD"
        toogle = await self.check_cooldowns(ctx, ctx.author, action)
        if toogle is True:
            weighted_sample = [1] * 152 + [x for x in range(49) if x > 1]
            brownies = random.choice(weighted_sample)

            author_brownies = await self.config.guild(ctx.guild).Players.get_raw(ctx.author.id, "brownies")
            await self.config.guild(ctx.guild).Players.set_raw(ctx.author.id, "brownies", value=author_brownies+brownies)
            if brownies > 1:
                await ctx.send("{0} found {1} brownies!".format(ctx.author.name, brownies))
            else:
                await ctx.send('{} found 1 brownie!'.format(ctx.author.name))

    @commands.command()
    @commands.guild_only()
    async def brownies(self, ctx):
        """Check how many brownie points you have"""
        try:
            brownies = await self.config.guild(ctx.guild).Players.get_raw(ctx.author, "brownies")
            msg = "{0} has **{1}** brownie points".format(
                ctx.author.name, brownies)
        except KeyError:
            msg = "{} has no brownies points".format(ctx.author.name)
        await ctx.send(msg)

    @commands.command(aliases=['giveb', ])
    @commands.guild_only()
    async def givebrownie(self, ctx, user: discord.Member, brownies: int):
        """Gives another user your brownies"""
        author = ctx.author
        if ctx.author.id == user.id:
            return await ctx.send("You can't give yourself brownie points.")
        await self.account_check(ctx.author, user)
        sender_brownies = await self.config.guild(ctx.guild).Players.get_raw(ctx.author.id, "brownies")
        user_brownies = await self.config.guild(ctx.guild).Players.get_raw(user.id, "brownies")

        if 0 < brownies <= sender_brownies:
            await self.config.guild(ctx.guild).Players.set_raw(author.id, "brownies", value=sender_brownies - brownies)
            await self.config.guild(ctx.guild).Players.set_raw(user.id, "brownies", value=user_brownies + brownies)
            msg = "{0} gave {1} brownies to {2}".format(
                ctx.author.name, brownies, user.name
            )
        else:
            msg = "You don't have enough brownies points"
        await ctx.send(msg)

    @commands.command()
    @commands.guild_only()
    async def nom(self, ctx):
        """Eat a brownie"""
        author = ctx.author
        await self.account_check(ctx.author)
        user_brownies = await self.config.guild(ctx.guild).Players.get_raw(author.id, "brownies")
        if user_brownies == 0:
            return await ctx.send("There are no brownies to eat")
        user_brownies -= 1
        await self.config.guild(ctx.guild).Players.set_raw(author.id, "brownies", value=user_brownies)
        if user_brownies > 1:
            msg = "Nom nom nom.\n{0.name} has {1} brownie points remaining".format(
                ctx.author, user_brownies
            )
        elif user_brownies == 1:
            msg = "Nom nom nom.\n{0.name} has 1 brownie point remaining".format(
                ctx.author
            )
        else:
            msg = "Nom nom nom.\n{0.name} has no more brownie points.".format(
                ctx.author
            )
        await ctx.send(msg)

    @commands.command()
    @commands.guild_only()
    async def steal(self, ctx, user: discord.Member = None):
        """Steal brownies from another user"""
        author = ctx.author
        guild = ctx.guild

        if user is None:
            user = await self.random_user(author, guild)
        if user == "Fail":
            return await ctx.send("I could not find anyone with brownie points.")
        elif user.bot:
            return await ctx.send(
                "Stealing failed because the picked target is a bot.\nYou can retry stealing again, your cooldown is not consumed."
            )
        msg = await self.steal_logic(user, author)
        await ctx.send("{} is on the prowl to steal brownies.".format(ctx.author.name))
        await asyncio.sleep(4)
        await ctx.send(msg)

    async def check_cooldowns(self, ctx: commands.Context, user: discord.Member, action: str) -> bool:
        guild_cooldown = await self.config.guild(ctx.guild).Config.get_raw(action)
        cooldown = await self.config.guild(ctx.guild).Players.get_raw(user.id, action)
        if abs(cooldown - int(time.perf_counter())) >= guild_cooldown:
            cooldown = int(time.perf_counter())
            await self.config.guild(ctx.guild).Players.set_raw(user, action, value=cooldown)
            return True
        elif cooldown == 0:
            cooldown = int(time.perf_counter)
            await self.config.guild(ctx.guild).Players.set_raw(user, action, value=cooldown)
            return True
        else:
            s = abs(
                cooldown - int(time.perf_counter())
            )
            seconds = abs(s - guild_cooldown)
            remaining = self.time_formatting(seconds)
            await ctx.send("This action has a cooldown. You still have:\n{}".format(remaining))
            return False

    async def account_check(self, *users: discord.Member) -> None:
        for user in users:
            try:
                await self.config.guild(user.guild).Players.get_raw(user.id)
            except KeyError:
                default_user = {"Steal CD": 5, "brownie CD": 5, "brownies": 0}
                await self.config.guild(user.guild).Players.set_raw(user.id, value=default_user)

    async def steal_logic(self, user: discord.Member, author) -> str:
        success_chance = random.randint(1, 100)
        if user == "Fail":
            msg = "I couldn't find anyone with brownie points"
            return msg
        players = await self.config.guild(user.guild).Players.get_raw()
        print(players)
        if user.id not in players:
            return "I could not find that user"

        await self.account_check(user, author)
        brownies = await self.config.guild(author.guild).Players.get_raw(user.id, "brownies")
        author_brownies = await self.config.guild(author.guild).Players.get_raw(author.id, "brownies")

        if brownies == 0:
            msg = ('{} has no brownie points.'.format(user.name))
        else:
            if success_chance <= 90:
                brownie_jar = await self.config.guild(author.guild).Players.get_raw(user.id)
                brownies_stolen = int(brownie_jar * 0.75)

                if brownies_stolen == 0:
                    brownies_stolen = 1

                stolen = random.randint(1, brownies_stolen)
                await self.config.guild(author.guild).Players.set_raw(user.id, value=brownies - brownies_stolen)
                await self.config.guild(author.guild).Players.set_raw(author.id, value=author_brownies + brownies_stolen)
                msg = ("{0} stole {1} brownie points from {2}!".format(
                    author.name, stolen, user.name))
            else:
                msg = "I could not find their brownie points"

        return msg

    async def random_user(self, author, server):
        filter_users = [server.get_member(x) for x in await self.config.guild(server).get_raw("Players") if hasattr(server.get_member(x), "name")]
        legit_users = [x for x in filter_users if x.id !=
                       author.id and x is not x.bot]

        users = [x for x in legit_users if await self.config.guild(server).Players.get_raw(x.id, "brownies") > 0]

        if not users:
            user = "Fail"
        else:
            user = random.choice(users)
            if user == user.bot:
                users.remove(user.bot)

                await self.config.Players.clear_raw(user.bot)
                user = random.choice(users)

        return user

    def time_formatting(self, seconds):

        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        data = PluralDict({'hour': h, 'minute': m, 'second': s})
        if h > 0:
            fmt = "{hour} hour{hour(s)}"
            if data["minute"] > 0 and data["second"] > 0:
                fmt += ", {minute} minute{minute(s)}, and {second} second{second(s)}"
            if data["second"] > 0 == data["minute"]:
                fmt += ", and {second} second{second(s)}"
            msg = fmt.format_map(data)
        elif h == 0 and m > 0:
            if data["second"] == 0:
                fmt = "{minute} minute{minute(s)}"
            else:
                fmt = "{minute} minute{minute(s)}, and {second} second{second(s)}"
            msg = fmt.format_map(data)
        elif m == 0 and h == 0 and s > 0:
            fmt = "{second} second{second(s)}"
            msg = fmt.format_map(data)
        elif m == 0 and h == 0 and s == 0:
            msg = "None"
        return msg
