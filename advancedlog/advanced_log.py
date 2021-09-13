# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import discord
from redbot.core import commands, Config, modlog
from redbot.core.bot import Red


_config_structure = {
    "global": {
        "registered": False,
    },
    "guild": {
        "enabled": False
    }
}

async def modlog_exists(guild: discord.Guild) -> bool:
    try:
        await modlog.get_modlog_channel(guild)
    except RuntimeError:
        return False
    else:
        return True

class AdvancedLog(commands.Cog):
    """Log different moderator actions using the modlog."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, 544974305445019651, True)
        self.config.register_global(**_config_structure["global"])
        self.config.register_guild(**_config_structure["guild"])
        self._init_task = self.bot.loop.create_task(self.init())

    async def init(self):
        if await self.config.registered():
            return
        try:
            await modlog.register_casetype("Moderator log message", True, "\N{MEMO}", "Moderator log message")
        except RuntimeError:
            pass
        finally:
            await self.config.registered.set(True)

    @commands.command(aliases=["mlog"])
    @commands.mod_or_permissions(administrator=True)
    async def moderatorlog(self, ctx: commands.Context, user: discord.User, *, message: str):
        """Create a modlog case logging something."""
        if not await self.config.guild(ctx.guild).enabled():
            return await ctx.send(\
                f"Moderator logging is not enabled on this guild."
                f"\nHave an admin run `{ctx.clean_prefix}moderatorlogset enabled`"
            )
        elif not await modlog_exists(ctx.guild):
            return await ctx.send("The modlog is not setup on this guild. Please have an admin set one up")
        await modlog.create_case(self.bot, ctx.guild, ctx.message.created_at, "Moderator log message", user, ctx.author, message)
        await ctx.tick()

    @commands.group(name="moderatorlogset", aliases=["mlogset"])
    @commands.admin_or_permissions(administrator=True)
    async def moderator_log_set(self, ctx: commands.Context):
        """Setup the moderator log"""

    @moderator_log_set.command(name="enable", aliases=["disable"])
    async def moderator_log_enable(self, ctx: commands.Context):
        """Enable/disable the moderator log"""
        if not await modlog_exists(ctx.guild):
            return await ctx.send("The modlog is not setup! Please create a modlog on this guild before running this")
        current = not await self.config.guild(ctx.guild).enabled()
        disabled = "enabled" if current else "disabled"
        await ctx.send(f"The moderator log is now {disabled}")
        await self.config.guild(ctx.guild).enabled.set(current)

    async def cog_check(self, ctx: commands.Context):
        return ctx.guild is not None
