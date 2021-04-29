# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import logging
from typing import List, Literal, Optional

import discord
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box
from tabulate import tabulate

log = logging.getLogger("red.JojoCogs.calculations")
_headers = ["Input", "Output"]
_nautical = {"km": 1.852, "miles": 1.15078}


class Calculations(commands.Cog):
    """Different calculations including binary to decimal and vice versa :D"""

    __author__ = ["Jojo#7791"]
    __version__ = "1.0.0"

    def __init__(self, bot: Red):
        self.bot = bot

    async def red_delete_data_for_user(self, *, requester, user_id):
        """Nothing to delete"""
        return

    def format_help_for_context(self, ctx: commands.Context):
        pre = super().format_help_for_context(ctx)
        return (
            f"{pre}\n\nAuthor: {', '.join(self.__author__)}\nVersion: {self.__version__}"
        )

    @staticmethod
    def _get_tabulated(data: List[str]) -> str:
        return box(tabulate([data[0]], data[1], tablefmt="fancy_grid"))

    @staticmethod
    def _nautical_to_other(conver: int, _type: Literal["km", "miles"]):
        num = _nautical.get(_type, None)
        if num is None:
            return f"{_type} is not a valid type"
        return Calculations._get_tabulated(
            [[f"{conver} Nautical miles", f"{round(conver * num, 2)} {_type}"], _headers]
        )

    @staticmethod
    def _other_to_nautical(conver: int, _type: Literal["km", "miles"]):
        num = _nautical.get(_type, None)
        if num is None:
            return f"{_type} is not a valid type"
        return Calculations._get_tabulated(
            [[f"{conver} {_type}", f"{round(conver/num, 2)} Nautical miles"], _headers]
        )

    @commands.command(aliases=["bin"])
    async def binary(self, ctx, number: int):
        """Convert a number into binary!"""
        num = bin(number).replace("0b", "")  # Get the binary number and remove the prefix
        await ctx.send(self._get_tabulated([[str(number), num], _headers]))

    @commands.command()
    async def decimal(self, ctx, number: int):
        """Convert a binary number to decimal"""
        try:
            num = int(str(number), 2)  # Convert to an int with a base of 2
        except ValueError:
            return await ctx.send("That wasn't a binary number!")
        await ctx.send(self._get_tabulated([[number, str(num)], _headers]))

    @commands.command(usage="[kilometres or miles] <nautical miles>")
    async def nautical(self, ctx, miles: int, _type: Optional[str] = "km"):
        """Convert nautical miles to kilometres or miles"""
        _type = _type.replace("kilometers", "km")
        await ctx.send(self._nautical_to_other(miles, _type))

    @commands.command()
    async def othernautical(self, ctx, nm: int, _type: Optional[str] = "km"):
        """Convert miles or kilometres"""
        await ctx.send(self._other_to_nautical(nm, _type))
