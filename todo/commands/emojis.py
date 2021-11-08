# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import discord

from redbot.core import commands
from redbot.core.utils.predicates import ReactionPredicate
from typing import Optional

from ..abc import TodoMixin


__all__ = ["Emojis"]


class Emojis(TodoMixin):
    """Emojis for todo... fun"""

    @commands.group()
    async def todo_settings(self, *args):
        ...

    @commands.check(no_markdown)
    @todo_settings.command(name="todoemoji", aliases=("temoji",))
    async def todo_emoji(self, ctx: commands.Context, reset: Optional[bool], emoji: discord.Emoji = None):
        """Set the emoji used for todos

        This will prompt you to react with an emoji. Note that the emoji must be one the bot can use.

        **Arguments**
            - `reset` Whether to reset the emoji back to default.
        """

        if reset:
            await self.cache.set_user_setting(ctx.author, "todo_emoji", None)
            return await ctx.send("Done. Your emoji has been reset.")
        if emoji:
            emoji = str(emoji)
            await self.cache.set_user_setting(ctx.author, "todo_emoji", emoji)
            return await ctx.send(f"I have set your todo emoji to '{todo_emoji}'")
        msg = await ctx.send("Please react with the emoji you want for the uncompleted todos")
        pred = ReactionPredicate.same_context(message=msg, user=ctx.author)
        try:
            emoji = (await self.bot.wait_for("reaction_add", check=pred))[0].emoji
        except asyncio.TimeoutError:
            return await ctx.send("Okay, I won't set your emojis")
        if not isinstance(emoji, str) and not self.bot.get_emoji(emoji.id):
            return await ctx.send("Please use an emoji that I can use.")
        todo_emoji = str(emoji)
        await self.cache.set_user_setting(ctx.author, "todo_emoji", todo_emoji)
        await ctx.send(f"I have set your todo emoji to '{todo_emoji}'")

    @todo_settings.command(name="completeemoji", aliases=("cemoji",))
    async def todo_complete_emoji(self, ctx: commands.Context, reset: Optional[bool], emoji: discord.Emoji = None):
        """Set the completed emoji used for completed todos.

        This will prompt you to react with an emoji.
        Note that only emojis that [botname] can use will work

        **Arguments**
            - `reset` Whether to reset the emoji back to default.
            - `emoji` The emoji to use for the complete mark. This has to be custom and can only be an emoji that [botname] can use.
        """
        if reset:
            await self.cache.set_user_setting(ctx.author, "completed_emoji", None)
            return await ctx.send("Done. Your emoji has been reset.")
        if emoji:
            emoji = str(emoji)
            await self.cache.set_user_setting(ctx.author, "completed_emoji", emoji)
            return await ctx.send(f"I have set your completed emoji to '{emoji}'")
        msg = await ctx.send("Please react with the emoji you want for the completed todos")
        pred = ReactionPredicate.same_context(message=msg, user=ctx.author)
        try:
            emoji = (await self.bot.wait_for("reaction_add", check=pred))[0].emoji
        except asyncio.TimeoutError:
            return await ctx.send("Okay, I won't set your emoji")
        if not isinstance(emoji, str) and not self.bot.get_emoji(emoji.id):
            return await ctx.send("Please use an emoji that I can use.")
        emoji = str(emoji)
        await self.cache.set_user_setting(ctx.author, "completed_emoji", emoji)
        await ctx.send(f"I have set your completed emoji to '{emoji}'")


