# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from redbot import version_info, VersionInfo
from redbot.core.bot import Red
from discord import User, Member, Role, Guild
from typing import Set, Union, Iterable, Optional


if version_info.dev_release is None and version_info >= VersionInfo.from_str("3.4.13"):
    add_to_blacklist = Red.add_to_blacklist
    get_blacklist = Red.get_blacklist
else:
    UserOrRole = Union[User, Member, Role, int]

    async def add_to_blacklist(bot: Red, users_or_roles: Iterable[UserOrRole], *, guild: Optional[Guild] = None) -> None:
        to_add = {getattr(x, "id", x) for x in users_or_roles}
        await bot._whiteblacklist_cache.add_to_blacklist(guild, to_add)
        bot.dispatch("blacklist_add", to_add, guild)

    async def get_blacklist(bot: Red, guild: Optional[Guild] = None) -> Set[int]:
        return await bot._whiteblacklist_cache.get_blacklist(guild)


async def in_blacklist(bot: Red, user: Union[User, Member, int], guild: Optional[Guild] = None) -> bool:
    blacklist = await get_blacklist(bot, guild)
    return getattr(user, "id", user) in blacklist
