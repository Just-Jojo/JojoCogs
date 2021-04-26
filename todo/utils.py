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
from redbot.core.utils.chat_formatting import bold, box
from redbot.vendored.discord.ext import menus
from jojo_utils import Menu


__all__ = ["TodoPages", "TodoMenu", "todo_positive_int"]


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
        if not await ctx.embed_requested() or not self.use_embeds:
            return (
                f"{bold(self.title)}\n"
                + page
                + f"\nPage {menu.current_page + 1}/{self.get_max_pages()}"
            )

        embed = discord.Embed(title=self.title, colour=await ctx.embed_colour())
        embed.description = page
        embed.set_footer(text=f"Page {menu.current_page + 1}/{self.get_max_pages()}")
        return embed



def todo_positive_int(arg: str) -> int:
    """A slightly modified type hint for the "todo" group command"""
    try:
        ret = int(arg)
    except ValueError:
        raise commands.UserInputError()
    if ret <= 0:
        raise commands.BadArgument(f"'{arg}' is not a positive integer")
    return ret
