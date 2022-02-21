# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from __future__ import annotations

from contextlib import suppress
from typing import Union

import discord # type:ignore
from redbot.core import commands
from redbot.vendored.discord.ext.menus import ListPageSource # type:ignore

__all__ = ["CmdMenu", "CmdPages"]


class CmdPages(ListPageSource):
    def __init__(self, data: list):
        super().__init__(data, per_page=1)

    async def format_page(self, menu: CmdMenu, page: str) -> Union[discord.Embed, str]:
        ctx: commands.Context = menu.ctx
        footer = f"Page {menu.current_page + 1}/{self.get_max_pages()}"

        if await ctx.embed_requested():
            embed = discord.Embed(
                title="Cmd logging", description=page, colour=await ctx.embed_colour()
            ).set_footer(text=footer)
            return embed
        return f"**Cmd logging**\n{page}\n{footer}"


class CmdMenu(discord.ui.View):
    def __init__(self, source: CmdPages, ctx: commands.Context):
        self.ctx = ctx
        self.source = source
        super().__init__()
        self.response: discord.Message = None
        if m := self.source.get_max_pages():
            if m < 2:
                for n, c in enumerate(self.children):
                    if n == 2:
                        continue
                    c.disabled = True
            elif m < 4:
                self.children[0].disabled = True
                self.children[-1].disabled = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("You are not authorized to use this menu", ephemeral=True)
            return False
        return True

    async def _get_kwargs_from_page(self, page: str) -> dict:
        data = await discord.utils.maybe_coroutine(self.source.format_page, self, page)
        if isinstance(data, dict):
            return data
        elif isinstance(data, discord.Embed):
            return {"embed": data}
        return {"content": str(data)}

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

    async def show_page(self, page_number: int) -> None:
        page = await self.source.get_page(page_number)
        self.current_page = page_number
        kwargs = await self._get_kwargs_from_page(page)
        if not self.response:
            self.response = await self.ctx.send(**kwargs, view=self)
            return
        await self.response.edit(**kwargs, view=self)

    async def on_timeout(self):
        await self.response.edit(view=None)

    @discord.ui.button(style=discord.ButtonStyle.grey, emoji="\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}")
    async def go_to_first_page(self, button: discord.ui.Button, inter: discord.Interaction):
        await self.show_page(0)

    @discord.ui.button(style=discord.ButtonStyle.grey, emoji="\N{BLACK LEFT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}")
    async def go_to_previous_page(self, button: discord.ui.Button, inter: discord.Interaction):
        await self.show_checked_page(self.current_page - 1)

    @discord.ui.button(style=discord.ButtonStyle.red, emoji="\N{HEAVY MULTIPLICATION X}\N{VARIATION SELECTOR-16}")
    async def stop_pages(self, button: discord.ui.Button, inter: discord.Interaction):
        await self.response.delete()
        self.stop()

    @discord.ui.button(style=discord.ButtonStyle.grey, emoji="\N{BLACK RIGHT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}")
    async def go_to_next_page(self, button: discord.ui.Button, inter: discord.Interaction):
        await self.show_checked_page(self.current_page + 1)

    @discord.ui.button(style=discord.ButtonStyle.grey, emoji="\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}")
    async def go_to_last_page(self, button: discord.ui.Button, inter: discord.Interaction):
        await self.show_checked_page(-1)
