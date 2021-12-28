# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from ..abc import TodoMixin
from ..utils import formatting
from redbot.core import commands

from typing import Optional

try:
    import regex as re
except ImportError:
    import re # type:ignore


class Search(TodoMixin):
    """Search todos and find them or something"""

    @commands.group()
    async def todo(self, *args):
        ...

    @todo.command(name="search")
    async def todo_search(self, ctx: commands.Context, regex: Optional[bool], *, query: str):
        """Query your todo list for todos matching a pattern or a word

        **Arguments**
            - `regex` Whether this query will be a regular expression. You can check your regex at https://regex101.com
            - `query` The pattern or terms to query your list.
        """
        if not (data := await self.cache.query_list(ctx.author, regex=bool(regex), query=query)):
            return await ctx.send("I could not find any todos matching that query.")
        user_settings = await self.cache.get_user_item(ctx.author, "user_settings")
        pinned, todos = await self._get_todos(data, timestamp=user_settings["use_timestamps"], md=user_settings["use_markdown"])
        todos = await formatting._format_todos(pinned, todos, **user_settings)
        await self.page_logic(ctx, todos, "Todos matching that query", **user_settings)
