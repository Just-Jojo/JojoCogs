# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import discord
from redbot.core import commands

__all__ = ["CommandOrCogConverter", "NoneChannelConverter"]


if TYPE_CHECKING:
    CommandOrCogConverter = Union[commands.Command, commands.Cog]
else:

    class CommandOrCogConverter(commands.Converter):
        async def convert(
            self, ctx: commands.Context, arg: str
        ) -> Union[commands.Command, commands.Cog]:
            ret = ctx.bot.get_cog(arg)
            if ret:
                return ret
            ret = ctx.bot.get_command(arg)
            if ret is None:
                raise commands.BadArgument(f"'{arg}' is not a command or a cog")
            return ret


if TYPE_CHECKING:
    NoneChannelConverter = Union[None, discord.TextChannel, discord.Thread]
else:

    class NoneChannelConverter(commands.Converter):
        async def convert(self, ctx: commands.Context, arg: str) -> Union[discord.GuildChannel, discord.Thread]:
            if arg == "None":
                return None

            try:
                return await commands.ThreadConverter().convert(ctx, arg)
            except commands.BadArgument:
                return await commands.GuildChannelConverter().convert(ctx, arg)
