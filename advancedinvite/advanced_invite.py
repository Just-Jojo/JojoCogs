# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import asyncio
import datetime
import logging
from typing import Any, Dict, Final, List, Optional, Union, Tuple, TypeVar, TYPE_CHECKING

import aiohttp
import discord
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_list, humanize_number

from .utils import *

log = logging.getLogger("red.JojoCogs.advanced_invite")


if TYPE_CHECKING:
    NoneStrict = NoneConverter
else:
    class NoneStrict(NoneConverter):
        strict = True


async def can_invite(ctx: commands.Context) -> bool:
    return await ctx.bot.is_owner(ctx.author) or await ctx.bot.is_invite_url_public()


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
    __version__: Final[str] = "4.0.0"

    def __init__(self, bot: Red):
        self.bot = bot
        self._invite_command: Optional[commands.Command] = self.bot.remove_command("invite")
        self.config = Config.get_conf(self, 544974305445019651, True)
        self.config.register_global(**_config_structure)
        self._supported_images: Tuple[str, ...] = ("jpg", "jpeg", "png", "gif")

    async def cog_unload(self) -> None:
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

    @commands.command(hidden=True)
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

        if TYPE_CHECKING:
            channel: discord.TextChannel
        else:
            channel = (
                await self._get_channel(ctx)
                if not send_in_channel and await self.bot.is_owner(ctx.author)
                else ctx.channel
            )
        settings = await self.config.all()
        title, message = self._get_items(settings, ["title", "custom_message"], ctx)
        url = await self.bot.get_invite_url()
        time = datetime.datetime.now(tz=datetime.timezone.utc)
        support_msg = (
            f"Join the support server <{support}>\n"
            if (support := settings.get("support_server")) else ""
        )
        invite_emoji, support_emoji = (
            Emoji.from_data(settings.get(x)) for x in ("invite_emoji", "support_emoji")
        )
        footer = settings.get("footer")
        if footer:
            footer = footer.replace("{bot_name}", ctx.me.name).replace(
                "{guild_count}", humanize_number(len(ctx.bot.guilds))
            ).replace(
                "{user_count}",
                humanize_number(len(self.bot.users))
            )
        kwargs: Dict[str, Any] = {
            "content": (
                f"**{title}**\n\n{message}\n<{url}>\n{support_msg}\n\n{footer}"
            ),
        }
        if await self._embed_requested(ctx, channel):
            message = f"{message}\n{url}" if settings.get("extra_link") else f"[{message}]({url})"
            embed = discord.Embed(
                title=title,
                description=message,
                colour=await ctx.embed_colour(),
                timestamp=time,
            )
            if support:
                embed.add_field(name="Join the support server", value=support)
            if curl := settings.get("custom_url"):
                embed.set_thumbnail(url=curl)
            if iurl := settings.get("image_url"):
                embed.set_image(url=iurl)
            if footer:
                embed.set_footer(text=footer)
            kwargs = {"embed": embed}
        view = discord.ui.View()
        view.add_item(self._make_button(url, f"Invite {ctx.me.name}", invite_emoji))
        if support:
            view.add_item(self._make_button(support, "Join the support server", support_emoji))
        kwargs["view"] = view
        try:
            await channel.send(**kwargs)
        except discord.Forbidden: # Couldn't dm
            if channel == ctx.author.dm_channel:
                return await ctx.send("I could not dm you!")
            await ctx.send(
                "I'm sorry, something went wrong when trying to send the invite."
                "Please let my owner know if this problem continues."
            )
        except discord.HTTPException:
            await ctx.send(
                "I'm sorry, something went wrong when trying to send the invite."
                "Please let my owner know if this problem continues."
            )

    @staticmethod
    def _make_button(url: str, label: str, emoji: Optional[Emoji]) -> discord.ui.Button:
        emoji_data = emoji.as_emoji() if emoji else None
        return discord.ui.Button(style=discord.ButtonStyle.url, label=label, url=url, emoji=emoji_data)

    @staticmethod
    def _get_items(settings: dict, keys: List[str], ctx: commands.Context) -> list:
        return [
            settings.get(key, _config_structure[key]).replace(
                "{bot_name}", ctx.me.name,
            ) for key in keys
        ]

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
        """Set the thumbnail url for the invite command's embed

        This setting only applies for embeds.

        **Arguments**
            - `url` The thumbnail url for embed command. This can also be a file (upload the image when you run the command)
            Type `none` to reset the url.
        """
        if len(ctx.message.attachments) == 0 and url is None:
            return await ctx.send_help()

        if len(ctx.message.attachments) > 0:
            if not (attach := ctx.message.attachments[0]).filename.endswith(
                self._supported_images
            ):
                return await ctx.send("That image is invalid.")
            url = attach.url
        elif url is not None:
            if url.lower == "none":
                await self.config.custom_url.clear()
                return await ctx.send("I have reset the thumbnail url.")
            if url.startswith("<") and url.endswith(">"):
                url = url[1:-1]
            if not url.endswith(self._supported_images):
                return await ctx.send(
                    f"That url does not point to a proper image type, ({', '.join(self._supported_images)})"
                )
            async with ctx.typing():
                async with aiohttp.ClientSession() as sess:
                    try:
                        async with sess.get(url) as re:
                            await re.read()
                    except aiohttp.InvalidURL:
                        return await ctx.send("That is not a valid url.")
                    except aiohttp.ClientError:
                        return await ctx.send(
                            "Something went wrong while trying to get the image."
                        )
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
        kwargs: dict = {"content": msg}
        if await ctx.embed_requested():
            embed = discord.Embed(
                title="Invite settings",
                colour=await ctx.embed_colour(),
                timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
            )
            [embed.add_field(name=key, value=value, inline=False) for key, value in _data.items()]
            kwargs = {"embed": embed}
        await ctx.send(**kwargs)

    async def _get_channel(self, ctx: commands.Context) -> Union[discord.TextChannel, discord.DMChannel]:
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
