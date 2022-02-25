# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from typing import TYPE_CHECKING

import discord
from redbot.core import commands

__all__ = ["PositiveInt", "NonBotMember"]


if TYPE_CHECKING:
    PositiveInt = int
else:

    class PositiveInt(commands.Converter):
        def __init__(self, strict: bool = True):
            self.strict = strict

        async def convert(self, ctx: commands.Context, arg: str) -> int:
            try:
                ret = int(arg)
            except ValueError:
                if self.strict:
                    raise commands.BadArgument("That was not an integer.")
                raise commands.UserInputError
            if ret <= 0:
                raise commands.BadArgument(f"'{arg}' is not a positive integer.")
            return ret


if TYPE_CHECKING:
    NonBotMember = discord.Member
else:

    class NonBotMember(commands.MemberConverter):
        def __init__(self, strict: bool = True):
            self.strict = strict
            super().__init__()

        async def convert(self, ctx: commands.Context, arg: str) -> discord.Member:
            try:
                member = await super().convert(ctx, arg)
            except commands.BadArgument as e:
                if self.strict:
                    raise
                raise commands.UserInputError
            if member.bot:
                raise commands.BadArgument("That member is a bot")
            return member
