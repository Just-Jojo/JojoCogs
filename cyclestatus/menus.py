# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from typing import List, Union

import discord
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box
from redbot.vendored.discord.ext import menus  # type:ignore

__all__ = ["Pages"]


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


class Menu(menus.MenuPages, inherit_buttons=False):  # type:ignore
    message: discord.Message

    def __init__(self, source: Pages):
        super().__init__(
            source,
            timeout=30.0,
            delete_message_after=False,
            clear_reactions_after=True,
            message=None,
        )

    @property
    def source(self) -> Pages:
        return self._source

    async def send_initial_message(self, ctx, channel) -> discord.Message:
        page = await self.source.get_page(0)
        kwargs = await self._get_kwargs_from_page(page)
        return await channel.send(**kwargs)

    async def show_checked_page(self, page_number: int) -> None:
        max_pages = self.source.get_max_pages()
        try:
            if max_pages is None or max_pages > page_number >= 0:
                await self.show_page(page_number)
            elif page_number >= max_pages:
                await self.show_page(0)
            elif page_number < 0:
                await self.show_page(max_pages - 1)
        except IndexError:
            pass

    def _skip_triangle_buttons(self) -> bool:
        max_pages = self.source.get_max_pages()
        if max_pages is None:
            return True
        return max_pages == 1

    def _skip_double_triangle_buttons(self) -> bool:
        max_pages = self.source.get_max_pages()
        if max_pages is None:
            return True
        return max_pages <= 5

    @menus.button(
        "\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}",
        position=menus.First(0),
        skip_if=_skip_double_triangle_buttons,
    )
    async def go_to_first_page(self, payload):
        await self.show_page(0)

    @menus.button(
        "\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}",
        position=menus.Last(1),
        skip_if=_skip_double_triangle_buttons,
    )
    async def go_to_last_page(self, payload):
        await self.show_page(self.source.get_max_pages() - 1)

    @menus.button(
        "\N{LEFTWARDS BLACK ARROW}\N{VARIATION SELECTOR-16}",
        position=menus.First(1),
        skip_if=_skip_triangle_buttons,
    )
    async def go_to_previous_page(self, payload):
        await self.show_checked_page(self.current_page - 1)

    @menus.button(
        "\N{BLACK RIGHTWARDS ARROW}\N{VARIATION SELECTOR-16}",
        position=menus.Last(0),
        skip_if=_skip_triangle_buttons,
    )
    async def go_to_next_page(self, payload):
        await self.show_checked_page(self.current_page + 1)

    @menus.button("\N{CROSS MARK}")
    async def stop_pages(self, payload):
        self.stop()
        with contextlib.suppress(discord.Forbidden):
            await self.message.delete()


class PositiveInt(commands.Converter):
    async def convert(self, ctx: commands.Context, arg: str) -> int:
        try:
            ret = int(arg)
        except ValueError:
            raise commands.BadArgument("That was not an integer")
        if ret <= 0:
            raise commands.BadArgument(f"'{arg}' is not a positive integer")
        return ret
