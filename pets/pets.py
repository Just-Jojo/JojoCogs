from typing import Literal

from redbot.core import commands, Config, bank
from redbot.core import checks
from redbot.core.utils import AsyncIter, menus
import asyncio

import discord
import traceback as tb
from .embed_maker import Embed
import random

import logging

log = logging.getLogger(name="red.jojo.pets")


class Pets(commands.Cog):
    async def red_delete_data_for_user(
        self, *, requester: Literal["discord", "owner", "user", "user_strict"], user_id: int
    ) -> None:
        await self.config.user_from_id(user_id).clear()

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 2958485)
        self.config.register_global(
            fish=15,
            dog=30,
            snake=30,
            cat=35,
            birb=40,
            lizard=45,
            panda=60
        )
        self.config.register_user(
            pets={}
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if isinstance(message.channel, discord.DMChannel):
            return
        if message.author.bot:
            return
        if message.content[0] in await self.bot.get_prefix(message):
            return
        if message.channel.id != 758775890954944572:
            return
        pets = await self.config.user(message.author).get_raw("pets")
        if len(pets.keys()) <= 0:
            return
        pet_type = random.choice(list(pets.keys()))
        log.info(pet_type)
        chosen = random.choice(pets[pet_type])
        old_health = await self.config.user(message.author).pets.get_raw(pet_type, chosen, "hunger")
        if old_health >= 100:
            return await message.channel.send("{}, your pet has 100 hunger points! You need to feed them before they get removed!".format(message.author.name))
        await self.config.user(message.author).pets.set_raw(pet_type, chosen, "hunger", value=old_health + 2)

    async def update_balance(self, user: discord.Member, amount: int) -> None:
        """Update a user's balance with the bank module"""
        old_bal = await bank.get_balance(user)
        new_bal = old_bal - amount
        await bank.set_balance(user, new_bal)

    async def page_logic(self, ctx: commands.Context, dictionary: dict, item: str, field_num: int = 15) -> None:
        """Convert a dictionary into a pagified embed"""
        embeds = []
        count = 0
        title = item
        embed = Embed.create(
            self, ctx, title=title, thumbnail=ctx.guild.icon_url
        )

        for key, value in dictionary.items():
            if count == field_num - 1:
                embed.add_field(name=key, value=value, inline=True)
                embeds.append(embed)

                embed = Embed.create(
                    self, ctx=ctx, title=title, thumbnail=ctx.guild.icon_url
                )
                count = 0
            else:
                embed.add_field(name=key, value=value, inline=True)
                count += 1
        else:
            embeds.append(embed)

        msg = await ctx.send(embed=embeds[0])
        control = menus.DEFAULT_CONTROLS if len(embeds) > 1 else {
            "\N{CROSS MARK}": menus.close_menu
        }
        asyncio.create_task(menus.menu(ctx, embeds, control, message=msg))
        menus.start_adding_reactions(msg, control.keys())

    @commands.command(name="buypet")
    async def buy_pet(self, ctx, pet_type: str, *, pet_name: str):
        """Purchase a pet"""
        try:
            cost = await self.config.get_raw(pet_type)
        except KeyError:
            await ctx.send("I could not find that pet!")
            return

        if await bank.can_spend(ctx.author, cost):
            await self.config.user(ctx.author).pets.set_raw(
                pet_type, pet_name, value={"cost": cost, "hunger": 0}
            )
            await ctx.send("You have purchased a {0} and called it {1}".format(pet_type, pet_name))
            await self.update_balance(ctx.author, cost)
        else:
            await ctx.send("You do not have enough money to buy that pet!")

    @commands.command()
    async def pets(self, ctx):
        """List the pets that you own"""
        try:
            pet_list = await self.config.user(ctx.author).get_raw("pets")
        except:
            await ctx.send("You don't have any pets!")
            return
        if len(pet_list.keys()) > 0:
            await self.page_logic(ctx, pet_list, item="{}'s pets".format(ctx.author.name))
        else:
            await ctx.send("You don't have any pets!")

    @commands.command()
    async def hunger(self, ctx, pet_name: str):
        """Check the hunger of a pet"""
        try:
            pet = await self.config.user(ctx.author).pets.get_raw(pet_name)
        except KeyError:
            await ctx.send("You don't own that pet!")
            return
        hunger = pet.get("hunger")
        await ctx.send("Your pet has {0}/100 hunger".format(hunger))

    @commands.command()
    async def feed(self, ctx, pet_name: str, food: int):
        """Feed on of your pets"""
        try:
            pet = await self.config.user(ctx.author).pets.get_raw(pet_name)
        except KeyError:
            await ctx.send("You don't own that pet!")
            return

        hunger = pet.get("hunger")
        new_hunger = max(hunger - food, 0)

        await self.config.user(ctx.author).pets.set_raw(
            pet_name, "hunger", value=new_hunger
        )
        await ctx.send("Your pet is now at {0}/100 hunger!".format(new_hunger))

    @commands.command(name="petlist", aliases=["plist"])
    async def pet_list(self, ctx):
        """Lists all of the pets in your guild"""
        try:
            pet_list = await self.config.get_raw()
        except:
            await ctx.send("I could not find any pets!")
            return
        await self.page_logic(ctx, pet_list, item="{}'s Pet Store".format(ctx.guild.name))
