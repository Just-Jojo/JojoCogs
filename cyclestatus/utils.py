# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from __future__ import annotations

from typing import List, Union, TYPE_CHECKING

import discord
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box

__all__ = ["Pages", "Menu", "PositiveInt"]


class Pages:
    """Custom list page source for the menu"""

    def __init__(self, entries: List[str], title: str):
        self.entries = entries
        self._title = title

    def get_max_pages(self) -> int:
        return len(self.entries)

    async def get_page(self, page_number: int) -> str:
        return self.entries[page_number]

    async def format_page(self, menu: Menu, page: str) -> Union[discord.Embed, str]:
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


class Menu(discord.ui.View):
    def __init__(self, source: Pages, ctx: commands.Context):
        self.source = source
        self.ctx = ctx
        super().__init__()
        self.response: discord.Message = None
        self.current_page: int = 0
        if m := self.source.get_max_pages():
            if m < 2:
                for n, c in enumerate(self.children):
                    if n == 2: continue
                    c.disabled = True
            elif m < 5:
                [setattr(self.children[x], "disabled", True) for x in (0, -1)] # type:ignore

    async def _get_kwargs_from_page(self, page: str) -> dict:
        data = await self.source.format_page(self, page)
        if isinstance(data, dict):
            return data
        elif isinstance(data, discord.Embed):
            return {"embed": data}
        return {"content": str(data)}

    async def show_checked_page(self, page_number: int) -> None:
        max_pages = self.source.get_max_pages()
        try:
            if not max_pages or max_pages > page_number >= 0:
                await self.show_page(page_number)
            elif max_pages <= page_number:
                await self.show_page(0)
            elif page_number < 0:
                await self.show_page(max_pages - 1)
        except IndexError:
            pass

    async def show_page(self, page_number: int):
        page = await self.source.get_page(page_number)
        self.current_page = page_number
        kwargs = await self._get_kwargs_from_page(page)
        if not self.response:
            self.response = await self.ctx.send(**kwargs, view=self)
            return
        await self.response.edit(**kwargs)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("You are not authorized to use this menu", ephemeral=True)
            return False
        return True

    @discord.ui.button(
        style=discord.ButtonStyle.grey,
        emoji="\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}"
    )
    async def go_to_first_page(self, button: discord.ui.Button, inter: discord.Interaction):
        await self.show_page(0)

    @discord.ui.button(
        style=discord.ButtonStyle.grey,
        emoji="\N{BLACK LEFT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}",
    )
    async def go_to_previous_page(self, button: discord.ui.Button, inter: discord.Interaction):
        await self.show_checked_page(self.current_page - 1)

    @discord.ui.button(
        style=discord.ButtonStyle.red,
        emoji="\N{HEAVY MULTIPLICATION X}\N{VARIATION SELECTOR-16}",
    )
    async def stop_pages(self, button: discord.ui.Button, inter: discord.Interaction):
        await self.response.delete()
        self.stop()

    @discord.ui.button(
        style=discord.ButtonStyle.grey,
        emoji="\N{BLACK RIGHT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}",
    )
    async def go_to_next_page(self, button: discord.ui.Button, inter: discord.Interaction):
        await self.show_checked_page(self.current_page + 1)

    @discord.ui.button(
        style=discord.ButtonStyle.grey,
        emoji="\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}",
    )
    async def go_to_last_page(self, button: discord.ui.Button, inter: discord.Interaction):
        await self.show_checked_page(-1)


if TYPE_CHECKING:
    PositiveInt = int
else:

    class PositiveInt(commands.Converter):
        async def convert(self, ctx: commands.Context, arg: str) -> int:
            try:
                ret = int(arg)
            except ValueError:
                raise commands.BadArgument("That was not an integer")
            if ret <= 0:
                raise commands.BadArgument(f"'{arg}' is not a positive integer")
            return ret
