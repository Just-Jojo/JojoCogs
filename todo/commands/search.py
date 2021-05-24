# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

# type:ignore[union-attr]

from typing import Optional

from redbot.core import commands

from .abc import ToDoMixin

try:
    import regex as re
except ImportError:
    import re


__all__ = ["Search"]  # Mypy is a bitch


class Search(ToDoMixin):
    """Commands for searching for todos"""

    @commands.group()
    async def todo(self, *args, **kwargs):
        pass

    @todo.command()
    async def search(
        self, ctx: commands.Context, use_regex: Optional[bool], *, to_search: str
    ):
        """Search your todo list for todos matching either a regex pattern or a string"""
        todos = await self.config.user(ctx.author).todos()
        found = []
        if use_regex:
            to_search = re.compile(to_search)
        for num, todo in enumerate(todos, 1):
            if _ := re.search(to_search, todo) if use_regex else to_search in todo:
                found.append(f"{num}. {todo}")
        if not found:
            return await ctx.send("I could not find any todos with that pattern")
        conf = await self._get_user_config(ctx.author)
        await self.page_logic(
            ctx,
            found,
            "Todo search",
            use_md=conf.get("use_md", True),
            use_embeds=conf.get("use_embeds", True),
            private=False,
        )
