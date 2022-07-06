# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import asyncio
import datetime
import logging
from typing import Any, Dict, Final, List, Optional, Tuple, TypeVar

import aiohttp
import discord
from redbot import VersionInfo, version_info
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.core_commands import CoreLogic
from redbot.core.utils.chat_formatting import humanize_list, humanize_number

from .utils import *

log = logging.getLogger("red.JojoCogs.advanced_invite")


class NoneStrict(NoneConverter):
    strict = True


async def can_invite(ctx: commands.Context) -> bool:
    return await CoreLogic._can_get_invite_url(ctx)


_config_structure: Final[Dict[str, Any]] = {
    "custom_url": None,
    "image_url": None,
    "custom_message": "Thanks for choosing {bot_name}!",
    "send_in_channel": False,
    "embeds": True,
    "title": "Invite {bot_name}",
    "support_server": None,
    "footer": None,
    "extra_link": False,
    "support_server_emoji": {},
    "invite_emoji": {},
}


class AdvancedInvite(commands.Cog):
    """An advanced invite for [botname]

    To configure the invite command, check out `[p]invite set`.
    """

    __authors__: Final[List[str]] = ["Jojo#7791"]
    __version__: Final[str] = "3.0.10"

    def __init__(self, bot: Red):
        self.bot = bot
        self._invite_command: Optional[commands.Command] = self.bot.remove_command("invite")
        self.config = Config.get_conf(self, 544974305445019651, True)
        self.config.register_global(**_config_structure)
        self._supported_images: Tuple[str, ...] = ("jpg", "jpeg", "png", "gif")

    def cog_unload(self) -> None:
        self.bot.remove_command("invite"), self.bot.add_command(  # type:ignore
            self._invite_command
        ) if self._invite_command else None

    @staticmethod
    def _humanize_list(data: List[str]) -> str:
        return humanize_list([f"`{i}`" for i in data])

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
    async def invite(self, ctx: commands.Context, send_in_channel: Optional[bool] = False):
        """Invite [botname] to your server!"""

        check = send_in_channel and await self.bot.is_owner(ctx.author)
        channel = await self._get_channel(ctx) if not check else ctx.channel
        settings = await self.config.all()
        title = settings.get("title", _config_structure["title"]).replace(
            "{bot_name}", ctx.me.name
        )
        message = settings.get("custom_message", _config_structure["custom_message"]).replace(
            "{bot_name}", ctx.me.name
        )
        url = await self._invite_url()
        time = datetime.datetime.now(tz=datetime.timezone.utc)
        footer = settings.get("footer")
        if footer:
            footer = (
                footer.replace("{bot_name}", ctx.me.name)
                .replace("{guild_count}", humanize_number(len(ctx.bot.guilds)))
                .replace("{user_count}", humanize_number(len(self.bot.users)))
            )
        timestamp = f"<t:{int(time.timestamp())}>"
        support = settings.get("support_server")

        support_msg = f"\nJoin the support server! <{support}>\n" if support is not None else ""
        kwargs: Dict[str, Any] = {
            "content": f"**{title}**\n{message}\n<{url}>{support_msg}\n\n{footer}\n{timestamp}"
        }
        support_server_emoji, invite_emoji = [
            Emoji.from_data(settings.get(x)) for x in ["support_server_emoji", "invite_emoji"]
        ]
        if await self._embed_requested(ctx, channel):
            message = (
                f"{message}\n{url}" if await self.config.extra_link() else f"[{message}]({url})"
            )
            embed = discord.Embed(
                title=title,
                description=message,
                colour=await ctx.embed_colour(),
                timestamp=time,
            )
            if support is not None:
                embed.add_field(name="Join the support server", value=support)
            if curl := settings.get("custom_url"):
                embed.set_thumbnail(url=curl)
            if iurl := settings.get("image_url"):
                embed.set_image(url=iurl)
            if footer:
                embed.set_footer(text=footer)
            kwargs = {"embed": embed}
        kwargs["channel"] = channel
        kwargs["url"] = url
        buttons = [Button(f"Invite {ctx.me.name}!", url, invite_emoji)]
        if support is not None:
            buttons.append(
                Button("Join the support server!", url=support, emoji=support_server_emoji)
            )
        kwargs["components"] = [Component(buttons)]
        try:
            await send_button(ctx, **kwargs)
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
        await self.config.embeds.set(toggle)

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
        elif len(message) > 1500:
            return await ctx.send("The message's length cannot be more than 1500 characters.")
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
        """Set the footer for the invite command

        **Variables**
            - `{bot_name}` Displays [botname] in the footer
            - `{guild_count}` Displays in how many guilds is the bot in
            - `{user_count}` Displays how many users in total

        **Arguments**
            - `footer` The footer for the invite command.
        """

        if not footer:
            await self.config.footer.set(None)
            return await ctx.send("The footer has been reset.")
        if len(footer) > 100:
            return await ctx.send("The footer's length cannot be over 100 characters long.")
        await self.config.footer.set(footer)
        await ctx.send("The footer has been set.")

    @invite_settings.command(name="public")
    async def invite_send_in_channel(self, ctx: commands.Context, toggle: bool):
        """Set whether the invite command should send in the channel it was invoked in

        **Arguments**
            - `toggle` Whether or not the invite command should be sent in the channel it was used in.
        """
        await self.config.send_in_channel.set(toggle)
        now_no_longer = "now" if toggle else "no longer"
        await ctx.send(
            f"The invite command will {now_no_longer} send the message in the channel it was invoked in"
        )

    @invite_settings.command(name="supportserveremoji", aliases=["ssemoji"])
    async def support_server_emoji(self, ctx: commands.Context, emoji: EmojiConverter):
        """Set the emoji for the support server invite button.

        Type "None" to remove it.

        **Arguments**
            - `emoji` The emoji for the support server button. Type "none" to remove it.
        """
        if not emoji:
            await self.config.support_server_emoji.clear()
            return await ctx.send("I have reset the support server emoji.")
        await self.config.support_server_emoji.set(emoji.to_dict())
        await ctx.send(f"Set the support server emoji to {emoji.as_emoji()}")

    @invite_settings.command(name="inviteemoji", aliases=["iemoji"])
    async def invite_emoji(self, ctx: commands.Context, emoji: EmojiConverter):
        """Set the emoji for the invite button.

        Type "None" to remove it.

        **Arguments**
            - `emoji` The emoji for the invite button. Type "none" to remove it.
        """
        if not emoji:
            await self.config.invite_emoji.clear()
            return await ctx.send("I have reset the invite emoji.")
        await self.config.invite_emoji.set(emoji.to_dict())
        await ctx.send(f"Set the invite emoji to {emoji.as_emoji()}")

    @invite_settings.command(name="thumbnailurl")
    async def invite_custom_url(self, ctx: commands.Context, url: str = None):
        """Set the thumbnail url for the invite command's embed.

        This setting only applies for embeds.

        **Arguments**
            - `url` The thumbnail url for embed command. This can also be a file (upload the image when you run the command)
            Type `none` to reset the url.
        """
        if len(ctx.message.attachments) > 0:
            if not (attach := ctx.message.attachments[0]).filename.endswith(
                self._supported_images
            ):
                return await ctx.send("That image is invalid.")
            url = attach.url
        elif url is not None:
            if url.lower == "none":
                await self.config.custom_url.clear()
                return await ctx.send("I have reset the image url.")
            if url.startswith("<") and url.endswith(">"):
                url = url[1:-1]
            if not url.endswith(self._supported_images):
                return await ctx.send(
                    f"That url does not point to a proper image type, ({', '.join(self._supported_images)})"
                )
            async with ctx.typing():
                try:
                    async with aiohttp.request("GET", url) as re:
                        await re.read()
                except aiohttp.InvalidURL:
                    return await ctx.send("That is not a valid url.")
                except aiohttp.ClientError:
                    return await ctx.send("Something went wrong while trying to get the image.")
        else:
            return await ctx.send_help()
        await self.config.custom_url.set(url)
        await ctx.send("Done. I have set the thumbnail url.")

    @invite_settings.command(name="imageurl", usage="<url or image>")
    async def invite_image_url(self, ctx: commands.Context, url: str = None):
        """Set the image url for the invite command.

        This setting only applies for embeds.

        **Arguments**
            - `url` The url for the embed's image. Type `none` to clear it.
            You can also upload an image instead of providing this argument
        """
        if len(ctx.message.attachments) > 0:
            # Attachments take priority
            if not (attach := ctx.message.attachments[0]).filename.endswith(
                self._supported_images
            ):
                return await ctx.send("That image is invalid.")
            url = attach.url
        elif url is not None:
            if url == "none":
                await self.config.image_url.clear()
                return await ctx.send("Reset the image url.")
            async with ctx.typing():
                try:
                    async with aiohttp.request("GET", url) as re:
                        await re.read()
                except aiohttp.InvalidURL:
                    return await ctx.send("That url is invalid.")
                except aiohttp.ClientError:
                    return await ctx.send("Something went wrong when trying to validate that url.")
        else:
            # as much as I hate else blocks this is hard to bypass
            return await ctx.send_help()
        await self.config.image_url.set(url)
        await ctx.send("Done. I have set the image url.")

    @invite_settings.command(name="extralink")
    async def invite_extra_links(self, ctx: commands.Context, toggle: bool):
        """Toggle whether the invite command's embed should have extra links showing the invite url

        **Arguments**
            - `toggle` Whether the invite command's embed should have extra links.
        """
        await self.config.extra_link.set(toggle)
        now_no_longer = "now" if toggle else "no longer"
        await ctx.send(f"Extra links are {now_no_longer} enabled.")

    @invite_settings.command(name="showsettings")
    async def invite_show_settings(self, ctx: commands.Context):
        """Show the settings for the invite command"""
        _data: dict = {}
        settings = await self.config.all()
        for key, value in settings.items():
            if key == "mobile_check":
                continue
            key = key.replace("_", " ").replace("custom ", "")
            key = " ".join(x.capitalize() for x in key.split())
            if key.lower() == "url":
                key = "Embed Thumbnail Url"
            _data[key] = value
        msg = "**Invite settings**\n\n" + "\n".join(
            f"**{key}:** {value}" for key, value in _data.items()
        )
        kwargs: Dict[str, Union[str, discord.Embed]] = {"content": msg}
        if await ctx.embed_requested():
            embed = discord.Embed(
                title="Invite settings",
                colour=await ctx.embed_colour(),
                timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
            )
            [embed.add_field(name=key, value=value, inline=False) for key, value in _data.items()]
            kwargs = {"embed": embed}
        await ctx.send(**kwargs)

    async def _get_channel(self, ctx: commands.Context) -> discord.TextChannel:
        if await self.config.send_in_channel():
            return ctx.channel

        if ret := ctx.author.dm_channel:
            return ret
        return await ctx.author.create_dm()

    async def _embed_requested(self, ctx: commands.Context, channel: discord.TextChannel) -> bool:
        if not await self.config.embeds():
            return False
        if isinstance(channel, discord.DMChannel):
            return True
        return channel.permissions_for(ctx.me).embed_links

    async def _invite_url(self) -> str:
        if not version_info.dev_release and version_info >= VersionInfo.from_str("3.4.16"):
            return await self.bot.get_invite_url()
        # This is all for backwards compatibility
        # Even if a method for this gets added it would be redundant considering
        # `bot.get_invite_url` exists in the latest red versions
        app_info = await self.bot.application_info()
        data = await self.bot._config.all()
        commands_scope = data["invite_commands_scope"]
        scopes = ("bot", "applications.commands") if commands_scope else None
        perms_int = data["invite_perm"]
        permissions = discord.Permissions(perms_int)
        return discord.utils.oauth_url(app_info.id, permissions, scopes=scopes)
