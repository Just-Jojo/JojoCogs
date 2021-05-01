# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import asyncio

import discord
from jojo_utils import positive_int
from redbot.core import commands
from redbot.core.utils.predicates import MessagePredicate
from redbot.core.utils.chat_formatting import pagify

from .abc import ToDoMixin


class Deleting(ToDoMixin):
    """Commands having to do with deletion of todos"""

    # Since this is a mixin I have to define the command groups here
    # they'll be overridden by the main class though

    @commands.group()
    async def todo(self, ctx):
        pass

    @todo.group()
    async def complete(self, ctx, *indexes: positive_int):
        pass

    @todo.command(require_var_positional=True, aliases=["del", "rm", "delete"])
    async def remove(self, ctx, *indexes: positive_int):
        """Delete todos!"""
        if not await self.config.user(ctx.author).todos():
            return await ctx.send(self._no_todo_message.format(prefix=ctx.clean_prefix))
        async with ctx.typing():
            async with self.config.user(ctx.author).todos() as todos:
                indexes = [x - 1 for x in indexes]
                indexes.sort(reverse=True)
                fails, failed, comp, completed = 0, [], 0, []
                for index in indexes:
                    try:
                        completed.append(f"`{todos.pop(index)}`")
                    except IndexError:
                        fails += 1
                        failed.append(f"`{index}`")
                    else:
                        comp += 1
        msg = "Done."
        details = await self.config.user(ctx.author).detailed_pop()
        if comp:
            plural = "" if comp == 1 else "s"
            msg += f"\nRemoved {comp} todo{plural}"
            if details:
                msg += "\n" + "\n".join(completed)
        if fails:
            plural = "" if fails else "s"
            msg += f"\nFailed to removed {fails} todo{plural} {self._failure_explanation}"
            if details:
                msg += "\n" + "\n".join(failed)
        await self._maybe_autosort(ctx)
        if len(msg) > 2000:
            await ctx.send_interactive(pagify(msg))
        else:
            await ctx.send(msg)

    @todo.command(aliases=["delall"])
    async def removeall(self, ctx):
        """Remove all of your todos"""
        await ctx.send(
            "WARNING, this will remove **ALL** of your todos. Would you like to remove your todos? (y/n)"
        )
        pred = MessagePredicate.yes_or_no(ctx)
        try:
            await self.bot.wait_for("message", check=pred)
        except asyncio.TimeoutError:
            await ctx.send("Okay, I won't delete your todos")
        else:
            if not pred.result:
                await ctx.send("Okay, I won't delete your todos")
            else:
                await self.config.user(ctx.author).todos.clear()
                await ctx.send("Removed your todos.")

    @complete.command(
        require_var_positional=True, name="remove", aliases=["del", "rm", "delete"]
    )
    async def complete_delete(self, ctx, *indexes: positive_int):
        """Remove your completed todos"""
        if not await self.config.user(ctx.author).completed():
            return await ctx.send(
                self._no_completed_message.format(prefix=ctx.clean_prefix)
            )
        async with ctx.typing():
            async with self.config.user(ctx.author).completed() as cd:
                indexes = [x - 1 for x in indexes]
                indexes.sort(reverse=True)
                fails, failed, removes, removed = 0, [], 0, []
                for index in indexes:
                    try:
                        removed.append(f"`{cd.pop(index)}`")
                    except IndexError:
                        fails += 1
                        failed.append(f"`{index}`")
                    else:
                        removes += 1
        msg = "Done."
        details = await self.config.user(ctx.author).detailed_pop()
        if removes:
            plural = "" if removes == 1 else "s"
            msg += f"\nRemoved {removes} todo{plural}"
            if details:
                msg += "\n" + "\n".join(removed)
        if fails:
            plural = "" if fails == 1 else "s"
            msg += f"\nFailed to remove {fails} todo{plural} {self._failure_explanation}"
            if details:
                msg += "\n" + "\n".join(failed)
        await self._maybe_autosort(ctx)
        if len(msg) > 2000:
            await ctx.send_interactive(pagify(msg))
        else:
            await ctx.send(msg)

    @complete.command(name="removeall", aliases=["delall", "rma"])
    async def complete_removeall(self, ctx):
        """Remove all of your completed todos"""
        await ctx.send(
            "WARNING, this will remove **ALL** of your completed todos. Would you like to remove them? (y/n)"
        )
        pred = MessagePredicate.yes_or_no(ctx)
        try:
            await self.bot.wait_for("message", check=pred)
        except asyncio.TimeoutError:
            await ctx.send("Okay, I won't delete your completed todos")
        else:
            if not pred.result:
                await ctx.send("Okay, I won't delete your completed todos")
            else:
                await self.config.user(ctx.author).completed.clear()
                await ctx.send("Removed your completed todos.")
