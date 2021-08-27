# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import logging
from datetime import datetime
from typing import Optional

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


def embed_check(ctx):
    """Small fuction for command checks"""
    return ctx.cog._settings_cache["embeds"] is True


def can_invite():
    async def inner_spirit_animal(ctx: commands.Context):
        return await ctx.bot.get_cog("Core")._can_get_invite_url(ctx)

    return commands.check(inner_spirit_animal)


class AdvancedInvite(commands.Cog):
    """An "advanced" invite cog.

    This cog was requested by DSC#6238"""

    __authors__ = ["Jojo#7791"]
    __version__ = "2.0.2"

    def format_help_for_context(self, ctx: commands.Context):
        pre = super().format_help_for_context(ctx)
        plural = "s" if len(self.__authors__) > 1 else ""
        return (
            f"{pre}\n"
            f"Author{plural}: `{humanize_list(self.__authors__)}`\n"
            f"Version: `{self.__version__}`"
        )

    async def red_delete_data_for_user(self, **kwargs):
        return

    async def red_get_data_for_user(self, **kwargs):
        return {}

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, 544974305445019651, True)
        self.config.register_global(**_config_structure)
        self._settings_cache: dict
        self._invite_command: Optional[commands.Command]

    @classmethod
    async def init(cls, bot: Red):
        """Initialize the cog and the cache"""
        self = cls(bot)
        self._settings_cache = await self.config.all()
        self._invite_command = self.bot.remove_command("invite")
        return self

    def cog_unload(self):
        if self._invite_command:
            bot.remove_command("invite")
            bot.add_command(self._invite_command)
        self.task.cancel()

    async def maybe_reset_cooldown(self, ctx: commands.Context) -> discord.TextChannel:
        """I abstracted this into its own function just because I didn't want too bulky of a function"""
        channel = ctx.channel
        if not self._settings_cache["send_in_channel"]:
            ctx.command.reset_cooldown(ctx)  # Don't need to have it if it's in dms
            channel = ctx.author.dm_channel
            if not channel:
                await ctx.author.create_dm()
                channel = ctx.author.dm_channel
        elif await self.bot.is_owner(ctx.author):
            ctx.command.reset_cooldown(ctx)  # Owners can bypass it
        elif isinstance(channel, discord.DMChannel):
            # This time, we have to check explicitly if it's in a dm
            # And then reset the cooldown
            ctx.command.reset_cooldown(ctx)
        return channel

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
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def invite(self, ctx: commands.Context):
        """Invite [botname] to your server"""
        core = self.bot.get_cog(
            "Core"
        )  # NOTE This will only break if someone is dumb enough to eval or debug out Core
        channel = await self.maybe_reset_cooldown(ctx)
        url = await core._invite_url()  # type:ignore
        inv = f"Here is {ctx.me}'s invite url: {url}"
        support = self._settings_cache["support_server"]
        message = self._settings_cache["custom_message"].format(
            bot_name=self.bot.user.name
        )
        support_msg = (
            f"**Join the support server!**\n{support}\n" if support is not None else ""
        )
        kwargs = {"content": f"{message}\n{inv}\n{support_msg}{timestamp_format()}"}

        if (
            await self.bot.embed_requested(channel, ctx.author)
            and self._settings_cache["embeds"]
        ):
            title = self._settings_cache["title"].format(bot_name=self.bot.user.name)
            embed = discord.Embed(
                title=title,
                description=(
                    f"{message}\n" f"\nHere is **[{ctx.me.name}'s invite]({url})**"
                ),
                colour=await ctx.embed_colour(),
                timestamp=datetime.utcnow(),
            )
            if support is not None:
                embed.add_field(name="Join the support server!", value=support)

            if isinstance(ctx.channel, discord.DMChannel):
                member_converter = commands.MemberConverter()
                try:
                    member = await member_converter.convert(ctx, str(ctx.author.id))
                except commands.MemberNotFound:
                    member = False
            else:
                member = ctx.author

            if (
                member and member.mobile_status.value != "offline"
                and self._settings_cache["mobile_check"]
            ):
                embed.add_field(name="Here's a link if you're on mobile", value=url)
            url = self._settings_cache["custom_url"] or ctx.me.avatar_url
            embed.set_thumbnail(url=url)
            if footer := self._settings_cache["footer"]:
                embed.set_footer(text=footer)
            kwargs = {"embed": embed}

        try:
            await channel.send(**kwargs)
        except discord.Forbidden as e:
            if not self._settings_cache["send_in_channel"]:
                await ctx.send(
                    "I cannot send you DMs. Please enable them so I can DM you."
                )
            else:
                await ctx.send("Hm, something went wrong...")
                log.error("Error in command 'invite'", exc_info=e)

    @invite.group(name="settings")
    @commands.is_owner()
    async def invite_settings(self, ctx: commands.Context):
        """Settings for the invite command"""
        pass

    @invite_settings.command(name="url")
    async def invite_url(self, ctx: commands.Context, url: NoneConverter):
        """Set the invite url for the embed.

        \u200b
        **Arguments**
            - `url` Sets the url for the embed thumbnail. Defaults to the bot's avatar. Type `None` to reset the url
        """
        # type:ignore
        if url:
            if not url.endswith((".gif", ".png", ".jpg", ".jpeg")):
                return await ctx.send("That url did not end with a supported image type.")
            try:
                await ctx.trigger_typing()
                async with aiohttp.request("GET", url) as re:
                    if re.status != 200:
                        return await ctx.send("I could not access that url.")
            except aiohttp.InvalidURL:
                return await ctx.send("That was an invalid url.")
        await self.config.custom_url.set(url)
        self._settings_cache["custom_url"] = url
        await ctx.tick()

    @invite_settings.command(name="channel")
    async def invite_channel(self, ctx: commands.Context, toggle: bool):
        """Sets if the invite should be sent in the channel the command was invoked in.

        For example, if the toggle is true when a user types `[p]invite` it will send it in that channel

        **Arguments**
            - `toggle` If the message should be sent in channel it was invoked in or not
        """
        if toggle == self._settings_cache["send_in_channel"]:
            nt = "" if toggle else "doesn't "
            plural = "s" if toggle else ""
            return await ctx.send(
                f"Invite already {nt}send{plural} the message in the invoked channel."
            )
        await self.config.send_in_channel.set(toggle)
        self._settings_cache["send_in_channel"] = toggle
        await ctx.tick()

    @invite_settings.command(name="message")
    async def invite_message(self, ctx: commands.Context, *, msg: NoneConverter):
        """Set the message for invites.

        This will be before the invite url.

        **Arguments**
            - `msg` The custom message for the invite command. Type `None` to revert to the default 'Thanks for choosing [botname]'
            **NOTE** If you want to include the botname, add `{bot_name}`
        """
        if not msg and not self._settings_cache["custom_message"]:
            return await ctx.send(
                "The message is already set to default. If you would like to view the help for this command, "
                f"use `{ctx.clean_prefix}help invite message`"
            )
        msg = msg or _default_message  # type:ignore
        self._settings_cache["custom_message"] = msg
        await self.config.custom_message.set(msg)
        await ctx.tick()

    @invite_settings.command(name="embed")
    async def invite_embeds(self, ctx: commands.Context, toggle: bool):
        """Set whether the invite command should use embeds

        \u200b
        **Arguments**
            - `toggle` Whether the invite command should use embeds
        """
        if self._settings_cache["embeds"] == toggle:
            is_isnt = "" if toggle else "doesn't "
            plural = "s" if toggle else ""
            return await ctx.send(f"The invite already {is_isnt}use{plural} embeds")
        self._settings_cache["embeds"] = toggle
        await ctx.tick()

    @invite_settings.command(name="footer")
    @commands.check(embed_check)
    async def invite_footer(
        self, ctx: commands.Context, *, footer: NoneConverter(strict=True)  # type:ignore
    ):
        """Set the invite footer (note, this will only work if embeds are enabled. This might change later)

        \u200b
        **Arguments**
            - `footer` The footer for the embed. Type `None` to reset it.
        """
        self._settings_cache["footer"] = footer
        await self.config.footer.set(footer)
        await ctx.tick()

    @invite_settings.command(name="title")
    @commands.check(embed_check)
    async def invite_title(
        self, ctx: commands.Context, *, title: NoneConverter(strict=True)  # type:ignore
    ):
        r"""Set the title for the embed

        **Arguments**
            - `title` The title of the embed. Type `None` to reset it
        """
        self._settings_cache["title"] = title
        await self.config.title.set(title)
        await ctx.tick()

    @invite_settings.command(name="support")
    async def invite_support(self, ctx: commands.Context, invite: InviteNoneConverter):
        """Set the support server for your bot.

        Type `None` to remove it

        **Arguments**
            - `invite` The invite for your support server. Type `None` to remove it
        """
        if invite is None and self._settings_cache["support_server"] is None:
            return await ctx.send("The support server is already disabled")
        elif invite is not None and invite.url == self._settings_cache["support_server"]:
            return await ctx.send(
                f"The invite link for your support server is already `{discord.utils.escape_markdown(invite.url)}`"
            )

        if invite is None:
            self._settings_cache["support_server"] = None
            await self.config.support_server.set(None)
            msg = "Removed the support server invite"
        else:
            self._settings_cache["support_server"] = url = invite.url
            await self.config.support_server.set(url)
            msg = (
                f"The support server invite is now `{discord.utils.escape_markdown(url)}`"
            )
        await ctx.send(msg)

    @invite_settings.command(name="mobilecheck")
    async def invite_check_mobile(self, ctx: commands.Context, check: bool):
        """Determines if the bot should check if the user is on mobile when running the invite command

        **Arguments**
            - `check` Whether to check mobile status or not
        """
        enabled = "enabled" if check else "disabled"
        if self._settings_cache["mobile_check"] == check:
            return await ctx.send(f"Mobile checking is already {enabled}")
        self._settings_cache["mobile_check"] = check
        await self.config.mobile_check.set(check)
        await ctx.send(f"Mobile checking is now {enabled}")
