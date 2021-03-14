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

import discord
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box, bold
from redbot.vendored.discord.ext import menus


__all__ = ["TodoPages", "TodoMenu", "positive_int"]


class TodoPages(menus.ListPageSource):
    def __init__(self, data, use_md: bool, use_embeds: bool, title: str):
        super().__init__(data, per_page=1)
        self.md = use_md
        self.use_embeds = use_embeds
        self.title = title

    def is_paginating(self):
        return True

    async def format_page(self, menu, page):
        bot: Red = menu.bot
        ctx: commands.Context = menu.ctx
        if self.md:
            page = box(page, "md")
        if await ctx.embed_requested() and self.use_embeds:
            embed = discord.Embed(title=self.title, colour=await ctx.embed_colour())
            embed.description = page
            embed.set_footer(
                text=f"Page {menu.current_page + 1}/{self.get_max_pages()}"
            )
            return embed
        else:
            return (
                f"{bold(self.title)}\n"
                + page
                + f"\nPage {menu.current_page + 1}/{self.get_max_pages()}"
            )


class TodoMenu(menus.MenuPages, inherit_buttons=False):
    _source: menus.ListPageSource

    def __init__(self, source: menus.ListPageSource, page_start: int = 0, **kwargs):
        super().__init__(source=source, **kwargs)
        self.page_start = page_start

    async def send_initial_message(
        self, ctx: commands.Context, channel: discord.TextChannel
    ):
        self.current_page = self.page_start
        page = await self._source.get_page(self.page_start)
        kwargs = await self._get_kwargs_from_page(page)
        return await channel.send(**kwargs)

    def _skip_double_triangle_buttons(self):
        max_pages = self._source.get_max_pages()
        if max_pages is None:
            return True
        return max_pages <= 4

    def _skip_single_arrows(self):
        max_pages = self._source.get_max_pages()
        if max_pages is None:
            return True
        return max_pages == 1

    async def show_checked_page(self, page_number: int):
        max_pages = self._source.get_max_pages()
        try:
            if max_pages is None or max_pages > page_number >= 0:
                await self.show_page(page_number)
            elif page_number >= max_pages:
                await self.show_page(0)
            elif page_number < 0:
                await self.show_page(max_pages - 1)
        except IndexError:
            pass

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
        await self.show_checked_page(page_number=self._source.get_max_pages() - 1)

    @menus.button(
        "\N{LEFTWARDS BLACK ARROW}",
        position=menus.First(1),
        skip_if=_skip_single_arrows,
    )
    async def go_to_previous_page(self, payload):
        await self.show_checked_page(page_number=self.current_page - 1)

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


def positive_int(arg: str) -> int:
    """Type hint for positive ints"""
    try:
        ret = int(arg)
    except ValueError:  # Isn't an int
        raise commands.BadArgument(f"{arg} is not an integer")
    if ret <= 0:
        raise commands.BadArgument(f"{arg} is not a positive integer")
    return ret
