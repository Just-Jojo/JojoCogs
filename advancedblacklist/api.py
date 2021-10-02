# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from typing import Iterable, Optional, Set, Union

import discord
from redbot import VersionInfo, version_info
from redbot.core.bot import Red

__all__ = [
    "add_to_blacklist",
    "remove_from_blacklist",
    "get_blacklist",
    "clear_blacklist",
    "add_to_whitelist",
    "remove_from_whitelist",
    "get_whitelist",
    "clear_whitelist",
]

# Backwards compatability :D

# Check for dev version as a fork might not have the blacklist api. Better safe than sorry
if version_info >= VersionInfo.from_str("3.4.13") and version_info.dev_release is None:
    add_to_blacklist = Red.add_to_blacklist
    remove_from_blacklist = Red.remove_from_blacklist
    get_blacklist = Red.get_blacklist
    clear_blacklist = Red.clear_blacklist
    add_to_whitelist = Red.add_to_whitelist
    remove_from_whitelist = Red.remove_from_whitelist
    get_whitelist = Red.get_whitelist
    clear_whitelist = Red.clear_whitelist
else:
    UserOrRole = Union[discord.Member, discord.User, discord.Role, int]

    async def add_to_blacklist(
        bot: Red,
        users_or_roles: Iterable[UserOrRole],
        *,
        guild: Optional[discord.Guild] = None,
    ):
        to_add = {getattr(uor, "id", uor) for uor in users_or_roles}
        await bot._whiteblacklist_cache.add_to_blacklist(guild, to_add)

    async def remove_from_blacklist(
        bot: Red,
        users_or_roles: Iterable[UserOrRole],
        *,
        guild: Optional[discord.Guild] = None,
    ):
        to_remove = {getattr(uor, "id", uor) for uor in users_or_roles}
        await bot._whiteblacklist_cache.remove_from_blacklist(guild, to_remove)

    async def get_blacklist(bot: Red, guild: Optional[discord.Guild] = None) -> Set[int]:
        return await bot._whiteblacklist_cache.get_blacklist(guild)

    async def clear_blacklist(bot: Red, guild: Optional[discord.Guild] = None):
        await bot._whiteblacklist_cache.clear_blacklist(guild)

    async def add_to_whitelist(
        bot: Red,
        users_or_roles: Iterable[UserOrRole],
        *,
        guild: Optional[discord.Guild] = None,
    ) -> None:
        to_add = {getattr(uor, "id", uor) for uor in users_or_roles}
        await bot._whiteblacklist_cache.add_to_whitelist(guild, to_add)

    async def remove_from_whitelist(
        bot: Red,
        users_or_roles: Iterable[UserOrRole],
        *,
        guild: Optional[discord.Guild] = None,
    ) -> None:
        to_remove = {getattr(uor, "id", uor) for uor in users_or_roles}
        await bot._whiteblacklist_cache.remove_from_whitelist(guild, to_remove)

    async def get_whitelist(bot: Red, guild: Optional[discord.Guild] = None) -> Set[int]:
        return await bot._whiteblacklist_cache.get_whitelist(guild)

    async def clear_whitelist(bot: Red, guild: Optional[discord.Guild] = None) -> None:
        await bot._whiteblacklist_cache.clear_whitelist(guild)
