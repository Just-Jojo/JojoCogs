# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from contextlib import suppress
from typing import Union

import discord  # type:ignore
from redbot.core import commands
from redbot.core.utils.chat_formatting import box
from redbot.vendored.discord.ext import menus  # type:ignore


class Page(menus.ListPageSource):
    def __init__(self, data: list, title: str):
        super().__init__(data, per_page=1)
        self.title = title

    async def format_page(self, menu: "Menu", page: str) -> Union[discord.Embed, str]:
        ctx: commands.Context = menu.ctx
        footer = f"Page {menu.current_page + 1}/{self.get_max_pages()}"
        ret = f"**{self.title}**\n{box(page, 'md')}\n{footer}"
        if await ctx.embed_requested():
            ret = discord.Embed(
                title=self.title,
                description=box(page, "md"),
                colour=await ctx.embed_colour(),
            ).set_footer(text=footer)
        return ret


class Menu(menus.MenuPages, inherit_buttons=False):  # type:ignore
    def __init__(self, source: Page):
        super().__init__(source)

    async def show_checked_page(self, page_number: int):
        max_pages = self.source.get_max_pages()
        try:
            if max_pages is None or max_pages > page_number >= 0:
                await self.show_page(page_number)
            elif max_pages <= page_number:
                await self.show_page(0)
            elif 0 > page_number:
                await self.show_page(max_pages - 1)
        except IndexError:
            pass

    async def send_initial_message(
        self, ctx: commands.Context, channel: discord.TextChannel
    ) -> discord.Message:
        page = await self.source.get_page(0)
        self.current_page = 0
        kwargs = await self._get_kwargs_from_page(page)
        return await ctx.send(**kwargs)

    def _skip_double_triangle_buttons(self) -> bool:
        max_pages = self.source.get_max_pages()
        if max_pages is None:
            return True
        return max_pages < 5

    def _skip_single_triangle_buttons(self) -> bool:
        max_pages = self.source.get_max_pages()
        if max_pages is None:
            return True
        return max_pages == 1

    @menus.button(
        "\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}\N{VARIATION SELECTOR-16}",
        position=menus.First(0),
        skip_if=_skip_double_triangle_buttons,
    )
    async def go_to_first_page(self, payload):
        await self.show_page(0)

    @menus.button(
        "\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}\N{VARIATION SELECTOR-16}",
        position=menus.Last(1),
        skip_if=_skip_double_triangle_buttons,
    )
    async def go_to_last_page(self, payload):
        await self.show_page(self.source.get_max_pages() - 1)

    @menus.button(
        "\N{LEFTWARDS BLACK ARROW}\N{VARIATION SELECTOR-16}",
        position=menus.First(1),
        skip_if=_skip_single_triangle_buttons,
    )
    async def go_to_previous_page(self, payload):
        await self.show_checked_page(self.current_page - 1)

    @menus.button(
        "\N{BLACK RIGHTWARDS ARROW}\N{VARIATION SELECTOR-16}",
        position=menus.Last(0),
        skip_if=_skip_single_triangle_buttons,
    )
    async def go_to_next_page(self, payload):
        await self.show_checked_page(self.current_page + 1)

    @menus.button("\N{CROSS MARK}")
    async def stop_pages(self, payload):
        self.stop()
        with suppress(discord.Forbidden):
            await self.message.delete()
