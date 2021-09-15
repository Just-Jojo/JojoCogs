# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import discord # type:ignore
from redbot.core import commands, Config, modlog
from redbot.core.bot import Red
from redbot.core.utils import AsyncIter
from redbot.core.utils.chat_formatting import pagify

from .utils import *
from .api import NotAuthor, NoteApi, modlog_exists
from .menus import Menu, Page
import logging


log = logging.getLogger("red.JojoCogs.advanced_log")
_config_structure = {
    "guild": {
        "modlog_enabled": False,
    },
    "member": {
        "notes": [],
    },
}


class AdvancedLog(commands.Cog):
    """An advanced log for moderators to add notes to users"""

    __authors__ = ["Jojo#7791"]
    __version__ = "1.0.0"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, 544974305445019651, True)
        self.config.register_guild(**_config_structure["guild"])
        self.config.register_member(**_config_structure["member"])
        self.api = NoteApi(self.config, self.bot)
        self.startup = self.bot.loop.create_task(self._init())

    def cog_unload(self):
        self.startup.cancel()

    async def _init(self):
        try:
            await modlog.register_casetype("Mod Note", True, "\N{MEMO}", "Mod Note")
        except RuntimeError:
            pass

    async def cog_check(self, ctx: commands.Context):
        return ctx.guild is not None

    def format_help_for_context(self, ctx: commands.Context) -> str:
        plural = "" if len(self.__authors__) == 1 else "s"
        return (
            f"{super().format_help_for_context(ctx)}\n"
            f"**Author{plural}:** {', '.join(self.__authors__)}\n"
            f"**Version:** `{self.__version__}`"
        )

    async def red_delete_data_for_user(self, requester, user_id: int):
        if requester != "discord_deleted_user":
            return
        all_members = await self.config.all_members()
        async for guild_id, guild_data in AsyncIter(all_members.items(), steps=100):
            if user_id in guild_data:
                await self.config.member_from_ids(guild_id, user_id).clear()

        async def red_get_data_for_user(self, *args, **kwargs):
            return {}

    @commands.group()
    @commands.admin_or_permissions(administrator=True)
    async def modnoteset(self, ctx: commands.Context):
        """Setup modnotes"""
        pass

    @modnoteset.command()
    async def usemodlog(self, ctx: commands.Context, toggle: bool):
        """Toggle whether to use the modlog or not
        
        If toggled, whenever a note is created on a user it will create a case in the modlog

        **Arguments**
            - `toggle` Whether to enable or disable the modlog logging
        """
        if toggle and not await modlog_exists(ctx.guild):
            return await ctx.send("I could not find the modlog channel. Please set one up in order to use this feature")
        current = await self.config.guild(ctx.guild).modlog_enabled()
        disabled = "enabled" if toggle else "disabled"
        if current == toggle:
            return await ctx.send(f"The modlog logging is already {disabled}")
        await ctx.send(f"Modlog logging is now {disabled}")
        await self.config.guild(ctx.guild).modlog_enabled.set(toggle)

    @commands.group(aliases=("mnote",), invoke_without_command=True)
    @commands.mod_or_permissions(administrator=True)
    async def modnote(self, ctx: commands.Context, user: NonBotMember(False), *, note: str): # type:ignore
        """Create a note for a user. This user cannot be a bot

        If enabled this will also log to the modlog

        **Arguments**
            - `user` A non-bot user to log for.
            - `note` The note to add to them.
        """
        await ctx.send(f"Done. I have added that as a note for {user.name}")
        await self.api.create_note(ctx.guild, user, ctx.author, note)

    @modnote.command()
    async def remove(self, ctx: commands.Context, user: NonBotMember, index: PositiveInt):
        """Remove a note from a user.
        
        Note that you must be the author of the note to remove it
        
        **Arguments**
            - `user` The user to remove a note from
            - `index` The index of the note to remove
        """
        try:
            await self.api.remove_note(ctx.guild, index - 1, user, ctx.author)
        except NotAuthor:
            await ctx.send("You are not the author of that note.")
        except IndexError:
            await ctx.send(f"I could not find a note at index {index}.")
        else:
            await ctx.send(f"Removed a note from that user at index {index}")

    @modnote.command()
    async def edit(self, ctx: commands.Context, user: NonBotMember, index: PositiveInt, *, note: str):
        """Edit a note on a user
        
        Note that you can only edit notes that you have created

        **Arguments**
            - `user` The user to edit a note on
            - `index` The index of the reason to edit
            - `note` The new note
        """
        try:
            await self.api.edit_note(ctx.guild, index - 1, user, ctx.author, note)
        except NotAuthor:
            await ctx.send("You are not the author of that note.")
        except IndexError:
            await ctx.send(f"I could not find a note at index {index}.")
        else:
            await ctx.send(f"Edited the note at index {index}.") # TODO(Jojo) Maybe send the new + old note?

    @modnote.command(name="list")
    async def list_notes(self, ctx: commands.Context, user: NonBotMember):
        """List the notes on a certain user
        
        This user cannot be a bot

        **Arguments**
            - `user` The user to view notes of
        """
        data = await self.config.member(user).notes()
        if not data:
            return await ctx.send("That user does not have any notes")
        act = []
        for note in data:
            act.append([getattr(ctx.guild.get_member(note["author"]), "name", note["author"]), note["note"]])
        msg = "# Moderator\tNote\n"
        msg += "\n".join(f"{num}. {mod}\t\t{note}" for num, (mod, note) in enumerate(act, 1))
        await Menu(Page(list(pagify(msg)), f"{user.name}'s notes")).start(ctx)
