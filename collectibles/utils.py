from typing import Any, Union

import discord
from jojo_utils import Menu
from redbot.core.commands import Context
from redbot.vendored.discord.ext.menus import ListPageSource  # type:ignore[attr-defined]


class Page(ListPageSource):
    def __init__(self, entries: list, title: str):
        self.title = title
        super().__init__(entries, per_page=1)

    def is_paginating(self) -> bool:
        return True

    async def format_page(self, menu: Menu, page: str) -> Union[str, discord.Embed]:
        ctx: Context = menu.ctx
        footer = f"Page {menu.current_page + 1}/{self.get_max_pages()}"
        if ctx is not None and await ctx.embed_requested():
            return discord.Embed(
                title=self.title, description=page, colour=await ctx.embed_colour()
            ).set_footer(text=footer)
        return f"**{self.title}**\n{page}\n{footer}"
