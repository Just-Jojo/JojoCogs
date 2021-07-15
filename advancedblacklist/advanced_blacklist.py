# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import asyncio
import logging
from typing import Dict, List, Optional, Union

import discord
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

log = logging.getLogger("red.JojoCogs.advancedblacklist")
_config_structure = {
    "global": {
        "blacklist": {},  # Dict[str, str]. String version of the uid and reason
        "use_reasons": True,
        "local_blacklist": {},  # Dict[str, Dict[str, str]]. String version of guild id and then same as blacklist
        "names": {},  # Dict[str, bool]. The search pattern and if it's a regex or not
    }
}
BLACKLIST_COMMAND: Optional[commands.Command] = None
LOCAL_BLACKLIST_COMMAND: Optional[commands.Command] = None


class AdvancedBlacklist(commands.Cog):
    """An advanced blacklist cog"""

    __authors__ = ["Jojo#7791"]
    __version__ = "1.0.4"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, 544974305445019651, True)
        self.config.register_global(**_config_structure["global"])
        self.task: asyncio.Task = self.bot.loop.create_task(self.init())
        self.blacklist_name_cache: Dict[str, List[bool]] = {}

    def format_help_for_context(self, ctx: commands.Context):
        pre_processed = super().format_help_for_context(ctx)
        plural = "s" if len(self.__authors__) > 1 else ""
        return (
            f"{pre_processed}\n\n"
            f"Author{plural}: `{humanize_list(self.__authors__)}\n"
            f"Version: `{self.__version__}`"
        )

    async def red_delete_data_for_user(self, *args, **kwargs):
        """Nothing to delete"""
        return

    def cog_unload(self):
        global BLACKLIST_COMMAND, LOCAL_BLACKLIST_COMMAND
        self.task.cancel()
        cmds = [BLACKLIST_COMMAND, LOCAL_BLACKLIST_COMMAND]
        for cmd, name in zip(cmds, ("blacklist", "localblacklist")):
            if cmd:
                try:
                    self.bot.remove_command(name)
                except Exception as e:
                    log.debug(f"Error in removing command: {name}", exc_info=e)
                finally:
                    self.bot.add_command(cmd)

    async def init(self):
        async with self.config.blacklist() as bl:
            blacklist = await self.bot._whiteblacklist_cache.get_blacklist()
            for uid in blacklist:
                if str(uid) in bl.keys():
                    continue
                bl[str(uid)] = "No reason provided"
        self.blacklist_name_cache = await self.config.names()

    @commands.group(aliases=["localblocklist"])
    @commands.guild_only()
    @commands.admin_or_permissions(administrator=True)
    async def localblacklist(self, ctx: commands.Context):
        """Add a user to a guild's blacklist list"""
        pass

    @localblacklist.command(name="add")
    async def local_blacklist_add(
        self,
        ctx: commands.Context,
        user: NonBotMember,
        *,
        reason: str = "No reason provided.",
    ):
        """Add a user to this guild's blacklist

        This will stop them from being able to use commands on this server

        **Arguments**
            - `user` The user to blacklist. This cannot be a bot.
            - `reason` The reason for adding a user to the blacklist. Defaults to "No reason provided."
        """
        if ctx.guild.owner == user:
            return await ctx.send(
                "You cannot add the owner of this server to the blocklist."
            )
        elif await self.bot.is_mod(user):
            return await ctx.send("You cannot add a moderator to the blocklist.")
        user = user.id
        # as much as I dislike this I have to use this until Red releases an api method for this
        await self.bot._whiteblacklist_cache.add_to_blacklist(
            guild=ctx.guild, role_or_user=(user,)
        )
        gid = str(ctx.guild.id)
        async with self.config.local_blacklist() as lbl:
            try:
                lbl[gid][str(user)] = reason
            except KeyError:
                lbl[gid] = {str(user): reason}
        await ctx.tick()

    @localblacklist.command(name="remove", alises=["del", "delete"])
    async def local_blacklist_remove(self, ctx: commands.Context, user: discord.User):
        """Remove a user from this guild's blacklist

        This will allow them to use commands again

        **Arguments**
            - `user` The user to remove from the blacklist.
        """
        user = user.id
        await self.bot._whiteblacklist_cache.remove_from_blacklist(
            guild=ctx.guild, role_or_user=(user,)
        )
        async with self.config.local_blacklist() as lbl:
            try:
                del lbl[str(ctx.guild.id)][str(user)]
            except KeyError:
                pass
        await ctx.tick()

    @localblacklist.command(name="list")
    async def local_blacklist_list(self, ctx: commands.Context):
        """List the users who are blacklisted in this guild"""
        lbl = (await self.config.local_blacklist()).get(str(ctx.guild.id))
        if not lbl:
            await ctx.send("There are no users on the blacklist")
        users = []
        for uid, reason in lbl.items():
            users.append([f"{uid} ({await self._get_user_name(uid)})", reason])
        tabulated = tabulate(users, ("User", "Reason"), "plain")
        await ctx.send_interactive(pagify(tabulated), box_lang="")

    @localblacklist.command(name="reason")
    async def local_blacklist_reason(
        self, ctx: commands.Context, user: discord.User, *, reason: str
    ):
        """Add a reason to a user that is locally blacklisted

        This will modify the reason for the user's blacklisting

        **Arguments**
            - `user` The user to edit the reason for blacklisting.
            - `reason` The new reason.
        """
        gid = str(ctx.guild.id)
        user = str(user.id)
        async with self.config.local_blacklist() as lb:
            lbl = lb.get(gid)
            if not lbl:
                return await ctx.send("The local blacklist is empty")
            elif user not in lbl.keys():
                return await ctx.send("That user is not blacklisted")
            lbl[user] = reason
            lb[gid] = lbl
        await ctx.tick()

    @localblacklist.command(name="clear")
    async def local_blacklist_clear(self, ctx: commands.Context):
        """Clear this guild's blacklist

        **Warning** this will allow the previously blacklisted users to use commands again
        """
        await ctx.send("Would you like to clear this guild's blacklist? (y/n)")
        pred = MessagePredicate.yes_or_no()
        try:
            await self.bot.wait_for("message", check=pred)
        except asyncio.TimeoutError:
            pass
        if not pred.result:
            return await ctx.send("Okay, I will not clear the blacklist")
        await ctx.tick()
        async with self.config.local_blacklist() as lbl:
            try:
                lbl[str(ctx.guild.id)].clear()
            except KeyError:
                pass

    @commands.is_owner()
    @commands.group(aliases=["blocklist"])  # Meh, might as well
    async def blacklist(self, ctx: commands.Context):
        """Add/remove users from the blacklist"""
        pass

    @blacklist.command(name="list")
    async def blacklist_list(self, ctx: commands.Context):
        """List the users in your blacklist"""
        blacklist = await self.config.blacklist()
        if not blacklist:
            return await ctx.send("The blacklist is empty.")
        users = []
        for uid, reason in blacklist.items():
            users.append([f"{uid} ({await self._get_user_name(uid)})", reason])
        tabulated = tabulate(users, ("User", "Reason"), "plain")
        await ctx.send_interactive(pagify(tabulated), box_lang="")

    async def _get_user_name(self, uid: int) -> str:
        try:
            return await self.bot.get_or_fetch_user(uid)
        except discord.NotFound:
            return "Unknown or Deleted User."

    @blacklist.group(name="name", aliases=["names"])
    async def blacklist_name(self, ctx: commands.Context):
        """Blacklist users by names.

        For example, you can add `Jojo` to it and it would blacklist anyone with the name `Jojo`
        This also supports regexes, which you can test at https://regex101.com/ (make sure to set it to python)
        """
        pass

    @blacklist_name.command(
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
        """Add a pattern to the blacklisted name cache.

        If you would like a regex, use the command list this `[p]blacklist name add True ^jojo+$`
        If you would like it to match casing use `[p]blacklist name add <regex value> True Jojo`

        **Arguments**
            - `use_regex` Whether to use regex or not. Defaults to False.
            - `case_insensitive` Whether to match the exact casing or not. Defaults to True.
            - `pattern` The name to watch for. If `use_regex` is True this will need to be a regular expression.
        """
        use_regex = use_regex if use_regex is not None else False
        lower_case = lower_case if lower_case is not None else True
        self.blacklist_name_cache[pattern] = [use_regex, lower_case]
        regex = "will" if use_regex else "won't"
        lower = "won't" if lower_case else "will"
        await ctx.send(
            f"Added this as a blacklist pattern `{pattern}`.\nIt {regex} be regex and {lower} be case sensitive."
        )
        async with self.config.names() as names:
            names[pattern] = [use_regex, lower_case]

    @blacklist_name.command(name="list")
    async def blacklist_name_list(self, ctx: commands.Context):
        """List the blacklisted names."""
        if not self.blacklist_name_cache:
            return await ctx.send("There are no blacklisted user names.")
        ret = []
        for pattern, (reg, lc) in self.blacklist_name_cache.items():
            ret.append([pattern, f"{reg}|{lc}"])
        tabulated = tabulate(ret, ("Pattern", "Regex? | Case sensitve?"))
        await ctx.send_interactive(pagify(tabulated), box_lang="")

    @blacklist_name.command(name="remove", aliases=["del", "delete"])
    async def blacklist_name_remove(self, ctx: commands.Context, *, pattern: str):
        """Remove a pattern from the blacklisted names cache.

        \u200b
        **Arguments**
            - `pattern` The pattern to remove.
        """
        if pattern not in self.blacklist_name_cache.keys():
            return await ctx.send(
                "I could not find a pattern like that in the blacklisted names."
            )
        async with self.config.names() as names:
            names.pop(pattern)
            self.blacklist_name_cache.pop(pattern)
        await ctx.tick()

    @blacklist.command(name="add")
    async def blacklist_add(
        self,
        ctx: commands.Context,
        user: NonBotUser,
        *,
        reason: str = "No reason provided",
    ):
        r"""Add a user to the blacklist

        This will remove their ability to use commands with the bot

        **Arguments**
            - `user` The user to blacklist.
            - `reason` The reason for blacklisting the user. Defaults to "No reason provided.".
        """
        user = user.id
        await self.bot._whiteblacklist_cache.add_to_blacklist(
            guild=None, role_or_user=(user,)
        )
        async with self.config.blacklist() as blacklist:
            blacklist[str(user)] = reason
        await ctx.tick()

    @blacklist.command(name="clear")
    async def blacklist_clear(self, ctx: commands.Context):
        """Clear the blacklist

        **Warning** Every user that was previously blacklisted will now be able to use commands
        """
        msg = await ctx.send("Would you like to clear the blacklist? (y/n)")
        pred = MessagePredicate.yes_or_no()
        try:
            await self.bot.wait_for("message", check=pred)
        except asyncio.TimeoutError:
            pass
        if not pred.result:
            return await ctx.send("Okay. I will not clear the blacklist")
        await self.bot._whiteblacklist_cache.clear_blacklist()
        async with self.config.blacklist() as bl:
            bl.clear()
        await ctx.tick()

    @blacklist.command(name="remove", aliases=["del", "rm"])
    async def blacklist_remove(self, ctx: commands.Context, user: discord.User):
        """Remove users from the blacklist

        The user will be able to use commands again

        **Arguments**
            - `user` The user to remove from the blacklist
        """
        user = user.id
        await self.bot._whiteblacklist_cache.remove_from_blacklist(
            guild=None, role_or_user=(user,)
        )
        async with self.config.blacklist() as blacklist:
            try:
                del blacklist[str(user)]
            except KeyError:
                return await ctx.send("That user is not blacklisted")
        await ctx.tick()

    @blacklist.command(name="reason")
    async def blacklist_reason(
        self, ctx: commands.Context, user: discord.User, *, reason: str
    ):
        """Add or edit the reason for a blacklisted user

        \u200b
        **Arguments**
            - `user` The user to edit the reason for blacklisting.
            - `reason` The new reason for blacklisting the user.
        """
        uid = str(user.id)
        async with self.config.blacklist() as bl:
            if uid not in bl.keys():
                return await ctx.send("That user is not blacklisted")
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
                    await self.bot._whiteblacklist_cache.add_to_blacklist(
                        guild=None, role_or_user=(msg.author.id,)
                    )
                    bl[str(msg.author.id)] = "Name matched the blacklisted name list."
                    log.info(
                        f"Blacklisted {msg.author.name} as they had a blacklisted name."
                    )
                    return


def setup(bot: Red):
    global BLACKLIST_COMMAND, LOCAL_BLACKLIST_COMMAND
    BLACKLIST_COMMAND = bot.remove_command("blocklist")
    LOCAL_BLACKLIST_COMMAND = bot.remove_command("localblocklist")
    bot.add_cog(AdvancedBlacklist(bot))
