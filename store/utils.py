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

import typing

import discord
from redbot.core import commands
from redbot.vendored.discord.ext import menus

__all__ = ["JojoPages", "JojoMenu"]


class JojoPages(menus.ListPageSource):
    def __init__(self, data: list):
        super().__init__(data, per_page=1)

    def is_paginating(self):
        return True

    async def format_page(self, menu, page):
        if not menu.ctx.channel.permissions_for(menu.ctx.me).embed_links:
            return page

        embed = discord.Embed(
            title=f"{menu.bot.user.name} Pages",
            description=page,
            colour=await menu.ctx.embed_colour(),
        )
        embed.set_footer(
            text=f"Page {menu.current_page + 1}/{self.get_max_pages()}"
        )
        return embed


class JojoMenu(menus.MenuPages, inherit_buttons=False):
    def __init__(
        self,
        source: menus.ListPageSource,
        timeout: int = 30,
        delete_message_after: bool = False,
        clear_reactions_after: bool = True,
        message: discord.Message = None,
        page_start: int = 0,
        **kwargs: typing.Any,
    ):
        super().__init__(
            source=source,
            delete_message_after=delete_message_after,
            timeout=timeout,
            clear_reactions_after=clear_reactions_after,
            message=message,
            **kwargs,
        )
        self.page_start = page_start

    async def send_initial_message(
        self, ctx: commands.Context, channel: discord.TextChannel
    ):
        self.current_page = self.page_start
        page = await self._source.get_page(self.page_start)
        kwargs = await self._get_kwargs_from_page(page)
        return await channel.send(**kwargs)

    async def show_checked_page(self, page_number: int):
        max_pages = self._source.get_max_pages()
        if max_pages is None or max_pages > page_number >= 0:
            await self.show_page(page_number)
        elif page_number >= max_pages:
            await self.show_page(0)
        else:
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
        await self.show_checked_page(page_number=self._source.max_pages() - 1)

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


def lowercase_str(thing: str):
    return thing.lower()


def positive_int(thing: str):
    try:
        ret = int(thing)
    except ValueError:
        raise commands.BadArgument(f"`{thing}` is not an int")
    if ret < 1:
        raise commands.BadArgument(f"{thing} was not a positive integer")
    return ret
