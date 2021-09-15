# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from redbot.core import commands

__all__ = ["NonBotMember", "PositiveInt"]


class NonBotMember(commands.Converter):
    def __init__(self, strict: bool = True):
        self.strict = strict

    async def convert(self, ctx: commands.Context, arg: str):
        try:
            user = await commands.MemberConverter().convert(ctx, arg)
        except commands.BadArgument:
            if self.strict:
                raise
            raise commands.UserInputError from None
        else:
            if user.bot:
                raise commands.BadArgument("The user cannot be a bot")
            return user


class PositiveInt(commands.Converter):
    async def convert(self, ctx: commands.Context, arg: str):
        try:
            ret = int(arg)
        except ValueError:
            raise commands.BadArgument("That was not an integer")
        else:
            if ret <= 0:
                raise commands.BadArgument("That was not a positive integer")
            return ret
