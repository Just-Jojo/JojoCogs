# Copyright (c) 2021 - Amy (jojo7791)
# Licensed under MIT

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Literal, Optional, Tuple, Union

import discord

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self  # type:ignore

import datetime

import yaml
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.dev_commands import cleanup_code  # NOTE lazy :p
from redbot.core.utils.chat_formatting import escape

from ._types import (
    ChannelType,
    GlobalCache,
    GreedyUserOrRole,
    GuildCache,
    UserOrRole,
    UsersOrRoles,
)
from .constants import __author__, __version__, config_structure, default_format
from .menus import Menu, Page
from .patching import Patch


def _timestamp() -> datetime.datetime:
    return datetime.datetime.now(tz=datetime.timezone.utc)


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


async def _filter_internal(
    c: commands.Context, u: UsersOrRoles
) -> Tuple[UsersOrRoles, Optional[str]]:
    r: UsersOrRoles = []
    for i in u:
        if isinstance(i, int):
            i = discord.Object(i)  # type:ignore
        if await c.bot.is_owner(i):  # type:ignore
            return [], "You cannot add yourself to the blocklist"
        elif isinstance(i, discord.Member) and i.bot:
            continue
        r.append(getattr(i, "id", i))  # type:ignore
    return r, ""


async def _filter_bots(
    ctx: commands.Context,
    users_or_roles: UsersOrRoles,
    white_black_list: _WhiteBlacklist,
) -> Tuple[bool, UsersOrRoles]:
    for i in range(2):
        if not users_or_roles:
            if i == 1:
                await ctx.send("Those users were bots!")
            else:
                await ctx.send_help()
            return False, []
        if white_black_list == "whitelist":
            # NOTE Since the allowlist is just people who
            # can use the bot, we can just filter out the bots.
            # However the blocklist needs some more finagling as
            # adding the owner to the blocklist is kinda not good
            users_or_roles = filter(lambda x: not getattr(x, "bot", False), users_or_roles)
            continue
        users_or_roles, string = await _filter_internal(ctx, users_or_roles)
        if string:
            await ctx.send(string)
            return False, []
    return True, users_or_roles


class AdvancedBlacklist(commands.Cog):
    """An extension of the core blocklisting and allowlisting commands

    Allows for adding reasons for blocklisting/allowlisting users/roles
    and changing the format for the lists

    See `[p]advancedblacklistversion` for version and author information
    """

    def __init__(self, bot: Red):
        self.bot = bot
        self._patch = Patch(self.bot)
        self.config = Config.get_conf(self, 544974305445019651, True)
        for config_type, data in config_structure.items():
            getattr(self.config, f"register_{config_type}")(**data)
        del config_type, data
        self._original_coms: List[commands.Command] = []
        self._bl_cache: GlobalCache = {}
        self._bl_guild_cache: GuildCache = {}
        self._wl_cache: GlobalCache = {}
        self._wl_guild_cache: GuildCache = {}

    @classmethod
    async def async_init(cls, bot: Red) -> Self:
        self = cls(bot)
        await self._patch.startup()
        for name in _original_commands:
            local = "local" + name
            global_com = bot.remove_command(name)
            local_com = bot.remove_command(local)
            if TYPE_CHECKING:
                assert isinstance(global_com, commands.Command), "mypy"
                assert isinstance(local_com, commands.Command), "mypy"
            self._original_coms.append(global_com)
            self._original_coms.append(local_com)
        del name, local, global_com, local_com
        return self

    async def cog_unload(self) -> None:
        await self._patch.destroy()
        for com in self._original_coms:
            self.bot.add_command(com)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        original = super().format_help_for_context(ctx)
        return f"""{original}

        **Author:** {__author__}
        **Version:** {__version__}
        """

    async def red_delete_data_for_user(self, *, requester: Literal["discord_deleted_user", "owner", "user", "user_strict"], user_id: int) -> None:
        if requester not in ("discord_deleted_user", "owner"):
            return

        # NOTE just gonna handle the reason parts
        guilds = await self.config.all_guilds()
        actual = str(user_id)
        for guild, guild_data in guilds.items():
            if TYPE_CHECKING:
                assert isinstance(guild_data, dict), "mypy"
            for list_type, user_data in guild_data.items():
                if actual in user_data:
                    del user_data[actual]
                if list_type == "whitelist":
                    self._wl_guild_cache[guild].update(user_data)
                else:
                    self._bl_guild_cache[guild].update(user_data)

        async with self.config.blacklist() as bl:
            if actual in bl:
                del bl[actual]
                self._bl_cache.update(bl)
        async with self.config.whitelist() as wl:
            if actual in wl:
                del wl[actual]
                self._wl_cache.update(wl)

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
            embed.set_footer(text=footer)
            data = {"embed": embed}
        else:
            title = f"**{title}**" if title else ""
            message = f"{title}\n\n{message}"
            if footer:
                message += f"\n\n-# {footer}"
            data = {"content": message}
        return await ctx.send(**data)

    def _get_cache(
        self, white_black_list: _WhiteBlacklist, guild: Optional[discord.Guild]
    ) -> Dict[str, str]:
        if guild:
            return (
                self._bl_guild_cache if white_black_list == "blacklist" else self._wl_guild_cache
            )[guild.id]
        return self._bl_cache if white_black_list == "blacklist" else self._wl_cache

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
                cache = self._get_cache(white_black_list, guild)
                cache[actual] = reason
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
        cache = self._get_cache(white_black_list, guild)
        cache.clear()
        if guild:
            await getattr(self.config.guild(guild), white_black_list).clear()
        else:
            await getattr(self.config, white_black_list).clear()
        await getattr(self.bot, f"clear_{white_black_list}")(guild=guild)

    async def get_list(
        self, *, white_black_list: _WhiteBlacklist, guild: Optional[discord.Guild] = None
    ) -> Dict[str, str]:
        blacklist = self._get_cache(white_black_list, guild)
        if blacklist:
            return blacklist
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
        cache = self._get_cache(white_black_list, guild)
        async with config() as blacklist:
            actual = str(getattr(user_or_role, "id", user_or_role))
            blacklist[actual] = reason
            cache[actual] = reason
        del blacklist, actual

    async def in_list(
        self,
        user_or_role: UserOrRole,
        *,
        white_black_list: _WhiteBlacklist,
        guild: Optional[discord.Guild] = None,
    ) -> bool:
        actual = str(getattr(user_or_role, "id", user_or_role))
        cache = self._get_cache(white_black_list, guild)
        if actual in cache:
            return True
        config = getattr((self.config.guild(guild) if guild else self.config), white_black_list)
        data = await config()
        if TYPE_CHECKING:
            assert isinstance(data, dict)
        if actual in data:
            return True

        # Okay, didn't find it in the config
        # Let's try in the bot
        data = await self.bot.get_blacklist(guild)
        return int(actual) in data

    @commands.command(name="advancedblacklistversion", aliases=["advblversion"], hidden=True)
    async def advbl_version(self, ctx: commands.Context) -> None:
        """Get the version info for advancedblacklist"""
        version_info = (
            "{bot_name} running version {__version__}\n"
            "For more information/bug reporting, see [the github]"
            "(https://github.com/Just-Jojo/JojoCogs)"
        ).format(bot_name=ctx.me.name, __version__=__version__)
        footer = "Made with ❤ by Amy (jojo7791)"
        await self.maybe_send_embed(
            ctx, version_info, title="AdvancedBlacklist - JojoCogs", footer=footer
        )

    @commands.group(name="blocklist", aliases=["denylist", "blacklist"])
    @commands.is_owner()
    async def blocklist(self, ctx: commands.Context) -> None:
        """Commands manage the blocklist on [botname].

        Use `[p]blocklist clear` to disable the blocklist
        """
        pass

    @blocklist.group(name="settings", aliases=["set"])
    async def blocklist_settings(self, ctx: commands.Context) -> None:
        """Settings for AdvancedBlacklist"""
        pass

    @blocklist.command(name="showsettings", aliases=["show"])
    async def blocklist_settings_showsettings(self, ctx: commands.Context) -> None:
        """Show the settings for AdvancedBlacklist"""

    @blocklist_settings.command(name="format")
    async def blocklist_format(
        self, ctx: commands.Context, *, new_format: Optional[str] = None
    ) -> None:
        """Set the format for listing the block/allow list

        **Arguments:**
            `new_format`    The new format the bot will use to list the block/allowlist.
            This will be loaded as YAML.

        **Keys:**
            \- `title`                 The title the list will use
            \- `user_or_role`          The user/role and the reason they were added to the list
            \- `footer`                The footer on the page

        **Variables:**
            `{bot_name}` -> `[botname]`
            `user_or_role` -> The user or role on the list
            `{allow_deny_list}` -> `allowlist` or `blocklist`
            `{version_info}` -> version of AdvancedBlacklist you are running
            `{reason}` -> reason for adding a user/role to the block/allow list
        """
        if not new_format:
            await self._show_format(ctx)
            return

        new_format = escape(cleanup_code(new_format))

        try:
            json_obj = yaml.safe_load(new_format)
        except yaml.scanner.ScannerError:
            await ctx.send("That was not valid yaml!")
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
        title = settings["title"]
        users_or_roles = settings["users_or_roles"]
        footer = settings["footer"]
        if not await ctx.embed_requested():
            await ctx.send(
                (
                    "# AdvancedBlacklist format\n\n"
                    f"**Title:** `{title}`\n"
                    f"**User or Role:** {users_or_roles}\n"
                    f"**Footer:** {footer}"
                )
            )
            return
        embed = discord.Embed(
            colour=await ctx.embed_colour(),
            title="AdvancedBlacklist format",
            timestamp=_timestamp(),
        )
        embed.add_field(name="Title", value=title)
        embed.add_field(name="User or Role", value=users_or_roles)
        embed.add_field(name="Footer", value=footer)
        await ctx.send(embed=embed)

    @blocklist.command(name="add")
    async def blocklist_add(
        self,
        ctx: commands.Context,
        users_roles: GreedyUserOrRole,
        *,
        reason: Optional[str] = None,
    ) -> None:
        """Add a user or role to the blocklist

        **Arguments:**
            \- `users_roles`           The users/roles to add to the blocklist
            \- `reason`                Optional reason, defaults to "No reason provided."
        """
        worked, users_or_roles = await _filter_bots(ctx, users_roles, "blacklist")
        if not worked:
            return

        if not reason:
            reason = "No reason provided"

        await self.add_to_list(users_or_roles, white_black_list="blacklist", reason=reason)
        if len(tuple(users_or_roles)) > 1:
            await ctx.send(
                (
                    "I have added those users/roles to the blocklist with the reason: `{reason}`"
                ).format(reason=reason)
            )
        else:
            await ctx.send(
                (
                    "I have added that user/role to the blocklist with the reason: `{reason}`"
                ).format(reason=reason)
            )

    @blocklist.command(name="remove", aliases=["del", "delete"])
    async def blocklist_remove(self, ctx: commands.Context, users_roles: GreedyUserOrRole) -> None:
        """Remove users/roles from the blocklist

        **Arguments:**
            \- `users_or_roles`        The users or roles to remove from the blocklist
        """
        worked, users_or_roles = await _filter_bots(ctx, users_roles, "blacklist")
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

        **Arguments:**
            \- `user_or_role`          The user or role to edit the reason of
            \- `reason`                The new reason
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
        await self.send_list(ctx, white_black_list="blacklist", guild=None)

    @commands.group(name="allowlist", aliases=["whitelist"])
    @commands.is_owner()
    async def allowlist(self, ctx: commands.Context) -> None:
        """Commands managing the allowlist on [botname]

        Any users or roles added to the allowlist will be the only users
        able to use [botname]
        """
        pass

    @allowlist.command(name="add")
    async def allowlist_add(
        self,
        ctx: commands.Context,
        users_roles: GreedyUserOrRole,
        *,
        reason: Optional[str] = None,
    ) -> None:
        """Add users/roles to the allowlist

        **Arguments:**
            \- `users_roles`           The users/roles to add to the allowlist
            \- `reason`                Optional reason, defaults to "No reason provided"
        """
        worked, users_or_roles = await _filter_bots(ctx, users_roles, "whitelist")

        if not worked:
            return

        if not reason:
            reason = "No reason provided"

        await self.add_to_list(
            users_or_roles, white_black_list="whitelist", reason=reason, guild=None
        )

        if len(tuple(users_or_roles)) > 1:
            await ctx.send(
                f"I have added those users/roles to the allowlist with the reason: `{reason}`"
            )
        else:
            await ctx.send(
                f"I have added that user/role to the allowlist with the reason: `{reason}`"
            )

    @allowlist.command(name="edit")
    async def allowlist_edit(self, ctx: commands.Context, user_or_role: UserOrRole, *, reason: str) -> None:
        """"""
        if isinstance(user_or_role, discord.Member) and user_or_role.bot:
            await ctx.send("That user is a bot!")
            return
        elif not await self.in_list(user_or_role, white_black_list="whitelist"):
            await ctx.send("That user/role is not in the allowlist!")
            return

        await self.edit_reason(user_or_role, white_black_list="whitelist", reason=reason)
        await ctx.send("Edited the reason for that user/role")

    @allowlist.command(name="remove", aliases=["del", "delete"])
    async def allowlist_remove(self, ctx: commands.Context, users_roles: GreedyUserOrRole) -> None:
        """Remove users/roles from the allowlist

        **Arguments:**
            \- `users_roles`           The users/roles to remove from the allowlist
        """
        worked, users_or_roles = await _filter_bots(ctx, users_roles, "whitelist")
        if not worked:
            return

        await self.remove_from_list(users_or_roles, white_black_list="whitelist", guild=ctx.guild)
        if len(tuple(users_or_roles)) > 1:
            await ctx.send("Removed those users/roles from the allowlist")
        else:
            await ctx.send("Removed that user/role from the allowlist")

    @allowlist.command(name="list")
    async def allowlist_list(self, ctx: commands.Context) -> None:
        """Shows the users/roles on the allowlist"""
        await self.send_list(ctx, white_black_list="whitelist", guild=None)

    @commands.group(name="localblocklist", aliases=["localblacklist", "localdenylist"])
    @commands.guild_only()
    @commands.admin_or_permissions(administrator=True)
    async def local_blocklist(self, ctx: commands.Context) -> None:
        """Manage the users/roles on the local blocklist"""
        pass

    @local_blocklist.command(name="add")
    async def local_blocklist_add(
        self,
        ctx: commands.Context,
        users_or_roles: GreedyUserOrRole,
        *,
        reason: Optional[str] = None,
    ) -> None:
        """Add users or roles to the local blocklist

        The users or users in the roles will not be able to use [botname]

        **Arguments:**
            \- `users_or_roles`        The users/roles to add to the local blocklist
            \- `reason`                The reason you added the users/roles
        """
        worked, users_or_roles = await _filter_bots(ctx, users_or_roles, "blacklist")
        if not worked:
            return

        if not reason:
            reason = "No reason provided"

        await self.add_to_list(
            users_or_roles, white_black_list="blacklist", reason=reason, guild=ctx.guild
        )
        if len(tuple(users_or_roles)) > 1:
            await ctx.send("Added those users/roles to the local blocklist")
        else:
            await ctx.send("Added that user/role to the local blocklist")

    @local_blocklist.command(name="edit")
    async def local_blocklist_edit(
        self, ctx: commands.Context, user_or_role: UserOrRole, *, reason: str
    ) -> None:
        """Edit the reason for a locally blocklisted user/role

        **Arguments:**
            \- `user_or_role`          The user or role to edit the reason of
            \- `reason`                The new reason
        """
        if isinstance(user_or_role, discord.Member) and user_or_role.bot:
            await ctx.send("That user is a bot!")
            return
        elif not await self.in_list(user_or_role, white_black_list="blacklist"):
            await ctx.send("That user/role is not in the blocklist")
            return
        await self.edit_reason(user_or_role, white_black_list="blacklist", reason=reason, guild=ctx.guild)
        await ctx.send("Edited the reason for that user/role")

    @local_blocklist.command(name="remove", aliases=["delete", "del"])
    async def local_blocklist_remove(
        self, ctx: commands.Context, users_or_roles: GreedyUserOrRole
    ) -> None:
        """Remove users/roles from the local blocklist

        **Arguments**
            \- `users_or_roles`        The users/roles to remove from the local blocklist
        """
        worked, users_or_roles = await _filter_bots(ctx, users_or_roles, "blacklist")
        if not worked:
            return

        await self.remove_from_list(users_or_roles, white_black_list="blacklist", guild=ctx.guild)
        if len(tuple(users_or_roles)) > 1:
            await ctx.send("Removed those users/roles from the local blocklist")
        else:
            await ctx.send("Removed that user/role from the local blocklist")

    @local_blocklist.command(name="list")
    async def local_blocklist_list(self, ctx: commands.Context) -> None:
        """List the users/roles in the local blocklist"""
        await self.send_list(ctx, white_black_list="blacklist", guild=ctx.guild)

    @commands.group(name="localallowlist")
    @commands.guild_only()
    @commands.admin_or_permissions(administrator=True)
    async def local_allowlist(self, ctx: commands.Context) -> None:
        """Manage the users/roles on the local allowlist

        Any users or roles added to the local allowlist will be the only users
        able to use [botname]
        """
        pass

    @local_allowlist.command(name="add")
    async def local_allowlist_add(
        self, ctx: commands.Context, users_roles: GreedyUserOrRole, *, reason: Optional[str] = None
    ) -> None:
        """Add users/roles to the local allowlist

        **Arguments:**
            \- `users_roles`           The users/roles to add to the local allowlist
            \- `reason`                Optional reason, defaults to "No reason provided"
        """
        worked, users_or_roles = await _filter_bots(ctx, users_roles, "whitelist")
        if not worked:
            return

        if not reason:
            reason = "No reason provided"

        await self.add_to_list(
            users_or_roles, white_black_list="whitelist", reason=reason, guild=ctx.guild
        )
        if len(tuple(users_or_roles)) > 1:
            await ctx.send("Added those users/roles to the local allowlist")
        else:
            await ctx.send("Added that user/role to the local allowlist")

    @local_allowlist.command(name="remove", aliases=["del", "delete"])
    async def local_allowlist_remove(
        self, ctx: commands.Context, users_roles: GreedyUserOrRole
    ) -> None:
        """Remove users/roles from the local allowlist

        **Arguments:**
            \- `users_roles`           The users to remove from the local allowlist
        """
        worked, users_or_roles = await _filter_bots(ctx, users_roles, "whitelist")
        if not worked:
            return

        await self.remove_from_list(users_or_roles, white_black_list="whitelist", guild=ctx.guild)

        if len(tuple(users_or_roles)) > 1:
            await ctx.send("Removed those users/roles from the local allowlist")
        else:
            await ctx.send("Removed that user/role from the local allowlist")

    @local_allowlist.command(name="edit")
    async def local_allowlist_edit(self, ctx: commands.Context, user_or_role: UserOrRole, *, reason: str) -> None:
        """"""
        if isinstance(user_or_role, discord.Member) and user_or_role.bot:
            await ctx.send("That user is a bot!")
            return
        elif not await self.in_list(user_or_role, white_black_list="whitelist", guild=ctx.guild):
            await ctx.send("That user/role is not in the allowlist!")
            return

        await self.edit_reason(user_or_role, white_black_list="whitelist", reason=reason, guild=ctx.guild)
        await ctx.send("Edited the reason for that user/role")

    @local_allowlist.command(name="list")
    async def local_allowlist_list(self, ctx: commands.Context):
        """List the users/roles in the local allowlist"""
        await self.send_list(ctx, white_black_list="whitelist", guild=ctx.guild)

    async def send_list(
        self,
        ctx: commands.Context,
        *,
        white_black_list: _WhiteBlacklist,
        guild: Optional[discord.Guild],
    ) -> None:
        list_format: Dict[str, str] = await self.config.format()
        format_settings = {
            "{reason}": "",
            "{bot_name}": ctx.me.name,
            "{version_info}": str(__version__),
            "{user_or_role}": "",
        }
        title = _format_str(list_format["title"], format_settings)
        footer = _format_str(list_format["footer"], format_settings)
        user_or_role = list_format["user_or_role"]
        show: List[str] = []

        blocklist = await self.get_list(white_black_list=white_black_list, guild=guild)
        if not blocklist:
            allow_deny = "allowlist" if white_black_list == "whitelist" else "blocklist"
            await ctx.send("There are no users/roles on the {allow_deny}").format(
                allow_deny=allow_deny
            )
            return
        for item, reason in blocklist.items():
            maybe_user = getattr(self.bot.get_user(int(item)), "name", item)
            format_settings.update({"{user_or_role}": maybe_user, "{reason}": reason})
            show.append(_format_str(user_or_role, format_settings))
        del maybe_user, item, reason

        show = _format_pages(show)
        page = Page(ctx, show, title=title, footer=footer)
        await Menu.start(page, ctx)
