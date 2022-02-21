# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from __future__ import annotations

from contextlib import suppress
from typing import Union

import discord  # type:ignore
from redbot.core import commands
from redbot.core.utils.chat_formatting import box
from redbot.vendored.discord.ext import menus  # type:ignore


class Page(menus.ListPageSource):
    def __init__(self, data: list, title: str):
        super().__init__(data, per_page=1)
        self.title = title

    async def format_page(self, menu: Menu, page: str) -> Union[discord.Embed, str]:
        ctx: commands.Context = menu.ctx
        footer = f"Page {menu.current_page + 1}/{self.get_max_pages()}"
        ret = f"**{self.title}**\n{box(page, 'md')}\n{footer}"
        if await ctx.embed_requested():
            ret = discord.Embed(
                title=self.title,
                description=box(page, "md"),
                colour=await ctx.embed_colour(),
            ).set_footer(text=footer)
        return ret


class Menu(discord.ui.View):
    def __init__(self, source: Page, ctx: commands.Context):
        self.source = source
        self.ctx = ctx
        super().__init__()
        self.current_page: int = 0
        self.response: discord.Message = None
        if (m := self.source.get_max_pages()):
            if m < 2:
                for child in self.children:
                    if child.style.value == discord.ButtonStyle.red.value:
                        continue
                    child.disabled = True
            elif m < 5:
                self.children[0].disabled = True
                self.children[-1].disabled = True

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.response.edit(view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("You are not authorized to use this menu", ephemeral=True)
            return False
        return True

    async def show_checked_page(self, page_number: int) -> None:
        max_pages = self.source.get_max_pages()
        try:
            if max_pages is None or max_pages > page_number >= 0:
                await self.show_page(page_number)
            elif max_pages <= page_number:
                await self.show_page(0)
            elif 0 > page_number:
                await self.show_page(max_pages - 1)
        except IndexError:
            pass

    async def _get_kwargs_from_page(self, page: str) -> dict:
        data = await discord.utils.maybe_coroutine(self.source.format_page, self, page)
        if isinstance(data, dict):
            return data
        elif isinstance(data, discord.Embed):
            return {"embed": data}
        return {"content": str(data)}

    async def show_page(self, page_number: int) -> None:
        page = await self.source.get_page(page_number)
        self.current_page = page_number
        kwargs = await self._get_kwargs_from_page(page)
        if not self.response:
            self.response = await self.ctx.send(**kwargs, view=self)
            return
        await self.response.edit(**kwargs, view=self)

    @discord.ui.button(
        style=discord.ButtonStyle.grey,
        emoji="\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}",
    )
    async def go_to_first_page(self, button, interaction: discord.Interaction):
        await self.show_checked_page(0)

    @discord.ui.button(
        style=discord.ButtonStyle.grey,
        emoji="\N{BLACK LEFT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}",
    )
    async def go_to_prevoius_page(self, button, interaction: discord.Interaction):
        await self.show_checked_page(self.current_page - 1)

    @discord.ui.button(
        style=discord.ButtonStyle.red,
        emoji="\N{HEAVY MULTIPLICATION X}\N{VARIATION SELECTOR-16}",
    )
    async def stop_pages(self, button, interaction: discord.Interaction):
        self.stop()
        await self.response.delete()

    @discord.ui.button(
        style=discord.ButtonStyle.grey,
        emoji="\N{BLACK RIGHT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}",
    )
    async def go_to_next_page(self, button, interaction: discord.Interaction):
        await self.show_checked_page(self.current_page + 1)

    @discord.ui.button(
        style=discord.ButtonStyle.grey,
        emoji="\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}",
    )
    async def go_to_last_page(self, button, interaction: discord.Interaction):
        await self.show_page(self.source.get_max_pages() - 1)
