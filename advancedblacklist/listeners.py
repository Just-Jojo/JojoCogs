# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from redbot.core import commands, Config
from redbot.core.bot import Red
import discord

from typing import Optional, Set



class BlacklistEvent:
    config: Config
    bot: Red

    @commands.Cog.listener()
    async def on_blacklist_add(self, guild: Optional[discord.Guild], items: Set[int]):
        coro = self.config
        if guild:
            coro = coro.guild(guild)
        users = sorted(list(items), key=lambda x: self.bot.get_user(x) is not None)
        users = [str(x) for x in users]
        async with coro.blacklist() as bl:
            for user in users:
                if bl.get(user):
                    continue
                bl[user] = f"Blacklisted via external means"

    @commands.Cog.listener()
    async def on_blacklist_remove(self, guild: Optional[discord.Guild], items: Set[int]):
        coro = self.config
        if guild:
            coro = coro.guild(guild)
        users = sorted(list(items), key=lambda x: self.bot.get_user(x) is not None)
        users = [str(x) for x in users]
        async with coro.blacklist() as bl:
            for user in users:
                try:
                    bl.remove(user)
                except ValueError:
                    pass

    @commands.Cog.listener()
    async def on_blacklist_clear(self, guild: Optional[discord.Guild]):
        coro = self.config
        if guild:
            coro = coro.guild(guild)
        await coro.blacklist.set({})

    @commands.Cog.listener()
    async def on_whitelist_add(self, guild: Optional[discord.Guild], items: Set[int]):
        coro = self.config
        if guild:
            coro = coro.guild(guild)
        users = sorted(list(items), key=lambda x: self.bot.get_user(x) is not None)
        users = [str(x) for x in users]
        async with coro.whitelist() as bl:
            for user in users:
                if bl.get(user):
                    continue
                bl[user] = "Whitelisted via external means"

    @commands.Cog.listener()
    async def on_whitelist_remove(self, guild: Optional[discord.Guild], items: Set[int]):
        coro = self.config
        if guild:
            coro = coro.guild(guild)
        users = sorted(list(items), key=lambda x: self.bot.get_user(x) is not None)
        users = [str(x) for x in users]
        async with coro.whitelist() as wl:
            for user in users:
                try:
                    wl.remove(user)
                except ValueError:
                    pass

    @commands.Cog.listener()
    async def on_whitelist_clear(self, guild: Optional[discord.Guild]):
        coro = self.config
        if guild:
            coro = coro.guild(guild)
        await coro.whitelist.set({})
