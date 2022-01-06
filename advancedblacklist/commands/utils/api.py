# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from typing import Dict, Iterable, Optional, Union

from discord import Guild, Member, Role, User
from redbot.core import Config
from redbot.core.bot import Red

from ...const import _config_structure  # type:ignore

__all__ = [
    "add_to_blacklist",
    "add_to_whitelist",
    "clear_blacklist",
    "clear_whitelist",
    "edit_reason",
    "get_blacklist",
    "get_whitelist",
    "in_blacklist",
    "in_whitelist",
    "remove_from_blacklist",
    "remove_from_whitelist",
]

_config = Config.get_conf(None, 544974305445019651, True, "AdvancedBlacklist")
[getattr(_config, f"register_{x}", lambda **z: z)(**z) for x, z in _config_structure.items()]
UserOrRole = Union[Role, Member, User]


async def add_to_blacklist(
    bot: Red,
    users_or_roles: Iterable[UserOrRole],
    reason: str,
    *,
    guild: Optional[Guild] = None,
    override: Optional[bool] = False,
) -> None:
    coro = _config if not guild else _config.guild(guild)
    async with coro.blacklist() as bl:
        for item in users_or_roles:
            item = str(getattr(item, "id", item))
            bl[item] = reason
    if override:
        return
    await bot._whiteblacklist_cache.add_to_blacklist(  # type:ignore
        guild, {getattr(u, "id", u) for u in users_or_roles}, dispatch=False
    )


async def remove_from_blacklist(
    bot: Red,
    users_or_roles: Iterable[UserOrRole],
    *,
    guild: Optional[Guild] = None,
    override: Optional[bool] = False,
) -> None:
    coro = _config if not guild else _config.guild(guild)
    async with coro.blacklist() as bl:
        for item in users_or_roles:
            item = str(getattr(item, "id", item))
            bl.pop(item, None)
    if override:
        return
    await bot._whiteblacklist_cache.remove_from_blacklist(  # type:ignore
        guild, {getattr(u, "id", u) for u in users_or_roles}, dispatch=False
    )


async def in_blacklist(bot: Red, id: int, guild: Optional[Guild] = None) -> bool:
    coro = _config if not guild else _config.guild(guild)
    data = await coro.blacklist()
    return str(id) in data.keys()


async def edit_reason(
    bot: Red,
    user: Union[User, Member, int],
    reason: str,
    whitelist: bool,
    *,
    guild: Optional[Guild] = None,
) -> None:
    attr = "whitelist" if whitelist else "blacklist"
    coro = getattr((_config if not guild else _config.guild(guild)), attr)
    uid = getattr(user, "id", user)
    async with coro() as edit:
        edit[str(uid)] = reason


async def get_blacklist(bot: Red, guild: Optional[Guild] = None) -> Dict[str, str]:
    coro = _config if not guild else _config.guild(guild)
    return await coro.blacklist()


async def clear_blacklist(
    bot: Red, guild: Optional[Guild] = None, override: Optional[bool] = False
) -> None:
    coro = _config if not guild else _config.guild(guild)
    await coro.blacklist.clear()
    if override:
        return
    await bot._whiteblacklist_cache.clear_blacklist(guild, dispatch=False)  # type:ignore


async def add_to_whitelist(
    bot: Red,
    users_or_roles: Iterable[UserOrRole],
    reason: str,
    *,
    guild: Optional[Guild] = None,
    override: Optional[bool] = False,
) -> None:
    coro = _config if not guild else _config.guild(guild)
    async with coro.whitelist() as wl:
        for item in users_or_roles:
            item = str(getattr(item, "id", item))
            wl[item] = reason
    if override:
        return
    await bot._whiteblacklist_cache.add_to_whitelist(  # type:ignore
        guild, {getattr(u, "id", u) for u in users_or_roles}, dispatch=False
    )


async def remove_from_whitelist(
    bot: Red,
    users_or_roles: Iterable[UserOrRole],
    *,
    guild: Optional[Guild] = None,
    override: Optional[bool] = False,
) -> None:
    coro = _config if not guild else _config.guild(guild)
    async with coro.whitelist() as wl:
        for item in users_or_roles:
            item = str(getattr(item, "id", item))
            wl.pop(item, None)
    if override:
        return
    await bot._whiteblacklist_cache.remove_from_whitelist(  # type:ignore
        guild, {getattr(u, "id", u) for u in users_or_roles}, dispatch=False
    )


async def get_whitelist(bot: Red, guild: Optional[Guild] = None) -> Dict[str, str]:
    coro = _config if not guild else _config.guild(guild)
    return await coro.whitelist()


async def in_whitelist(bot: Red, id: int, guild: Optional[Guild] = None) -> bool:
    coro = _config if not guild else _config.guild(guild)
    data = await coro.whitelist()
    return str(id) in data.keys()


async def clear_whitelist(
    bot: Red, guild: Optional[Guild] = None, override: Optional[bool] = False
) -> None:
    coro = _config if not guild else _config.guild(guild)
    await coro.whitelist.clear()
    if override:
        return
    await bot._whiteblacklist_cache.clear_whitelist(guild, dispatch=False)  # type:ignore
