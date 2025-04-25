# Copyright (c) 2021 - Amy (jojo7791)
# Licensed under MIT

from __future__ import annotations

import discord
from typing import Dict, List, Literal, Union, Optional, Self, TYPE_CHECKING

from redbot.core import commands, Config
from redbot.core.bot import Red

from ._types import ChannelType, UserOrRole, UsersOrRoles
from .constants import __author__, __version__
from .menus import Menu, Page
from .patching import startup, destroy

import datetime

try:
    from datetime import UTC

    def _timestamp() -> datetime.datetime:
        return datetime.datetime.now(tz=UTC)

except ImportError:

    def _timestamp() -> datetime.datetime:
        return datetime.datetime.utcnow()


__all___ = ["AdvancedBlacklist"]


_original_commands = ["blocklist", "allowlist"]
_WhiteBlacklist = Literal["whitelist", "blacklist"]


def _format_pages(show: List[str]) -> List[str]:
    pages: List[str]
    current_page: str = ""
    for page in show:
        current_page += f"\n{page}"
        if len(current_page) > 1800:
            pages.append(current_page)
            current_page = ""
    if current_page:
        pages.append(current_page)
    return pages


def _filter_bots(user_or_role: UserOrRole) -> bool:
    return not getattr(user_or_role, "bot", False)


class AdvancedBlacklist(commands.Cog):
    """An extension of the core blacklisting and whitelisting commands

    Allows for adding reasons for blacklisting/whitelisting users/roles
    """

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, 544974305445019651, True)
        self._original_coms: List[commands.Command] = []
        self.log_channel: Optional[ChannelType]

    @classmethod
    async def async_init(cls, bot: Red) -> Self:
        self = cls(bot)
        startup(bot)
        for name in _original_commands:
            local = "local" + name
            self._original_coms.append(bot.remove_command(name))  # type:ignore
            self._original_coms.append(bot.remove_command(local))  # type:ignore
        del name, local
        return self

    async def cog_unload(self) -> None:
        for com in self._original_coms:
            self.bot.add_command(com)
        destroy(self.bot)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        original = super().format_help_for_context(ctx)
        return f"{original}\n\n" f"**Author:** {__author__}\n" f"**Version:** {__version__}"

    @commands.command(name="advancedblacklistversion", hidden=True)
    async def advbl_version(self, ctx: commands.Context) -> None:
        """Get the version info for advancedblacklist"""
        await ctx.send("")

    async def maybe_send_embed(
        self, ctx: commands.Context, message: str, *, title: Optional[str] = None
    ) -> discord.Message:
        footer = "Written with ❤ - Amy (jojo7791)"
        data: Dict[str, Union[str, discord.Embed]]
        if await ctx.embed_requested():
            embed = discord.Embed(
                title=title,
                colour=await ctx.embed_colour(),
                timestamp=_timestamp(),
                description=message,
            )
            embed.set_footer(text=footer)
            data = {"embed": embed}
        else:
            title = f"**{title}**" if title else ""
            message = f"{title}\n\n" f"{message}\n\n" f"-# {footer}"
            data = {"content": message}
        return await ctx.send(**data)

    async def add_to_list(
        self,
        users_or_roles: UsersOrRoles,
        *,
        white_black_list: _WhiteBlacklist,
        reason: str,
        guild: Optional[discord.Guild] = None,
    ) -> None:
        config = getattr((self.config.guild(guild) if guild else self.config), white_black_list)
        async with config.blacklist() as blacklist:
            for item in users_or_roles:
                actual = str(getattr(item, "id", item))
                blacklist[actual] = reason
        del blacklist, item, actual
        await getattr(self.bot, f"add_to_{white_black_list}")(users_or_roles, guild=guild)

    async def remove_from_list(
        self,
        users_or_roles: UsersOrRoles,
        *,
        white_black_list: _WhiteBlacklist,
        guild: Optional[discord.Guild] = None,
    ) -> None:
        config = getattr((self.config.guild(guild) if guild else self.config), white_black_list)
        async with config() as blacklist:
            for item in users_or_roles:
                actual = str(getattr(item, "id", item))
                del blacklist[actual]
        del blacklist, item, actual
        await getattr(self.bot, f"remove_from_{white_black_list}")(users_or_roles, guild=guild)

    async def clear_list(
        self, *, white_black_list: _WhiteBlacklist, guild: Optional[discord.Guild] = None
    ) -> None:
        if guild:
            await getattr(self.config.guild(guild), white_black_list).clear()
        else:
            await getattr(self.config, white_black_list).clear()
        await getattr(self.bot, f"clear_{white_black_list}")(guild=guild)

    async def get_list(
        self, *, white_black_list: _WhiteBlacklist, guild: Optional[discord.Guild] = None
    ) -> Dict[str, str]:
        config = getattr((self.config.guild(guild) if guild else self.config), white_black_list)
        blacklist = await config()
        if blacklist:
            return blacklist

        # We don't have anyone in the blacklist currently
        # Let's check if the bot has anybody in the blacklist
        bot_blacklist = await getattr(self.bot, f"get_{white_black_list}")(guild)
        if not blacklist:
            return {}
        blacklist = {str(i): "No reason provided." for i in bot_blacklist}
        await config.set(blacklist)
        return blacklist

    async def edit_reason(
        self,
        users_or_roles: UsersOrRoles,
        *,
        white_black_list: _WhiteBlacklist,
        reason: str,
        guild: Optional[discord.Guild] = None,
    ) -> None:
        config = getattr((self.config.guild(guild) if guild else self.config), white_black_list)
        async with config() as blacklist:
            for item in users_or_roles:
                actual = str(getattr(item, "id", item))
                blacklist[actual] = reason
        del blacklist, actual, item

    async def in_list(
        self,
        user_or_role: UserOrRole,
        *,
        white_black_list: _WhiteBlacklist,
        guild: Optional[discord.Guild] = None,
    ) -> bool:
        config = getattr((self.config.guild(guild) if guild else self.config), white_black_list)
        actual = str(getattr(user_or_role, "id", user_or_role))
        data = await config()
        if TYPE_CHECKING:
            assert isinstance(data, dict)
        if actual in data.keys():
            return True

        # Okay, didn't find it in the config
        # Let's try in the bot
        data = await self.bot.get_blacklist(guild)
        return int(actual) in data

    @commands.group(name="blocklist", aliases=["denylist", "blacklist"])
    @commands.is_owner()
    async def blocklist(self, ctx: commands.Context) -> None:
        """"""
        pass

    @blocklist.group(name="settings", aliases=["set"])
    async def blocklist_settings(self, ctx: commands.Context) -> None:
        """Settings for AdvancedBlacklist"""
        pass  # TODO Show settings?

    @blocklist_settings.command(name="format")
    async def blocklist_format(
        self, ctx: commands.Context, *, new_format: Optional[str] = None
    ) -> None:
        """Set the format for listing the block/allow list

        Variables:
            `{bot_name}` -> `[botname]`
            `{allow_deny_list}` -> `allowlist` or `blocklist`
            `{version_info}` -> version of AdvancedBlacklist you are running
            `{reason}` -> reason for adding a user/role to the block/allow list
        """
        if not new_format:
            ...  # TODO Show format
            return

    @blocklist.command(name="add")
    async def blocklist_add(
        self,
        ctx: commands.Context,
        users_or_roles: commands.Greedy[UserOrRole],
        *,
        reason: Optional[str] = None,
    ) -> None:
        """Add a user or role to the blocklist

        **Arguments**
            `users_or_roles`        The users or roles to add to the blocklist
            `reason`                      Optional reason, defaults to "No reason provided."
        """
        if not users_or_roles:
            await ctx.send_help(ctx.command)
            return
        users_or_roles = filter(_filter_bots, users_or_roles)  # type:ignore
        if not reason:
            reason = "No reason provided"
        await self.add_to_list(users_or_roles, white_black_list="blacklist", reason=reason)
        await ctx.send("I have added those users/roles to the blocklist")

    @blocklist.command(name="edit")
    async def blocklist_edit(self, ctx: commands.Context, user_or_role: UserOrRole, *, reason: str) -> None:
        """Edit the reason for a blocklisted user/role
        
        **Arguments**
            `user_or_role`         The user or role to edit the reason of
            `reason`                   The new reason
        """
        await self.edit_reason([user_or_role], white_black_list="blacklist", reason=reason)
        await ctx.send("Edited the reason for that user.")

    @blocklist.command(name="list")
    async def blocklist_list(self, ctx: commands.Context) -> None:
        """List the users/roles in the bot's blocklist"""
        list_format: Dict[str, str] = await self.config.format()
        title = list_format["title"].replace("{bot_name}", ctx.me.name)
        footer = list_format["footer"].replace("{}", "")
        user_or_role = list_format["user_or_role"]
        show: List[str] = []

        blocklist = await self.get_list(white_black_list="blacklist", guild=None)
        for item, reason in blocklist.items():
            maybe_user = getattr(self.bot.get_user(int(item)), "name", item)
            user_or_role = user_or_role.replace("{user_or_role}", maybe_user)
            user_or_role = user_or_role.replace("{reason}", reason)
            show.append(user_or_role)
        del maybe_user, item, reason

        show = _format_pages(show)
        page = Page(ctx, show, title=title, footer=footer)
        await Menu.start(page, ctx)
