# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import discord
from redbot.core import commands
from typing import Union


__all__ = ["CommandOrCogConverter", "NoneChannelConverter"]


class CommandOrCogConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, arg: str) -> Union[commands.Command, commands.Cog]:
        ret = ctx.bot.get_cog(arg)
        if ret:
            return ret
        ret = ctx.bot.get_command(arg)
        if ret is None:
            raise commands.BadArgument(f"'{arg}' is not a command or a cog")
        return ret


class NoneChannelConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, arg: str) -> discord.TextChannel:
        if arg == "None":
            return None
        return await commands.TextChannelConverter().convert(ctx, arg)
