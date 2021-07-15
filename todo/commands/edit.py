# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from datetime import datetime

import discord
from redbot.core import commands

from ..abc import TodoMixin
from ..utils import PositiveInt, timestamp_format


class Edit(TodoMixin):
    """Mixin for editing todos"""

    @commands.group()
    async def todo(self, *args):
        pass

    @todo.command(name="edit")
    async def todo_edit(
        self, ctx: commands.Context, index: PositiveInt, *, new_todo: str
    ):
        """Edit a todo

        \u200b
        **Arguments**
            - `index` The index of the todo you wish to edit
            - `new_todo` The new task
        """
        todos = await self.cache.get_user_item(ctx.author, "todos")
        if not todos:
            return await ctx.send(self._no_todo_message.format(ctx.clean_prefix))
        act_index = index - 1
        try:
            old = todos.pop(act_index)["task"]
        except IndexError:
            return await ctx.send("You do not have a todo at that index!")
        todos.insert(act_index, new_todo)
        timestamp = await self.cache.get_user_setting(ctx.author, "use_timestamps")
        title = "Todo Edit"
        msg = f"**Old Todo**\n`{old}`\n**New Todo**\n`{new_todo}`" + (
            f"\n{timestamp_format()}" if timestamp else ""
        )
        kwargs = {"content": f"**{title}**\n\n{msg}"}
        if await self._embed_requested(ctx, ctx.author):
            embed = discord.Embed(
                title="Todo Edit",
                description=msg,
                colour=await ctx.embed_colour(),
                timestamp=datetime.utcnow(),
            )
            kwargs = {"embed": embed}
        await ctx.send(**kwargs)
        await self.cache.set_user_item(ctx.author, "todos", todos)
