# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import asyncio
import logging
from contextlib import suppress
from functools import wraps
from typing import Any, Callable, Final, Iterable, List, Optional, Union, TYPE_CHECKING

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_list, inline, pagify
from redbot.core.utils.predicates import MessagePredicate

from .converters import CommandOrCogConverter, NoneChannelConverter
from .menus import Page, Menu

log = logging.getLogger("red.JojoCogs.cmd_logger")


def humanize_list_with_ticks(data: Iterable[Any]) -> str:
    return humanize_list([inline(x) for x in data])


def listify(func: Callable):
    """Wraps a function's return type in a list"""

    @wraps(func)
    def wrapper(*args, **kwargs) -> list:
        return list(func(*args, **kwargs))

    return wrapper


pagify = listify(pagify)


class CmdLogger(commands.Cog):
    """Log used commands"""

    __authors__: Final[List[str]] = ["Jojo#7791"]
    __version__: Final[str] = "1.0.2"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, 544974305445019651, True)
        self.config.register_global(log_channel=None, commands=[], cogs=[], ignore_owner=True)
        if 544974305445019651 in self.bot.owner_ids: # type:ignore
            with suppress(RuntimeError):
                self.bot.add_dev_env_value("cmdlog", lambda x: self)

        self.log_channel: Optional[Union[discord.TextChannel, discord.Thread]] = None

    async def cog_unload(self) -> None:
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

    async def cog_check(self, ctx: commands.Context) -> bool: # type:ignore
        return await ctx.bot.is_owner(ctx.author)

    @commands.group(name="cmdlogger", aliases=["cmdlog"])
    async def cmd_logger(self, ctx: commands.Context):
        """Commands working with the cmd logger cog"""
        pass

    @cmd_logger.command(name="version")
    async def cmd_log_version(self, ctx: commands.Context):
        """Get the version of Cmd Logger that [botname] is running"""
        await ctx.send(f"Cmd Logger, Version `{self.__version__}`. Made with :heart: by Jojo#7791")

    @cmd_logger.group(name="settings", aliases=["set"])
    async def cmd_settings(self, ctx: commands.Context):
        """Manage the settings for cmd logger"""
        pass

    @cmd_settings.command(name="logall", hidden=True)
    async def cmd_log_all(
        self, ctx: commands.Context, value: bool, confirm: Optional[bool] = False
    ):
        """Log every command used

        This is not recommended if your bot is semi-large (or large) and you have a log channel set.

        **Arguments**
            - `confirm` Skips the confirmation check
        """
        if not confirm and value:
            msg = await ctx.send("Are you sure you would like to log every command? (y/n)")
            pred = MessagePredicate.yes_or_no(ctx)
            try:
                umsg = await ctx.bot.wait_for("message", check=pred)
            except asyncio.TimeoutError:
                pass
            with suppress(discord.Forbidden, discord.NotFound):
                await msg.delete()
                await umsg.add_reaction("\N{WHITE HEAVY CHECK MARK}")
            if not pred.result:
                await ctx.send("Okay, I won't log every command.")
        await self.config.log_all.set(value)
        await ctx.tick()

    @cmd_settings.command(name="ignoreowner")
    async def cmd_settings_ignore_owner(self, ctx: commands.Context, value: bool):
        """Whether the command logger should ignore the owner

        **Arguments**
            - `value` Whether the command logger should ignore the owner or not.
        """
        await self.config.ignore_owner.set(value)
        await ctx.tick()

    @cmd_settings.command(name="channel", usage="<channel or None>")
    async def cmd_channel(self, ctx: commands.Context, channel: NoneChannelConverter):
        """Set the logging channel

        Whenever a tracked command is used a message will be sent here

        **Arguments**
            - `channel` The channel to log command usages to. Type `None` to reset it.
        """
        conf = await self.config.log_channel()
        cid = getattr(channel, "id", channel)
        if cid is None and conf is None:
            return await ctx.send("The log channel is already None")
        elif channel is not None and cid == conf:
            return await ctx.send(f"The log channel is already {channel.name}")
        self.log_channel = channel
        await self.config.log_channel.set(cid)
        await ctx.tick()

    @cmd_logger.command(name="add", usage="<command or cog>")
    async def cmd_add(self, ctx: commands.Context, *, cmd_or_cog: CommandOrCogConverter):
        """Add a command or cog to the tracker.

        If it is a command whenever a user uses this command it will be logged.
        If it is a cog whenever a user uses a command inside this cog it will be logged.

        **Arguments**
            - `command or cog` A command or cog that is registered in the bot.
        """
        cmd = cmd_or_cog.qualified_name
        is_cog = isinstance(cmd_or_cog, commands.Cog)
        key = "cog" if is_cog else "command"
        async with getattr(self.config, f"{key}s")() as cmds:
            if cmd in cmds:
                return await ctx.send(
                    f"I am already tracking the {key} `{cmd}`.\n"
                    f"If this {key} isn't being tracked, please make an issue on my github"
                )
            cmds.append(cmd)
        await ctx.tick()

    @cmd_logger.command(name="delete", aliases=["del", "remove"], usage="<command or cog>")
    async def cmd_remove(self, ctx: commands.Context, *, cmd_or_cog: CommandOrCogConverter):
        """Remove a command or cog from being tracked

        If it is a command this command will no longer be tracked by the bot.
        If it is a cog any commands in this cog will not be tracked by the bot (unless otherwise defined).

        **Arguments**
            - `command or cog` The command or cog to remove from the tracker.
        """
        cmd = cmd_or_cog.qualified_name
        is_cog = isinstance(cmd_or_cog, commands.Cog)
        key = "cog" if is_cog else "command"
        async with getattr(self.config, f"{key}s")() as cmds:
            if cmd not in cmds:
                return await ctx.send(
                    f"I am already not tracking the {key} `{cmd}`.\n"
                    f"If this {key} is being tracked, please make an issue on my github\n"
                    "<https://github.com/Just-Jojo/JojoCogs>"
                )
            cmds.remove(cmd)
        await ctx.tick()

    @cmd_logger.command(name="list")
    async def cmd_list(self, ctx: commands.Context):
        """List the commands and cogs tracked by [botname]"""
        if await self.config.log_all():
            return await ctx.send("I am currently logging every command used.")
        cmds = await self.config.commands()
        cogs = await self.config.cogs()
        if not cmds and not cogs:
            return await ctx.send(
                "I am not tracking any commands or cogs.\n"
                "If I am still tracking commands please make an issue on my github\n"
                "<https://github.com/Just-Jojo/JojoCogs>"
            )
        if cmds:
            cmds.insert(0, "**Commands**")
        if cogs:
            cogs.insert(0, "**Cogs**")
        cmds.extend(cogs)
        data: list = pagify("\n".join(cmds), page_length=200) # type:ignore
        await Menu(Page(data), ctx).start()

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        conf = await self.config.all()
        name = ctx.command.qualified_name
        if (
            not conf["log_all"]
            and (conf["ignore_owner"] and await ctx.bot.is_owner(ctx.author))
            and ctx.command.qualified_name not in conf["commands"]
            and (ctx.cog is None or ctx.cog.qualified_name not in conf["cogs"])
        ):
            return  # Large if statements are fucking dumb
        if await self.bot.is_owner(ctx.author) and conf["ignore_owner"]:
            return
        guild_data = "Guild: None" if not ctx.guild else f"Guild: {ctx.guild} ({ctx.guild.id})"
        msg = f"Command '{ctx.command.qualified_name}' was used by {ctx.author} ({ctx.author.id}). {guild_data}"
        log.info(msg)
        if not self.log_channel:
            channel = conf["log_channel"]
            if not channel:
                return

            async def get_or_fetch_channel(bot, channel_id: int):
                channel = bot.get_channel(channel_id)
                if not channel:
                    channel = await bot.fetch_channel(channel_id)
                return channel

            try:
                self.log_channel = await get_or_fetch_channel(self.bot, channel)
            except discord.HTTPException as e:
                # I'd rather just catch exception rather than any discord related exception
                # as it's possible I could miss some
                log.warning("I could not find the log channel")
                await self.config.log_channel.clear()
                return
        if TYPE_CHECKING:
            assert isinstance(self.log_channel, discord.TextChannel), "mypy momen"
        try:
            await self.log_channel.send(msg)
        except discord.Forbidden:
            log.warning(
                f"I could not send a message to channel '{self.log_channel.name}'"
                "\nAs such I am disabling channel logging."
            )
            await self.config.log_channel.clear()
            self.log_channel = None  # maybe this is wise?
