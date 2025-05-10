# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import logging
from datetime import datetime, timezone

import discord  # type:ignore
from redbot.core import Config, modlog
from redbot.core.bot import Red

from typing import Optional


log = logging.getLogger("red.JojoCogs.advanced_log.api")


class ApiError(Exception):
    """Base exception for the api"""


class NotAuthor(ApiError):
    def __init__(self, moderator: discord.Member):
        super().__init__(f"{moderator.name} is not the author of that note")


def no_exception_bool(func):
    async def inner(*args, **kwargs):
        try:
            await func(*args, **kwargs)
        except RuntimeError:
            return False
        else:
            return True

    return inner


modlog_exists = no_exception_bool(modlog.get_modlog_channel)


class NoteApi:
    __slots__ = ("config", "bot")

    def __init__(self, config: Config, bot: Red):
        self.config = config
        self.bot = bot

    async def _modlog_enabled(self, guild: discord.Guild) -> bool:
        if not await self.config.guild(guild).modlog_enabled():
            return False
        return await modlog_exists(guild)

    async def create_note(
        self,
        guild: discord.Guild,
        user: discord.User,
        moderator: discord.Member,
        note: str,
    ) -> None:
        async with self.config.member_from_ids(guild.id, user.id).notes() as notes:
            case_num: Optional[int] = None
            if await self._modlog_enabled(guild):
                case = await modlog.create_case(
                    self.bot, guild, datetime.utcnow(), "Mod Note", user, moderator, note
                )
                case_num = case.case_number  # type:ignore
            notes.append({"author": moderator.id, "note": note, "case_number": case_num})
        log.debug(
            f"Moderator {moderator.name} ({moderator.id}) added note "
            f"'{note}' to {user.name}'s ({user.id}) notes"
        )

    async def edit_note(
        self,
        guild: discord.Guild,
        index: int,
        user: discord.User,
        moderator: discord.Member,
        new_note: str,
    ) -> str:
        old_note: str
        async with self.config.member_from_ids(guild.id, user.id).notes() as notes:
            data = notes[index]
            if (
                data["author"] != moderator.id and not
                await self.config.guild(guild).allow_other_edits()
            ):
                raise NotAuthor(moderator)
            old_note = data["note"]
            data["note"] = new_note
            data["amend_author"] = str(moderator)
            data["amend_time"] = int(datetime.now(timezone.utc).timestamp())
            if await self._modlog_enabled(guild):
                if not data["case_number"]:
                    case = await modlog.create_case(
                        self.bot,
                        guild,
                        datetime.utcnow(),
                        "Mod Note",
                        user,
                        moderator,
                        new_note,
                    )
                    data["case_number"] = case.case_number  # type:ignore
                else:
                    case = await modlog.get_case(data["case_number"], guild, self.bot)
                    await case.edit(
                        {"modified_at": datetime.utcnow().timestamp(), "reason": new_note}
                    )
            notes[index] = data
        log.debug(
            f"Moderator {moderator.name} ({moderator.id}) edited the "
            f"note on {user.name} ({user.id}) at index {index} to {new_note}"
        )
        return old_note

    async def remove_note(
        self,
        guild: discord.Guild,
        index: int,
        user_id: int,
        moderator: discord.Member,
    ) -> None:
        async with self.config.member_from_ids(guild.id, user_id).notes() as notes:
            note = notes[index]
            if (
                note["author"] != moderator.id and not
                await self.config.guild(guild).allow_other_edits()
            ):
                raise NotAuthor(moderator)
            notes.pop(index)
            if await self._modlog_enabled(guild) and (cn := note["case_number"]):
                case = await modlog.get_case(cn, guild, self.bot)
                await case.edit(
                    {
                        "modified_at": datetime.utcnow().timestamp(),
                        "reason": "Removed this note.",
                    }
                )
