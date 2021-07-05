# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import discord

from redbot.core import commands

from ..abc import TodoMixin
from ..utils import PositiveInt


__all__ = ["Deleting"]


class Deleting(TodoMixin):
    """Commands for deleting todos :D"""

    @commands.group()
    async def todo(self, *args):
        pass

    @todo.command(name="delete", aliases=["del", "remove"])
    async def todo_delete(self, ctx: commands.Context, *indexes: PositiveInt):
        """Delete a todo task

        This will remove it from your list entirely

        **Arguments**
            - `indexes` The indexes of the todos you want to delete
        """
        indexes = [i - 1 for i in indexes]
        data = await self.cache.get_user_data(ctx.author.id)
        todos = data.get("todos")
        if not todos:
            return await ctx.send(self._no_todo_message.format(prefix=ctx.clean_prefix))
        for index in indexes:
            try:
                del todos[index]
            except IndexError:
                pass
            except Exception as e:
                self.log.error("Exception in 'todo delete'", exc_info=e)
        amount = len(indexes)
        plural = "" if amount == 1 else "s"
        msg = f"Done. Deleted {amount} todo{plural}"
        await self.cache.set_user_item(ctx.author, "todos", todos)
        await ctx.send(msg)
