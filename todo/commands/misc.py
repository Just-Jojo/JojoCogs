# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from datetime import datetime

import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_list

from ..abc import TodoMixin


class Miscellaneous(TodoMixin):
    """Miscellaneous todo commands"""

    @commands.group()
    async def todo(self, *args):
        ...

    @todo.command(name="version")
    async def todo_version(self, ctx: commands.Context):
        """Get todo's version"""
        msg = (
            f"ToDo, created with ❤ by Jojo#7791. Version `{self.__version__}`\n"
            f"Have fun :)"
        )
        await self.maybe_send_embed(ctx, msg)

    @todo.command(name="suggestions", aliases=["suggest"])
    async def todo_suggestions(self, ctx: commands.Context):
        """Get information about how you can suggest features for this cog"""
        url = "https://github.com/Just-Jojo/JojoCogs/issues/15"
        hyper_link = (
            f"[link]({url})"
            if await self._embed_requested(ctx, ctx.author)
            else f"link: <{url}>"
        )
        msg = (
            f"First, thanks! Suggestions help me keep todo user friendly and fun to work with\n"
            f"For suggestions, you can follow this {hyper_link}\n"
            "Again, thanks! ❤"
        )
        await self.maybe_send_embed(ctx, msg, title="Todo suggestions")

    @todo.command(name="suggestors")
    async def todo_suggestors(self, ctx: commands.Context):
        """A thank you command for everyone who has either contributed, requested a feature, or reported a bug"""
        msg = (
            f"A big thank you to everyone who's suggested something for todo!\n\nSuggestors: `{humanize_list(self.__suggestors__)}`\n"
            "Also a big thank you to Kreusada who's helped me design things and keep myself sane whilst developing this cog"
        )
        await self.maybe_send_embed(ctx, msg, title="Todo Suggestors")

    async def maybe_send_embed(self, ctx: commands.Context, msg: str, *, title: str = ""):
        kwargs = {"content": f"**{title}**\n\n{msg}", "embed": None}
        if await self._embed_requested(ctx, ctx.author):
            colour = await self.cache.get_user_setting(ctx.author, "colour")
            colour = colour if colour is not None else await ctx.embed_colour()
            embed = discord.Embed(
                title=title, description=msg, colour=colour, timestamp=datetime.utcnow()
            )
            kwargs = {"embed": embed, "content": None}
        await ctx.send(**kwargs)
