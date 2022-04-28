# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from __future__ import annotations

import abc
from contextlib import suppress
from typing import Union, TYPE_CHECKING

import discord  # type:ignore
from redbot.core import commands
from redbot.core.utils.chat_formatting import box
from redbot.vendored.discord.ext import menus  # type:ignore


if TYPE_CHECKING:
    from typing_extensions import Self


class ButtonABC(abc.ABC):
    def __init__(self, *_args):
        self.view: Menu
        super().__init__()


class FirstPageButton(discord.ui.Button, ButtonABC):
    def __init__(self, disabled: bool = False):
        super().__init__(
            style=discord.ButtonStyle.gray, 
            emoji="\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}",
            disabled=disabled,
        )

    async def callback(self, inter: discord.Interaction) -> None:
        await self.view.show_page(0)


class PreviousPageButton(discord.ui.Button, ButtonABC):
    def __init__(self, disabled: bool = False):
        super().__init__(
            style=discord.ButtonStyle.gray,
            emoji="\N{BLACK LEFT-POINTING TRIANGLE}",
            disabled=disabled,
        )

    async def callback(self, inter: discord.Interaction) -> None:
        await self.view.show_checked_page(self.view.current_page - 1)


class StopButton(discord.ui.Button, ButtonABC):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.red,
            emoji="\N{HEAVY MULTIPLICATION X}\N{VARIATION SELECTOR-16}",
            disabled=False
        )

    async def callback(self, inter: discord.Interaction) -> None:
        self.view.stop()
        with suppress(discord.Forbidden):
            await self.view.msg.delete()


class NextPageButton(discord.ui.Button, ButtonABC):
    def __init__(self, disabled: bool = False):
        super().__init__(
            style=discord.ButtonStyle.gray,
            emoji="\N{BLACK RIGHT-POINTING TRIANGLE}",
            disabled=disabled
        )

    async def callback(self, inter: discord.Interaction) -> None:
        await self.view.show_checked_page(self.view.current_page + 1)


class LastPageButton(discord.ui.Button, ButtonABC):
    def __init__(self, disabled: bool = False):
        super().__init__(
            style=discord.ButtonStyle.gray,
            emoji="\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}",
            disabled=disabled,
        )

    async def callback(self, inter: discord.Interaction) -> None:
        await self.view.show_checked_page(-1)


class Page:
    def __init__(self, data: list, title: str, *, use_md: bool = True):
        self.data = data
        self.max_pages = len(data)
        self.title = title
        self.use_md = use_md

    async def format_page(self, menu: Menu, page: str) -> Union[discord.Embed, str]:
        ctx: commands.Context = menu.ctx
        footer = f"Page {menu.current_page + 1}/{self.max_pages}"
        page = box(page, "md") if self.use_md else page
        ret = f"**{self.title}**\n{page}\n{footer}"
        if await ctx.embed_requested():
            ret = discord.Embed(
                title=self.title,
                description=page,
                colour=await ctx.embed_colour(),
            ).set_footer(text=footer)
        return ret

    async def get_page(self, page_number: int) -> str:
        return self.data[page_number]


class Menu(discord.ui.View):
    def __init__(self, ctx: commands.Context, source: Page):
        super().__init__()
        self.source = source
        self.ctx = ctx
        self.msg: discord.Message

        single_disabled = self.source.max_pages == 1
        multiple_disabled = self.source.max_pages < 5

        self.add_item(FirstPageButton(multiple_disabled))
        self.add_item(PreviousPageButton(single_disabled))
        self.add_item(StopButton())
        self.add_item(NextPageButton(single_disabled))
        self.add_item(LastPageButton(multiple_disabled))

    def add_item(self, item: discord.ui.Item) -> Self:
        if getattr(item, "disabled", False):
            return self
        return super().add_item(item)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "You are not authorized to use this menu",
                ephemeral=True,
            )
            return False
        return True

    async def show_checked_page(self, page_number: int):
        max_pages = self.source.max_pages
        try:
            if max_pages is None or max_pages > page_number >= 0:
                await self.show_page(page_number)
            elif max_pages <= page_number:
                await self.show_page(0)
            elif 0 > page_number:
                await self.show_page(max_pages - 1)
        except IndexError:
            pass

    async def show_page(self, page_number: int) -> None:
        page = await self.source.get_page(page_number)
        self.current_page = page_number
        kwargs = await self._get_kwargs_from_page(page)
        await self.msg.edit(**kwargs, view=self)

    async def _get_kwargs_from_page(self, page: str) -> dict:
        data = await self.source.format_page(self, page)
        if isinstance(data, discord.Embed):
            return {"embed": data}
        return {"content": str(data)}

    async def start(
        self
    ) -> discord.Message:
        page = await self.source.get_page(0)
        self.current_page = 0
        kwargs = await self._get_kwargs_from_page(page)
        self.msg = await self.ctx.send(**kwargs, view=self)
