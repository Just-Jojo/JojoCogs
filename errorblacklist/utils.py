# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import discord

from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_list as hl
from discord.utils import copy_doc

from typing import Union


__all__ = ["humanize_list", "PositiveInt", "UserOrCommand"]

@copy_doc(hl)
def humanize_list(items: list, *args) -> str:
    return hl([f"`{x}`" for x in items], *args)


class PositiveInt(commands.Converter):
    async def convert(self, ctx: commands.Context, arg: str) -> int:
        try:
            ret = int(arg)
        except ValueError:
            raise commands.BadArgument("That was not an integer.") from None
        else:
            if ret <= 0:
                raise commands.BadArgument("That was not a positive integer.")
            return ret


class UserOrCommand(commands.Converter):
    async def convert(self, ctx: commands.Context, arg: str) -> Union[discord.User, commands.Command]:
        maybe_com = ctx.bot.get_command(arg)
        if maybe_com:
            return maybe_com
        try:
            return await commands.UserConverter().convert(ctx, arg)
        except commands.UserNotFound:
            raise commands.BadArgument("I could not find a user or a command.") from None
