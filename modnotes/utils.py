# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from redbot.core import commands

__all__ = ["NonBotMember", "PositiveInt"]


if TYPE_CHECKING:
    NonBotMember = discord.Member
else:

    class NonBotMember(commands.MemberConverter):
        def __init__(self, strict: bool = True):
            self.strict = strict
            super().__init__()

        async def convert(self, ctx: commands.Context, arg: str) -> discord.Member:
            try:
                user = await super().convert(ctx, arg)
            except commands.BadArgument:
                if self.strict:
                    raise
                raise commands.UserInputError from None
            else:
                if user.bot:
                    raise commands.BadArgument("The user cannot be a bot")
                elif user == ctx.author:
                    raise commands.BadArgument("The user cannot be yourself")
                return user


if TYPE_CHECKING:
    PositiveInt = int
else:

    class PositiveInt(commands.Converter):
        async def convert(self, ctx: commands.Context, arg: str) -> int:
            try:
                ret = int(arg)
            except ValueError:
                raise commands.BadArgument("That was not an integer")
            else:
                if ret <= 0:
                    raise commands.BadArgument("That was not a positive integer")
                return ret
