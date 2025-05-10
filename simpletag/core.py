# Copyright (c) 2025 - Amy (jojo7791)
# Licensed under MIT

from __future__ import annotations

import contextlib
import datetime
import logging
from typing import TYPE_CHECKING, Dict, List, Final, Literal, Optional, Tuple, Union, overload

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.commands import GuildContext
from redbot.core.config import Value
from redbot.core.utils.menus import SimpleMenu
from redbot.core.utils.chat_formatting import pagify

__all__: Final[Tuple[str]] = ("SimpleTag",)

__author__: Final[str] = "Amy (jojo7791)"
__version__: Final[str] = "1.0.0"

log: logging.Logger = logging.getLogger("redbot.jojocogs.simpletags")
bad_cog_names: Final[Tuple[str, ...]] = ("customcom", "CustomCommands", "customcommands")
Requester = Literal["discord_deleted_user", "owner", "user", "user_strict"]


class Confirm(discord.ui.View):
    confirmed: bool = False

    def __init__(self):
        super().__init__(timeout=100.0)

    @discord.ui.button(style=discord.ButtonStyle.green, emoji="\N{WHITE HEAVY CHECK MARK}")
    async def confirm(self, inter: discord.Interaction, button: discord.ui.Button) -> None:
        await inter.response.defer()
        self.confirmed = True
        self.stop()

    @discord.ui.button(
        style=discord.ButtonStyle.red, emoji="\N{HEAVY MULTIPLICATION X}\N{VARIATION SELECTOR-16}"
    )
    async def deny(self, inter: discord.Interaction, button: discord.ui.Button) -> None:
        await inter.response.defer()
        self.stop()


def _get_author(
    author_id: int,
    guild: Optional[discord.Guild] = None,
    owners: Optional[Dict[int, discord.User]] = None,
    global_tag: bool = True,
) -> Optional[Union[discord.User, discord.Member]]:
    maybe_author: Optional[Union[discord.User, discord.Member]]
    if global_tag:
        if TYPE_CHECKING:
            assert isinstance(owners, dict)
        maybe_author = owners.get(author_id)
    else:
        if TYPE_CHECKING:
            assert guild is not None
        maybe_author = guild.get_member(author_id)
    return maybe_author


async def _handle_confirm(ctx: commands.Context) -> bool:
    view = Confirm()
    msg = await ctx.send("Do you want to delete all of your tags?", view=view)
    await view.wait()
    confirm = view.confirmed
    if not view.confirmed:
        await ctx.send("Okay, I won't delete your tags")
    with contextlib.suppress(discord.Forbidden):
        await msg.delete()
    return confirm


@overload
def _get_timestamp() -> int: ...


@overload
def _get_timestamp(dt: bool = True) -> datetime.datetime: ...


def _get_timestamp(dt: bool = False) -> Union[int, datetime.datetime]:
    ret = datetime.datetime.now(datetime.timezone.utc)
    if dt:
        return ret
    return int(ret.timestamp())


async def _del_helper(coro: Value, user_id: int) -> None:
    async with coro() as tags:
        to_remove = []
        for tag_name, tag_info in tags.items():
            if tag_info.get(user_id) == user_id:
                to_remove.append(tag_name)
        for tag_name in to_remove:
            del tags[tag_name]


class SimpleTag(commands.Cog):
    """A simple tag system that acts like R.Danny's tags"""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, 544974305445019651, force_registration=True)
        # {
        #   global_tag: {content: str tag_content, author: int id,
        #   created_at: int timestamp, last_edit: int | None}
        # }
        self.config.register_guild(tags={})
        # {
        #   guild_tag: {
        #       author: author_id, content: str tag_content,
        #       created_at: int timestamp, last_edit: int | None
        #   }
        # }
        self.config.register_global(tags={})
        self._owners: Dict[int, discord.User] = {}

    async def cog_load(self) -> None:
        for o_id in self.bot.owner_ids:  # type:ignore
            user = self.bot.get_user(o_id)
            if user is None:
                continue
            self._owners[o_id] = user

    def format_help_for_context(self, ctx: commands.Context) -> str:
        return (
            f"{super().format_help_for_context(ctx)}\n\n"
            f"**Author:** {__author__}\n"
            f"**Version:** {__version__}"
        )

    async def red_delete_data_for_user(self, *, requester: Requester, user_id: int) -> None:
        await _del_helper(self.config.tags, user_id)
        for guild in await self.config.all_guilds():
            await _del_helper(self.config.guild_from_id(guild), user_id)

    @commands.group(name="tag")
    async def tag(self, ctx: commands.Context) -> None:
        """Create simple tags"""
        pass

    @tag.group(name="global", invoke_without_command=True)
    async def tag_global(self, ctx: commands.Context, tag_name: str) -> None:
        """Send a tag that the owner of [botname] created"""
        tags = await self.config.tags()
        if tag_name not in tags:
            await ctx.send_help()
            return
        tag = tags[tag_name]["content"]
        await ctx.send(tag)

    @tag_global.command(name="add", aliases=["create"])
    @commands.is_owner()
    async def tag_global_create(self, ctx: commands.Context, tag_name: str, *, tag: str) -> None:
        """Create a tag

        There are no context variables or things that will change, it will just be
        sent as plain text
        """
        async with self.config.tags() as tags:
            if tag_name in tags:
                await ctx.send(f"A tag by the name `{tag_name}` already exists!")
                return
            tags[tag_name] = {
                "content": tag,
                "timestamp": _get_timestamp(),
                "last_edit": None,
                "author": ctx.author.id,
            }
        await ctx.send(f"Created a tag with the name `{tag_name}`")

    @tag_global.command(name="information", aliases=["info"])
    async def tag_global_information(self, ctx: commands.Context, tag_name: str) -> None:
        """Get information on a tag"""
        tags = await self.config.tags()
        if tag_name not in tags:
            await ctx.send("That tag doesn't exist!")
            return
        tag_info = tags[tag_name]
        await self.send_tag_info(ctx, tag_name, tag_info)

    @tag_global.command(name="edit")
    @commands.is_owner()
    async def tag_global_edit(self, ctx: commands.Context, tag_name: str, *, new_tag: str) -> None:
        """Edit a tag"""
        async with self.config.tags() as tags:
            if tag_name not in tags:
                await ctx.invoke(self.tag_global_create, tag_name=tag_name, tag=new_tag)
                return
            tags[tag_name].update({"content": new_tag, "last_edit": _get_timestamp()})
        await ctx.send(f"Edited the tag `{tag_name}`")

    @tag_global.command(name="delete", aliases=("del", "remove", "rm"))
    @commands.is_owner()
    async def tag_global_delete(self, ctx: commands.Context, tag_name: str) -> None:
        """Delete a tag"""
        async with self.config.tags() as tags:
            if tag_name not in tags:
                await ctx.send("That tag doesn't exist!")
                return
            del tags[tag_name]
        await ctx.send("Deleted that tag")

    @tag_global.command(name="deleteall", aliases=("delall", "removeall", "rmall"))
    @commands.is_owner()
    async def tag_global_delete_all(self, ctx: commands.Context, confirm: bool = False) -> None:
        """"""
        if not confirm and not await _handle_confirm(ctx):
            return
        await self.config.tags.clear()
        await ctx.send("I have deleted all of the global tags")

    @tag_global.command(name="list")
    async def tag_global_list(self, ctx: commands.Context) -> None:
        """List all of the tags [botname] has"""
        tags = await self.config.tags()
        if not tags:
            await ctx.send(f"{ctx.me.name} has no tags")
            return
        await self.list_tags(ctx, tags)

    @tag.group(name="guild", aliases=("local",), invoke_without_command=True)
    @commands.guild_only()
    async def tag_guild(self, ctx: GuildContext, tag_name: str) -> None:
        """Send a tag that was created in this guild"""
        async with self.config.guild(ctx.guild).tags() as tags:
            maybe_tag = tags.get(tag_name)
            if not maybe_tag:
                await ctx.send_help()
                return
            tag_info = maybe_tag["content"]
        await ctx.send(tag_info)

    @tag_guild.command(name="create", aliases=("add", "upload"))
    async def tag_guild_create(
        self, ctx: GuildContext, tag_name: str, *, tag_content: str
    ) -> None:
        """Create a tag in this guild"""
        async with self.config.guild(ctx.guild).tags() as tags:
            if tag_name in tags:
                await ctx.send("That's already a tag")
                return
            tags[tag_name] = {
                "author": ctx.author.id,
                "content": tag_content,
                "timestamp": _get_timestamp(),
                "last_edit": None,
            }
        await ctx.send(f"Created a tag with the name `{tag_name}`")

    @tag_guild.command(name="edit")
    async def tag_guild_edit(self, ctx: GuildContext, tag_name: str, *, new_tag: str) -> None:
        """Edit a tag in this guild. You must be the author to edit it"""
        is_mod = await self.bot.is_mod(ctx.author)
        async with self.config.guild(ctx.guild).tags() as tags:
            tag_info = tags.get(tag_name)
            if not tag_info:
                await ctx.send("I could not find a tag with that name")
                return
            author_id = tag_info["author"]
            if not is_mod and author_id != ctx.author.id:
                await ctx.send("You are not the author of that tag")
                return
            tag_info["content"] = new_tag
            tag_info["last_edit"] = _get_timestamp()
        await ctx.send(f"Edited the tag `{tag_name}`")

    @tag_guild.command(name="list")
    async def tag_guild_list(self, ctx: GuildContext) -> None:
        """List the tags in this guild"""
        tags = await self.config.guild(ctx.guild).tags()
        if not tags:
            await ctx.send("There are no tags in this guild")
            return
        await self.list_tags(ctx, tags)

    @tag_guild.command(name="delete", aliases=("remove", "rm", "del"))
    async def tag_guild_delete(self, ctx: GuildContext, tag_name: str) -> None:
        """Delete a tag in this guild. You must be the author or a moderator to delete"""
        is_mod = await self.bot.is_mod(ctx.author)
        async with self.config.guild(ctx.guild).tags() as tags:
            tag_info = tags.get(tag_name)
            if not tag_info:
                await ctx.send("I could not find a tag with that name")
                return
            author_id = tags["author"]
            if not is_mod and author_id != ctx.author.id:
                await ctx.send("You are not the author of that tag")
                return
            del tags[tag_name]
        await ctx.send(f"Deleted the tag `{tag_name}`")

    @tag_guild.command(name="removeall", aliases=("delall", "deleteall"))
    async def tag_guild_remove_all(self, ctx: GuildContext, confirm: bool = False) -> None:
        """Remove all of your tags from this guild"""
        if not confirm and not await _handle_confirm(ctx):
            return
        await _del_helper(self.config.guild(ctx.guild), ctx.author.id)
        await ctx.send("I have deleted all of your tags")

    @tag_guild.command(name="information", aliases=("info",))
    async def tag_guild_information(self, ctx: GuildContext, tag_name: str) -> None:
        """Get information on a tag that was created in this server"""
        tags = await self.config.guild(ctx.guild).tags()
        if tag_name not in tags:
            await ctx.send("I couldn't find a tag with that name")
            return
        tag_info = tags[tag_name]
        await self.send_tag_info(ctx, tag_name, tag_info, False)

    async def send_tag_info(
        self,
        ctx: commands.Context,
        tag_name: str,
        tag_info: dict,
        global_tag: bool = True,
    ) -> None:
        author_id: int = tag_info["author"]
        maybe_author = _get_author(author_id, ctx.guild, self._owners)
        timestamp: int = tag_info["timestamp"]
        display_timestamp = f"<t:{timestamp}:R>"
        last_edit: Optional[int] = tag_info["last_edit"]
        if last_edit:
            display_edit = f"<t:{last_edit}:R>"
        tag_content = tag_info["content"]

        if await ctx.embed_requested():
            embed = discord.Embed(
                title=f"Tag {tag_name}",
                description=tag_content,
                colour=await ctx.embed_colour(),
                timestamp=_get_timestamp(dt=True),
            )
            if maybe_author:
                embed.set_footer(
                    text=f"Created by {maybe_author.display_name}",
                    icon_url=maybe_author.display_avatar,
                )
            embed.add_field(name="Created At", value=display_timestamp)
            if last_edit:
                embed.add_field(name="Last Edited", value=display_edit)
            await ctx.send(embed=embed)
            return
        if maybe_author:
            display_author = f"## Created by\n{maybe_author.name} ({maybe_author.id})\n"
        else:
            display_author = ""
        content = (
            f"# Tag {tag_name}\n\n"
            f"{tag_content}\n\n{display_author}"
            f"## Created at\n{display_timestamp}"
        )
        if last_edit:
            content += f"## Last Edited\n{display_edit}"
        content += f"\n-# <t:{_get_timestamp()}:R>"
        await ctx.send(content)

    async def list_tags(self, ctx: commands.Context, tags: dict) -> None:
        if ctx.guild:
            title = f"Tags in {ctx.guild.name}"
        else:
            title = "Global tags"
        footer = f"-# <t:{_get_timestamp()}>"
        to_pagify = []
        for tag_name, tag_info in tags.items():
            author_id = tag_info["author"]
            maybe_author = _get_author(author_id, ctx.guild, self._owners, ctx.guild is not None)
            actual = getattr(maybe_author, "display_name", author_id)
            to_pagify.append(f"`{tag_name}` author: {actual}")
        menu: List[Union[str, discord.Embed]] = []
        for page in pagify("\n".join(to_pagify), page_length=1800):
            if not await ctx.embed_requested():
                menu.append(f"# {title}\n\n{page}\n\n{footer}")
                continue
            embed = discord.Embed(
                title=title,
                description=page,
                timestamp=_get_timestamp(dt=True),
                colour=await ctx.embed_colour(),
            )
            if ctx.guild:
                embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)
            menu.append(embed)
        await SimpleMenu(
            menu, disable_after_timeout=True,  # type:ignore
        ).start(ctx, user=ctx.author)
