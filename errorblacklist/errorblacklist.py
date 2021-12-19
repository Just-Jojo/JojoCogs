# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

# type:ignore[missing-import]

import logging
from typing import Literal

import discord
from discord.ext import tasks
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import pagify

from .api import *
from .menus import Menu, Page
from .utils import *

log = logging.getLogger("red.JojoCogs.error_blacklist")
RequestType = Literal["discord_deleted_user", "owner", "user", "user_strict"]

_config_structure = {
    "global": {
        "enabled": False,
        "amount": 5,
        "clear_usage": True,
        "whitelist": {
            "commands": [],  # List[str] commands that are ignored by this cog
            "cogs": [],  # List[str]
            "users": [],  # List[int] users who are ignored by this cog
        },
        "ignore": {
            "guilds": [],  # List[int] guilds that are ignored by this cog
            "channels": [],  # List[int] channels that are ignored by this cog
        },
        "message": (
            "Please do not use this command anymore.\n\n"
            "Continued usage of this command will result in you being blacklisted from using "
            "my commands."
        ),
        "message_enabled": True,
    },
    "user": {
        "errors": {},  # Commands name and the amount of times the command has been used
    },
}


async def enabled(ctx: commands.Context):
    return await ctx.cog.config.message_enabled()


class ErrorBlacklist(commands.Cog):
    """
    Blacklist users if they use a command that errors too many times
    """

    __authors__ = ["Jojo#7791"]
    __version__ = "1.1.0"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        plural = "" if len(self.__authors__) == 1 else "s"
        return (
            f"{super().format_help_for_context(ctx)}\n"
            f"**Author{plural}:** {humanize_list(self.__authors__)}\n"
            f"**Version:** `{self.__version__}`"
        )

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, 544974305445019651, True)
        for key, value in _config_structure.items():
            getattr(self.config, f"register_{key}", lambda **x: x)(**value)
        self._cache: dict = {}
        self.first_run: bool = True

    async def startup(self):
        if await self.config.clear_usage():
            self.clear_cache.start()
        self._cache = await self.config.all_users()

    def cog_unload(self):
        if self.clear_cache.is_running():
            self.clear_cache.cancel()

    async def red_delete_data_for_user(self, *, requester: RequestType, user_id: int):
        """This cog does not store any data"""
        return

    @commands.command()
    async def errblversion(self, ctx: commands.Context):
        """Get the version of error blacklist"""
        await ctx.maybe_send_embed(
            f"Error blacklist. Version `{self.__version__}`, written by {', '.join(self.__authors__)}"
        )

    @commands.is_owner()
    @commands.group(aliases=["errorbl", "errbl"])
    async def errorblacklist(self, ctx: commands.Context):
        """Manage the error blacklist cog's settings"""
        pass

    @errorblacklist.group(name="ignore")
    async def error_blacklist_ignore(self, ctx: commands.Context):
        """Ignore channels or guilds

        Any time a command errors on that channel/guild it will be ignored
        """
        pass

    @error_blacklist_ignore.command(name="add")
    async def ignore_add(self, ctx: commands.Context, guild_or_channel: ChannelOrGuild):
        """Ignore a guild or channel.

        Commands that error in this guild/channel will be ignored by the error watcher.

        **Arguments**
            - `guild_or_channel` The guild or channel to ignore.
        """
        guild = "guild" if isinstance(guild_or_channel, discord.Guild) else "channel"
        coro = getattr(self.config.ignore, f"{guild}s")  # Being lazy is fun
        async with coro() as data:
            if guild_or_channel.id in data:
                return await ctx.send(f"That {guild} is already being ignored")
            data.append(guild_or_channel.id)
        await ctx.send(f"I will now ignore the {guild} `{guild_or_channel.name}`")

    @error_blacklist_ignore.command(name="remove", aliases=["del", "delete", "rm"])
    async def ignore_remove(self, ctx: commands.Context, guild_or_channel: ChannelOrGuild):
        """Remove a guild or channel from the ignored list.

        Commands that error in this guild/channel will no longer be ignored by the error watcher.

        **Arguments**
            - `guild_or_channel` The guild or channel to remove from the ignored list.
        """
        guild = "guild" if isinstance(guild_or_channel, discord.Guild) else "channel"
        coro = getattr(self.config.ignore, f"{guild}s")
        async with coro() as data:
            if (_id := guild_or_channel.id) not in data:
                return await ctx.send(f"That {guild} is not in the ignored list")
            data.remove(_id)
        await ctx.send(f"I will no longer ignore the {guild} `{guild_or_channel.name}`")

    @error_blacklist_ignore.command(name="list")
    async def ignore_list(self, ctx: commands.Context):
        """List the ignored channels and guilds"""
        coro = self.config.ignore
        data = []
        if guilds := await coro.guilds():
            guilds.insert(0, "**Guilds**")
            data.extend(guilds)
        if channels := await coro.channels():
            channels.insert(0, "**Channels**")
            data.extend(channels)
        if not data:
            return await ctx.send("The ignore list is empty")

        data = list(pagify("\n".join(str(x) for x in data), page_length=200))
        await Menu(Page(data, title="Ignore List")).start(ctx)

    @errorblacklist.command(name="enable", aliases=["disable", "toggle"])
    async def error_blacklist_enable(self, ctx: commands.Context):
        """Enable the error watcher

        If enabled it will watch for when a user uses a command that errors.
        """
        coro = self.config.enabled
        await coro.set(not await coro())
        enabled = "enabled" if await coro() else "disabled"
        await ctx.send(f"The error watcher is now {enabled}.")

    @errorblacklist.command(name="clearusage")
    async def error_blacklist_clear_usage(self, ctx: commands.Context, toggle: bool):
        """Have the watcher remove command usage after a day"""
        coro = self.config.clear_usage
        enabled = "enabled" if toggle else "disabled"
        if await coro() is toggle:
            return await ctx.send(f"Usage clearing is already {enabled}.")
        await coro.set(toggle)
        await ctx.send(f"Usage clearing is now {enabled}.")

    @errorblacklist.command(name="amount")
    async def error_blacklist_amount(self, ctx: commands.Context, amount: PositiveInt):
        """Set the amount of times a user has to use a command that errors to be blacklisted"""
        if amount == 1:
            return await ctx.send("1?! Have mercy on them for Billy Bob's sake")
        await self.config.amount.set(amount)
        await ctx.send(
            f"Done. If a user uses a command that errors `{amount}` times they will be blacklisted"
        )

    @errorblacklist.group(name="whitelist")
    async def error_blacklist_whitelist(self, ctx: commands.Context):
        """Manage the whitelist for the error blacklist cog.

        You can whitelist users or commands
        """
        pass

    @error_blacklist_whitelist.command(name="add", usage="<user_com_or_cog>")
    async def whitelist_add(self, ctx: commands.Context, user_or_command: UserOrCommandCog):
        """Add an itme to the whitelist.

        If it's a user that user will be ignored by the error checker.
        If it's a command when the command errors it will be ignored by the error checker.
        If it's a cog if any of its commands errors it will be ignored by the error checker.

        **Arguments**
            - `user_or_command` The user, cog, or command to whitelist.
        """
        if is_user := isinstance(user_or_command, discord.User):
            user = "user"
        elif isinstance(user_or_command, commands.Command):
            user = "command"
        else:
            user = "cog"
        to_add = getattr(user_or_command, "qualified_name", user_or_command.id)
        val = getattr(self.config.whitelist, f"{user}s")
        if to_add in await val():
            return await ctx.send(f"That {user} is already in the whitelist.")
        user = f"{user} id" if is_user else user
        await ctx.send(f"Done. Added `{to_add}` to the whitelist as a {user}.")
        async with val() as f:
            f.append(to_add)

    @error_blacklist_whitelist.command(name="remove", aliases=["del", "delete"])
    async def whitelist_remove(self, ctx: commands.Context, user_or_command: UserOrCommandCog):
        """Remove a user, cog, or command from the whitelist.

        The object will then no longer be ignored by the error watcher

        **Arguments**
            - `user_or_command` The user, cog, or command to be removed from the whitelist
        """
        if is_user := isinstance(user_or_command, discord.User):
            user = "user"
        elif isinstance(user_or_command, commands.Cog):
            user = "cog"
        else:
            user = "command"
        val = getattr(self.config.whitelist, f"{user}s")
        to_add = getattr(user_or_command, "qualified_name", user_or_command.id)
        if to_add not in await val():
            return await ctx.send(f"That {user} is not in the whitelist.")
        user = f"{user} id" if is_user else user
        await ctx.send(f"Done. Removed `{to_add}` from the whitelist as a {user}")

        async with val() as f:
            f.remove(to_add)

    @error_blacklist_whitelist.command(name="list")
    async def whitelist_list(self, ctx: commands.Context):
        """List the whitelist showing both users, cogs and commands"""
        coro = self.config.whitelist
        coms = await coro.commands()
        cogs = await coro.cogs()
        users = await coro.users()
        if not any([coms, cogs, users]):
            return await ctx.send("The whitelist is empty.")
        data: list = []
        if coms:
            coms.insert(0, "**Commands**")
            data.extend(coms)
        if cogs:
            cogs.insert(0, "**Cogs**")
            data.extend(cogs)
        if users:
            users.insert(0, "**Users**")
            data.extend(users)
        data = [str(x) for x in data]

        data = list(pagify("\n".join(data), page_length=200))
        await Menu(Page(data)).start(ctx)

    @errorblacklist.group(name="message")
    async def error_blacklist_message(self, ctx: commands.Context):
        """Manage the settings for the message sent when someone uses an erroring command"""
        pass

    @commands.check(enabled)
    @error_blacklist_message.command(name="set")
    async def message_set(self, ctx: commands.Context, *, message: NoneConverter):
        """Set the warning message that gets sent when a user uses an erroring command

        Type `None` to reset it.

        **Arguments**
            - `message` The message sent to warn the user. Type `None` to reset it.
        """
        set_reset = "set" if message else "reset"
        message = message or _config_structure["message"]
        await self.config.message.set(message)
        await ctx.send(f"The message has been {set_reset}")

    @error_blacklist_message.command(name="enable", aliases=("toggle", "disable"))
    async def message_enable(self, ctx: commands.Context):
        """Toggle whether the warning message should be sent or not."""
        data = await (coro := self.config.message_enabled)()
        toggle = "disabled" if data else "enabled"
        await coro.set(not data)
        await ctx.send(f"The warning message has been {toggle}.")

    @errorblacklist.command(name="showsettings", aliases=["settings"])
    async def error_blacklist_settings(self, ctx: commands.Context):
        """Show error blacklist's settings"""
        coro = self.config
        data = {
            "Enabled": await coro.enabled(),
            "Times a user has to use an erroring command": await coro.amount(),
            "Clear a user's error logs": await coro.clear_usage(),
            "Message enabled": await coro.message_enabled(),
        }
        if data["Message enabled"]:
            data["Message"] = await coro.message()
        kwargs = {
            "content": (
                f"**Error Blacklist settings**\n"
                "\n".join(f"**{key}:** {value}" for key, value in data.items())
            )
        }
        if await ctx.embed_requested():
            embed = discord.Embed(
                title="Error Blacklist settings", colour=await ctx.embed_colour()
            )
            [embed.add_field(name=key, value=value, inline=False) for key, value in data.items()]
            kwargs = {"embed": embed}
        await ctx.send(**kwargs)

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context, err: Exception, unhandled_by_cog=False
    ):
        if not unhandled_by_cog:
            if hasattr(ctx.command, "on_error"):
                return

            if ctx.cog and ctx.cog.has_error_handler():
                return

        if not isinstance(err, commands.CommandInvokeError) or not ctx.command.cog:
            return

        whitelist = await self.config.whitelist()
        user = ctx.author
        if not await self.config.enabled() or await self.bot.is_owner(user):
            return

        if ctx.guild:
            log.debug("In a guild")
            gid, cid = [getattr(ctx, x).id for x in ("guild", "channel")]  # LAZY
            coro = self.config.ignore
            if gid in await coro.guilds() or cid in await coro.channels():
                log.debug("Ignored tbh")
                return

        name = ctx.command.qualified_name
        if name in await self.config.whitelist.commands():
            return
        if user.id in await self.config.whitelist.users():
            return
        if await self.config.message_enabled():
            await ctx.send(await self.config.message())

        if user.id not in self._cache.keys():
            self._cache[user.id] = {name: 1}
        else:
            try:
                self._cache[user.id][name] += 1
            except KeyError:
                self._cache[user.id][name] = 1

        amount = await self.config.amount()
        if (am := self._cache[user.id].get(ctx.command.name)) and am >= amount:
            log.info(
                f"Blacklisted {user} ({user.id}) as they have used a command that has errored {am} times."
            )
            await add_to_blacklist(self.bot, {user})
            self.bot.dispatch("error_blacklist", user, ctx.command)

    @tasks.loop(hours=24)
    async def clear_cache(self):
        if self.first_run:
            self.first_run = False
            return
        if not await self.config.clear_usage():
            self.clear_cache.cancel()
            return
        for user in (await self.config.all_users()).keys():
            await self.config.user_from_id(user).clear()
        log.debug("Cleared user usage")

    @clear_cache.before_loop
    async def before_clear(self):
        await self.bot.wait_until_red_ready()
