# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from typing import Union

import discord
from redbot.core import commands
from abc import ABC

__all__ = ["NonBotUser", "NonBotMember"]


class _NonBotMixin(commands.Converter, ABC):
    """Remember kids, Don't Repeat Yourself (D.R.Y)"""

    converter_type: commands.Converter
    _whitelist_mode: bool

    def __init__(self, *, whitelist: bool = False):
        self._whitelist_mode = whitelist

    async def convert(
        self, ctx: commands.Context, arg: str
    ) -> Union[discord.Member, discord.User]:
        maybe_user = await self.converter_type().convert(ctx, arg)
        if maybe_user.bot:
            raise commands.BadArgument("That user is a bot")
        elif self._whitelist_mode:
            return maybe_user
        elif maybe_user == ctx.author:
            raise commands.BadArgument("You cannot blacklist yourself")
        elif await ctx.bot.is_owner(maybe_user):
            raise commands.BadArgument("You cannot blacklist this bot's owner")
        return maybe_user


class NonBotUser(_NonBotMixin):
    converter_type = commands.UserConverter


class NonBotMember(_NonBotMixin):
    converter_type = commands.MemberConverter
