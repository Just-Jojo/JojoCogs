# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import asyncio
import logging
from datetime import datetime
from typing import Optional, TypeVar, Any

import aiohttp
import discord
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_list

from .utils import *

log = logging.getLogger("red.JojoCogs.advanced_invite")


_default_message = "Thanks for choosing {bot_name}!"
_default_title = "Invite {bot_name}"
_config_structure = {
    "custom_url": None,
    "custom_message": _default_message,
    "send_in_channel": False,
    "embeds": True,
    "footer": None,
    "title": _default_title,
    "support_server": None,
    "mobile_check": True,
}
AI = TypeVar("AI", bound="AdvancedInvite")


def embed_check(ctx) -> bool:
    """Small fuction for command checks"""
    return ctx.cog._settings_cache["embeds"] is True


def can_invite():
    async def inner_spirit_animal(ctx: commands.Context) -> bool:
        return await ctx.bot.get_cog("Core")._can_get_invite_url(ctx)

    return commands.check(inner_spirit_animal)


class AdvancedInvite(commands.Cog):
    """An "advanced" invite cog.

    This cog was requested by DSC#6238"""

    __authors__ = ["Jojo#7791"]
    __version__ = "2.1.0"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        pre = super().format_help_for_context(ctx)
        plural = "s" if len(self.__authors__) > 1 else ""
        return (
            f"{pre}\n"
            f"Author{plural}: `{humanize_list(self.__authors__)}`\n"
            f"Version: `{self.__version__}`"
        )

    async def red_delete_data_for_user(self, **kwargs) -> None:
        return

    async def red_get_data_for_user(self, **kwargs) -> dict:
        return dict()

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, 544974305445019651, True)
        self.config.register_global(**_config_structure)
        self._settings_cache: dict = {}
        self._invite_command: Optional[commands.Command] = None

    @classmethod
    async def init(cls, bot: Red) -> AI:
        """Initialize the cog and the cache"""
        self = cls(bot)
        self._settings_cache = await self.config.all()
        self._invite_command = self.bot.remove_command("invite")
        return self

    def cog_unload(self) -> None:
        if self._invite_command:
            self.bot.remove_command("invite")
            self.bot.add_command(self._invite_command)

    @commands.command(name="inviteversion")
    async def invite_version(self, ctx: commands.Context):
        """Get the version of Advanced Invite"""
        msg = (
            f"Advanced Invite Version: {self.__version__}"
            f"\nThis cog was requested by DSC#6238, a good friend of mine."
        )
        kwargs = {"content": msg, "embed": None}
        if await ctx.embed_requested():
            embed = discord.Embed(
                title="Advanced Invite Version",
                colour=await ctx.embed_colour(),
                description=msg,
            )
            kwargs.update({"embed": embed, "content": None})
        await ctx.send(**kwargs)

    @commands.group(invoke_without_command=True)
    # This check is similar to the one core uses
    # see https://github.com/Cog-Creators/Red-DiscordBot/blob/V3/develop/redbot/core/core_commands.py#L1490
    @can_invite()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def invite(self, ctx: commands.Context):
        """Invite [botname] to your server"""
        kwargs: dict

        title = self._settings_cache["title"].replace("{bot_name}", ctx.me.name)
        support = self._settings_cache["support_server"]
        invite = await self.bot.get_cog("Core")._invite_url()
        cm = self._settings_cache["custom_message"].replace("{bot_name}", ctx.me.name)
        support_msg = (
            f"**Join the support server!**\n{support}\n" if support else ""
        )
        kwargs = {
            "content": f"**{title}**\n{cm}\n{invite}\n{support_msg}{timestamp_format()}"
        }
        if await ctx.embed_requested() and self._settings_cache["embeds"]:
            embed = discord.Embed(
                title=title,
                description=cm,
                colour=await ctx.embed_colour(),
            ).add_field(
                name="Invite URL", value=invite, inline=False
            )
            if support_msg:
                embed.add_field(name="Support", value=support_msg, inline=False)
            kwargs = {"embed": embed}
        await self._handle_invite(ctx, **kwargs)

    async def _handle_invite(self, ctx: commands.Context, **kwargs: Any):
        if not isinstance(ctx.channel, discord.abc.GuildChannel) or not self._settings_cache["send_in_channel"]:
            ctx.command.reset_cooldown(ctx)
        if self._settings_cache["send_in_channel"]:
            return await ctx.send(**kwargs)
        try:
            await ctx.author.send(**kwargs)
        except discord.Forbidden:
            await ctx.send("I'm sorry, I can't dm you.")

    @invite.group(name="settings")
    @commands.is_owner()
    async def invite_settings(self, ctx: commands.Context):
        """Manage Advanced Invite's settings"""
        stngs = self._settings_cache
        _enabled = lambda x: "Enabled" if x else "Disabled"
        data = {
            "Dm only": _enabled(not stngs["send_in_channel"]),
            "Embedded": _enabled(stngs["embeds"]),
            "URL": stngs["custom_url"] or "No url",
            "Message": stngs["custom_message"],
            "Footer": stngs["footer"],
            "Title": stngs["title"],
            "Support server": stngs["support_server"] or "No support server",
        }
        if await ctx.embed_requested():
            embed = discord.Embed(title="Invite Settings", colour=await ctx.embed_colour())
            for key, value in data.items():
                embed.add_field(name=key, value=value, inline=False)
            kwargs = {"embed": embed}
        else:
            msg = "**Invite Settings**\n\n"
            for key, value in data.items():
                msg += f"**{key}:** {value}"
            kwargs = {"content": msg}
        await ctx.send(**kwargs)

    @invite_settings.command(name="title")
    async def invite_title(self, ctx: commands.Context, *, title: str):
        """Set the title for the invite message

        You can use '{bot_name}' in your message to have it be formatted with the name of the bot

        Eg. 'Invite {bot_name}!' => 'Invite [botname]'

        **Arguments**
            - `title` The title of the message.
        """
        await self.config.title.set(title)
        await ctx.send(f"Done. The title is now '{title}'")
        self._settings_cache["title"] = title

    @invite_settings.command(name="message")
    async def invite_message(self, ctx: commands.Context, *, msg: str):
        """Set the message for the invite command

        You can use '{bot_name}' in this message to have it be formatted with the name of the bot

        Eg. 'Here is {bot_name}'s invite' => 'Here is [botname]'s invite'

        **Arguments**
            - `msg` The invite message for your bot.
        """
        await self.config.custom_message.set(msg)
        await ctx.send(f"Done. The invite message is now '{msg}'")
        self._settings_cache["custom_message"] = msg

    @invite_settings.command(name="support")
    async def invite_support(self, ctx: commands.Context, invite_code: InviteNoneConverter):
        """Set the support server invite for [botname]'s invite message

        Type `None` to set it to none

        **Arguments**
            - `invite_code` The discord invite to your support server. Type `None` to reset it.
        """
        msg = "Done. I have removed the support server invite from the invite message"
        if invite_code:
            msg = f"Done. The support server invite is now set to {invite_code.url()}"
        await ctx.send(msg)
        self._settings_cache["support_server"] = getattr(invite_code, "url", invite_code)

    @invite_settings.command(name="embed")
    async def invite_embed(self, ctx: commands.Context, toggle: bool):
        """Set whether the invite message should be embedded or not.

        **Arguments**
            - `toggle` Whether to enable or disable embeds.
        """
        enabled = "enabled" if toggle else "disabled"
        if toggle == self._settings_cache["embeds"]:
            return await ctx.send(f"Embeds are already {enabled}!")
        await ctx.send(f"Embeds are now {enabled}")
        self._settings_cache["embeds"] = toggle

    @invite_settings.command(name="private")
    async def invite_private(self, ctx: commands.Context, toggle: bool):
        """Toggle whether the invite should be sent in dms or in the channel it was invoked in

        **Arguments**
            - `toggle` Whether invite should be private or not
        """
        act = not toggle
        if self._settings_cache["send_in_channel"] == act:
            enabled = "" if toggle else "not "
            return await ctx.send(f"Invite is already {enabled}private.")
        enabled = "now" if toggle else "no longer"
        await ctx.send(f"Invite is {enabled} private")
        self._settings_cache["send_in_channel"] = act

    @commands.check(embed_check)
    @invite_settings.command(name="url")
    async def invite_url(self, ctx: commands.Context, url: NoneConverter):
        """Set the thumbnail url for the embed"""
        msg = f"The url is now {url}" if url else "Reset the url"
        await ctx.send(msg)
        self._settings_cache["custom_url"] = url
        await self.config.custom_url.set(url)
