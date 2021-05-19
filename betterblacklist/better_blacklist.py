# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

# type:ignore[assignment]

import logging
from asyncio import Task

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box

log = logging.getLogger("red.JojoCogs.betterblacklist")
_config_structure = {
    "global": {
        "blacklist": {},  # Dict[str, str]. String version of the uid and reason
        "use_reasons": True,
    }
}
BLACKLIST_COMMAND: commands.Command = None


class BetterBlacklist(commands.Cog):
    """A "better" blacklist cog"""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, 544974305445019651, True)
        self.config.register_global(**_config_structure["global"])
        self.task: Task = self.bot.loop.create_task(self.init())

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
        await self.bot.wait_for_red_ready()
        async with self.config.blacklist() as bl:
            blacklist = await self.bot._whiteblacklist_cache.get_blacklist()
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
        formatted = "\n".join(f"{uid}\t|\t{reason}" for uid, reason in blacklist.items())
        await ctx.send(box(formatted))

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
    bot.add_cog(BetterBlacklist(bot))
