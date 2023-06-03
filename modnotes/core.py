# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import logging
from typing import Any, Dict, Final, List

import discord  # type:ignore
from redbot.core import Config, commands, modlog
from redbot.core.bot import Red
from redbot.core.utils import AsyncIter
from redbot.core.utils.chat_formatting import pagify

from .api import NotAuthor, NoteApi, modlog_exists
from .menus import Menu, Page
from .utils import *

log = logging.getLogger("red.JojoCogs.advanced_log")
_config_structure: Dict[str, Dict[str, Any]] = {
    "guild": {
        "modlog_enabled": False,
        "allow_other_edits": False,
    },
    "member": {
        "notes": [],
    },
}


class ModNotes(commands.Cog):
    """A mod note cog for moderators to add notes to users"""

    __authors__: Final[List[str]] = ["Jojo#7791"]
    __version__: Final[str] = "1.0.1"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(None, 544974305445019651, True, cog_name="AdvancedLog")
        self.config.register_guild(**_config_structure["guild"])
        self.config.register_member(**_config_structure["member"])
        self.config.register_global(updated=False)
        self.api = NoteApi(self.config, self.bot)

    async def cog_load(self) -> None:
        try:
            await modlog.register_casetype("Mod Note", True, "\N{MEMO}", "Mod Note")
        except RuntimeError:
            pass

    async def cog_check(self, ctx: commands.Context) -> bool:
        return ctx.guild is not None

    def format_help_for_context(self, ctx: commands.Context) -> str:
        plural = "" if len(self.__authors__) == 1 else "s"
        return (
            f"{super().format_help_for_context(ctx)}\n"
            f"**Author{plural}:** {', '.join(self.__authors__)}\n"
            f"**Version:** `{self.__version__}`"
        )

    async def red_delete_data_for_user(self, requester, user_id: int) -> None:
        if requester != "discord_deleted_user":
            return
        all_members = await self.config.all_members()
        async for guild_id, guild_data in AsyncIter(all_members.items(), steps=100):
            if user_id in guild_data:
                await self.config.member_from_ids(guild_id, user_id).clear()

    async def red_get_data_for_user(self, *args, **kwargs) -> Dict[Any, Any]:
        return {}

    @commands.group()
    @commands.admin_or_permissions(administrator=True)
    async def modnoteset(self, ctx: commands.Context):
        """Setup modnotes"""
        pass

    @modnoteset.command()
    async def usemodlog(self, ctx: commands.Context, toggle: bool):
        """Toggle whether to use the modlog or not.

        If toggled, whenever a note is created on a user it will create a case in the modlog.

        **Arguments**
            - `toggle` Whether to enable or disable the modlog logging.
        """
        if toggle and not await modlog_exists(ctx.guild):
            return await ctx.send(
                "I could not find the modlog channel. Please set one up in order to use this feature."
            )
        current = await self.config.guild(ctx.guild).modlog_enabled()
        disabled = "enabled" if toggle else "disabled"
        if current == toggle:
            return await ctx.send(f"The modlog logging is already {disabled}.")
        await ctx.send(f"Modlog logging is now {disabled}.")
        await self.config.guild(ctx.guild).modlog_enabled.set(toggle)

    @modnoteset.command(name="nonauthoredits", aliases=("nae",))
    async def non_author_edits(self, ctx: commands.Context, toggle: bool):
        """Allow any moderator to edit notes, regardless of who authored it
        
        **Arguments**
            - `toggle` Whether moderators other than the author can edit notes.
        """
        if toggle == await self.config.guild(ctx.guild).allow_other_edits():
            enabled = "" if toggle else "'t"
            return await ctx.send(
                f"Moderators already can{enabled} edit notes that weren't authored by them."
            )
        await self.config.guild(ctx.guild).allow_other_edits.set(toggle)
        now_no_longer = "now" if toggle else "no longer"
        await ctx.send(f"Moderators can {now_no_longer} edit notes not authored by them.")

    @commands.group(aliases=("mnote",), invoke_without_command=True)
    @commands.guild_only()
    @commands.mod_or_permissions(administrator=True)
    async def modnote(
        self, ctx: commands.Context, user: NonBotMember(False), *, note: str  # type:ignore
    ):
        """Create a note for a user. This user cannot be a bot.

        If enabled this will also log to the modlog.

        **Arguments**
            - `user` A non-bot user to log for.
            - `note` The note to add to them.
        """
        await ctx.send(f"Done. I have added that as a note for {user.name}.")
        await self.api.create_note(ctx.guild, user, ctx.author, note)

    @modnote.command(name="listall")
    async def modnote_list_all(self, ctx: commands.Context):
        """List all the members with notes in this guild"""
        data = await self.config.all_members(ctx.guild)
        if not data:
            return await ctx.send("There are no notes in this guild.")
        # data = {user.id: {"notes": [{author=id, note=str, case_number=int or None}]}}
        msg = ""
        for user_id, user_data in data.items():
            user = str(ctx.guild.get_member(user_id) or user_id)
            user_data = user_data["notes"]
            for note_data in user_data:
                author = str(ctx.guild.get_member((a := note_data["author"])) or a)
                note = note_data["note"]
                if cn := note_data["case_number"]:
                    note += f" {cn}"
                msg += f"**{user}:** (by {author}) {note}"
        title = f"Notes in {ctx.guild} ({ctx.guild.id})."
        await Menu(ctx, Page(list(pagify(msg, page_length=200)), title, use_md=False)).start()

    @modnote.command()
    async def remove(self, ctx: commands.Context, user: NonBotMember, index: PositiveInt):
        """Remove a note from a user. This user cannot be a bot.

        **Arguments**
            - `user` The user to remove a note from.
            - `index` The index of the note to remove.
        """
        try:
            await self.api.remove_note(ctx.guild, index - 1, user, ctx.author)
        except NotAuthor:
            await ctx.send("You are not the author of that note.")
        except IndexError:
            await ctx.send(f"I could not find a note at index {index}.")
        else:
            await ctx.send(f"Removed a note from that user at index {index}.")

    @modnote.command()
    async def edit(
        self, ctx: commands.Context, user: NonBotMember, index: PositiveInt, *, note: str
    ):
        """Edit a note on a user. This user cannot be a bot.

        **Arguments**
            - `user` The user to edit a note on. This user cannot be a bot.
            - `index` The index of the reason to edit.
            - `note` The new note.
        """
        try:
            await self.api.edit_note(ctx.guild, index - 1, user, ctx.author, note)
        except NotAuthor:
            await ctx.send("You are not the author of that note.")
        except IndexError:
            await ctx.send(f"I could not find a note at index {index}.")
        else:
            await ctx.send(
                f"Edited the note at index {index}."
            )  # TODO(Jojo) Maybe send the new + old note?

    @modnote.command(name="list")
    async def modnote_list(self, ctx: commands.Context, user: NonBotMember):
        """List the notes on a certain user.

        This user cannot be a bot.

        **Arguments**
            - `user` The user to view notes of.
        """
        data = await self.config.member(user).notes()
        if not data:
            return await ctx.send("That user does not have any notes.")
        act = []
        for note in data:
            act.append(
                [
                    str(ctx.guild.get_member(note["author"]) or note["author"]),
                    note["note"],
                ]
            )
        msg = "# Moderator\tNote\n"
        msg += "\n".join(f"{num}. {mod}\t\t{note}" for num, (mod, note) in enumerate(act, 1))
        await Menu(ctx, Page(list(pagify(msg)), f"Notes on {str(user)} ({user.id})")).start()
