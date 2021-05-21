# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

# type:ignore[assignment]

import logging
import asyncio

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box
from redbot.core.utils.predicates import MessagePredicate
from tabulate import tabulate


log = logging.getLogger("red.JojoCogs.betterblacklist")
_config_structure = {
    "global": {
        "blacklist": {},  # Dict[str, str]. String version of the uid and reason
        "use_reasons": True,
    }
}
BLACKLIST_COMMAND: commands.Command = None


class AdvancedBlacklist(commands.Cog):
    """An advanced blacklist cog"""

    __version__ = "1.0.0Dev"
    __author__ = ["Jojo#7791"]

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, 544974305445019651, True)
        self.config.register_global(**_config_structure["global"])
        self.task: asyncio.Task = self.bot.loop.create_task(self.init())

    def format_help_for_context(self, ctx: commands.Context):
        pre_processed = super().format_help_for_context(ctx)
        return (
            f"{pre_processed}\n\n"
            f"Author: `{', '.join(self.__author__)}`\n"
            f"Version: `{self.__version__}`"
        )

    def cog_unload(self):
        global BLACKLIST_COMMAND
        if self.task:
            self.task.cancel()
        if BLACKLIST_COMMAND:
            try:
                self.bot.remove_command("blocklist")
            except Exception as e:
                log.debug(exc_info=e)
            finally:
                self.bot.add_command(BLACKLIST_COMMAND)

    async def init(self):
        log.info("Hello")
        await self.bot.wait_until_red_ready()
        log.info("Line 48")
        async with self.config.blacklist() as bl:
            blacklist = await self.bot._whiteblacklist_cache.get_blacklist()
            log.info("Line 51")
            log.info(blacklist)
            for uid in blacklist:
                if str(uid) in bl.keys():
                    continue
                bl[str(uid)] = "No reason provided"

    @commands.group(aliases=["blocklist"])  # Meh, might as well
    async def blacklist(self, ctx: commands.Context):
        """Add/remove users from the blacklist"""
        pass

    @blacklist.command(name="list")
    async def blacklist_list(self, ctx: commands.Context):
        """List the users in your blacklist"""
        blacklist = await self.config.blacklist()
        users = []
        for uid, reason in blacklist.items():
            users.append([f"{uid} ({await self._get_user_name(uid)})", reason])
        tabulated = tabulate(users, ("User", "Reason"), "plain")
        await ctx.send(box(tabulated))

    async def _get_user_name(self, uid: int) -> str:
        try:
            return await self.bot.get_or_fetch_user(uid)
        except discord.NotFound:
            return "Unknown or Deleted User."

    @blacklist.command(name="add")
    async def blacklist_add(
        self, ctx: commands.Context, user_id: int, *, reason: str = "No reason provided"
    ):
        """Add a user to the blacklist"""
        await self.bot._whiteblacklist_cache.add_to_blacklist(
            guild=None, role_or_user=[user_id]  # type:ignore[arg-type]
        )
        async with self.config.blacklist() as blacklist:
            blacklist[str(user_id)] = reason
        await ctx.tick()

    @blacklist.command(name="clear")
    async def blacklist_clear(self, ctx: commands.Context):
        """Clear the blacklist"""
        msg = await ctx.send("Would you like to clear the blacklist?")
        pred = MessagePredicate.yes_or_no()
        try:
            await self.bot.wait_for("message", check=pred)
        except asyncio.TimeoutError:
            pred.result = False
        if not pred.result:
            return await ctx.send("Okay. I will not clear the blacklist")
        await self.bot._whiteblacklist_cache.clear_blacklist()
        async with self.config.blacklist() as bl:
            bl.clear()
        await ctx.tick()

    @blacklist.command(name="remove", aliases=["del", "rm"])
    async def blacklist_remove(self, ctx: commands.Context, user_id: int):
        """Remove users from the blacklist"""
        await self.bot._whiteblacklist_cache.remove_from_blacklist(
            guild=None, role_or_user=[user_id]  # type:ignore[arg-type]
        )
        async with self.config.blacklist() as blacklist:
            try:
                del blacklist[str(user_id)]
            except KeyError:
                pass
        await ctx.tick()

    async def cog_check(self, ctx: commands.Context) -> bool:
        # Owner only cog check
        return await self.bot.is_owner(ctx.author)


def setup(bot: Red):
    global BLACKLIST_COMMAND
    BLACKLIST_COMMAND = bot.remove_command("blocklist")
    bot.add_cog(AdvancedBlacklist(bot))
