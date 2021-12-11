# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import logging
from typing import Callable, Dict, Set

import discord
from redbot.core.bot import Red
from redbot.core.settings_caches import WhitelistBlacklistManager

log = logging.getLogger("red.jojocogs.advancedblacklist.patch")
__all__ = ["init", "destory"]

_monke_patched_names: Set[str] = {
    "add_to_blacklist",
    "remove_from_blacklist",
    "clear_blacklist",
    "add_to_whitelist",
    "remove_from_whitelist",
    "clear_whitelist",
}
_original_funcs: Dict[str, Callable] = {}
initialized: bool = False


def init(bot: Red):
    global initialized
    if initialized:
        return
    initialized = True

    async def add_to_blacklist(
        self: WhitelistBlacklistManager,
        guild: discord.Guild,
        user_or_role: Set[int],
        *,
        dispatch: bool = True
    ):
        await _original_funcs["add_to_blacklist"](self, guild, user_or_role)
        if dispatch:
            bot.dispatch("blacklist_add", guild, user_or_role)

    async def remove_from_blacklist(
        self: WhitelistBlacklistManager,
        guild: discord.Guild,
        user_or_role: Set[int],
        *,
        dispatch: bool = True
    ):
        await _original_funcs["remove_from_blacklist"](self, guild, user_or_role)
        if dispatch:
            bot.dispatch("blacklist_remove", guild, user_or_role)

    async def clear_blacklist(
        self: WhitelistBlacklistManager, guild: discord.Guild, *, dispatch: bool = True
    ):
        await _original_funcs["clear_blacklist"](self, guild)
        if dispatch:
            bot.dispatch("blacklist_clear", guild)

    async def add_to_whitelist(
        self: WhitelistBlacklistManager,
        guild: discord.Guild,
        user_or_role: Set[int],
        *,
        dispatch: bool = True
    ):
        await _original_funcs["add_to_whitelist"](self, guild, user_or_role)
        if dispatch:
            bot.dispatch("whitelist_add", guild, user_or_role)

    async def remove_from_whitelist(
        self: WhitelistBlacklistManager,
        guild: discord.Guild,
        user_or_role: Set[int],
        *,
        dispatch: bool = True
    ):
        await _original_funcs["remove_from_whitelist"](self, guild, user_or_role)
        if dispatch:
            bot.dispatch("whitelist_remove", guild, user_or_role)

    async def clear_whitelist(
        self: WhitelistBlacklistManager, guild: discord.Guild, *, dispatch: bool = True
    ):
        await _original_funcs["clear_whitelist"](self, guild)
        if dispatch:
            bot.dispatch("whitelist_clear", guild)

    # This cog is basically "How lazy can Jojo be?"
    l = locals()
    for name in _monke_patched_names:
        _original_funcs[name] = getattr(WhitelistBlacklistManager, name)
        setattr(WhitelistBlacklistManager, name, l[name])


def destroy():
    if not initialized:
        return
    for key, value in _original_funcs.items():
        setattr(WhitelistBlacklistManager, key, value)
