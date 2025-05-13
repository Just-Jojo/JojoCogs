# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import asyncio
from typing import Final

from redbot.core import Config, commands
from redbot.core.utils import AsyncIter
from redbot.core.utils.predicates import MessagePredicate

from ..abc import TodoMixin


class Importer(TodoMixin):
    """Import todos from epic guy's todo cog (maybe)"""

    _epic_guy_config: Config = Config.get_conf(None, 6732102719277, True, cog_name="Todo")

    @commands.group()
    async def todo(self, *args): ...

    @todo.command(name="importall")
    @commands.is_owner()  # First owner only command in todo :ducksweat:
    async def todo_import_all(self, ctx: commands.Context, confirm: bool = False):
        """Import every user's todos from epic guy's todo cog

        This will only import todos from this bot's config.

        **Arguments**
            - `confirm` Skips the confirmation check.
        """
        if not confirm:
            await ctx.send("Would you like to import all the todos? (y/n)")
            pred = MessagePredicate.yes_or_no(ctx)
            try:
                await self.bot.wait_for("message", check=pred, timeout=10.0)
            except asyncio.TimeoutError:
                pass
            if not pred.result:
                return await ctx.send("Okay, I won't import all the todos.")
        users = await self._epic_guy_config.all_users()
        if not users:
            return await ctx.send("There is no user data for me to import.")
        await ctx.send("Importing todos. This may take a while.")
        async with ctx.typing():
            async for uid, todos in AsyncIter(users.items(), steps=100):
                data = todos["todos"]
                todos = []
                for todo in data:
                    task = todo[1] if isinstance(todo, list) else todo
                    todos.append({"task": task, "pinned": False, "timestamp": None})
                u_todos = await self.cache.get_user_item(uid, "todos")
                u_todos.extend(todos)
                await self.cache.set_user_item(uid, "todos", u_todos)
        await ctx.send("I have imported all todos from epic's todo cog.")

    @todo.command(name="import")
    async def todo_import(self, ctx: commands.Context, confirm: bool = False):
        """Import your todos from epic guy's todo cog.

        This will only import todos from this bot's config.
        To import todos from another bot, check out `[p]todo multiadd`

        **Arguments**
            - `confirm` Skips the confirmation check.
        """

        if not confirm:
            await ctx.send("Would you like to import your todos? (y/n)")
            pred = MessagePredicate.yes_or_no(ctx)
            try:
                await self.bot.wait_for("message", check=pred, timeout=10.0)
            except asyncio.TimeoutError:
                pass
            finally:
                if not pred.result:
                    return await ctx.send("Okay, I will not import your todos.")

        data = await self._epic_guy_config.user(ctx.author).all()
        not_found = "I could not find your todos from epic's todo cog."
        if not data:
            return await ctx.send(not_found)
        elif not (todos := data.get("todos")):
            return await ctx.send(not_found)
        current_todos = await self.cache.get_user_item(ctx.author, "todos")
        payload = []
        async with ctx.typing():
            for todo in todos:
                to_add = todo
                if isinstance(todo, list):
                    to_add = to_add[1]
                payload.append(
                    {"task": to_add, "pinned": False, "timestamp": self._gen_timestamp()}
                )
            current_todos.extend(payload)
        await ctx.send("Done. I have imported your todos")
        await self.cache.set_user_item(ctx.author, "todos", current_todos)
        await self.cache._maybe_autosort(ctx.author)
