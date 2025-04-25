# Copyright (c) 2021 - Amy (jojo7791)
# Licensed under MIT

# I HATE MENUS
# I HATE MENUS
# I HATE MENUS
# I HATE MENUS
# I HATE MENUS
# I HATE MENUS
# I HATE MENUS
# I HATE MENUS
# I HATE MENUS
# I HATE MENUS


from __future__ import annotations

import discord
from contextlib import suppress
from typing import List, TYPE_CHECKING

from redbot.core import commands
from redbot.core.bot import Red


__all__ = ["Page", "Menu"]

button_emojis = {
    (False, True): "\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}",
    (False, False): "\N{BLACK LEFT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}",
    (True, False): "\N{BLACK RIGHT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}",
    (True, True): "\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}",
}


class BaseButton(discord.ui.Button):
    def __init__(self, forward: bool, skip: bool, disabled: bool = False):
        super().__init__(
            style=discord.ButtonStyle.grey, emoji=button_emojis[(forward, skip)], disabled=disabled
        )
        self.forward = forward
        self.skip = skip
        if TYPE_CHECKING:
            self.view: Menu

    async def callback(self, interaction: discord.Interaction) -> None:
        if self.skip:
            page_num = 1 if self.forward else -1
        else:
            current_num = self.view.current_page
            page_num = current_num + 1 if self.forward else current_num - 1
        await self.view.show_checked_page(page_num)


class StopButton(discord.ui.Button):
    if TYPE_CHECKING:
        view: Menu

    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.red,
            emoji="\N{HEAVY MULTIPLICATION X}\N{VARIATION SELECTOR-16}",
            disabled=False,
        )

    async def callback(self, inter: discord.Interaction) -> None:
        self.view.stop()
        with suppress(discord.Forbidden):
            if self.view.msg:
                await self.view.msg.delete()


class Page:
    def __init__(self, ctx: commands.Context, data: List[str], *, title: str, footer: str):
        self.ctx = ctx
        self.data = data
        self.title = title
        self.footer = footer
        self.max_len = len(self.data)

    async def format_page(self, page: str) -> dict:
        if await self.ctx.embed_requested():
            embed = discord.Embed(
                title=self.title,
                description=page,
                colour=await self.ctx.embed_colour(),
            )
            embed.set_footer(text=self.footer)
            return {"embed": embed}
        page = "\n".join(page)
        string = f"# {self.title}\n\n{page}\n-# {self.footer}"
        return {"content": string}


class Menu(discord.ui.View):
    def __init__(self, source: Page, bot: Red, ctx: commands.Context):
        super().__init__()
        self.source = source
        self.bot = bot
        self.ctx = ctx
        self.msg: discord.Message  # NOTE This class will always be called with `start`
        self.current_page: int = 0

    def _add_buttons(self) -> None:
        self.add_item(BaseButton(False, True))
        self.add_item(BaseButton(False, False))
        self.add_item(StopButton())
        self.add_item(BaseButton(True, False))
        self.add_item(BaseButton(True, True))

    @classmethod
    async def start(cls, source: Page, ctx: commands.Context) -> None:
        self = cls(source, ctx.bot, ctx)
        page = self.source.data[0]
        kwargs = await self.source.format_page(page)
        self.msg = await ctx.send(view=self, **kwargs)

    async def show_page(self, page_num: int) -> None:
        page = self.source.data[page_num]
        self.current_page = page_num
        kwargs = await self.source.format_page(page)
        await self.msg.edit(view=self, **kwargs)

    async def show_checked_page(self, page_number: int) -> None:
        max_len = self.source.max_len
        try:
            if max_len > page_number >= 0:
                await self.show_page(page_number)
            elif max_len <= page_number:
                await self.show_page(0)
            else:
                await self.show_page(max_len - 1)
        except IndexError:
            pass

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "You are not authorized to use this menu.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self) -> None:
        with suppress(discord.Forbidden):
            await self.msg.delete()
