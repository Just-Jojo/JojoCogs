from redbot.core import commands, Config, bank
from redbot.core import checks
from redbot.core.utils import AsyncIter
import discord
import traceback as tb
from typing import Literal


class Pets(commands.Cog):
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

    def readable_dict(self, dictionary: dict):
        """Transform a dict into human readable data"""
        x = []
        for key, item in dictionary.items():
            y = "{0}: {1}".format(key, item)
            x.append(y)
        return "\n".join(x)

    async def update_balance(self, user: discord.Member, amount: int):
        """Update a user's balance with the bank module"""
        old_bal = await bank.get_balance(user)
        new_bal = old_bal - amount
        await bank.set_balance(user, new_bal)

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

    @commands.command(name="petsclear")
    @commands.is_owner()
    async def clear_pets(self, ctx, confirm: bool = False):
        """Clear all of the pets in a guild"""
        if confirm is True:
            try:
                await self.config.clear_all()
                await ctx.send("Cleared the data")
            except:
                await ctx.send("Could not clear the data")
        else:
            await ctx.send("You need to confirm that you want to erase the data. Please use `[p]petsclear True` to erase the data")

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
            pet_list_humanized = self.readable_dict(pet_list)
            await ctx.send(pet_list_humanized)
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
        pet_list_readable = self.readable_dict(pet_list)
        await ctx.send("Pet: cost\n{0}".format(pet_list_readable))
