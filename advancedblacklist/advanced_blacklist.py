# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import asyncio
import logging
from contextlib import suppress
from typing import Dict, Iterable, List, Optional, Set, TypeVar, Union

import discord
from redbot import VersionInfo, version_info
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_list, pagify
from redbot.core.utils.predicates import MessagePredicate
from tabulate import tabulate

try:
    import regex as re
except ImportError:
    import re  # type:ignore

from .converters import *
from .api import * # type:ignore
from .monkey import setup, teardown
from .listeners import BlacklistEvent


log = logging.getLogger("red.JojoCogs.advancedblacklist")
_config_structure = {
    "global": {
        "blacklist": {},  # Dict[str, str]. String version of the uid and reason
        "use_reasons": True,
        "names": {},  # Dict[str, bool]. The search pattern and if it's a regex or not
        "whitelist": {},
    },
    "guild": {
        "blacklist": {},  # Dict[str, str]. String version of the uid and reason
        "whitelist": {},
    },
}
AB = TypeVar("AB", bound="AdvancedBlacklist")


class AdvancedBlacklist(BlacklistEvent, commands.Cog):
    """An advanced blacklist cog"""

    __authors__ = ["Jojo#7791"]
    __version__ = "1.2.0"

    def __init__(self, bot: Red):
        self.bot = bot

        self.config = Config.get_conf(self, 544974305445019651, True)
        self.config.register_global(**_config_structure["global"])
        self.config.register_guild(**_config_structure["guild"])

        self.blacklist_name_cache: Dict[str, List[bool]] = {}
        self._cmds: List[commands.Command] = []

        self.task: asyncio.Task = self.bot.loop.create_task(self._startup())
        self._schema_task = self.bot.loop.create_task(self._schema_0_to_1())
        setup(self.bot)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        pre_processed = super().format_help_for_context(ctx)
        plural = "s" if len(self.__authors__) > 1 else ""
        return (
            f"{pre_processed}\n\n"
            f"Author{plural}: `{humanize_list(self.__authors__)}\n"
            f"Version: `{self.__version__}`"
        )

    async def red_delete_data_for_user(self, *args, **kwargs) -> None:
        """Nothing to delete"""
        return

    def cog_unload(self) -> None:
        teardown()
        for cmd in self._cmds:
            if cmd:
                try:
                    self.bot.remove_command(cmd.name)
                except Exception as e:
                    log.debug(f"Error in removing command: {cmd.name}", exc_info=e)
                finally:
                    self.bot.add_command(cmd)
        self.task.cancel()
        self._schema_task.cancel()
        with suppress(Exception):
            self.bot.remove_dev_env_value("advblc")

    @classmethod
    async def init(cls, bot: Red) -> AB:
        self = cls(bot)
        for cmd in ["blocklist", "localblocklist", "allowlist", "localallowlist"]:
            self._cmds.append(self.bot.remove_command(cmd))
        return self

    async def _startup(self) -> None:
        async with self.config.blacklist() as bl:
            blacklist = await get_blacklist(self.bot)
            for uid in blacklist:
                if str(uid) in bl.keys():
                    continue
                bl[str(uid)] = "No reason provided"
        self.blacklist_name_cache = await self.config.names()
        with suppress(RuntimeError):
            self.bot.add_dev_env_value("advblc", lambda s: self)

    async def _schema_0_to_1(self) -> None:
        conf = await self.config.all()
        if conf.get("schema_v1"):
            return  # Don't care about this

        guild_data = conf.pop("local_blacklist", None)
        if guild_data is not None:
            for g_id, data in guild_data.keys():
                await self.config.guild_from_id(int(g_id)).set_raw("blacklist", value=data)
        conf["schema_v1"] = True
        await self.config.clear_all_globals()
        await self.config.set(conf)

    @commands.command(name="blacklistversion")
    async def blacklist_version(self, ctx: commands.Context):
        """Get the version of Advanced Blacklist that [botname] is running"""

        await ctx.send(
            f"Advanced Blacklist, Version `{self.__version__}`. Made with :heart: by Jojo#7791"
        )

    @commands.group(name="whitelist", aliases=["allowlist"])
    @commands.is_owner()
    async def whitelist(self, ctx: commands.Context):
        """Manage [botname]'s allowlist"""
        pass

    @whitelist.command(name="add")
    async def whitelist_add(
        self,
        ctx: commands.Context,
        users: commands.Greedy[NonBotUser(whitelist=True)],
        *,
        reason: str = None,
    ):
        """Add a user to [botname]'s allowlist

        Everyone else will be locked from using the bot unless they are on the allowlist or are an owner

        **Arguments**
            - `users` The users to add to the allowlist.
            - `reason` The reason to add these users to the allowlist.
        """
        if not users:
            raise commands.UserInputError
        reason = reason or "No Reason Provided."
        async with self.config.whitelist() as whitelist:
            for user in users:
                whitelist[user.id] = reason
        await ctx.tick()

    @whitelist.command(name="list")
    async def whitelist_list(self, ctx: commands.Context):
        """List [botname]'s allowlist"""
        wl = await self.config.whitelist()
        if not wl:
            return await ctx.send("There are no users on the allowlist.")
        sending = "Allowlisted Users:"
        for user, reason in wl.items():
            sending += f"\n\t- [{user}] {await self._get_user_name(user)}: {reason}"
        await ctx.send_interactive(pagify(sending, page_length=1995), box_lang="yaml")

    @whitelist.command(name="remove", aliases=["del", "delete"], require_var_positional=True)
    async def whitelist_remove(self, ctx: commands.Context, *users: discord.User):
        """Remove users from [botname]'s allowlist.

        These users will no longer be able to use the bot unless the allowlist is cleared.

        **Arguments**
            - `users` The users to remove from the allowlist.
        """
        await remove_from_whitelist(self.bot, users)
        async with self.config.whitelist() as wl:
            for user in users:
                wl.pop(user, None)
        await ctx.tick()

    @whitelist.command(name="clear")
    async def whitelist_clear(self, ctx: commands.Context, confirm: bool = False):
        """Clear [botname]'s allowlist

        Everyone will be able to use commands on [botname] unless they are blocklisted.
        """
        if not confirm:
            await ctx.send("Are you sure that you would like to clear the allowlist?")
            pred = MessagePredicate.yes_or_no(ctx)
            try:
                await self.bot.wait_for("message", check=pred)
            except asyncio.TimeoutError:
                pass
            finally:
                if not pred.result:
                    return await ctx.send("Okay, I will not clear the allowlist")
        await clear_whitelist(self.bot)
        await ctx.tick()

    @commands.group(aliases=["localwhitelist"])
    @commands.guild_only()
    @commands.admin_or_permissions(administrator=True)
    async def localallowlist(self, ctx: commands.Context):
        """Manage the local allowlist on this guild"""
        pass

    @localallowlist.command(name="add")
    async def local_whitelist_add(self, ctx: commands.Context, users: commands.Greedy[NonBotUser(whitelist=True)], *, reason: str = None):
        """Add users to the local allowlist

        Only these users and the owner of the guild will be able to use the bot.

        **Arguments**
            - `users` The users to add to the local allowlist. These cannot be bots.
            - `reason` The reason for adding these users to the allowlist.
        """
        if not users:
            raise commands.UserInputError
        await add_to_whitelist(self.bot, users, guild=ctx.guild)
        async with self.config.guild(ctx.guild).whitelist() as lwl:
            for user in users:
                lwl[user.id] = reason
        await ctx.tick()

    @localallowlist.command(name="remove", aliases=["del", "delete", "rm"], require_var_positional=True)
    async def local_whitelist_remove(self, ctx: commands.Context, *users: discord.User):
        """Remove users from the local allowlist.

        These users will no longer be able to use [botname] here unless the local allowlist is cleared.

        **Arguments**
            - `users` The users to remove from the local allowlist.
        """
        await remove_from_whitelist(self.bot, users, guild=ctx.guild)
        async with self.config.guild(ctx.guild).whitelist() as lwl:
            for user in users:
                lwl.pop(user.id, None)
        await ctx.tick()

    @localallowlist.command(name="clear")
    async def local_whitelist_clear(self, ctx: commands.Context, confirm: bool = False):
        """Clear the local allowlist."""
        if not confirm:
            await ctx.send("Would you like to clear the local allowlist? (y/n)")
            pred = MessagePredicate.yes_or_no()
            try:
                await self.bot.wait_for("message", check=pred)
            except asyncio.TimeoutError:
                pass
            finally:
                if not pred.result:
                    return await ctx.send("Okay, I will not clear the local allowlist")
        await clear_whitelist(self.bot, guild=ctx.guild)
        await ctx.tick()

    @localallowlist.command(name="list")
    async def local_whitelist_list(self, ctx: commands.Context):
        """List the locally allowlisted users"""
        lwl = await self.config.guild(ctx.guild).whitelist()
        if not lwl:
            return await ctx.send("There are no locally allowlisted users")
        sending = "Locally Allowlisted Users:"
        for user, reason in lwl.items():
            sending += f"\n\t- [{user}] {await self._get_user_name(user)}: {reason}"
        await ctx.send_interactive(pagify(sending, page_length=1995), box_lang="yaml")

    @commands.group(aliases=["localblacklist"])
    @commands.guild_only()
    @commands.admin_or_permissions(administrator=True)
    async def localblocklist(self, ctx: commands.Context):
        """Add a user to a guild's blocklist list"""
        pass

    @localblocklist.command(name="add")
    async def local_blocklist_add(
        self,
        ctx: commands.Context,
        users: commands.Greedy[NonBotMember],
        *,
        reason: str = "No reason provided.",
    ):
        """Add a user to this guild's blocklist

        This will stop them from being able to use commands on this server

        **Arguments**
            - `user` The user to add to the blocklist. This cannot be a bot.
            - `reason` The reason for adding a user to the blocklist. Defaults to "No reason provided."
        """

        async def sorter(items: Iterable[discord.Member]) -> List[discord.Member]:
            ret = []
            for item in items:
                if await self.bot.is_owner(item):
                    continue
                elif await self.bot.is_mod(item):
                    continue
                ret.append(item)
            return ret

        users = await sorter(users)
        if not users:
            raise commands.UserInputError
        # I got an api added to red now fuck yes :D
        await add_to_blacklist(self.bot, users, guild=ctx.guild)
        async with self.config.guild(ctx.guild).blacklist() as lbl:
            for user in users:
                lbl[str(user.id)] = reason
        await ctx.tick()

    @localblocklist.command(name="remove", alises=["del", "delete"])
    async def local_blocklist_remove(self, ctx: commands.Context, *users: discord.User):
        """Remove a user from this guild's blocklist

        This will allow them to use commands again

        **Arguments**
            - `user` The user to remove from the blocklist.
        """
        await remove_from_blacklist(self.bot, users, guild=ctx.guild)
        async with self.config.guild(ctx.guild).blacklist() as lbl:
            for user in users:
                lbl.pop(str(user.id), None)
        await ctx.tick()

    @localblocklist.command(name="list")
    async def local_blocklist_list(self, ctx: commands.Context):
        """List the users who are blocklisted in this guild"""
        lbl = await self.config.guild(ctx.guild).blacklist()
        if not lbl:  # *sigh*
            return await ctx.send("There are no users on the blacklist")
        sending = "Locally Blocklisted Users:"
        for uid, reason in lbl.items():
            sending += f"\n\t- [{uid}] {await self._get_user_name(uid)}: {reason}"
        await ctx.send_interactive(pagify(sending, page_length=1995), box_lang="yaml")

    @localblocklist.command(name="reason")
    async def local_blocklist_reason(
        self, ctx: commands.Context, user: discord.User, *, reason: str
    ):
        """Add a reason to a user that is locally blocklisted

        This will modify the reason for the user's blocklisting

        **Arguments**
            - `user` The user to edit the reason for blocklisting.
            - `reason` The new reason.
        """
        user = str(user.id)
        async with self.config.guild.blacklist() as lbl:
            if not lbl:
                return await ctx.send("The local blocklist is empty")
            elif user not in lbl.keys():
                return await ctx.send("That user is not blocklisted")
            lbl[user] = reason
        await ctx.tick()

    @localblocklist.command(name="clear")
    async def local_blocklist_clear(self, ctx: commands.Context, confirm: bool = False):
        """Clear this guild's blocklist

        **Warning** this will allow the previously blocklisted users to use commands again
        """
        if not confirm:
            await ctx.send("Would you like to clear this guild's blocklist? (y/n)")
            pred = MessagePredicate.yes_or_no()
            try:
                await self.bot.wait_for("message", check=pred)
            except asyncio.TimeoutError:
                pass
            finally:
                if not pred.result:
                    return await ctx.send("Okay, I will not clear the blocklist")
        await ctx.tick()
        await clear_blacklist(self.bot, guild=ctx.guild)
        async with self.config.guild(ctx.guild).blacklist() as lbl:
            lbl.clear()

    @commands.is_owner()
    @commands.group(aliases=["blacklist"])
    async def blocklist(self, ctx: commands.Context):
        """Add/remove users from the blocklist"""
        pass

    @blocklist.command(name="list")
    async def blocklist_list(self, ctx: commands.Context):
        """List the users in your blocklist"""
        blacklist = await self.config.blacklist()
        if not blacklist:
            return await ctx.send("The blocklist is empty.")
        sending = "Blocklisted Users:"
        for uid, reason in blacklist.items():
            sending += f"\n\t- [{uid}] {await self._get_user_name(uid)}: {reason}"
        await ctx.send_interactive(pagify(sending, page_length=1995), box_lang="yaml")

    async def _get_user_name(self, uid: int) -> str:
        try:
            return (await self.bot.get_or_fetch_user(uid)).name
        except discord.NotFound:
            return "Unknown or Deleted User."

    @blocklist.group(name="name", aliases=["names"])
    async def blocklist_name(self, ctx: commands.Context):
        """Blocklist users by names.

        For example, you can add `Jojo` to it and it would blocklist anyone with the name `Jojo`
        This also supports regexes, which you can test at https://regex101.com/ (make sure to set it to python)
        """
        pass

    @blocklist_name.command(
        name="add", usage="[use_regex=False] [lower_case=True] <pattern>"
    )
    async def blacklist_name_add(
        self,
        ctx: commands.Context,
        use_regex: Optional[bool],
        case_sensitive: Optional[bool],
        *,
        pattern: str,
    ):
        """Add a pattern to the blocklisted name cache.

        If you would like a regex, use the command list this `[p]blacklist name add True ^jojo+$`
        If you would like it to match casing use `[p]blacklist name add <regex value> True Jojo`

        **Arguments**
            - `use_regex` Whether to use regex or not. Defaults to False.
            - `case_insensitive` Whether to match the exact casing or not. Defaults to True.
            - `pattern` The name to watch for. If `use_regex` is True this will need to be a regular expression.
        """
        use_regex = use_regex if use_regex is not None else False
        lower_case = case_sensitive if case_sensitive is not None else True
        self.blacklist_name_cache[pattern] = [use_regex, lower_case]
        regex = "will" if use_regex else "won't"
        lower = "won't" if lower_case else "will"
        await ctx.send(
            f"Added this as a blocklist pattern `{pattern}`."
            f"\nIt {regex} be regex and {lower} be case sensitive."
        )
        async with self.config.names() as names:
            names[pattern] = [use_regex, lower_case]

    @blocklist_name.command(name="list")
    async def blacklist_name_list(self, ctx: commands.Context):
        """List the blocklisted names."""
        if not self.blacklist_name_cache:
            return await ctx.send("There are no blocklisted user names.")
        ret = []
        for pattern, (reg, lc) in self.blacklist_name_cache.items():
            ret.append([pattern, f"{reg}|{lc}"])
        tabulated = tabulate(ret, ("Pattern", "Regex? | Case sensitive?"))
        await ctx.send_interactive(pagify(tabulated), box_lang="")

    @blocklist_name.command(name="remove", aliases=["del", "delete"])
    async def blacklist_name_remove(self, ctx: commands.Context, *, pattern: str):
        """Remove a pattern from the blocklisted names cache.

        \u200b
        **Arguments**
            - `pattern` The pattern to remove.
        """
        if pattern not in self.blacklist_name_cache.keys():
            return await ctx.send(
                "I could not find a pattern like that in the blocklisted names."
            )
        async with self.config.names() as names:
            names.pop(pattern)
            self.blacklist_name_cache.pop(pattern)
        await ctx.tick()

    @blocklist.command(name="add")
    async def blacklist_add(
        self,
        ctx: commands.Context,
        users: commands.Greedy[NonBotUser],
        *,
        reason: str = "No reason provided",
    ):
        """Add a user to the blocklist

        This will remove their ability to use commands with the bot

        **Arguments**
            - `user` The user to blocklist.
            - `reason` The reason for blocklisting the user. Defaults to "No reason provided.".
        """
        if not users:
            raise commands.UserInputError
        await add_to_blacklist(self.bot, users)
        async with self.config.blacklist() as blacklist:
            for user in users:
                blacklist[str(user.id)] = reason
        await ctx.tick()

    @blocklist.command(name="clear")
    async def blacklist_clear(self, ctx: commands.Context, confirm: bool = False):
        """Clear the blocklist

        **Warning** Every user that was previously blocklisted will now be able to use commands
        """
        if not confirm:
            await ctx.send("Would you like to clear the blocklist? (y/n)")
            pred = MessagePredicate.yes_or_no()
            try:
                await self.bot.wait_for("message", check=pred)
            except asyncio.TimeoutError:
                pass
            finally:
                if not pred.result:
                    return await ctx.send("Okay. I will not clear the blocklist")
        await clear_blacklist(self.bot)
        async with self.config.blacklist() as bl:
            bl.clear()
        await ctx.tick()

    @blocklist.command(name="remove", aliases=["del", "rm"], require_var_positional=True)
    async def blacklist_remove(self, ctx: commands.Context, *users: discord.User):
        """Remove users from the blocklist

        The user will be able to use commands again

        **Arguments**
            - `user` The user to remove from the blocklist
        """
        await remove_from_blacklist(self.bot, users)
        async with self.config.blacklist() as blacklist:
            for user in users:
                try:
                    del blacklist[str(user)]
                except KeyError:
                    pass
        await ctx.tick()

    @blocklist.command(name="reason")
    async def blacklist_reason(
        self, ctx: commands.Context, user: discord.User, *, reason: str
    ):
        """Add or edit the reason for a blocklisted user

        \u200b
        **Arguments**
            - `user` The user to edit the reason for blocklisting.
            - `reason` The new reason for blocklisting the user.
        """
        uid = str(user.id)
        async with self.config.blacklist() as bl:
            if uid not in bl.keys():
                return await ctx.send("That user is not blocklisted")
            bl[uid] = reason
        await ctx.tick()

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        author_name: str = msg.author.name
        if await self.bot.is_owner(msg.author) or msg.author.bot:
            return
        async with self.config.blacklist() as bl:
            if str(msg.author.id) in bl.keys():
                return
            for pattern, (reg, lower) in self.blacklist_name_cache.items():
                if lower:
                    author_name = author_name.lower()
                    pattern = pattern.lower()
                if reg:
                    pattern = re.compile(pattern)
                if re.search(pattern, author_name) if reg else pattern in author_name:
                    await add_to_blacklist(self.bot, [msg.author])
                    bl[str(msg.author.id)] = "Name matched the blocklisted name list."
                    log.info(
                        f"Blocklisted {msg.author.name} as they had a blocklisted name."
                    )
                    return

    @commands.Cog.listener()
    async def on_error_blacklist(self, user: discord.User, command: commands.Command):
        async with self.config.blacklist() as bl:
            if str(user.id) in bl.keys():
                return
            bl[str(user.id)] = (
                f"Blacklisted for using the erroring command '{command.qualified_name}' too many times"
            )
