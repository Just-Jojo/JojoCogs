from redbot.core import commands, Config, bank, checks
from .embed import Embed
import discord
import random
import json
import os
import discord
from discord.utils import get


class Collectables(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=153607829, force_registration=True)
        self.config.register_guild(
            Vanguards=100
        )
        self.config.register_user(
            collectables={}
        )

    def readable_dict(self, dictionary: dict):  # Remove at a future date
        x = []
        for key, item in dictionary.items():
            y = "{0}: {1}".format(key, item)
            x.append(y)
        return "\n".join(x)

    @commands.group()
    async def collectable(self, ctx):
        """Commands working with the Collectable cog!"""

    @collectable.command()
    @commands.admin_or_permissions(manage_guild=True)
    async def add(self, ctx, user: discord.Member = None, *, collectable: str = None):
        """Add a collectable to someone's collection"""
        if collectable is not None:
            try:
                collectable_data = await self.config.guild(ctx.guild).get_raw(collectable)
            except KeyError:
                return await ctx.send("I could not find that collectable!")
            data = Embed.create(self, ctx, description="Success!", title="Adding {} to {}'s collection".format(
                collectable, user.display_name), footer="Collectables | Collect them all!")
            await ctx.send(embed=data)
            await self.config.user(user).collectables.set_raw(collectable, value=collectable_data)

    @collectable.command()
    @checks.guildowner_or_permissions(administrator=True)
    async def create(self, ctx, collectable_name: str, price: int = 100):
        """Adds collectables to a user."""
        data = Embed.create(self, ctx, title='Adding {0} as a Collectable. :trophy:',
                            description='Added {0} as a Collectable which can be purchased for {1}'.format(collectable_name, price))
        await self.config.guild(ctx.guild).set_raw(collectable_name, value=price)
        await ctx.send(embed=data)

    @collectable.command(name="list")
    async def collectable_list(self, ctx):
        """List all of the collectables in your guild"""
        try:
            coll = await self.config.guild(ctx.guild).get_raw()
        except Exception:
            return await ctx.send("Your guild does not have any collectables!\nHave an admin run `{}collectable create <collectable> [cost]` to start collecting!".format(ctx.clean_prefix))
        data = Embed.create(
            self, ctx, title="{}'s Collectables".format(ctx.guild.name)
        )
        for key, item in coll:
            data.add_field(name=key, value=item, inline=False)
        await ctx.send(embed=data)

    @collectable.command()
    async def buy(self, ctx, collectable: str):
        try:
            cost = await self.config.guild(ctx.guild).get_raw(collectable)
        except KeyError:
            await ctx.send("I could not find that Collectable")
            return

        if await bank.can_spend(ctx.author, cost):
            await self.config.user(ctx.author).collectables.set_raw(
                collectable, value=cost
            )
            await ctx.send("You have purchased {0} for {1}!".format(collectable, cost))
            await bank.withdraw_credits(ctx.author, cost)

    @commands.command()
    async def collectables(self, ctx, user: discord.Member = None):
        """Displays a users collectables."""
        if user is None:
            user = ctx.author
        try:
            collectable_list = await self.config.user(user).get_raw("collectables")
        except Exception:
            return await ctx.send("{} doesn't have any collectables!".format(user.display_name))
        data = Embed.create(
            self, ctx, title="{}'s collectables".format(user.display_name))
        for key, item in collectable_list.items():
            data.add_field(name=key, value=item, inline=False)
        await ctx.send(embed=data)

    @commands.command(name='99', help='Responds with a random quote from Brooklyn 99')
    async def nine_nine(self, ctx):
        brooklyn_99_quotes = [
            'I\'m the human form of the 💯 emoji.',
            'Bingpot!',
            (
                'Cool. Cool cool cool cool cool cool cool, '
                'no doubt no doubt no doubt no doubt.'
            ),
        ]

        await ctx.send(random.choice(brooklyn_99_quotes))
