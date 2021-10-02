# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from typing import Callable, Iterable, List, Optional

import discord
from discord.utils import copy_doc
from redbot.core.bot import Red
from redbot.core.settings_caches import WhitelistBlacklistManager as WBM

__all__ = ["setup", "teardown"]
BOT: Optional[Red] = None

# Monke
#        _
#      c ".
# \_   / \^
#   \_| ||


@copy_doc(WBM.add_to_blacklist)
async def add_to_blacklist(
    self: WBM, guild: Optional[discord.Guild], role_or_user: Iterable[int]
):
    d = await _FUNCS[0](self, guild, role_or_user)
    if BOT:
        BOT.dispatch("blacklist_add", guild, set(role_or_user))
    return d


@copy_doc(WBM.remove_from_blacklist)
async def remove_from_blacklist(
    self: WBM, guild: Optional[discord.Guild], role_or_user: Iterable[int]
):
    d = await _FUNCS[1](self, guild, role_or_user)
    if BOT:
        BOT.dispatch("blacklist_remove", guild, set(role_or_user))
    return d


@copy_doc(WBM.clear_blacklist)
async def clear_blacklist(self: WBM, guild: Optional[discord.Guild]):
    d = await _FUNCS[2](self, guild)
    if BOT:
        BOT.dispatch("blacklist_clear", guild)
    return d


@copy_doc(WBM.add_to_whitelist)
async def add_to_whitelist(
    self: WBM, guild: Optional[discord.Guild], role_or_user: Iterable[int]
):
    d = await _FUNCS[3](self, guild, role_or_user)
    if BOT:
        BOT.dispatch("whitelist_add", guild, set(role_or_user))
    return d


@copy_doc(WBM.remove_from_whitelist)
async def remove_from_whitelist(
    self: WBM, guild: Optional[discord.Guild], role_or_user: Iterable[int]
):
    d = await _FUNCS[4](self, guild, role_or_user)
    if BOT:
        BOT.dispatch("whitelist_remove", guild, set(role_or_user))
    return d


@copy_doc(WBM.clear_whitelist)
async def clear_whitelist(self: WBM, guild: Optional[discord.Guild]):
    d = await _FUNCS[5](self, guild)
    if BOT:
        BOT.dispatch("whitelist_clear", guild)
    return d


_ = [
    add_to_blacklist,
    remove_from_blacklist,
    clear_blacklist,
    add_to_whitelist,
    remove_from_whitelist,
    clear_whitelist,
]
funcs = {func.__name__: func for func in _}
_OG = {func.__name__: getattr(WBM, func.__name__) for func in _}
_FUNCS = list(_OG.values())


def setup(bot: Red):
    global BOT
    BOT = bot
    for key, value in funcs.items():
        setattr(WBM, key, value)


def teardown():
    for key, value in _OG.items():
        setattr(WBM, key, value)
