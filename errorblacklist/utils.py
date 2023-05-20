# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from typing import TYPE_CHECKING, Any, List, Union

import discord
from discord.utils import copy_doc
from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_list as hl

__all__ = ["humanize_list", "PositiveInt", "UserOrCommandCog", "ChannelOrGuild", "NoneConverter"]


@copy_doc(hl)
def humanize_list(items: List[Any], *args) -> str:
    return hl([f"`{x}`" for x in items], *args)


if TYPE_CHECKING:
    PositiveInt = int
else:

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


if TYPE_CHECKING:
    UserOrCommandCog = Union[discord.User, commands.Command, commands.Cog]
else:

    class UserOrCommandCog(commands.Converter):
        async def convert(
            self, ctx: commands.Context, arg: str
        ) -> Union[discord.User, commands.Command, commands.Cog]:
            maybe_com = ctx.bot.get_command(arg)
            if maybe_com:
                return maybe_com
            maybe_cog = ctx.bot.get_cog(arg)
            if maybe_cog:
                return maybe_cog
            try:
                return await commands.UserConverter().convert(ctx, arg)
            except commands.UserNotFound:
                raise commands.BadArgument("I could not find a user or a command.") from None


if TYPE_CHECKING:
    ChannelOrGuild = Union[discord.TextChannel, discord.Guild]
else:

    class ChannelOrGuild(commands.Converter):
        async def convert(
            self, ctx: commands.Context, arg: str
        ) -> Union[discord.TextChannel, discord.Guild]:
            try:
                ret = await commands.TextChannelConverter().convert(ctx, arg)
            except commands.ChannelNotFound:
                try:
                    ret = await commands.GuildConverter().convert(ctx, arg)
                except commands.GuildNotFound:
                    raise commands.BadArgument("That was neither a guild or a channel.")

            return ret


if TYPE_CHECKING:
    NoneConverter = Union[str, None]
else:

    class NoneConverter(commands.Converter):
        async def convert(self, ctx: commands.Context, arg: str) -> Union[str, None]:
            if arg.lower() in ("none", "no", "nothing"):
                return None
            return arg
