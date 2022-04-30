# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from __future__ import annotations

import logging
from contextlib import suppress
from types import ModuleType
from typing import Optional, Set, Union

import discord  # type:ignore
import datetime
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_list, pagify

from .abc import CompositeMetaclass
from .commands import Blacklist, Whitelist
from .commands.utils import (add_to_blacklist, add_to_whitelist, clear_blacklist, clear_whitelist,
                             in_blacklist, in_whitelist, remove_from_blacklist,
                             remove_from_whitelist, startup)
from .const import __authors__, __version__
from .patch import destroy, init

log = logging.getLogger("red.jojocogs.advancedblacklist")


def api_tool(ctx: commands.Context) -> ModuleType:
    from .commands.utils import api

    return api


class AdvancedBlacklist(Blacklist, Whitelist, commands.Cog, metaclass=CompositeMetaclass):
    """An advanced blacklist cog for more control over your blacklist"""

    def __init__(self, bot: Red):
        self.bot = bot
        self._commands: Set[Optional[commands.Command]] = set()
        self.config = Config.get_conf(self, 544974305445019651, True) # Log channel stuff
        self._log_channel: Optional[discord.TextChannel] = None
        self._task = self.bot.loop.create_task(startup(self.bot))
        self._log_task = self.bot.loop.create_task(self._get_log_channel())
        init(self.bot)
        for k, v in {"advbl": (lambda x: self), "abapi": api_tool}.items():
            with suppress(RuntimeError):
                self.bot.add_dev_env_value(k, v)

    def cog_unload(self):
        for cmd in self._commands:
            self.bot.add_command(cmd)
        self._task.cancel()
        self._log_task.cancel()
        destroy()

    @classmethod
    async def init(cls, bot: Red) -> AdvancedBlacklist:
        self: AdvancedBlacklist = cls(bot)
        for c in ["blocklist", "allowlist"]:
            self._commands |= {self.bot.remove_command(y) for y in (c, f"local{c}")}
            # I am lazy :)
        return self

    async def _get_log_channel(self) -> None:
        await self.bot.wait_until_red_ready()
        cid = await self.config.log_channel()
        if not cid:
            return
        channel = self.bot.get_channel(cid)
        if not channel:
            try:
                channel = await self.bot.fetch_channel(cid)
            except discord.HTTPException:
                return
        self._log_channel = channel

    async def _log_message(self, msg: str) -> None:
        log.info(msg)
        msg += f"\n{self._get_timestamp()}"
        try:
            if len(msg) <= 2000:
                await self._log_channel.send(content=msg)
                return
            for i in pagify(msg, delims=[","], page_length=400):
                await self._log_channel.send(content=i)
        except discord.Forbidden:
            self._log_channel = None
            await self.config.log_channel.clear()
            log.info("Could not log to the log channel. Resetting log channel.")

    def format_help_for_context(self, ctx: commands.Context) -> str:
        plural = "" if len(__authors__) == 1 else "s"
        return (
            f"{super().format_help_for_context(ctx)}\n\n"
            f"**Author{plural}:** {humanize_list([f'`{a}`' for a in __authors__])}\n"
            f"**Version:** {__version__}"
        )

    @staticmethod
    def _guild_global(guild: Optional[discord.Guild]) -> str:
        return "the bot's" if not guild else f"{guild.name} ({guild.id})'s"

    @staticmethod
    def _get_timestamp() -> str:
        return f"<t:{int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())}>"

    @commands.command(name="advancedblacklistversion", aliases=("abversion",))
    async def advanced_blacklist_version(self, ctx: commands.Context):
        """Get the version of Advanced Blacklist that [botname] is running"""
        await ctx.send(
            f"Advanced Blacklist, version `{__version__}` "
            f"by {humanize_list([f'`{a}`' for a in __authors__])}"
        )

    @commands.Cog.listener()
    async def on_blacklist_add(self, guild: discord.Guild, users: Set[int]):
        u = str(users)[1:-1]
        users = {u for u in users if not await in_blacklist(self.bot, u, guild)}
        if users:
            log.debug(f"Adding these users to the blacklist config. {users = }. {guild = }")
            await add_to_blacklist(self.bot, users, "No reason provided.", guild=guild, override=True)
        if not self._log_channel:
            return
        msg = f"Added these users/roles to {self._guild_global(guild)} blacklist.\n\n{u}"
        await self._log_message(msg)

    @commands.Cog.listener()
    async def on_blacklist_remove(self, guild: discord.Guild, users: Set[int]):
        u = str(users)[1:-1]
        users = {u for u in users if await in_blacklist(self.bot, u, guild)}
        if users:
            log.debug(f"Removing these users from the blacklist config. {users = }. {guild = }")
            await remove_from_blacklist(self.bot, users, guild=guild, override=True)
        if not self._log_channel:
            return
        msg = f"Removed these users/roles from {self._guild_global(guild)} blacklist.\n\n{u}"
        await self._log_message(msg)

    @commands.Cog.listener()
    async def on_blacklist_clear(self, guild: discord.Guild):
        log.debug(f"Clearing blacklist config. {guild = }")
        await clear_blacklist(self.bot, guild, True)
        if not self._log_channel:
            return
        msg = f"Cleared {self._guild_global(guild)} blacklist."
        await self._log_message(msg)

    @commands.Cog.listener()
    async def on_whitelist_add(self, guild: discord.Guild, users: Set[int]):
        u = str(users)[1:-1]
        users = {u for u in users if not await in_whitelist(self.bot, u, guild)}
        if users:
            log.debug(f"Adding these users to the whitelist config. {users = }. {guild = }")
            await add_to_whitelist(self.bot, users, "No reason provided.", guild=guild, override=True)
        if not self._log_channel:
            return
        msg = f"Added these users/roles to {self._guild_global(guild)} whitelist.\n\n{u}"
        await self._log_message(msg)

    @commands.Cog.listener()
    async def on_whitelist_remove(self, guild: discord.Guild, users: Set[int]):
        u = str(users)[1:-1] # :kappa:
        users = {u for u in users if await in_whitelist(self.bot, u, guild)}
        if users:
            log.debug(f"Removing these users/roles from the whitelist config. {users = }. {guild = }")
            await remove_from_whitelist(self.bot, users, guild=guild, override=True)
        if not self._log_channel:
            return
        msg = (
            f"Removed these users from {self._guild_global(guild)} "
            f"whitelist.\n\n{u}\n\n{self._get_timestamp()}"
        )
        await self._log_message(msg)

    @commands.Cog.listener()
    async def on_whitelist_clear(self, guild: discord.Guild):
        log.debug(f"Clearing the whitelist config. {guild = }")
        await clear_whitelist(self.bot, guild, override=True)
        if not self._log_channel:
            return
        msg = f"Cleared {self._guild_global(guild)} whitelist."
        await self._log_message(msg)

    @commands.Cog.listener()
    async def on_error_blacklist(self, user: discord.User, command: commands.Command):
        await add_to_blacklist(
            self.bot,
            {user.id},
            f"Used the command '{command.name}' which errored too many times",
        )
        if not self._log_channel:
            return
        msg = f"Blacklisted {user.id} for using '{command.name}' which errored too many times."
        await self._log_message(msg)

    def _get_user(
        self, ctx: commands.Context, member_id: str
    ) -> Optional[Union[discord.Member, discord.User]]:
        mid = int(member_id)
        ret: Optional[discord.Member] = None
        if ctx.guild:
            ret = ctx.guild.get_member(mid)
        return ret or self.bot.get_user(mid)
