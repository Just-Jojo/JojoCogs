from typing import Any, Union

import discord
from redbot.core import commands
from redbot.vendored.discord.ext import menus


class Page(menus.ListPageSource):
    def __init__(self, entries: list, title: str):
        self.title = title
        super().__init__(entries, per_page=1)

    def is_paginating(self) -> bool:
        return True

    async def format_page(self, menu: "Menu", page: str) -> Union[str, discord.Embed]:
        ctx: commands.Context = menu.ctx
        footer = f"Page {menu.current_page + 1}/{self.get_max_pages()}"
        if ctx is not None and await ctx.embed_requested():
            return discord.Embed(
                title=self.title, description=page, colour=await ctx.embed_colour()
            ).set_footer(text=footer)
        return f"**{self.title}**\n{page}\n\n{footer}"


class Menu(menus.MenuPages, inherit_buttons=False):  # type:ignore
    message: discord.Message

    def __init__(self, source: Page):
        super().__init__(
            source,
            timeout=30.0,
            delete_message_after=False,
            clear_reactions_after=True,
            message=None,
        )

    @property
    def source(self) -> Page:
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
        return arg
