# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

# type:ignore[attr-defined]

from datetime import datetime
from typing import Optional, Union

import discord
from jojo_utils import Menu
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import bold, box
from redbot.vendored.discord.ext import menus #type:ignore[attr-defined]

__all__ = ["TodoPages", "TodoMenu", "todo_positive_int"]


class TodoPages(menus.ListPageSource):
    def __init__(self, data, use_md: bool, use_embeds: bool, title: str, colour: Optional[Union[str, int]]):
        super().__init__(data, per_page=1)
        self.md = use_md
        self.use_embeds = use_embeds
        self.title = title
        self.colour = colour

    def is_paginating(self):
        return True

    async def format_page(self, menu, page):
        bot: Red = menu.bot
        ctx: commands.Context = menu.ctx
        if self.md:
            page = box(page, "md")
        if not await ctx.embed_requested() or not self.use_embeds:
            return (
                f"{bold(self.title)}\n"
                + page
                + f"\nPage {menu.current_page + 1}/{self.get_max_pages()}"
            )

        embed = discord.Embed(title=self.title, colour=self.colour or await ctx.embed_colour())
        embed.description = page
        embed.set_footer(text=f"Page {menu.current_page + 1}/{self.get_max_pages()}")
        embed.timestamp = datetime.utcnow()
        return embed


def todo_positive_int(arg: str) -> Optional[int]:
    """A slightly modified type hint for the "todo" group command"""
    try:
        ret = int(arg)
    except ValueError:
        raise commands.UserInputError()
    if ret <= 0:
        raise commands.BadArgument(f"'{arg}' is not a positive integer")
    return ret
