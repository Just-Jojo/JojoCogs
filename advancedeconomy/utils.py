# Copyright (c) 2021 Jojo#7791
# Licensed under MIT

from redbot.core import commands

__all__ = ["PositiveInt"]


class PositiveInt(commands.Converter):
    async def convert(self, ctx: commands.Context, arg: str) -> int:
        try:
            ret = int(arg)
        except ValueError:
            raise commands.BadArgument("The argument must be an integer")
        if ret <= 0:
            raise commands.BadArgument("The argument must be positive")
        return ret
