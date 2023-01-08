# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from __future__ import annotations

from typing import TYPE_CHECKING, List, Union, Optional

from contextlib import suppress
import discord
import datetime
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box
from redbot.vendored.discord.ext import menus  # type:ignore

__all__ = ["Page", "Menu", "PositiveInt"]

button_emojis = {
    (False, True): "\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}",
    (False, False): "\N{BLACK LEFT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}",
    (True, False): "\N{BLACK RIGHT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}",
    (True, True): "\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}",
}


class BaseButton(discord.ui.Button):
    def __init__(
        self,
        forward: bool,
        skip: bool,
        disabled: bool = False,
    ) -> None:
        super().__init__(style=discord.ButtonStyle.grey, emoji=button_emojis[(forward, skip)], disabled=disabled)
        self.forward = forward  # If the menu should go to the next page or previous
        self.skip = skip  # If the menu should step once or go to the first/last page
        if TYPE_CHECKING:
            self.view: Menu

    async def callback(self, inter: discord.Interaction) -> None:
        page_num = 1 if self.forward else -1
        if self.skip:
            page_num = -1 if self.forward else 0 # -1 triggers the `else` clause which sends it to the last page
        await self.view.show_checked_page(page_number=page_num)


class StopButton(discord.ui.Button):
    if TYPE_CHECKING:
        view: Menu

    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.red,
            emoji="\N{HEAVY MULTIPLICATION X}\N{VARIATION SELECTOR-16}",
            disabled=False,
        )

    async def callback(self, inter: discord.Interaction) -> None:
        self.view.stop()
        with suppress(discord.Forbidden):
            if msg := self.view.msg:
                await msg.delete()


class Page:
    def __init__(self, entries: List[str], title: str):
        self.entries = entries
        self.title = title
        self.max_pages = len(entries)

    async def format_page(self, page: str, view: Menu) -> Union[str, discord.Embed]:
        ctx = view.ctx
        footer = f"Page {view.current_page + 1}/{self.max_pages}"
        if ctx and await ctx.embed_requested(): # not gonna embed unless 
            return discord.Embed(
                title=self.title,
                colour=await ctx.embed_colour(),
                description=page,
                timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
            ).set_footer(text=footer)
        return f"**{self.title}**\n\n{page}\n\n{footer}"


class Menu(discord.ui.View):
    if TYPE_CHECKING:
        ctx: commands.Context

    def __init__(self, source: Page, bot: Red, ctx: commands.Context):
        super().__init__()
        self.bot = bot
        self.ctx = ctx
        self.source = source

        self.msg: discord.Message = None # type:ignore
        self.current_page: int = 0
        self._add_buttons()

    def add_item(self, item: discord.ui.Item):
        # Editted to just not add the item if it's disabled
        if getattr(item, "disabled", False):
            return self
        return super().add_item(item)

    def _add_buttons(self) -> None:
        # Stupid me getting myself excited for something
        # that I can't even do lmfao
        single_disabled = self.source.max_pages <= 1
        multi_disabled = self.source.max_pages <= 5
        [self.add_item(i) for i in [
                BaseButton(False, True),
                BaseButton(False, False),
                StopButton(),
                BaseButton(True, False),
                BaseButton(True, True)
            ]
        ]

    async def on_timeout(self) -> None:
        with suppress(discord.Forbidden):
            await self.msg.delete()

    async def _get_kwargs_from_page(self, page: str) -> dict:
        data = await self.source.format_page(page, self)
        if isinstance(data, discord.Embed):
            return {"embed": data}
        return {"content": data}

    async def start(self) -> None:
        page = self.source.entries[0]
        kwargs = await self._get_kwargs_from_page(page)
        self.msg = await self.ctx.send(view=self, **kwargs)

    async def interaction_check(self, inter: discord.Interaction) -> bool:
        if inter.user.id != self.ctx.author.id:
            await inter.response.send_message(
                "You are not authorized to use this interaction.",
                ephemeral=True,
            )
            return False
        return True

    async def show_page(self, page_number: int) -> None:
        page = self.source.entries[page_number]
        self.current_page = page_number
        kwargs = await self._get_kwargs_from_page(page)
        await self.msg.edit(view=self, **kwargs)

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


if TYPE_CHECKING:
    PositiveInt = int
else:

    class PositiveInt(commands.Converter):
        async def convert(self, ctx: commands.Context, arg: str) -> int:
            try:
                ret = int(arg)
            except ValueError:
                raise commands.BadArgument("That was not an integer")
            if ret <= 0:
                raise commands.BadArgument(f"'{arg}' is not a positive integer")
            return ret
