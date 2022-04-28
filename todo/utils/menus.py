# Copyright (c) 2022 - Jojo#7791
# Licensed under MIT

from __future__ import annotations

import datetime
import discord

from typing import List, Union, Dict, Optional, Any, TYPE_CHECKING
from abc import ABC

from contextlib import suppress
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box

from .api import TodoApi
from .general import timestamp_format, TimestampFormats


if TYPE_CHECKING:
    from ..core import ToDo


class TodoPages:
    def __init__(self, data: List[str], title: str, user_settings: Dict[str, Any]):
        self.data = data
        self.title = title
        self.max_pages = len(data)
        self.user_settings = user_settings

    async def format_page(self, page: str, view: _MenuMixin) -> Union[str, discord.Embed]:
        ctx: Optional[commands.Context] = view.ctx
        page = page if not self.user_settings["use_markdown"] else box(page, lang="md")
        footer = f"Page {view.current_page + 1}/{self.max_pages}"
        if self._embed_requested(ctx):
            emb = discord.Embed(
                title=self.title,
                description=page,
                colour=self.user_settings["colour"],
                timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
            )
            emb.set_footer(text=footer)
            return emb
        return f"**{self.title}**\n\n{page}\n{footer}"

    def _embed_requested(self, ctx: Optional[commands.Context]) -> bool:
        if not self.user_settings["use_embeds"]:
            return False
        if ctx and ctx.guild and not ctx.channel.permissions_for(ctx.me).embed_links:
            return False
        return True

    async def get_page(self, page_number: int) -> str:
        return self.data[page_number]


class _ButtonMixin(ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if TYPE_CHECKING:
            self.view: TodoMenu


class FirstPageButton(discord.ui.Button, _ButtonMixin):
    def __init__(self, disabled: bool = False):
        super().__init__(
            style=discord.ButtonStyle.grey,
            emoji="\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}",
            disabled=disabled,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.view.show_page(0, interaction)


class PreviousPageButton(discord.ui.Button, _ButtonMixin):
    def __init__(self, disabled: bool = False):
        super().__init__(
            style=discord.ButtonStyle.grey,
            emoji="\N{BLACK LEFT-POINTING TRIANGLE}",
            disabled=disabled,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.view.show_checked_page(self.view.current_page - 1, interaction)


class StopButton(discord.ui.Button, _ButtonMixin):
    def __init__(self, disabled: bool = False):
        super().__init__(
            style=discord.ButtonStyle.red,
            emoji="\N{HEAVY MULTIPLICATION X}\N{VARIATION SELECTOR-16}",
            disabled=disabled,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        self.view.stop()
        try:
            if self.view.msg:
                await self.view.msg.delete()
        except discord.Forbidden:
            pass


class NextPageButton(discord.ui.Button, _ButtonMixin):
    def __init__(self, disabled: bool = False):
        super().__init__(
            style=discord.ButtonStyle.grey,
            emoji="\N{BLACK RIGHT-POINTING TRIANGLE}",
            disabled=disabled,
        )

    async def callback(self, interaction: discord.Intertion) -> None:
        await self.view.show_checked_page(self.view.current_page + 1, interaction)


class LastPageButton(discord.ui.Button, _ButtonMixin):
    def __init__(self, disabled: bool = False):
        super().__init__(
            style=discord.ButtonStyle.grey,
            emoji="\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}",
            disabled=disabled,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.view.show_checked_page(-1, interaction)


class _MenuMixin(discord.ui.View, ABC):
    if TYPE_CHECKING:
        source: TodoPages
        ctx: Optional[commands.Context]
        msg: Optional[discord.Message]

    async def _get_kwargs_from_page(self, page: str) -> Dict[str, Any]:
        data = await self.source.format_page(page, self)
        if isinstance(data, discord.Embed):
            return {"embed": data}
        return {"content": str(data)}

    async def show_page(self, page_number: int) -> None:
        ...

    async def show_checked_page(self, page_number: int) -> None:
        ...

    def _add_buttons(self, *, stop_button: bool = True) -> None:
        """DRY"""

        single_disabled = self.source.max_pages == 1
        multi_disabled = self.source.max_pages < 5

        self.add_item(FirstPageButton(multi_disabled))
        self.add_item(PreviousPageButton(single_disabled))
        if stop_button:
            # Don't need a stop button for ephemeral menus
            self.add_item(StopButton())
        self.add_item(NextPageButton(single_disabled))
        self.add_item(LastPageButton(multi_disabled))

    def add_item(self, item: discord.ui.Item) -> _MenuMixin:
        if getattr(item, "disabled", False):
            return self
        return super().add_item(item)


class TodoMenu(_MenuMixin):
    def __init__(self, source: TodoPages, bot: Red, ctx: commands.Context):
        super().__init__()
        self.ctx = ctx
        self.bot: Red = bot
        self.source = source
        self.current_page = 0
        self.msg: discord.Message = None

        self._add_buttons()

    async def on_timeout(self) -> None:
        with suppress(discord.Forbidden):
            await self.msg.edit(view=None)

    async def start(self) -> None:
        page = await self.source.get_page(0)
        kwargs = await self._get_kwargs_from_page(page)
        self.msg = await self.ctx.send(**kwargs, view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "You are not authorized to use this menu",
                ephemeral=True,
            )
            return False
        return True

    async def show_page(self, page_number: int, interaction: discord.Interaction) -> None:
        page = await self.source.get_page(page_number)
        self.current_page = page_number
        kwargs = await self._get_kwargs_from_page(page)
        await self.msg.edit(**kwargs)

    async def show_checked_page(self, page_number: int, interaction: discord.Interaction) -> None:
        max_pages = self.source.max_pages
        try:
            if max_pages > page_number >= 0:
                await self.show_page(page_number)
            elif max_pages <= page_number:
                await self.show_page(0)
            else:
                await self.show_page(max_pages - 1)
        except IndexError:
            pass


class TodoPrivateMenu(_MenuMixin):
    def __init__(self, source: TodoPages, bot: Red):
        super().__init__()

        # This doesn't need as much setup as the other menu
        # as this is ephemeral, so no need for interaction_check,
        # and most of the stuff to block out other users
        self.ctx = None
        self.msg = None
        self.source = source
        self.current_page: int = 0
        self.interaction = None

        self._add_buttons(stop_button=False)

    async def show_checked_page(self, page_number: int, interaction: discord.Interaction) -> None:
        max_pages = self.source.max_pages # no need to do this but writing `self.source.` is tough!!!!
        try:
            if max_pages > page_number >= 0:
                await self.show_page(page_number, interaction)
            elif max_pages <= page_number:
                await self.show_page(0, interaction)
            else:
                await self.show_page(max_pages - 1, interaction)
        except IndexError:
            pass

    async def show_page(self, page_number: int, interaction: discord.Interaction) -> None:
        if not self.interaction:
            self.interaction = interaction
        page = await self.source.get_page(page_number)
        self.current_page = page_number
        kwargs = await self._get_kwargs_from_page(page)
        await interaction.response.edit_message(**kwargs)

    async def on_timeout(self):
        await self.interaction.response.edit_message(view=None)


class PrivateMenuStarter(discord.ui.View):
    """This is a helper class to get the ephemeral menu to work"""

    def __init__(self, ctx: commands.Context, source: TodoPages):
        super().__init__()
        self.ctx = ctx
        self.author_id = self.ctx.author.id
        self.source = source
        self.msg: discord.Message = None

    async def start(self) -> None:
        self.msg = await self.ctx.send("Click the \N{CHEQUERED FLAG} emoji to start your menu", view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.author_id != interaction.user.id:
            await interaction.response.send_message(
                "You are not authorized to use this menu",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(style=discord.ButtonStyle.green, emoji="\N{CHEQUERED FLAG}")
    async def start_menu(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        view = TodoPrivateMenu(self.source, self.ctx.bot)
        page = await self.source.get_page(0)
        kwargs = await view._get_kwargs_from_page(page)
        await interaction.response.send_message(**kwargs, ephemeral=True, view=view)

    @discord.ui.button(
        style=discord.ButtonStyle.red,
        emoji="\N{HEAVY MULTIPLICATION X}\N{VARIATION SELECTOR-16}",
    )
    async def stop_menu(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.stop()
        with suppress(discord.Forbidden):
            await self.msg.delete()


class PinButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            emoji="\N{PUSHPIN}",
            style=discord.ButtonStyle.green,
        )
        if TYPE_CHECKING:
            self.view: ViewTodo

    async def callback(self, interaction: discord.Interaction) -> None:
        data = self.view.todo
        data["pinned"] = status = not data["pinned"]
        yes_no = "Unpinned" if not status else "Pinned"
        await interaction.response.send_message(f"{yes_no} that todo", ephemeral=True)
        await self.view.update_todo(data)


class EditButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.grey,
            emoji="\N{MEMO}",
            label="Edit your todo",
        )

        if TYPE_CHECKING:
            self.view: ViewTodo

    async def callback(self, interaction: discord.Interaction) -> None:
        modal = EditModal(self, self.view.todo)
        await interaction.response.send_modal(modal)


class EditModal(discord.ui.Modal):
    def __init__(self, button: EditButton, todo: Union[str, dict]):
        super().__init__(
            title="Edit your todo",
        )
        self.todo = todo
        self.text = discord.ui.TextInput(
            style=discord.TextStyle.long,
            label="Edit your todo",
            placeholder="Write a new todo",
            default=x if not isinstance((x := self.todo), dict) else self.todo["task"],
            required=True,
            min_length=1,
            max_length=2000
        )
        self.add_item(self.text)
        self.button = button

    async def on_submit(self, interaction: discord.Interaction) -> None:
        new_todo = self.text.value
        if isinstance(self.todo, dict):
            self.todo["task"] = new_todo
        else:
            self.todo = new_todo
        await interaction.response.send_message("Updated your todo", ephemeral=True)
        await self.button.view.update_todo(self.todo)


class DeleteButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.red,
            emoji="\N{WASTEBASKET}",
        )

        if TYPE_CHECKING:
            self.view: ViewTodo

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.view._delete_todo()


class ViewTodo(discord.ui.View):
    def __init__(self, ctx: commands.Context, todo: Union[str, dict], index: int, **settings):
        super().__init__()
        self.ctx = ctx
        self.cog: ToDo = ctx.cog
        self.cache: TodoApi = self.cog.cache
        self.todo = todo
        self.completed = isinstance(todo, str)
        self.index = index
        self.settings = settings
        self.msg: discord.Message = None

        self._make_buttons()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            msg = "You are not authorized to use this menu"
            if interaction.user.id == 204027971516891136:
                msg = "Go away slime fr"
            await interaction.response.send_message(msg, ephemeral=True)
            return False
        return True

    async def start(self) -> None:
        data = await self._format_page()
        self.msg = await self.ctx.send(**data, view=self)

    def _make_buttons(self):
        self.add_item(EditButton())
        if not self.completed:
            self.add_item(PinButton())
        self.add_item(DeleteButton())
        self.add_item(StopButton(False))

    async def _format_page(self) -> Dict[str, Any]:
        title = "Completed Todo" if self.completed else "Todo"
        title = f"{self.ctx.author.name} {title} #{self.index}"
        task = self.todo if self.completed else self.todo["task"]

        if not self.completed and (ts := self.todo.get("timestamp")):
            task = f"{task} - Added {timestamp_format(ts, ts_format=TimestampFormats.RELATIVE_TIME)}"

        if await self.cog._embed_requested(self.ctx, self.ctx.author):
            embed = discord.Embed(
                title=title,
                description=task,
                colour=await self.cog._embed_colour(self.ctx),
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            if not self.completed:
                embed.add_field(name="Pinned", value=self.todo["pinned"])
            return {"embed": embed}
        ret = f"**{title}**\n\n{task}"
        if not self.completed:
            ret += f"\n\n**Pinned:** {self.todo['pinned']}"
        if self.settings.get("use_timestamps"):
            ret += f"\n{timestamp_format()}"
        return {"content": ret}

    async def update_todo(self, data: Union[str, dict]) -> None:
        self.todo = data
        await self.msg.edit(**await self._format_page())

        key = "completed" if self.completed else "todos"
        todos: list = await self.cache.get_user_item(self.ctx.author, key)
        todos[self.index - 1] = data
        await self.cache.set_user_item(self.ctx.author, key, todos, fix=False)

    async def _delete_todo(self) -> None:
        self.stop()
        await self.msg.edit(content="Deleted that todo", embed=None, view=None)
        key = "completed" if self.completed else "todos"
        data = await self.cache.get_user_item(self.ctx.author, key)
        del data[self.index - 1]
        await self.cache.set_user_item(self.ctx.author, key, data)
