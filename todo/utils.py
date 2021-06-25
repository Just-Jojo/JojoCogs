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
from redbot.vendored.discord.ext import menus  # type:ignore[attr-defined]
from jojo_utils import Menu
from enum import Enum

__all__ = ["PresetConverter", "TodoPages", "todo_positive_int"]


class TodoPages(menus.ListPageSource):
    def __init__(
        self,
        data,
        use_md: bool,
        use_embeds: bool,
        title: str,
        colour: Optional[Union[str, int]],
    ):
        super().__init__(data, per_page=1)
        self.md = use_md
        self.use_embeds = use_embeds
        self.title = title
        self.colour = colour

    def is_paginating(self):
        return True

    async def format_page(self, menu: Menu, page: str):
        bot: Red = menu.bot
        ctx: commands.Context = menu.ctx
        if self.md:
            page = box(page, "md")
        footer = f"Page {menu.current_page + 1}/{self.get_max_pages()}"
        if not await ctx.embed_requested() or not self.use_embeds:
            return (
                f"{bold(self.title)}\n"
                f"{page}\n"
                f"{footer}\n<t:{round(datetime.now().timestamp())}>"
            )

        embed = discord.Embed(
            title=self.title, colour=self.colour or await ctx.embed_colour(),
            description=page,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"Page {menu.current_page + 1}/{self.get_max_pages()}")
        return embed


class Presets(Enum):
    minimal = {
        "use_md": False,
        "use_embeds": False,
        "colour": None,
        "autosort": False,
        "combined_lists": False,
        "detailed_pop": False,
    }
    fancy = {
        "use_md": True,
        "use_embeds": True,
        "colour": None,
        "autosort": True,
        "combined_lists": True,
        "detailed_pop": True,
    }


class PresetConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> str:
        if argument.lower() == "minimal":
            ret = Presets.minimal
        elif argument.lower() == "fancy":
            ret = Presets.fancy
        else:
            raise commands.BadArgument('Preset must be either "minimal" or "fancy"')
        return ret.value


def todo_positive_int(arg: str) -> Optional[int]:
    """A slightly modified type hint for the "todo" group command"""
    try:
        ret = int(arg)
    except ValueError:
        raise commands.UserInputError()
    if ret <= 0:
        raise commands.BadArgument(f"'{arg}' is not a positive integer")
    return ret
