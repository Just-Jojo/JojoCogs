# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from __future__ import annotations

from typing import Iterable, Optional, Set, Union

from discord import Guild, Member, Role, User
from redbot import VersionInfo, version_info
from redbot.core.bot import Red

__all__ = ["add_to_blacklist", "in_blacklist", "get_blacklist"]


if version_info.dev_release is None and version_info >= VersionInfo.from_str("3.4.13"):
    add_to_blacklist = Red.add_to_blacklist
    get_blacklist = Red.get_blacklist
else:
    UserOrRole = Union[int, User, Member, Role]

    async def add_to_blacklist(
        self: Red, users_or_roles: Iterable[UserOrRole], *, guild: Optional[Guild] = None
    ):
        to_add = {getattr(x, "id", x) for x in users_or_roles}
        await self._whiteblacklist_cache.add_to_blacklist(guild, to_add)
        self.dispatch("blacklist_add", to_add, guild)

    async def get_blacklist(self: Red, guild: Optional[Guild] = None) -> Set[int]:
        return await self._whiteblacklist_cache.get_blacklist(guild)


async def in_blacklist(
    bot: Red, user: Union[User, Member, int], guild: Optional[Guild] = None
) -> bool:
    blacklist = await get_blacklist(bot, guild)
    return getattr(user, "id", user) in blacklist
