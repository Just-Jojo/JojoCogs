# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import discord

from redbot.core import commands
from redbot.core.utils.chat_formatting import pagify

from ..abc import TodoMixin
from ..utils import NonBotMember, timestamp_format, PositiveInt
from ..utils.formatting import _format_todos, _format_completed

from typing import Optional


class SharedTodos(TodoMixin):
    """A "shared" todo list.
    
    These are lists that can be managed by other people and are given access to by the owner of the list
    """

    _no_todo_shared_message = "{user} does not have any todos. Use `{prefix}todo shared add {user} <task>` to add one"

    @commands.group()
    async def todo(self, *args):
        pass

    @todo.group()
    @commands.guild_only()
    async def shared(self, ctx: commands.Context):
        """Shared todo lists.
        
        These are lists that other users have given you access to, for adding/removing/completing
        """

        pass

    @shared.command(name="add")
    async def todo_shared_add(self, ctx: commands.Context, user: NonBotMember, pinned: Optional[bool], *, todo: str):
        """Add a todo to a user's list

        This will require you to have manager on their list

        **Arguments**.
            - `user` The user to add to their list. This **cannot** be a bot.
            - `pinned` Whether the todo should be pinned or not. Defaults to False.
            - `todo` The task to add to the user's list.
        """
        user: discord.Member
        pinned = bool(pinned)
        data = await self.cache.get_user_data(user.id)
        todos: list = data["todos"]
        managers = data["managers"]
        if not managers or ctx.author.id not in managers:
            return await ctx.send("You are not a manager of that user's todo list")

        todos.append({"task": todo, "pinned": pinned})
        await self.cache.set_user_item(user, "todos", todos)

        data = data["user_settings"]

        msg = f"Added that todo to {user.display_name}'s todo list"

        if data["extra_details"]:
            msg += f"\n'{discord.utils.escape_markdown(todo)}'"
        if data["use_timestamps"]:
            msg += f"\n{timestamp_format()}"

        task = None
        if len(msg) == 2000:
            task = self.bot.loop.create_task(ctx.send_interactive(pagify(msg)))
        else:
            await ctx.send(msg)
        await self._maybe_autosort(user)
        if task is not None:
            await task

    @shared.command(name="list")
    async def todo_shared_list(self, ctx: commands.Context, user: NonBotMember):
        """Lists a user's list that you manage
        
        This will *only* work if you manage that user's list

        **Arguments**
            - `user` A user who you manage a list for. This **cannot** be a bot.
        """
        user: discord.Member
        data = await self.cache.get_user_data(user.id)
        todos = data["todos"]
        completed = data["completed"]
        managers = data["managers"]
        settings = data["user_settings"]

        if not managers or ctx.author.id not in managers:
            return await ctx.send("You are not a manager of that user's list")
        elif not todos:
            if not all([completed, settings["combine_lists"]]):
                return await ctx.send(self._no_todo_shared_message.format(user=user, prefix=ctx.clean_prefix))
            return await self.page_logic(ctx, await _format_completed(completed, **settings), f"{user.name}'s Completed Todos" **settings)

        pinned, other = await self._get_todos(todos)
        todos = await _format_todos(pinned, other, **settings)
        if completed and settings["combine_lists"]:
            todos.extend(
                await _format_completed(completed, combined=True, **settings)
            )
        await self.page_logic(ctx, todos, title=f"{user.display_name}'s Todos", **settings)

    @shared.command(name="remove", aliases=["del", "delete"], require_var_positional=True)
    async def todo_shared_delete(self, ctx: commands.Context, user: NonBotMember, *indexes: PositiveInt):
        """Remove a todo from a user's list
        
        This will only work if you are a manager of that user's list

        **Arguments**
            - `user` The user you want to edit the list of. This **cannot** be a bot.
            - `index` The index of the todo you want to remove.
        """
        indexes = [i - 1 for i in indexes]
        user: discord.Member
        data = await self.cache.get_user_data(user.id)
        todos = data["todos"]
        managers = data["managers"]
        settings = data["user_settings"]

        if not managers or ctx.author.id not in managers:
            return await ctx.send("You are not a manger of that user's todo list")
        elif not todos:
            return await ctx.send(self._no_todo_shared_message.format(user=user, prefix=ctx.clean_prefix))

        tasks = []
        for index in indexes:
            try:
                tasks.append(todos.pop(index - 1)["task"])
            except IndexError:
                pass

        if not tasks:
            those_that = "Those" if len(indexes) > 1 else "That"
            plural = "" if len(indexes) == 1 else "es"
            return await ctx.send(f"{those_that} index{plural} was invalid!")
        plural = "" if len(tasks) == 1 else "s"
        msg = f"Done. Deleted {len(tasks)} todo{plural}."
        if settings["extra_details"]:
            msg += "\n" + "\n".join(tasks)
        if settings["use_timestamps"]:
            msg += f"\n{timestamp_format()}"
        task = None
        if len(msg) > 2000:
            task = self.bot.loop.create_task(ctx.send_interactive(pagify(msg)))
        else:
            await ctx.send(msg)
        await self.cache.set_user_item(user, "todos", todos)
        if task is not None:
            await task

    @shared.group(name="complete", aliases=["c"])
    async def shared_complete(self, ctx: commands.Context, user: NonBotMember(False), indexes: PositiveInt):
        """Complete todos on a user's list

        This only works if you are a moderator of that user's list

        **Arguments**
            - `user` The user for completing todos. This **cannot** be a bot.
            - `indexes` The indexes of the todos you want to complete
        """
        user: discord.Member
        indexes = [i - 1 for i in indexes]

        data = await self.cache.get_user_data(user.id)
        todos = data["todos"]
        completed = data["completed"]
        managers = data["managers"]
        settings = data["user_settings"]

        if not managers or ctx.author.id not in managers:
            return await ctx.send("You are not a manager of this user's todo list")
        elif not todos:
            return await ctx.send(self._no_todo_message.format(prefix=ctx.clean_prefix))

        comped = []
        for index in indexes:
            try:
                task = todos.pop(index)
            except IndexError:
                pass
            else:
                comped.append(task["task"])
        amount = len(comped)
        completed.extend(comped)
        if amount == 0:
            those_that = "that" if len(indexes) == 1 else "those"
            plural = "" if len(indexes) == 1 else "es"
            return await ctx.send(f"Hm, {those_that} index{plural}")
        plural = "" if amount == 1 else "s"
        msg = f"Completed {amount} todo{plural}"
        if settings["extra_details"]:
            msg += "\n" + "\n".join(comped)
        if settings["use_timestamps"]:
            msg += f"\n{timestamp_format()}"

        task = None
        if len(msg) > 2000:
            task = self.bot.loop.create_task(ctx.send_interactive(pagify(msg)))
        else:
            await ctx.send(msg)
        await self.cache.set_user_item(user, "todos", todos)
        await self.cache.set_user_item(user, "completed", completed)
        await self._maybe_autosort(user)
        if task is not None:
            await task

    @shared_complete.command(name="list")
    async def shared_complete_list(self, ctx: commands.Context, user: NonBotMember):
        """List a user's completed todos
        
        This only works if you are a manager of that user's todo list

        **Arguments**
            - `user` The user to view the list of. This **cannot** be a bot.
        """
        data = await self.cache.get_user_data(user.id)
        completed = data["completed"]
        managers = data["managers"]
        settings = data["user_settings"]

        if not managers or ctx.author.id not in managers:
            return await ctx.send("You are not a manager of that user's todo list")
        elif not completed:
            return await ctx.send(self._no_completed_message.format(prefix=ctx.clean_prefix))

        completed = await _format_completed(completed, **settings)
        await self.page_logic(ctx, completed, f"{user.display_name}'s Completed Todos", **settings)
