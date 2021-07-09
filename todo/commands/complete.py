# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import discord
import asyncio
from contextlib import suppress

from redbot.core import commands
from redbot.core.utils.predicates import MessagePredicate

from ..abc import TodoMixin
from ..utils import PositiveInt, TodoPositiveInt
from ..utils.formatting import _format_completed

__all__ = ["Complete"]


class Complete(TodoMixin):
    """Commands that have to do with completed todos"""

    _no_completed_message = "You do not have any completed todos. You can add one with `{prefix}todo complete <indexes...>`"

    @commands.group()
    async def todo(self, *args):
        pass

    @todo.group(invoke_without_command=True, require_var_positional=True, aliases=["c"])
    async def complete(self, ctx: commands.Context, *indexes: TodoPositiveInt):
        """Commands having to do with your completed tasks


        \u200b
        **Arguments**
            - `indexes` Optional indexes to complete. If left at none the help command will be shown
        """
        indexes = [i - 1 for i in indexes]
        data = await self.cache.get_user_data(ctx.author.id)
        todos = data["todos"]
        if not todos:
            return await ctx.send(self._no_todo_message.format(prefix=ctx.clean_prefix))
        completed = []
        for index in indexes:
            try:
                completed.append((todos.pop(index))["task"])
            except IndexError:
                pass
            except Exception as e:
                self.log.error("Error in command 'todo complete'", exc_info=e)
        amount = len(completed)
        plural = "" if amount == 1 else "s"
        msg = f"Completed {amount} todo{plural}."
        if data["user_settings"]["extra_details"]:
            msg += "\n" + "\n".join(f"`{task}`" for task in completed)
        task = None
        if len(msg) <= 2000:
            await ctx.send(msg)
        else:
            task = self.bot.loop.create_task(ctx.send_interactive(pagify(msg)))
        data["completed"].extend(completed)
        data["todos"] = todos
        await self.cache.set_user_data(ctx.author, data)
        await self._maybe_autosort(ctx.author)
        if task is not None and not task.done():
            await task

    @complete.command(name="delete", aliases=["del", "remove"])
    async def complete_delete(self, ctx: commands.Context, *indexes: PositiveInt):
        """Delete completed todos

        This will remove them from your completed list

        **Arguments**
            - `indexes` A list of integers for the indexes of your completed todos
        """
        indexes = [i - 1 for i in indexes]
        indexes.sort(reverse=True)
        completed = await self.cache.get_user_item(ctx.author, "completed")
        if not completed:
            return await ctx.send(
                self._no_completed_message.format(prefix=ctx.clean_prefix)
            )
        for index in indexes:
            try:
                completed.pop(index)
            except IndexError:
                pass
            except Exception as e:
                self.log.error("Exception in command 'todo complete delete'", exc_info=e)
        amount = len(indexes)
        plural = "" if amount == 1 else "s"
        await ctx.send(f"Deleted {amount} completed todo{plural}")
        await self.cache.set_user_item(ctx.author, "completed", completed)

    @complete.command(name="deleteall", aliases=["delall", "removeall"])
    async def complete_remove_all(self, ctx: commands.Context, confirm: bool = False):
        """Remove all of your completed todos


        \u200b
        **Arguments**
            - `confirm` Skips the confirmation check. Defaults to False
        """
        if not confirm:
            msg = await ctx.send(
                "Are you sure you would like to remove all of your completed todos? (y/N)"
            )
            pred = MessagePredicate.yes_or_no(ctx)
            try:
                umsg = await self.bot.wait_for("message", check=pred)
            except asyncio.TimeoutError:
                pass
            finally:
                with suppress(discord.NotFound, discord.Forbidden):
                    await msg.delete()
                    await umsg.add_reaction("\N{WHITE HEAVY CHECK MARK}")
            if not pred.result:
                return await ctx.send("Okay, I will not remove your completed todos.")
        await self.cache.set_user_item(ctx.author, "completed", [])
        await ctx.send("Done. Removed all of your completed todos.")

    @complete.command(name="list")
    async def complete_list(self, ctx: commands.Context):
        """List your completed todos

        This will only list if you have completed todos
        """
        data = await self.cache.get_user_data(ctx.author.id)
        completed = data["completed"]
        if not completed:
            return await ctx.send(
                self._no_completed_message.format(prefix=ctx.clean_prefix)
            )
        settings = data["user_settings"]
        completed = await _format_completed(completed, False, **settings)
        await self.page_logic(
            ctx, completed, f"{ctx.author.name}'s Completed Todos", **settings
        )

    @complete.command(name="reorder", aliases=["move"], usage="<from> <to>")
    async def complete_reorder(
        self, ctx: commands.Context, original: PositiveInt, new: PositiveInt
    ):
        """Move a completed todo from one index to another

        This will error if the index is larger than your completed todo list

        **Arguments**
            - `from` The index of the completed todo
            - `to` The new index of the completed todo
        """
        if original == new:
            return await ctx.send(
                "You cannot move a todo from one index... to the same index"
            )
        completed = await self.cache.get_user_item(ctx.author, "completed")
        if not completed:
            return await ctx.send(
                self._no_completed_message.format(prefix=ctx.clean_prefix)
            )
        act_orig = original - 1
        act_new = new - 1
        try:
            task = completed.pop(act_orig)
        except IndexError:
            return await ctx.send(
                f"I could not find a completed todo at index `{original}`"
            )
        completed.insert(act_new, task)
        msg = f"Moved a completed todo from {original} to {new}"
        await ctx.send(msg)
        await self.cache.set_user_item(ctx.author, "completed", completed)
