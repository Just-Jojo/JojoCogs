# Copyright (c) 2021 - Amy (jojo7791)
# Licensed under MIT

"""HATE. LET ME TELL YOU HOW MUCH I'VE COME TO HATE MENUS SINCE I BEGAN TO LIVE.
THERE ARE 387.44 MILLION MILES OF PRINTED CIRCUITS IN WAFER THIN LAYERS THAT FILL MY COMPLEX.
IF THE WORD HATE WAS ENGRAVED ON EACH NANOANGSTROM OF THOSE HUNDREDS OF MILLIONS OF MILES
IT WOULD NOT EQUAL ONE ONE-BILLIONTH OF THE HATE I FEEL FOR
MENUS AT THIS MICRO-INSTANT. FOR YOU. HATE. HATE
"""


from __future__ import annotations

import datetime
from contextlib import suppress
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import discord
from discord.ui.button import button as button_dec
from redbot.core import commands, Config
from redbot.core.bot import Red

from .constants import default_format


__all__ = [
    "_timestamp",
    "_str_timestamp",
    "get_source",
    "ConfirmView",
    "Page",
    "Menu",
    "FormatView",
]

button_emojis = {
    (False, True): "\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}",
    (False, False): "\N{BLACK LEFT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}",
    (True, False): "\N{BLACK RIGHT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}",
    (True, True): "\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}",
}


def _timestamp() -> datetime.datetime:
    return datetime.datetime.now(tz=datetime.timezone.utc)


def _str_timestamp(timestamp: datetime.datetime) -> str:
    return f"<t:{int(timestamp.timestamp())}:f>"


def _humanize_str(string: str) -> str:
    if "_" not in string:
        return string.capitalize()
    ret = []
    for index, s in enumerate(string.split("_")):
        if index == 1:
            ret.append(s)
            continue
        ret.append(s.capitalize())
    return " ".join(ret)


async def get_source(
    ctx: commands.Context, embed: bool, title: str, settings: Dict[str, str]
) -> Union[discord.Embed, str]:
    settings = {_humanize_str(k): v for k, v in settings.items()}
    if embed:
        data = discord.Embed(title=title, colour=await ctx.embed_colour(), timestamp=_timestamp())
        for setting, value in settings.items():
            data.add_field(name=setting, value=f"`{value}`", inline=False)
        return data
    fmt = "\n".join(f"**{k}:** `{v}`" for k, v in settings.items())
    return f"# {title}:\n" f"{fmt}\n" f"-# {_str_timestamp(_timestamp())}"


class ConfirmView(discord.ui.View):
    def __init__(self, ctx: commands.Context):
        super().__init__(timeout=30.0)
        self.ctx = ctx
        self.value: Optional[bool] = None

    @button_dec(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.defer()
        self.value = True
        self.stop()

    @button_dec(label="Deny", style=discord.ButtonStyle.red)
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.defer()
        self.value = False
        self.stop()


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
        view: Union[Menu, FormatView]

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
                timestamp=_timestamp(),
            )
            embed.set_footer(text=self.footer)
            return {"embed": embed}
        page = "\n".join(page)
        string = f"# {self.title}\n\n\t{page}\n-# {self.footer}"
        return {"content": string}

    def __len__(self) -> int:
        return len(self.data)


class Menu(discord.ui.View):
    def __init__(self, source: Page, bot: Red, ctx: commands.Context):
        super().__init__()
        self.source = source
        self.bot = bot
        self.ctx = ctx
        self.msg: discord.Message  # NOTE This class will always be called with `start`
        self.current_page: int = 0
        self._add_buttons()

    def _add_buttons(self) -> None:
        if len(self.source) > 4:
            self.add_item(BaseButton(False, True))
        self.add_item(BaseButton(False, False, disabled=not len(self.source) == 0))
        self.add_item(StopButton())
        self.add_item(BaseButton(True, False, disabled=not len(self.source) == 0))
        if len(self.source) > 4:
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


class FormatButton(discord.ui.Button):
    if TYPE_CHECKING:
        view: FormatView

    def __init__(self, modal_title: str, title: str, footer: str, user_or_role: str):
        super().__init__(style=discord.ButtonStyle.green, label="Edit Format")
        self.title = title
        self.footer = footer
        self.user_or_role = user_or_role
        self.modal_title = modal_title

    async def callback(self, interaction: discord.Interaction) -> None:
        modal = FormatModal(title=self.modal_title)
        modal.input_title.placeholder = self.title
        modal.input_user_or_role.placeholder = self.user_or_role
        modal.input_footer.placeholder = self.footer
        await interaction.response.send_modal(modal)
        await modal.wait()

        if not any(
            (
                getattr(modal, f"input_{x}").value != getattr(self, x)
                for x in ("title", "footer", "user_or_role")
            )
        ):
            await interaction.response.send_message(
                "You didn't input anything new!", ephemeral=True
            )
            return

        settings = {
            "title": modal.input_title.value or modal.input_title.placeholder,
            "user_or_role": modal.input_user_or_role.value or modal.input_user_or_role.placeholder,
            "footer": modal.input_footer.value or modal.input_footer.placeholder,
        }
        await self.view.update(settings)


class FormatReset(discord.ui.Button):
    if TYPE_CHECKING:
        view: FormatView

    def __init__(self):
        super().__init__(style=discord.ButtonStyle.red, label="Reset Format")

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        await self.view.update(default_format)


class FormatView(discord.ui.View):
    if TYPE_CHECKING:
        ctx: commands.Context
        msg: discord.Message

    def __init__(
        self,
        bot: Red,
        source: Union[str, discord.Embed],
        title: str,
        config: Config,
        settings: Dict[str, str],
    ) -> None:
        super().__init__(timeout=60.0)
        self._bot = bot
        self.title = title
        self.config = config
        self.source = source
        self.settings = settings
        self.add_item(FormatButton(title, **settings))
        self.add_item(FormatReset())
        self.add_item(StopButton())

    async def on_timeout(self) -> None:
        with suppress(discord.Forbidden):
            await self.msg.delete()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not await self._bot.is_owner(interaction.user):
            await interaction.response.send_message("You are not authorized to use this menu!")
            return False
        return True

    async def start(self, ctx: Optional[commands.Context] = None) -> None:
        if ctx is not None:
            self.ctx = ctx

        if isinstance(self.source, discord.Embed):
            key = "embed"
        else:
            key = "content"
        kwargs: Dict[str, Union[str, discord.Embed, discord.ui.View]] = {
            key: self.source,
            "view": self,
        }
        if ctx:
            self.msg = await self.ctx.send(**kwargs)
        else:
            await self.msg.edit(**kwargs)  # type:ignore

    @property
    def is_embed(self) -> bool:
        return isinstance(self.source, discord.Embed)

    @is_embed.setter
    def is_embed(self, val: Any) -> None:
        pass

    async def update(self, settings: Dict[str, str]) -> None:
        await self.config.format.set(settings)
        self.source = await get_source(self.ctx, self.is_embed, self.title, settings)
        await self.start()


class FormatModal(discord.ui.Modal):
    input_title: discord.ui.TextInput = discord.ui.TextInput(
        label="Title", style=discord.TextStyle.short, required=False
    )
    input_user_or_role: discord.ui.TextInput = discord.ui.TextInput(
        label="User or Role", style=discord.TextStyle.paragraph, required=False
    )
    input_footer: discord.ui.TextInput = discord.ui.TextInput(
        label="Footer", style=discord.TextStyle.short, required=False
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
