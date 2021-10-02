# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from typing import Literal

import discord
from redbot.core import commands, Config, bank
from redbot.core.bot import Red

import random
from .utils import PositiveInt

RequestType = Literal["discord_deleted_user", "owner", "user", "user_strict"]

_config_structure: dict = {
    "global": {
        "max_job_amount": 3000,
    },
    "user": {
        "intelligence": 5,
        "strength": 5,
        "agility": 5,
        "determination": 0, # iSad brought to you by apple
    }
}


class AdvancedEconomy(commands.Cog):
    """
    An advanced economy for Red
    """

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            self,
            544974305445019651,
            True
        )
        for key, value in _config_structure.items():
            getattr(self.config, f"register_{key}")(**value)

    @commands.group()
    @commands.is_owner()
    async def economyset(self, ctx: commands.Context):
        """Setup the economy system"""

    @economyset.command(name="highestjobamount")
    async def economy_highest_job_amount(self, ctx: commands.Context, amount: PositiveInt):
        """Set the highest amount that a job can give someone

        **Arguments**
            - `amount` The highest amount a job can pay someone
        """
        currency_name = await bank.get_currency_name()
        await ctx.send(f"Done. The highest amount a job will pay someone is now set to {amount} {currency_name}")
        await self.config.max_job_amount.set(amount)

    async def red_delete_data_for_user(self, *, requester: RequestType, user_id: int):
        """This cog does not store any data"""
        return
