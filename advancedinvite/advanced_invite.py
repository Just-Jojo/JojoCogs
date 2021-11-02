# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import asyncio
import logging
from datetime import datetime
from typing import Any, Optional, TypeVar

import aiohttp
import discord
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.core_commands import CoreLogic
from redbot.core.utils.chat_formatting import humanize_list

from .utils import *

log = logging.getLogger("red.JojoCogs.advanced_invite")


class NoneStrict(NoneConverter):
    strict = True


async def can_invite(ctx: commands.Context) -> bool:
    return await CoreLogic._can_get_invite_url(ctx)


_config_structure = {
    "custom_url": None,
    "custom_message": "Thanks for choosing {bot_name}!",
    "send_in_channel": False,
    "embeds": True,
    "title": "Invite {bot_name}",
    "support_server": None,
    "footer": None
}


class AdvancedInvite(commands.Cog):
    """An advanced invite for [botname]"""

    __authors__ = ["Jojo#7791"]
    __version__ = "3.0.2"

    def __init__(self, bot: Red):
        self.bot = bot
        self._invite_command: Optional[commands.Command] = self.bot.remove_command(
            "invite"
        )
        self.config = Config.get_conf(self, 544974305445019651, True)
        self.config.register_global(**_config_structure)

    def cog_unload(self):
        if self._invite_command:
            self.bot.remove_command("invite")
            self.bot.add_command(self._invite_command)

    @staticmethod
    def _humanize_list(data: list) -> list:
        return humanize_list([f"`{i}`" for i in data])  # type:ignore

    def format_help_for_context(self, ctx: commands.Context) -> str:
        plural = "" if len(self.__authors__) == 1 else "s"
        return (
            f"{super().format_help_for_context(ctx)}\n"
            f"**Author{plural}:** {self._humanize_list(self.__authors__)}\n"
            f"**Version:** `{self.__version__}`"
        )

    async def red_delete_data_for_user(self, *args, **kwargs) -> None:
        """Nothing to delete"""
        return

    @commands.command()
    async def inviteversion(self, ctx: commands.Context):
        """Get the version of Advanced Invite"""
        msg = (
            "**Advanced Invite**\n"
            f"Version: `{self.__version__}`\n\n"
            '"This cog was created for a friend of mine, and as such is close to my heart.\n'
            'Thanks for being awesome and using my stuff!" - Jojo (the author of this cog)\n\n'
            "Created with ❤"
        )
        await ctx.maybe_send_embed(msg)

    @commands.group(name="invite", usage="", invoke_without_command=True)
    @commands.check(can_invite)
    async def invite(
        self, ctx: commands.Context, send_in_channel: Optional[bool] = False
    ):
        """Invite [botname] to your server!"""

        check = send_in_channel and await self.bot.is_owner(ctx.author)
        channel = await self._get_channel(ctx) if not check else ctx.channel
        settings = await self.config.all()
        title = settings.get(
            "title", _config_structure["title"]
        ).replace("{bot_name}", ctx.me.name)
        message = settings.get(
            "custom_message", _config_structure["custom_message"]
        ).replace("{bot_name}", ctx.me.name)
        url = await CoreLogic._invite_url(self)
        timestamp = f"<t:{int(datetime.utcnow().timestamp())}>"
        footer = ret if (ret := settings.get("footer")) else ""
        support = settings.get("support_server")

        support_msg = (
            f"\nJoin the support server! <{support}>\n" if support is not None else ""
        )
        kwargs = {"content": f"**{title}**\n{message}{support}\n{url}\n{timestamp}"}
        if await self._embed_requested(ctx, channel):
            embed = discord.Embed(
                title=title,
                description=f"{message}\n\n{url}",
                colour=await ctx.embed_colour(),
                timestamp=datetime.utcnow(),
            )
            if support is not None:
                embed.add_field(name="Join the support server", value=support)
            if curl := settings.get("custom_url"):
                embed.set_thumbnail(url=curl)
            kwargs = {"embed": embed}
        try:
            await channel.send(**kwargs)
        except discord.HTTPException:
            await ctx.send("I could not dm you!")

    @invite.group(name="settings", aliases=("set",))
    @commands.is_owner()
    async def invite_settings(self, ctx: commands.Context):
        """Manage the settings for the invite command.

        You can set the title, message, support server invite.

        If you have embeds enabled you can also set the thumbnail url, and the footer.
        """
        pass

    @invite_settings.command(name="support")
    async def invite_support(self, ctx: commands.Context, invite: InviteNoneConverter):
        """Set the support server invite.

        Type `None` to reset it

        **Arguments**
            - `invite` The invite url for your support server. Type `None` to remove it.
        """
        invite = getattr(invite, "url", invite)
        set_reset = f"set as <{invite}>." if invite else "reset."
        await ctx.send(f"The support server has been {set_reset}")
        await self.config.support_server.set(invite)

    @invite_settings.command(name="embed")
    async def invite_embed(self, ctx: commands.Context, toggle: bool):
        """Set whether the invite command should use embeds.

        **Arguments**
            - `toggle` Whether the invite command should be embedded or not.
        """
        toggled = "enabled" if toggle else "disabled"
        await ctx.send(f"Embeds are now {toggled} for the invite command.")
        await self.config.embeds.set(toggled)

    @invite_settings.command(name="message")
    async def invite_message(self, ctx: commands.Context, *, message: NoneStrict):
        """Set the message for the invite command.

        Type `None` to reset it.
        You can use `{bot_name}` in your message to display [botname] in the message.

        **Arguments**
            - `message` The message for the invite command. Type `None` to reset it.
        """
        reset = False
        if message is None:
            reset = True
            message = _config_structure["custom_message"]
        set_reset = "reset" if reset else "set"

        await ctx.send(f"The message has been {set_reset}.")
        await self.config.custom_message.set(message)

    @invite_settings.command(name="title")
    async def invite_title(self, ctx: commands.Context, *, title: NoneStrict):
        """Set the title for the invite command.

        Type `None` to reset it.
        You can use `{bot_name}` to display [botname] in the title.

        **Arguments**
            - `title` The title for the invite command. Type `None` to reset it.
        """
        reset = False
        if title is None:
            reset = True
            title = _config_structure["title"]
        set_reset = "reset" if reset else "set"

        await ctx.send(f"The title has been {set_reset}")
        await self.config.title.set(title)

    @invite_settings.command(name="footer")
    async def invite_footer(self, ctx: commands.Context, *, footer: NoneConverter):
        """Set the footer for the invite command"""

        if not footer:
            await self.config.footer.set(None)
            return await ctx.send("The footer has been reset.")
        if len(footer) > 500:
            return await ctx.send("The footer's length cannot be over 500 characters long.")
        await self.config.footer.set(footer)
        await ctx.send("The footer has been set.")

    @invite_settings.command(name="showsettings")
    async def invite_show_settings(self, ctx: commands.Context):
        """Show the settings for the invite command"""
        _data: dict = {}
        settings = await self.config.all()
        for key, value in settings.items():
            if key in ("mobile_check", "footer"):
                continue
            key = key.replace("_", " ").replace("custom ", "")
            key = " ".join(x.capitalize() for x in key.split())
            _data[key] = value
        msg = "**Invite settings**\n\n" "\n".join(
            f"**{key}:** {value}" for key, value in _data.items()
        )
        kwargs = {"content": msg}
        if await ctx.embed_requested():
            embed = discord.Embed(
                title="Invite settings",
                colour=await ctx.embed_colour(),
                timestamp=datetime.utcnow(),
            )
            [
                embed.add_field(name=key, value=value, inline=False)
                for key, value in _data.items()
            ]
            kwargs = {"embed": embed}
        await ctx.send(**kwargs)

    async def _get_channel(self, ctx: commands.Context) -> discord.TextChannel:
        if await self.config.send_in_channel():
            return ctx.channel

        if ret := ctx.author.dm_channel:
            return ret
        return await ctx.author.create_dm()

    async def _embed_requested(
        self, ctx: commands.Context, channel: discord.TextChannel
    ) -> bool:
        if not await self.config.embeds():
            return False
        if isinstance(channel, discord.DMChannel):
            return True
        return channel.permissions_for(ctx.me).embed_links
