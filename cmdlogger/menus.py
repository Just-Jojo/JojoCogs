# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from contextlib import suppress
from typing import Union

import discord
from redbot.core import commands
from redbot.vendored.discord.ext.menus import First, Last, ListPageSource, MenuPages, button

__all__ = ["CmdMenu", "CmdPages"]


class CmdPages(ListPageSource):
    def __init__(self, data: list):
        super().__init__(data, per_page=1)

    async def format_page(self, menu: "CmdMenu", page: str) -> Union[discord.Embed, str]:
        ctx: commands.Context = menu.ctx
        footer = f"Page {menu.current_page + 1}/{self.get_max_pages()}"

        if await ctx.embed_requested():
            embed = discord.Embed(
                title="Cmd logging", description=page, colour=await ctx.embed_colour()
            ).set_footer(text=footer)
            return embed
        return f"**Cmd logging**\n{page}\n{footer}"


class CmdMenu(MenuPages):
    ctx: commands.Context

    @property
    def source(self) -> CmdPages:
        return self._source

    def __init__(self, source: CmdPages):
        super().__init__(source, clear_reactions_after=True)

    def _skip_double_triangle_buttons(self) -> bool:
        max_pages = self._source.get_max_pages()
        if max_pages is None:
            return True
        return max_pages <= 4

    async def send_initial_message(self, ctx, channel) -> discord.Message:
        page = await self.source.get_page(0)
        kwargs = await self._get_kwargs_from_page(page)
        return await channel.send(**kwargs)

    def _skip_single_triangle_buttons(self) -> bool:
        max_pages = self._source.get_max_pages()
        if max_pages is None:
            return True
        return max_pages == 1

    async def show_checked_page(self, page_number: int) -> None:
        max_pages = self.source.get_max_pages()
        try:
            if max_pages is None or max_pages > page_number >= 0:
                await self.show_page(page_number)
            elif max_pages <= page_number:
                await self.show_page(0)
            elif page_number < 0:
                await self.show_page(max_pages - 1)
        except IndexError:
            pass

    @button(
        "\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}\N{VARIATION SELECTOR-16}",
        skip_if=_skip_double_triangle_buttons,
        position=First(0),
    )
    async def go_to_first_page(self, payload):
        await self.show_page(0)

    @button(
        "\N{LEFTWARDS BLACK ARROW}\N{VARIATION SELECTOR-16}",
        skip_if=_skip_single_triangle_buttons,
        position=First(1),
    )
    async def go_to_previous_page(self, payload):
        await self.show_checked_page(self.current_page - 1)

    @button(
        "\N{BLACK RIGHTWARDS ARROW}\N{VARIATION SELECTOR-16}",
        skip_if=_skip_single_triangle_buttons,
        position=Last(0),
    )
    async def go_to_next_page(self, payload):
        await self.show_checked_page(self.current_page + 1)

    @button(
        "\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}\N{VARIATION SELECTOR-16}",
        skip_if=_skip_double_triangle_buttons,
        position=Last(1),
    )
    async def go_to_last_page(self, payload):
        await self.show_checked_page(self.source.get_max_pages() - 1)

    @button("\N{CROSS MARK}")
    async def stop_pages(self, payload):
        self.stop()
        with suppress(discord.Forbidden, discord.NotFound):
            await self.message.delete()
