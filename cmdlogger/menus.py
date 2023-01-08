# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from __future__ import annotations

from contextlib import suppress
from typing import Union, TYPE_CHECKING

import datetime
import discord
from redbot.core import commands
from redbot.core.bot import Red

__all__ = ["Menu", "Page"]

button_emojis = {
    (False, True): "\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}",
    (False, False): "\N{BLACK LEFT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}",
    (True, False): "\N{BLACK RIGHT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}",
    (True, True): "\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}",
}


class MenuButton(discord.ui.Button):
    def __init__(self, forward: bool, skip: bool, disabled: bool):
        super().__init__(emoji=button_emojis[(forward, skip)], style=discord.ButtonStyle.grey, disabled=disabled)
        self.forward = forward
        self.skip = skip
        if TYPE_CHECKING:
            self.view: Menu

    async def callback(self, interaction: discord.Interaction) -> None:
        if self.skip:
            return await self.view.show_checked_page(-1 if self.forward else 0)
        await self.view.show_checked_page(self.view.current_page + (1 if self.forward else -1))


class StopButton(discord.ui.Button):
    if TYPE_CHECKING:
        view: Menu

    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.red,
            emoji="\N{HEAVY MULTIPLICATION X}\N{VARIATION SELECTOR-16}",
            disabled=False,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        self.view.stop()
        with suppress(discord.Forbidden):
            if self.view.msg:
                await self.view.msg.delete()


class Page:
    def __init__(self, entries: list):
        self.entries = entries
        self.max_pages = len(entries)

    async def format_page(self, page: str, view: Menu) -> Union[str, discord.Embed]:
        ctx = view.ctx
        footer = f"Page {view.current_page + 1}/{self.max_pages}"
        if await ctx.embed_requested():
            return discord.Embed(
                title="Command Logging",
                description=page,
                colour=await ctx.embed_colour(),
                timestamp=datetime.datetime.now(tz=datetime.timezone.utc)
            ).set_footer(text=footer)
        return f"**Command Logging**\n\n{page}\n\n{footer}"


class Menu(discord.ui.View):
    def __init__(self, source: Page, ctx: commands.Context):
        super().__init__()
        self.source: Page = source
        self.ctx: commands.Context = ctx

        self.current_page: int = 0
        self.msg: discord.Message = None # type:ignore
        self.add_buttons()

    def add_item(self, item: discord.ui.Item):
        if getattr(item, "disabled", False):
            return self
        return super().add_item(item)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                content="You are not authorized to use this menu.",
                ephemeral=True,
            )
            return False
        return True

    def add_buttons(self) -> None:
        single_disabled = self.source.max_pages <= 1
        multi_disabled = self.source.max_pages <= 5
        [self.add_item(i) for i in [
                MenuButton(False, True, multi_disabled),
                MenuButton(False, False, single_disabled),
                StopButton(),
                MenuButton(True, False, single_disabled),
                MenuButton(True, True, multi_disabled),
            ]
        ]

    async def _get_kwargs_from_page(self, page: str) -> dict:
        data = await self.source.format_page(page, self)
        if isinstance(data, discord.Embed):
            return {"embed": data}
        return {"content": str(data)}

    async def show_checked_page(self, page_number: int) -> None:
        max_pages = self.source.max_pages
        try:
            if max_pages > page_number >= 0:
                await self.show_page(page_number)
            elif max_pages <= page_number:
                await self.show_page(0)
            else:
                await self.show_page(max_pages - 1)
        except IndexError:
            pass

    async def show_page(self, page_number: int) -> None:
        page = self.source.entries[page_number]
        self.current_page = page_number
        kwargs = await self._get_kwargs_from_page(page)
        await self.msg.edit(**kwargs)

    async def start(self) -> None:
        page = self.source.entries[0]
        kwargs = await self._get_kwargs_from_page(page)
        self.msg = await self.ctx.send(view=self, **kwargs)
