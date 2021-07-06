# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import asyncio
from contextlib import suppress

import discord
from redbot.core import commands
from redbot.core.utils.predicates import MessagePredicate

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

    @todo.command(name="deleteall", aliases=["delall", "removeall"])
    async def todo_delete_all(self, ctx: commands.Context, confirm: bool = False):
        """Remove all of your todos


        \u200b
        **Arguments**
            - `confirm` Skips the confirmation check. Defaults to False
        """
        if not confirm:
            msg = await ctx.send(
                "Are you sure you would like to remove all of your todos? (y/N)"
            )
            pred = MessagePredicate.yes_or_no(ctx)
            try:
                umsg = await self.bot.wait_for("message", check=pred)
            except asyncio.TimeoutError:
                pass
            with suppress(discord.NotFound, discord.Forbidden):
                await msg.delete()
                await umsg.add_reaction("\N{WHITE HEAVY CHECK MARK}")
            if not pred.result:
                return await ctx.send("Okay. I will not remove your todos.")
        await self.cache.set_user_item(ctx.author, "todos", [])
        await ctx.send("Done. Removed all of your todos.")
