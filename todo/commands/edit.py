# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from datetime import datetime

import discord
from redbot.core import commands
from tabulate import tabulate

from ..abc import TodoMixin
from ..utils import PositiveInt

__all__ = ["Edit"]


class Edit(TodoMixin):
    """Edit todos!"""

    @commands.group()
    async def todo(self, *args): ...

    @todo.command(name="edit")
    async def todo_edit(self, ctx: commands.Context, index: PositiveInt, *, new_todo: str):
        """Edit a todo!"""

        actual_index = index - 1
        if not (todos := await self.cache.get_user_item(ctx.author, "todos")):
            return await ctx.send(self._no_todo_message.format(prefix=ctx.clean_prefix))

        try:
            todo = todos.pop(actual_index)
        except IndexError:
            return await ctx.send("I could not find a todo at that index")
        old_todo = todo["task"]
        todo["task"] = new_todo
        todos.insert(actual_index, todo)

        kwargs = {"content": (tabulate([[old_todo, new_todo]], headers=("Old todo", "New todo")))}
        if await self._embed_requested(ctx, ctx.author):
            embed = discord.Embed(
                title="Todo Edit",
                colour=await self._embed_colour(ctx),
                timestamp=datetime.utcnow(),
            )
            [
                embed.add_field(name=key, value=value, inline=True)
                for key, value in {"Old todo": old_todo, "New todo": new_todo}.items()
            ]
            kwargs = {"embed": embed}
        await ctx.send(**kwargs)
        await self.cache.set_user_item(ctx.author, "todos", todos)
