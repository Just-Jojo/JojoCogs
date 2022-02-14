# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from typing import Dict, Iterable, Optional, Union

from discord import Guild, Member, Role, User
from redbot.core import Config
from redbot.core.bot import Red
import logging

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
    "startup",
]

log = logging.getLogger("red.jojocogs.advancedblacklist.api")
_config = Config.get_conf(None, 544974305445019651, True, "AdvancedBlacklist")
[getattr(_config, f"register_{x}", lambda **z: z)(**z) for x, z in _config_structure.items()]
UserOrRole = Union[Role, Member, User]

async def startup(bot: Red):
    await _schema_check()
    for i in ("whitelist", "blacklist"):
        async with getattr(_config, i)() as bl:
            blacklist = await getattr(bot._whiteblacklist_cache, f"get_{i}")(None)
            for uid in blacklist:
                if str(uid) in bl.keys():
                    continue
                bl[str(uid)] = "No reason provided."
            keys = list(bl.keys())
            for key in keys:
                if int(key) not in blacklist:
                    bl.pop(key)
    for guild in bot.guilds:
        for i in ("whitelist", "blacklist"):
            async with getattr(_config.guild(guild), i)() as bl:
                blacklist = await getattr(bot._whiteblacklist_cache, f"get_{i}")(guild)
                for uid in blacklist:
                    if str(uid) in bl.keys():
                        continue
                    bl[str(uid)] = "No reason provided."
                keys = list(bl.keys())
                for key in keys:
                    if int(key) not in blacklist:
                        bl.pop(key)


async def _schema_check():
    data = await _config.all()
    if data.get("schema_v1"):
        return
    log.debug("Schema no tbh")
    guild_data = data.pop("localblacklist", None)
    if guild_data:
        for gid, gdata in guild_data.items():
            await _config.guild_from_id(gid).set_raw("blacklist", value=gdata)
    await _config.schema_v1.set(True)


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
    return str(id) in data.keys() or id in await bot._whiteblacklist_cache.get_blacklist(guild)


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
    ret = await coro.blacklist()
    if not ret:
        # So, we don't have a blacklist in the config
        # Let's check if the bot has a blacklist in the cache
        blacklist = await bot._whiteblacklist_cache.get_blacklist(guild)
        if not blacklist:
            return {}
        ret = {str(i): "No reason provided." for i in blacklist}
        await coro.blacklist.set(ret)
    return ret


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
    ret = await coro.whitelist()
    if not ret:
        # Like with the `get_blacklist` method let's check the bot's whitelist
        whitelist = await bot._whiteblacklist_cache.get_whitelist(guild)
        if not whitelist:
            return {}
        ret = {str(i): "No reason provided." for i in whitelist}
        await coro.whitelist.set(ret)
    return ret


async def in_whitelist(bot: Red, id: int, guild: Optional[Guild] = None) -> bool:
    coro = _config if not guild else _config.guild(guild)
    data = await coro.whitelist()
    return str(id) in data.keys() or id in await bot._whiteblacklist_cache.get_whitelist(guild)


async def clear_whitelist(
    bot: Red, guild: Optional[Guild] = None, override: Optional[bool] = False
) -> None:
    coro = _config if not guild else _config.guild(guild)
    await coro.whitelist.clear()
    if override:
        return
    await bot._whiteblacklist_cache.clear_whitelist(guild, dispatch=False)  # type:ignore
