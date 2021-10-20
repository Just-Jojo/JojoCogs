# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import discord
import logging
from contextlib import suppress
from functools import wraps
from typing import Any, Callable, Iterable, List

from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_list, inline, pagify

from .converters import CommandConverter, NoneChannelConverter
from .menus import CmdMenu, CmdPages

log = logging.getLogger("red.JojoCogs.cmd_logger")


def humanize_list_with_ticks(data: Iterable) -> str:
    return humanize_list([inline(x) for x in data])


def listify(func: Callable):
    """Wraps a function's return type in a list"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        return list(func(*args, **kwargs))

    return wrapper


pagify = listify(pagify)


class CmdLogger(commands.Cog):
    """Log used commands"""

    __authors__ = ["Jojo#7791"]
    __version__ = "1.0.0"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, 544974305445019651, True)
        self.config.register_global(log_channel=None, commands=[])
        if 544974305445019651 in self.bot.owner_ids:
            with suppress(RuntimeError):
                self.bot.add_dev_env_value("cmdlog", lambda x: self)

    def cog_unload(self) -> None:
        with suppress(Exception):
            self.bot.remove_dev_env_value("cmdlog")

    def format_help_for_context(self, ctx: commands.Context) -> str:
        pre = super().format_help_for_context(ctx)
        plural = "" if len(self.__authors__) == 1 else "s"
        return (
            f"{pre}\n"
            f"Author{plural}: {humanize_list_with_ticks(self.__authors__)}\n"
            f"Version: `{self.__version__}`"
        )

    async def cog_check(self, ctx: commands.Context) -> bool:
        return await ctx.bot.is_owner(ctx.author)

    @commands.group(name="cmdlogger", aliases=["cmdlog"])
    async def cmd_logger(self, ctx: commands.Context):
        """Commands working with the cmd logger cog"""
        pass

    @cmd_logger.command(name="version")
    async def cmd_log_version(self, ctx: commands.Context):
        """Get the version of Cmd Logger that [botname] is running"""
        await ctx.send(
            f"Cmd Logger, Version `{self.__version__}`. Made with :heart: by Jojo#7791"
        )

    @cmd_logger.group(name="settings", aliases=["set"])
    async def cmd_settings(self, ctx: commands.Context):
        """Manage the settings for cmd logger"""
        pass

    @cmd_settings.command(name="channel", usage="<channel or None>")
    async def cmd_channel(self, ctx: commands.Context, channel: NoneChannelConverter):
        """Set the logging channel

        Whenever a tracked command is used a message will be sent here

        **Arguments**
            - `channel` The channel to log command usages to. Type `None` to reset it.
        """
        conf = await self.config.log_channel()
        cid = channel if channel is None else channel.id
        if cid is None and conf is None:
            return await ctx.send("The log channel is already None")
        elif cid is not None and cid == conf:
            return await ctx.send(f"The log channel is already {channel.name}")
        await self.config.log_channel.set(cid)
        await ctx.tick()

    @cmd_logger.command(name="add")
    async def cmd_add(self, ctx: commands.Context, command: CommandConverter):
        """Add a command to the tracker.

        Whenever a user uses this command it will be logged

        **Arguments**
            - `command` A command that is registered in the bot.
        """
        cmd = command.qualified_name
        async with self.config.commands() as cmds:
            if cmd in cmds:
                return await ctx.send(
                    f"I am already tracking the command `{cmd}`.\n"
                    "If this command isn't being tracked, please make an issue on my github"
                )
            cmds.append(cmd)
        await ctx.tick()

    @cmd_logger.command(name="delete", aliases=["del", "remove"])
    async def cmd_remove(self, ctx: commands.Context, command: CommandConverter):
        """Remove a command from being tracked

        This command will no longer be tracked by the bot

        **Arguments**
            - `command` The command to remove from the tracker.
        """
        cmd = command.qualified_name
        async with self.config.commands() as cmds:
            if cmd not in cmds:
                return await ctx.send(
                    f"I am already not the command `{cmd}`.\n"
                    "If this command is being tracked, please make an issue on my github"
                )
            cmds.remove(cmd)
        await ctx.tick()

    @cmd_logger.command(name="list")
    async def cmd_list(self, ctx: commands.Context):
        """List the commands tracked by [botname]"""
        cmds = await self.config.commands()
        if not cmds:
            return await ctx.send(
                f"I am not tracking any commands. Use `{ctx.clean_prefix}cmdlog add <command>` to add one"
            )
        data = pagify("\n".join(cmds), page_length=200)
        await CmdMenu(CmdPages(data)).start(ctx) # type:ignore

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        conf = await self.config.all()
        name = ctx.command.qualified_name
        if ctx.command.qualified_name in conf["commands"]:
            guild_data = (
                "Guild: None" if not ctx.guild else f"Guild: {ctx.guild} ({ctx.guild.id})"
            )
            msg = f"Command '{ctx.command.qualified_name}' was used by {ctx.author} ({ctx.author.id}). {guild_data}"
            log.info(msg)
            channel = conf["log_channel"]
            if not channel:
                return
            async def get_or_fetch_channel(bot, channel_id: int):
                channel = self.bot.get_channel(channel_id)
                if not channel:
                    channel = await bot.fetch_channel(channel_id)
                return channel
            try:
                channel = await get_or_fetch_channel(self.bot, channel)
            except Exception as e:
                # I'd rather just catch exception rather than any discord related exception
                # as it's possible I could miss some
                log.warning("I could not find the log channel")
                await self.config.log_channel.clear()
                return
            try:
                await channel.send(msg)
            except discord.Forbidden:
                log.warning(f"I could not send a message to channel '{channel.name}'")
                await self.config.log_channel.clear()
