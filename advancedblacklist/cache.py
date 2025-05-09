from __future__ import annotations

import discord

from typing import Optional
from ._types import UserOrRole


__all__ = ("Cache",)


class Cache:
    def __init__(self):
        self.__bl_internal = {"global": {}, "guild": {}}
        self.__wl_internal = {"global": {}, "guild": {}}

    def get_whitelist(self, guild: Optional[discord.Guild]) -> dict:
        if guild:
            return self.__wl_internal["guild"].get(guild.id, {})
        return self.__wl_internal["global"]

    def get_blacklist(self, guild: Optional[discord.Guild]) -> dict:
        if guild:
            return self.__bl_internal["guild"].get(guild.id, {})
        return self.__bl_internal["global"]

    def get_whitelist_user(self, guild: Optional[discord.Guild], user_or_role: UserOrRole) -> dict:
        return self.get_whitelist(guild).get(str(getattr(user_or_role, "id", user_or_role)), {})

    def get_blacklist_user(self, guild: Optional[discord.Guild], user_or_role: UserOrRole) -> dict:
        return self.get_blacklist(guild).get(str(getattr(user_or_role, "id", user_or_role)), {})

    def update_whitelist(self, guild: Optional[discord.Guild], data: dict) -> None:
        if guild:
            try:
                self.__wl_internal["guild"][guild.id].update(data)
            except KeyError:
                self.__wl_internal["guild"][guild.id] = data
            return
        self.__wl_internal["global"].update(data)

    def update_blacklist(self, guild: Optional[discord.Guild], data: dict) -> None:
        if guild:
            try:
                self.__bl_internal["guild"][guild.id].update(data)
            except KeyError:
                self.__bl_internal["guild"][guild.id] = data
            return
        self.__bl_internal["global"].update(data)

    def clear_whitelist(self, guild: Optional[discord.Guild]) -> None:
        if guild:
            self.__wl_internal["guild"][guild.id] = {}
            return
        self.__wl_internal["global"] = {}

    def clear_blacklist(self, guild: Optional[discord.Guild]) -> None:
        if guild:
            self.__bl_internal["guild"][guild.id] = {}
            return
        self.__bl_internal["global"] = {}
