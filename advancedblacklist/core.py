# Copyright (c) 2021 - Amy (jojo7791)
# Licensed under MIT

from __future__ import annotations

import discord
from typing import Dict, List, Literal, Union, Tuple, Optional, Self, TYPE_CHECKING

from redbot.core import commands, Config
from redbot.core.bot import Red

from ._types import ChannelType, GreedyUserOrRole, UserOrRole, UsersOrRoles
from .constants import __author__, __version__, default_format, config_structure
from .menus import Menu, Page
from .patching import startup, destroy


try:
    import orjson

except ImportError:
    import json as orjson  # type:ignore # mypy momen

import datetime

try:
    from datetime import UTC as DATETIME_UTC

except ImportError:
    from datetime import timezone

    DATETIME_UTC = timezone.utc


def _timestamp() -> datetime.datetime:
    return datetime.datetime.now(tz=DATETIME_UTC)


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


def _format_str(string: str, replace: Dict[str, str]) -> str:
    for key, value in replace.items():
        string = string.replace(key, value)
    return string


async def _filter_bots(
    ctx: commands.Context, users_or_roles: UsersOrRoles
) -> Tuple[bool, UsersOrRoles]:
    for i in range(2):
        if not users_or_roles:
            if i == 1:
                await ctx.send("Those users were bots!")
            else:
                await ctx.send_help()
            return False, []
        users_or_roles = filter(lambda x: not getattr(x, "bot", False), users_or_roles)
    return True, users_or_roles


class AdvancedBlacklist(commands.Cog):
    """An extension of the core blocklisting and allowlisting commands

    Allows for adding reasons for blocklisting/allowlisting users/roles
    and changing the format for the lists

    See `[p]advancedblacklistversion` for version and author information
    """

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, 544974305445019651, True)
        for config_type, data in config_structure.items():
            getattr(self.config, f"register_{config_type}")(**data)
        del config_type, data
        self._original_coms: List[commands.Command] = []
        self.log_channel: Optional[ChannelType]  # TODO(Amy) see if I wanna do this

    @classmethod
    async def async_init(cls, bot: Red) -> Self:
        self = cls(bot)
        startup(bot)
        for name in _original_commands:
            local = "local" + name
            global_com = bot.remove_command(name)
            local_com = bot.remove_command(local)
            if TYPE_CHECKING:
                assert isinstance(global_com, commands.Command), "mypy"
                assert isinstance(local_com, commands.Command), "mypy"
            self._original_coms.append(global_com)
            self._original_coms.append(local_com)
        del name, local
        return self

    async def cog_unload(self) -> None:
        destroy(self.bot)
        for com in self._original_coms:
            self.bot.add_command(com)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        original = super().format_help_for_context(ctx)
        return f"""{original}

        **Author:** {__author__}
        **Version:** {__version__}
        """

    async def maybe_send_embed(
        self,
        ctx: commands.Context,
        message: str,
        *,
        title: Optional[str] = None,
        footer: Optional[str] = None,
    ) -> discord.Message:
        data: Dict[str, Union[str, discord.Embed]]
        if await ctx.embed_requested():
            embed = discord.Embed(
                title=title,
                colour=await ctx.embed_colour(),
                timestamp=_timestamp(),
                description=message,
            )
            if footer:
                embed.set_footer(text=footer)
            data = {"embed": embed}
        else:
            title = f"**{title}**" if title else ""
            message = f"{title}\n\n{message}"
            if footer:
                message += f"\n\n-# {footer}"
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
                if actual in blacklist:
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
        user_or_role: UserOrRole,
        *,
        white_black_list: _WhiteBlacklist,
        reason: str,
        guild: Optional[discord.Guild] = None,
    ) -> None:
        config = getattr((self.config.guild(guild) if guild else self.config), white_black_list)
        async with config() as blacklist:
            actual = str(getattr(user_or_role, "id", user_or_role))
            blacklist[actual] = reason
        del blacklist, actual

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
        if actual in data:
            return True

        # Okay, didn't find it in the config
        # Let's try in the bot
        data = await self.bot.get_blacklist(guild)
        return int(actual) in data

    @commands.command(name="advancedblacklistversion", hidden=True)
    async def advbl_version(self, ctx: commands.Context) -> None:
        """Get the version info for advancedblacklist"""
        version_info = (
            f"{ctx.me.name} running version {__version__}\n"
            f"For more information/bug reporting, see [the github]"
            f"(https://github.com/Just-Jojo/JojoCogs)"
        )
        footer = "Made with ❤ by Amy (jojo7791)"
        await self.maybe_send_embed(
            ctx, version_info, title="AdvancedBlacklist - JojoCogs", footer=footer
        )

    @commands.group(name="blocklist", aliases=["denylist", "blacklist"])
    @commands.is_owner()
    async def blocklist(self, ctx: commands.Context) -> None:
        """"""
        pass

    @blocklist.group(name="settings", aliases=["set"])
    async def blocklist_settings(self, ctx: commands.Context) -> None:
        """Settings for AdvancedBlacklist"""
        pass

    @blocklist.command(name="showsettings", aliases=["settings"])
    async def blocklist_settings_showsettings(self, ctx: commands.Context) -> None:
        """Show the settings for AdvancedBlacklist"""

    @blocklist_settings.command(name="format")
    async def blocklist_format(
        self, ctx: commands.Context, *, new_format: Optional[str] = None
    ) -> None:
        """Set the format for listing the block/allow list

        Arguments:
            `new_format`    The new format the bot will use to list the block/allowlist.
            This will be loaded as JSON.

        Variables:
            `{bot_name}` -> `[botname]`
            `{allow_deny_list}` -> `allowlist` or `blocklist`
            `{version_info}` -> version of AdvancedBlacklist you are running
            `{reason}` -> reason for adding a user/role to the block/allow list
        """
        if not new_format:
            await self._show_format(ctx)
            return

        try:
            json_obj = orjson.loads(new_format)
        except orjson.JSONDecodeError:
            # TODO(Amy) maybe use yaml instead :p
            await ctx.send("That was not valid JSON, please try again")
            return
        else:
            if isinstance(json_obj, list):
                await ctx.send("Must be a map, not a list")
                return

        to_add = {}
        current_format = await self.config.format()
        if TYPE_CHECKING:
            assert isinstance(current_format, dict), "mypy"
            assert isinstance(json_obj, dict)
        for key, value in current_format.items():
            to_add[key] = json_obj.get(key, value)

        await self.config.format.set(to_add)
        await ctx.send("The block/allowlist will now use that format")

    async def _show_format(self, ctx: commands.Context) -> None:
        settings = await self.config.format()

    @blocklist.command(name="add")
    async def blocklist_add(
        self,
        ctx: commands.Context,
        users_or_roles: GreedyUserOrRole,
        *,
        reason: Optional[str] = None,
    ) -> None:
        """Add a user or role to the blocklist

        **Arguments**
            `users_or_roles`    The users or roles to add to the blocklist
            `reason`                  Optional reason, defaults to "No reason provided."
        """
        worked, users_or_roles = await _filter_bots(ctx, users_or_roles)
        if not worked:
            return

        if not reason:
            reason = "No reason provided"
        await self.add_to_list(users_or_roles, white_black_list="blacklist", reason=reason)
        await ctx.send("I have added those users/roles to the blocklist")

    @blocklist.command(name="remove", aliases=["del", "delete"])
    async def blocklist_remove(
        self, ctx: commands.Context, users_or_roles: GreedyUserOrRole
    ) -> None:
        """Remove users or roles from the blocklist"""
        worked, users_or_roles = await _filter_bots(ctx, users_or_roles)
        if not worked:
            return

        await self.remove_from_list(users_or_roles, white_black_list="whitelist", guild=None)
        if len(list(users_or_roles)) > 1:
            await ctx.send("Removed those users/roles from the blocklist")
        else:
            await ctx.send("Removed that user/role from the blocklist")

    @blocklist.command(name="edit")
    async def blocklist_edit(
        self, ctx: commands.Context, user_or_role: UserOrRole, *, reason: str
    ) -> None:
        """Edit the reason for a blocklisted user/role

        **Arguments**
            `user_or_role`         The user or role to edit the reason of
            `reason`                   The new reason
        """
        if isinstance(user_or_role, discord.Member) and user_or_role.bot:
            await ctx.send("That user is a bot!")
            return
        elif not await self.in_list(user_or_role, white_black_list="blacklist"):
            await ctx.send("That user/role is not in the blocklist")
            return
        await self.edit_reason(user_or_role, white_black_list="blacklist", reason=reason)
        await ctx.send("Edited the reason for that user")

    @blocklist.command(name="list")
    async def blocklist_list(self, ctx: commands.Context) -> None:
        """List the users/roles in the bot's blocklist"""
        list_format: Dict[str, str] = await self.config.format()
        format_settings = {
            "{reason}": "",
            "{bot_name}": ctx.me.name,
            "{version_info}": __version__,
            "{user_or_role}": "",
        }
        title = _format_str(list_format["title"], format_settings)
        footer = _format_str(list_format["footer"], format_settings)
        user_or_role = list_format["user_or_role"]
        show: List[str] = []

        blocklist = await self.get_list(white_black_list="blacklist", guild=None)
        for item, reason in blocklist.items():
            maybe_user = getattr(self.bot.get_user(int(item)), "name", item)
            format_settings.update({"{user_or_role}": maybe_user, "{reason}": reason})
            show.append(_format_str(user_or_role, format_settings))
        del maybe_user, item, reason

        show = _format_pages(show)
        page = Page(ctx, show, title=title, footer=footer)
        await Menu.start(page, ctx)
