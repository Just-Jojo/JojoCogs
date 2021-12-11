# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import logging
from abc import ABC
from typing import TYPE_CHECKING, Any, Literal, TypeVar

from redbot.core import commands

__all__ = ["NonBotMember", "NonBotUser"]
log = logging.getLogger("red.jojocogs.advancedblacklist.converters")


class _NonBotMixin(commands.Converter, ABC):
    """DRY, basically"""

    _actual: commands.Converter
    _whitelist_mode: bool

    def __init__(self, *, whitelist: bool = False):
        self._whitelist_mode = whitelist

    async def convert(self, ctx: commands.Context, arg: str) -> Any:
        try:
            ret = await self._actual.convert(ctx, arg)
        except Exception as e:
            log.debug("Conversion failed with this exception:", exc_info=e)
        if ret.bot:
            raise commands.BadArgument
        elif not self._whitelist_mode:
            if await ctx.bot.is_owner(ret):
                log.debug("Is a bot owner")
                raise commands.BadArgument
            elif ctx.guild and ctx.guild.owner_id == ret.id:
                log.debug("Is a guild owner")
                raise commands.BadArgument

        return ret

    def __class_getitem__(cls, whitelist: bool) -> "_NonBotMixin":
        log.debug(f"{whitelist = }")
        return cls(whitelist=bool(whitelist))


class NonBotMember(_NonBotMixin):
    _actual = commands.MemberConverter()


class NonBotUser(_NonBotMixin):
    _actual = commands.UserConverter()
