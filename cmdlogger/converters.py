# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import discord
from redbot.core import commands

__all__ = ["CommandConverter", "NoneChannelConverter"]


class CommandConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, arg: str) -> commands.Command:
        ret = ctx.bot.get_command(arg)
        if arg is None:
            raise commands.BadArgument(f"'{arg}' is not a command")
        return ret


class NoneChannelConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, arg: str) -> discord.TextChannel:
        if arg == "None":
            return None
        return await commands.TextChannelConverter().convert(ctx, arg)
