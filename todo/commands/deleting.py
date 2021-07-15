# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import asyncio
from contextlib import suppress
from typing import Optional

import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import pagify
from redbot.core.utils.predicates import MessagePredicate

from ..abc import TodoMixin
from ..utils import PositiveInt

__all__ = ["Deleting"]


class Deleting(TodoMixin):
    """Commands for deleting todos :D"""

    @commands.group()
    async def todo(self, *args):
        pass

    @todo.command(name="delete", aliases=["del", "remove"], require_var_positional=True)
    async def todo_delete(self, ctx: commands.Context, *indexes: PositiveInt):
        """Delete a todo task

        This will remove it from your list entirely

        **Arguments**
            - `indexes` The indexes of the todos you want to delete
        """
        indexes = [i - 1 for i in indexes]
        indexes.sort(reverse=True)
        data = await self.cache.get_user_data(ctx.author.id)
        todos = data.get("todos")
        if not todos:
            return await ctx.send(self._no_todo_message.format(prefix=ctx.clean_prefix))
        removed = []
        for index in indexes:
            try:
                removed.append(todos.pop(index)["task"])
            except IndexError:
                pass
            except Exception as e:
                self.log.error("Exception in 'todo delete'", exc_info=e)
        amount = len(indexes)
        if amount == 0:
            return await ctx.send(
                "Hm, somehow I wasn't able to delete those todos. Please make sure that the inputted indexes are valid"
            )
        plural = "" if amount == 1 else "s"
        msg = f"Done. Deleted {amount} todo{plural}"
        if data["user_settings"]["extra_details"]:
            msg += "\n" + "\n".join(f"`{task}`" for task in removed)
        task: Optional[asyncio.Task] = None
        if len(msg) <= 2000:
            await ctx.send(msg)
        else:
            task = self.bot.loop.create_task(ctx.send_interactive(pagify(msg)))
        await self.cache.set_user_item(ctx.author, "todos", todos)
        if task is not None and not task.done():
            await task

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
