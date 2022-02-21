# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from __future__ import annotations

import discord
from redbot.core import commands
from typing import Union, Optional, TYPE_CHECKING


__all__ = ["CommandOrCogConverter", "NoneChannelConverter"]


if TYPE_CHECKING:
    CommandOrCogConverter = Union[commands.Command, commands.Cog]
else:

    class CommandOrCogConverter(commands.Converter):
        async def convert(self, ctx: commands.Context, arg: str) -> Union[commands.Command, commands.Cog]:
            ret = ctx.bot.get_cog(arg)
            if ret:
                return ret
            ret = ctx.bot.get_command(arg)
            if ret is None:
                raise commands.BadArgument(f"'{arg}' is not a command or a cog")
            return ret


if TYPE_CHECKING:
    NoneChannelConverter = discord.TextChannel
else:

    class NoneChannelConverter(commands.Converter):
        async def convert(self, ctx: commands.Context, arg: str) -> Optional[discord.TextChannel]:
            if arg == "None":
                return None
            return await commands.TextChannelConverter().convert(ctx, arg)
