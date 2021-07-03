# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import asyncio
import discord

from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box
from redbot.core.utils.predicates import MessagePredicate
from redbot.vendored.discord.ext import menus  # type:ignore
from datetime import datetime
from typing import Union, Dict
import contextlib

from .cache import Cache
from .general import timestamp_format

import logging


__all__ = ["TodoPage", "TodoMenu", "ViewTodo"]
log = logging.getLogger("red.JojoCogs.todo.menus")

class TodoPage(menus.ListPageSource):
    def __init__(self, items: list, **settings):
        super().__init__(items, per_page=1)
        self.settings = settings

    async def format_page(self, menu: menus.MenuPages, page: str):
        ctx: commands.Context = menu.ctx
        bot: Red = menu.bot

        if self.settings["use_markdown"]:
            page = box(page, "md")
        title = f"{ctx.author.name}'s todos"
        footer = f"Page {menu.current_page + 1}/{self.get_max_pages()}"
        if await ctx.embed_requested() and self.settings["use_embeds"]:
            embed = discord.Embed(
                title=title,
                colour=self.settings["colour"] or await ctx.embed_colour(),
                description=page,
                timestamp=datetime.utcnow(),
            )
            embed.set_footer(text=footer)
            return embed
        msg = f"**{title}**\n\n{page}\n{footer}"
        if self.settings["use_timestamps"]:
            msg += f"\n{timestamp_format()}"
        return msg


class TodoMenu(menus.MenuPages, inherit_buttons=False):  # type:ignore
    message: discord.Message

    def __init__(self, source: TodoPage):
        super().__init__(
            source,
            timeout=30.0,
            delete_message_after=False,
            clear_reactions_after=True,
            message=None,
        )

    @property
    def source(self) -> TodoPage:
        return self._source

    async def send_initial_message(self, ctx, channel):
        page = await self.source.get_page(0)
        kwargs = await self._get_kwargs_from_page(page)
        log.debug(kwargs)
        return await channel.send(**kwargs)

    async def show_checked_page(self, page_number: int):
        max_pages = self.source.get_max_pages()
        try:
            if max_pages is None or max_pages > page_number >= 0:
                await self.show_page(page_number)
            elif page_number >= max_pages:
                await self.show_page(0)
            elif page_number < 0:
                await self.show_page(max_pages - 1)
        except IndexError:
            pass

    def _skip_triangle_buttons(self):
        max_pages = self.source.get_max_pages()
        if max_pages is None:
            return True
        return max_pages == 1

    def _skip_double_triangle_buttons(self):
        max_pages = self.source.get_max_pages()
        if max_pages is None:
            return True
        return max_pages <= 5

    @menus.button(
        "\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}\N{VARIATION SELECTOR-16}",
        position=menus.First(0),
        skip_if=_skip_double_triangle_buttons,
    )
    async def go_to_first_page(self, payload):
        await self.show_page(0)

    @menus.button(
        "\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}\N{VARIATION SELECTOR-16}",
        position=menus.Last(1),
        skip_if=_skip_double_triangle_buttons,
    )
    async def go_to_last_page(self, payload):
        await self.show_page(self.source.get_max_pages() - 1)

    @menus.button(
        "\N{LEFTWARDS BLACK ARROW}\N{VARIATION SELECTOR-16}",
        position=menus.First(1),
        skip_if=_skip_triangle_buttons,
    )
    async def go_to_previous_page(self, payload):
        await self.show_checked_page(self.current_page - 1)

    @menus.button(
        "\N{BLACK RIGHTWARDS ARROW}\N{VARIATION SELECTOR-16}",
        position=menus.Last(0),
        skip_if=_skip_triangle_buttons,
    )
    async def go_to_next_page(self, payload):
        await self.show_checked_page(self.current_page + 1)

    @menus.button("\N{CROSS MARK}")
    async def stop_pages(self, payload):
        self.stop()
        with contextlib.suppress(discord.Forbidden):
            await self.message.delete()


class ViewTodo(menus.Menu):
    ctx: commands.Context

    def __init__(self, index: int, cache: Cache, todo_data: Union[dict, str], *, completed: bool = False, **settings):
        self.index = index
        self.cache = cache
        self.data = todo_data
        self.settings = settings
        self.completed = completed
        if not self.completed and not isinstance(self.data, dict):
            raise TypeError(f"'data' must be type dict not {self.data.__class__!r}")
        super().__init__(
            timeout=30.0,
            delete_message_after=False,
            clear_reactions_after=True,
            message=None,
        )

    async def send_initial_message(self, ctx: commands.Context, channel: discord.TextChannel):
        return await ctx.send(**await self._format_page())

    def _skip_if_completed(self):
        return self.completed

    async def _format_page(self) -> Dict[str, Union[str, discord.Embed]]:
        todo = "Completed Todo" if self.completed else "Todo"
        title = f"{self.ctx.author.name} {todo} #{self.index}"
        task = self.data if self.completed else self.data["task"] # type:ignore
        if await self.ctx.embed_requested() and self.settings.get("use_embeds"):
            embed = discord.Embed(
                title=title,
                colour=self.settings["colour"] or await self.ctx.embed_colour(),
                description=task,
                timestamp=datetime.utcnow(),
            )
            if not self.completed:
                embed.add_field(name="Pinned", value=self.data["pinned"]) # type:ignore
            return {"embed": embed}
        ret = f"**{title}**\n\n{task}"
        if not self.completed:
            ret += f"\n\nPinned: {self.data['pinned']}" # type:ignore
        if self.settings.get("use_timestamps"):
            ret += f"\n{timestamp_format()}"
        return {"content": ret}

    @menus.button("\N{PUSHPIN}", skip_if=_skip_if_completed)
    async def pin_todo(self, payload):
        if self.completed:
            return # Skip
        self.data["pinned"] = not self.data["pinned"]
        data = await self.cache.get_user_data(self.ctx.author.id)
        data["todos"][self.index - 1] = self.data
        await self.cache.set_user_data(data)
        await self.update_message()

    @menus.button("\N{WASTEBASKET}\N{VARIATION SELECTOR-16}")
    async def delete_todo(self, payload):
        msg = await self.ctx.send("Would you like to remove this todo? (y/N)")
        pred = MessagePredicate.yes_or_no(self.ctx)
        try:
            await self.bot.wait_for("message", check=pred)
        except asyncio.TimeoutError:
            pass
        with contextlib.suppress(discord.NotFound):
            await msg.delete()
        if not pred.result:
            return await self.ctx.send("Okay, I will not delete that todo.", delete_after=5.0)
        self.stop()
        await self.update_message(message="Deleted todo!")
        key = "completed" if self.completed else "todos"
        data = await self.cache.get_user_item(self.ctx.author.id, key)
        del data[self.index - 1]
        await self.cache.set_user_item(self.ctx.author, key, data)

    @menus.button("\N{WHITE HEAVY CHECK MARK}", skip_if=_skip_if_completed)
    async def completed_todo(self, payload):
        if self.completed:
            return # Skip
        msg = await self.ctx.send("Would you like to complete this todo? (y/N)")
        pred = MessagePredicate.yes_or_no(self.ctx)
        try:
            await self.bot.wait_for("message", check=pred)
        except asyncio.TimeoutError:
            pass
        with contextlib.suppress(discord.NotFound):
            await msg.delete()
        if not pred.result:
            return await self.ctx.send("Okay, I will not complete that todo.", delete_after=5.0)
        self.completed = True
        self.data = self.data["task"]
        await self.update_message()
        data = await self.cache.get_user_data(self._author_id)
        del data["todos"][self.index - 1]
        data["completed"].append(self.data)
        await self.cache.set_user_data(self._author_id, data)

    @menus.button("\N{CROSS MARK}")
    async def stop_pages(self, payload):
        self.stop()
        with contextlib.suppress(discord.NotFound):
            await self.message.delete()

    async def update_message(self, message: str = None):
        if message:
            if await self.ctx.embed_requested() and self.settings.get("use_embeds"):
                embed = discord.Embed(
                    title=f"{self.ctx.author.name} Todo #{self.index}",
                    colour=self.settings["colour"] or await self.ctx.embed_colour(),
                    description=message,
                    timestamp=datetime.utcnow(),
                )
                kwargs = {"embed": embed}
            else:
                if self.settings.get("use_timestamps"):
                    message += f"\n{timestamp_format()}"
                kwargs = {"content": message}
        else:
            kwargs = await self._format_page()
        await self.message.edit(**kwargs)
