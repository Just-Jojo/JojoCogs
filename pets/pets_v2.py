# Bank for buying pets, food, etc.
from redbot.core import commands, Config, bank
from redbot.core.utils.chat_formatting import pagify
from redbot.core.utils.menus import menu, close_menu, start_adding_reactions, DEFAULT_CONTROLS

import logging

import discord
import asyncio
import random
from datetime import datetime

log = logging.getLogger("red.JojoCogs.pets")


class Pets(commands.Cog):
    DEFAULT_PETS = {  # dict(str, int) for defaults, this really just contains a dog, cat, and birb
        "dog": 500,
        "cat": 500,
        "bird": 500
    }
    __version__ = "2.0.1"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 544974305445019651)
        self.config.register_guild(
            **self.DEFAULT_PETS
        )
        # Here, pets will be a `str: [str, int]` for name and hunger
        self.config.register_member(pets={}, food=0)
        self.embed = Embed(self.bot)  # For embeds

    async def red_delete_data_for_user(
        self, *, requester: Literal["discord", "owner", "user", "user_strict"], user_id: int
    ) -> None:
        await self.config.member(user_id).clear()

    @commands.command()
    async def buypet(self, ctx: commands.Context, pet_type: str, *, name: str):
        """Buy a pet!
        Example:
        `[p]buypet dog Mrs. Woof`"""
        pet_type = pet_type.lower()
        av_pets = await self.config.guild(ctx.guild).get_raw()
        if pet_type in av_pets.keys():
            if await bank.can_spend(ctx.author, av_pets[pet_type]):
                await bank.withdraw_credits(ctx.author, av_pets[pet_type])
                pets = await self.config.member(ctx.author).get_raw("pets")
                pets[name] = [0, pet_type]
                await self.config.member(ctx.author).set_raw("pets", value=pets)
                await ctx.send(
                    f"You have successfully bought a"
                    f" {pet_type.capitalize()} and called it {name}"
                )
            else:
                await ctx.send("You didn't have enough money to buy that pet!")
        else:
            await ctx.send("That pet doesn't exist!")

    @commands.command()
    async def listpets(self, ctx: commands.Context):
        """List all of your pets in a clean, menued embed
        Example:
        `[p]listpets`"""
        # pets = list(await self.config.member(ctx.author).pets.get_raw())
        pets = await self.config.member(ctx.author).pets.get_raw()
        pets = list(pets.keys())
        if not "".join(pets):
            await ctx.send(f"You don't have any pets! Buy some using `{ctx.clean_prefix}buypet <pet type> <name>`")
            return
        embeds = []
        for page in pagify(", ".join(pets)):
            embed = self.embed.create(
                ctx, title=f"{ctx.author.display_name}'s pets")
            embed.add_field(name="Pets", value=page)
            embeds.append(embed)
        msg = await ctx.send(embed=embeds[0])
        conts = DEFAULT_CONTROLS if len(embeds) > 1 else {
            "\N{CROSS MARK}": close_menu}
        asyncio.create_task(menu(ctx, embeds, conts, msg, 0, 25.0))
        start_adding_reactions(msg, conts.keys())

    @commands.command()
    async def viewpet(self, ctx: commands.Context, *, pet_name: str):
        """Look at a pet's stats and type
        Example:
        `[p]viewpet Mr. Woof`"""
        try:
            pet = await self.config.member(ctx.author).pets.get_raw(pet_name)
        except KeyError:
            await ctx.send(f"I could not find a pet by the name of `{pet_name}`")
            return
        embed = self.embed.create(ctx, title=f"{pet_name}'s stats")
        embed.add_field(name="Type", value=pet[1].capitalize())
        embed.add_field(name="Hunger", value=pet[0])
        await ctx.send(embed=embed)

    # @commands.command()
    # async def buyfood(self, ctx: commands.Context, amount: int):
    #     """Buy food to feed your pets!"""
    #     if amount < 1:
    #         await ctx.send("You can't buy 0 or less food, silly!")
    #         return
    #     food_cost = 30 * amount
    #     if not await bank.can_spend(ctx.author, food_cost):
    #         await ctx.send("You don't have enough money to buy that much food!")
    #         return
    #     await bank.withdraw_credits(ctx.author, food_cost)
    #     await self.config.member(ctx.author).set_raw(
    #         "food", value=await self.config.member(ctx.author).get_raw("food") + 1
    #     )
    #     await ctx.send(f"You bought {amount} bits of food!")

    # @commands.command()
    # async def feedpet(self, ctx: commands.Context, amount: int, *, pet_name: str):
    #     """Feed one of your pets
    #     Example:
    #     `[p]feedpet 4 Mr. Woof"""
    #     org_amount = amount
    #     food = await self.config.member(ctx.author).get_raw("food")
    #     if amount > food:
    #         await ctx.send("You don't have that many food bits!")
    #         return
    #     try:
    #         pet = await self.config.member(ctx.author).pets.get_raw(pet_name)
    #     except KeyError:
    #         await ctx.send(f"You don't have a pet named {pet_name}")
    #         return
    #     act_amount = amount * 5
    #     hunger = pet[0]
    #     if hunger == 0:
    #         await ctx.send("That pet isn't hungry!")
    #         return
    #     pet[0] = hunger - act_amount if act_amount < hunger else 0
    #     amount = amount if act_amount < hunger else hunger
    #     await self.config.member(ctx.author).pets.set_raw(pet_name, value=pet)
    #     await self.config.member(ctx.author).set_raw("food", value=food-org_amount if food-org_amount > 0 else 0)
    #     await ctx.send(f"Fed {pet_name} {amount} bits of food!")

    # @commands.Cog.listener("on_message_without_command")
    # async def hunger_tracker(self, message: discord.Message):
    #     if message.author.bot:
    #         return
    #     async for msg in message.author.history(limit=10):
    #         if msg.author.id == message.author.id:
    #             now = datetime.utcnow() - message.created_at
    #             if now.total_seconds() > 400:
    #                 return
    #             pets = await self.config.member(message.author).pets.get_raw()
    #             # log.info(f"{pets} {list(pets)}")
    #             pet = random.choice(list(pets.keys()))
    #             # log.info("Passed the `IndexError`")
    #             hunger = pets[pet][0]
    #             if hunger == 100:
    #                 await message.channel.send(f"{message.author.name}, your pet {pet} is at 100 hunger! Please feed it!")
    #                 return
    #             pets[pet][0] += 1
    #             await self.config.member(message.author).pets.set_raw(value=pets)
    #             return


class Embed:
    def __init__(self, bot):
        self.bot = bot

    def create(self, ctx, title="", description="", image: str = None, thumbnail: str = None,
               footer_url: str = None, footer: str = None) -> discord.Embed:
        if isinstance(ctx.message.channel, discord.abc.GuildChannel):
            color = ctx.message.author.color
        data = discord.Embed(title=title, color=color)
        if description is not None:
            if len(description) <= 1500:
                data.description = description
        data.set_author(name=ctx.author.display_name,
                        icon_url=ctx.author.avatar_url)
        if image is not None:
            data.set_image(url=image)
        if thumbnail is not None:
            data.set_thumbnail(url=thumbnail)
        if footer is None:
            footer = "{0.name}'s Embed Maker".format(ctx.bot.user)
        if footer_url is None:
            footer_url = ctx.bot.user.avatar_url
        data.set_footer(text=footer, icon_url=footer_url)
        return data
