# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import asyncio

from redbot.core import commands, Config
from redbot.core.utils.predicates import MessagePredicate

from ..abc import TodoMixin


class Importer(TodoMixin):
    """Import todos from epic guy's todo cog (maybe)"""

    _epic_guy_config = Config.get_conf(None, 6732102719277, True, cog_name="Todo")

    @commands.group()
    async def todo(self, *args):
        ...

    @todo.command(name="import")
    async def todo_import(self, ctx: commands.Context, confirm: bool = False):
        """Import your todos from epic guy's todo cog"""

        if not confirm:
            await ctx.send("Would you like to import your todos? (y/n)")
            pred = MessagePredicate.yes_or_no()
            try:
                await self.bot.wait_for("message", check=pred)
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
                payload.append({"task": to_add, "pinned": False, "timestamp": self._gen_timestamp()})
            current_todos.extend(payload)
        await ctx.send("Done. I have imported your todos")
        await self.cache.set_user_item(ctx.author, "todos", current_todos)
        await self.cache._maybe_autosort(ctx.author)
