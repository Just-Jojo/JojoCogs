"""
MIT License

Copyright (c) 2020-2021 Jojo#7711

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from typing import List, Union

import discord
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box
from redbot.vendored.discord.ext import menus

__all__ = ["Pages", "Menu"]


class Pages(menus.ListPageSource):
    """Custom list page source for the menu"""

    def __init__(self, entries: Union[List[discord.Embed], List[str]], title: str):
        super().__init__(entries, per_page=1)
        self._title = title

    def is_paginating(self) -> bool:
        return True

    async def format_page(self, menu: "Menu", page: str) -> Union[discord.Embed, str]:
        ctx: commands.Context = menu.ctx
        footnote = f"Page {menu.current_page + 1}/{self.get_max_pages()}"
        if await ctx.embed_requested():
            embed = discord.Embed(
                title=self._title,
                colour=await ctx.embed_color(),
                description=box(page, "md"),
            )
            embed.set_footer(text=footnote)
            return embed
        return f"{self._title}\n{box(page, 'md')}\n{footnote}"


class Menu(menus.MenuPages, inherit_buttons=False):
    message: discord.Message
    ctx: commands.Context
    _source: Pages

    def __init__(
        self,
        source: Pages,
        clear_reactions_after: bool = True,
        delete_message_after: bool = False,
        message: discord.Message = None,
        timeout: float = 15.0,
    ):
        super().__init__(
            source,
            clear_reactions_after=clear_reactions_after,
            delete_message_after=delete_message_after,
            message=message,
            timeout=timeout,
        )
        self._page_start = 0

    async def send_initial_message(
        self, ctx: commands.Context, channel: discord.TextChannel
    ) -> discord.Message:
        self.current_page = self._page_start
        page = await self._source.get_page(self.current_page)
        kwargs = await self._get_kwargs_from_page(page)
        return await channel.send(**kwargs)

    async def show_checked_page(self, page_number: int):
        max_pages = self._source.get_max_pages()
        if max_pages is None or max_pages > page_number >= 0:
            await self.show_page(page_number)
        elif page_number > max_pages:
            await self.show_page(0)
        elif page_number < 0:
            await self.show_page(max_pages - 1)

    def _skip_single_arrows(self):
        max_pages = self._source.get_max_pages()
        if max_pages is None:
            return True
        return max_pages == 1

    def _skip_double_triangle_buttons(self):
        max_pages = self._source.get_max_pages()
        if max_pages is None:
            return True
        return max_pages <= 4

    @menus.button(
        "\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}",
        position=menus.First(0),
        skip_if=_skip_double_triangle_buttons,
    )
    async def go_to_first_page(self, payload):
        await self.show_checked_page(0)

    @menus.button(
        "\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}",
        position=menus.Last(1),
        skip_if=_skip_double_triangle_buttons,
    )
    async def go_to_last_page(self, payload):
        await self.show_checked_page(self._source.get_max_pages() - 1)

    @menus.button(
        "\N{LEFTWARDS BLACK ARROW}",
        position=menus.First(1),
        skip_if=_skip_single_arrows,
    )
    async def go_to_previous_page(self, payload):
        await self.show_checked_page(self.current_page - 1)

    @menus.button(
        "\N{BLACK RIGHTWARDS ARROW}",
        position=menus.Last(0),
        skip_if=_skip_single_arrows,
    )
    async def go_to_next_page(self, payload):
        await self.show_checked_page(self.current_page + 1)

    @menus.button("\N{CROSS MARK}")
    async def stop_pages(self, payload):
        self.stop()
        await self.message.delete()
