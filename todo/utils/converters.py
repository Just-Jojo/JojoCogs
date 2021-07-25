# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from redbot.core import commands

__all__ = ["PositiveInt", "TodoPositiveInt", "NonBotMember"]


class PositiveInt(commands.Converter):
    async def convert(self, ctx: commands.Context, arg: str):
        try:
            ret = int(arg)
        except ValueError:
            raise commands.BadArgument("That was not an integer.")
        if ret <= 0:
            raise commands.BadArgument(f"'{arg}' is not a positive integer.")
        return ret


class TodoPositiveInt(commands.Converter):
    async def convert(self, ctx: commands.Context, arg: str):
        try:
            ret = int(arg)
        except ValueError:
            raise commands.UserInputError
        if ret <= 0:
            raise commands.BadArgument(f"'{arg}' is not a positive integer.")
        return ret


class NonBotMember(commands.Converter):
    def __init__(self, strict: bool = True):
        self.strict = strict

    async def convert(self, ctx: commands.Context, arg: str):
        try:
            member = await commands.MemberConverter().convert(ctx, arg)
        except commands.BadArgument as e:
            if self.strict:
                raise
            raise commands.UserInputError
        if member.bot:
            raise commands.BadArgument("That member is a bot")
        return member
