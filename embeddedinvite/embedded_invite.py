# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import json
import logging
import pathlib
from datetime import datetime
from typing import Optional

import aiohttp
import discord
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_list

log = logging.getLogger("red.JojoCogs.embedded_invite")
with open(pathlib.Path(__file__).parent / "info.json") as fp:
    __red_end_user_data_statement__ = json.load(fp)["end_user_data_statement"]
del json, pathlib

INVITE_COMMAND: Optional[commands.Command] = None
__all__ = ["setup", "__red_end_user_data_statement__"]


class EmbeddedInvite(commands.Cog):
    """Embed invite links.

    This cog was requested by DSC#6238"""

    __authors__ = ["Jojo#7791"]
    __version__ = "1.0.1"

    def format_help_for_context(self, ctx: commands.Context):
        pre = super().format_help_for_context(ctx)
        plural = "s" if len(self.__authors__) > 1 else ""
        return (
            f"{pre}\n"
            f"Author{plural}: {humanize_list(self.__authors__)}\n"
            f"Version: `{self.__version__}`"
        )

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, 544974305445019651, True)
        self.config.register_global(custom_url=None, send_in_channel=False, custom_message=None)
        self._url_cache: Optional[str] = None
        self._channel_cache: Optional[bool] = None
        self._custom_message: Optional[str] = None
        self.task = self.bot.loop.create_task(self.init())

    async def init(self):
        self._url_cache = await self.config.custom_url()
        self._channel_cache = await self.config.send_in_channel()
        self._custom_message = await self.config.custom_message()

    def cog_unload(self):
        if INVITE_COMMAND:
            bot.remove_command("invite")
            bot.add_command(INVITE_COMMAND)
        self.task.cancel()

    @commands.group(invoke_without_command=True)
    @commands.check(lambda ctx: ctx.bot.get_cog("Core")._can_get_invite_url)
    async def invite(self, ctx: commands.Context):
        """Invite [botname] to your server"""
        core = self.bot.get_cog("Core")
        channel = ctx.channel
        if not self._channel_cache:
            channel = ctx.author.dm_channel
            if not channel:
                await ctx.author.create_dm()
                channel = ctx.author.dm_channel
        url = await core._invite_url()  # type:ignore
        message = self._custom_message or f"Thanks for choosing {ctx.me.name}!"
        kwargs = {"content": f"{message}\nHere is {ctx.me}'s invite url: {url}"}
        if await self.bot.embed_requested(channel, ctx.author):
            embed = discord.Embed(
                title=f"Invite {ctx.me.name}",
                description=(
                    f"{message}\n"
                    f"\nHere is **[{ctx.me.name}'s invite]({url})**"),
                colour=await ctx.embed_colour(),
                timestamp=datetime.utcnow(),
            )
            embed.add_field(name="Here's a link if you're on mobile", value=url)
            url = self._url_cache or ctx.me.avatar_url
            embed.set_thumbnail(url=url)
            kwargs = {"embed": embed}
        try:
            await channel.send(**kwargs)
        except discord.Forbidden as e:
            if not self._channel_cache:
                await ctx.send(
                    "I cannot send you DMs. Please enable them so I can DM you."
                )
            else:
                await ctx.send("Hm, something went wrong...")
                log.error("Error in command 'invite'", exc_info=e)

    @invite.command(name="url")
    @commands.is_owner()
    async def invite_url(self, ctx: commands.Context, url: str = None):
        """Set the invite url for the embed.

        **Arguments**
        >   url: Sets the url for the embed thumbnail. Defautls to the bot's avatar."""
        if url:
            if not url.endswith((".gif", ".png", ".jpg", ".jpeg")):
                return await ctx.send("That url did not end with a supported image type.")
            try:
                async with aiohttp.request("GET", url) as re:
                    if re.status != 200:
                        return await ctx.send("I could not access that url.")
            except aiohttp.InvalidURL:
                return await ctx.send("That was an invalid url.")
        await self.config.custom_url.set(url)
        self._url_cache = url
        await ctx.tick()

    @invite.command(name="channel")
    @commands.is_owner()
    async def invite_channel(self, ctx: commands.Context, toggle: bool):
        """Sets if the invite should be sent in the channel the command was invoked in.

        For example, if the toggle is true when a user types `[p]invite` it will send it in that channel

        **Arguments**
        >   toggle: If the message should be sent in channel it was invoked in or not"""
        if toggle == self._channel_cache:
            nt = "doesn't " if toggle else ""
            return await ctx.send(
                f"Invite already {nt}sends the message in the invoked channel."
            )
        await self.config.send_in_channel.set(toggle)
        self._channel_cache = toggle
        await ctx.tick()

    @invite.command(name="message")
    @commands.is_owner()
    async def invite_message(self, ctx: commands.Context, *, msg: str = None):
        """Set the message for invites.
        
        This will be before the invite url.
        
        **Arguments**
        >   msg: The custom message for the invite command. If no msg is given, it will revert to the default
        'Thanks for choosing [botname]'"""
        if not msg and not self._custom_message:
            return await ctx.send(
                "The message is already set to default. If you would like to view the help for this command, "
                f"use `{ctx.clean_prefix}help invite message`"
            )
        self._custom_message = msg
        await self.config.custom_message.set(msg)
        await ctx.tick()


def setup(bot: Red):
    global INVITE_COMMAND
    INVITE_COMMAND = bot.remove_command("invite")
    bot.add_cog(EmbeddedInvite(bot))
