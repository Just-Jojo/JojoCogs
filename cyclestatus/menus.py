# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from typing import List, Union

import discord
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box
from redbot.vendored.discord.ext import menus

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
