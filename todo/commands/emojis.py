# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import asyncio
import discord

from redbot.core import commands
from redbot.core.utils.predicates import ReactionPredicate
from typing import Optional

from ..abc import TodoMixin


__all__ = ["Emojis"]


async def pretty(ctx: commands.Context):
    return await ctx.cog.cache.get_user_setting(ctx.author, "pretty_todos")


class Emojis(TodoMixin):
    """Emojis for todo... fun"""

    @commands.group(name="todoset")
    async def todo_settings(self, *args):
        ...

    @todo_settings.group(name="categoryemojis", aliases=["catemojis"])
    async def category_emoji(self, ctx: commands.Context):
        """Set your category emojis"""
        pass

    @category_emoji.command(name="todoemoji", aliases=["temoji"])
    async def category_todo_emoji(self, ctx: commands.Context, reset: Optional[bool], emoji: discord.Emoji = None):
        """Set the emoji for the todo category.

        If you have markdown enabled only default emojis will work.

        By default the emoji will be '🔘'.

        **Arguments**
            - `reset` If specified this will reset the emoji back to default.
            - `emoji` The emoji that will be used for the category. This will skip the check. This argument can't be used if you have markdown enabled.
        """
        if reset:
            await self.cache.set_user_setting(ctx.author, "todo_category_emoji", None)
            return await ctx.send("Your todo category emoji has been reset.")
        use_md = await self.cache.get_user_setting(ctx.author, "use_markdown")
        if emoji:
            if use_md:
                return await ctx.send("You can't use custom emojis while having markdown enabled")
            emoji = str(emoji)
            await self.cache.set_user_setting(ctx.author, "todo_category_emoji", emoji)
            return await ctx.send(f"Your todo category emoji has been set to '{emoji}'.")
        msg = await ctx.send("Please react with the emoji you want for the todo category emoji")
        pred = ReactionPredicate.same_context(message=msg, user=ctx.author)
        try:
            emoji = (await self.bot.wait_for("reaction_add", check=pred)[0]).emoji
        except asyncio.TimeoutError:
            return await ctx.send("Okay, I won't set your emojis")
        if not isinstance(emoji, str):
            if use_md:
                return await ctx.send("You can't use custom emojis whilst having markdown enabled")
            if not self.bot.get_emoji(emoji.id):
                return await ctx.send("Please use an emoji that I can use.")
        c_emoji = str(emoji) # If it's animated then this will return the actual string for using the emoji, otherwise it's str("string") lol
        await self.cache.set_user_setting(ctx.author, "todo_category_emoji", c_emoji)
        await ctx.send(f"I have set your todo category emoji to '{c_emoji}'.")

    @category_emoji.command(name="completedemoji", aliases=["cemoji"])
    async def category_completed_emoji(self, ctx: commands.Context, reset: Optional[bool], emoji: discord.Emoji = None):
        """Set the emoji for the completed category.

        If you have markdown enabled only default emojis will work.

        By default the emoji will be '☑'.

        **Arguments**
            - `reset` If specified this will reset the emoji back to default.
            - `emoji` The emoji that will be used for the category. This will skip the check, and this argument can't be used if you have markdown enabled.
        """
        if reset:
            await self.cache.set_user_setting(ctx.author, "completed_category_emoji", None)
            return await ctx.send("Your completed category emoji has been reset")
        use_md = await self.cache.get_user_setting(ctx.author, "use_markdown")
        if emoji:
            if use_md:
                return await ctx.send("You can't use custom emojis while having markdown enabled")
            emoji = str(emoji)
            await self.cache.set_user_setting(ctx.author, "completed_category_emoji", emoji)
            return await ctx.send(f"Your completed category emoji has been set to '{emoji}'.")
        msg = await ctx.send("Please react with the emoji you want for the completed category emoji")
        pred = ReactionPredicate.same_context(message=msg, user=ctx.author)
        try:
            emoji = (await self.bot.wait_for("reaction_add", check=pred))[0].emoji
        except asyncio.TimeoutError:
            return await ctx.send("Okay, I won't set your emojis")
        if not isinstance(emoji, str):
            if use_md:
                return await ctx.send("You can't use custom emojis whilst having markdown enabled")
            if not self.bot.get_emoji(emoji.id):
                return await ctx.send("Please use an emoji that I can use.")
        c_emoji = str(emoji)
        await self.cache.set_user_setting(ctx.author, "completed_category_emoji", c_emoji)
        await ctx.send(f"I have set your completed category emoji to '{c_emoji}'.")

    @commands.check(pretty)
    @todo_settings.command(name="todoemoji", aliases=("temoji",))
    async def todo_emoji(self, ctx: commands.Context, reset: Optional[bool], emoji: discord.Emoji = None):
        """Set the emoji used for todos

        This will prompt you to react with an emoji. Note that the emoji must be one the bot can use.

        If you have markdown enabled only default emojis will work.

        **Arguments**
            - `reset` Whether to reset the emoji back to default.
            - `emoji` The emoji that will be used for this 
        """

        if reset:
            await self.cache.set_user_setting(ctx.author, "todo_emoji", None)
            return await ctx.send("Done. Your emoji has been reset.")
        use_md = await self.cache.get_user_setting(ctx.author, "use_markdown")
        if emoji:
            if use_md:
                return await ctx.send("You can't have custom emojis while markdown is enabled")
            emoji = str(emoji)
            await self.cache.set_user_setting(ctx.author, "todo_emoji", emoji)
            return await ctx.send(f"I have set your todo emoji to '{emoji}'")
        msg = await ctx.send("Please react with the emoji you want for the uncompleted todos")
        pred = ReactionPredicate.same_context(message=msg, user=ctx.author)
        try:
            emoji = (await self.bot.wait_for("reaction_add", check=pred))[0].emoji
        except asyncio.TimeoutError:
            return await ctx.send("Okay, I won't set your emojis")
        if not isinstance(emoji, str):
            if use_md:
                return await ctx.send("You can't have custom emojis whilst markdown is enabled")
            if not self.bot.get_emoji(emoji.id):
                return await ctx.send("Please use an emoji that I can use.")
        todo_emoji = str(emoji)
        await self.cache.set_user_setting(ctx.author, "todo_emoji", todo_emoji)
        await ctx.send(f"I have set your todo emoji to '{todo_emoji}'")

    @commands.check(pretty)
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
        use_md = await self.cache.get_user_setting(ctx.author, "use_markdown")
        if emoji:
            if use_md:
                return await ctx.send("You can't have custom emojis while markdown is enabled")
            emoji = str(emoji)
            await self.cache.set_user_setting(ctx.author, "completed_emoji", emoji)
            return await ctx.send(f"I have set your completed emoji to '{emoji}'")
        msg = await ctx.send("Please react with the emoji you want for the completed todos")
        pred = ReactionPredicate.same_context(message=msg, user=ctx.author)
        try:
            emoji = (await self.bot.wait_for("reaction_add", check=pred))[0].emoji
        except asyncio.TimeoutError:
            return await ctx.send("Okay, I won't set your emoji")
        if not isinstance(emoji, str):
            if use_md:
                return await ctx.send("You can't use custom emojis whilst markdown is enabled")
            if not self.bot.get_emoji(emoji.id):
                return await ctx.send("Please use an emoji that I can use.")
        emoji = str(emoji)
        await self.cache.set_user_setting(ctx.author, "completed_emoji", emoji)
        await ctx.send(f"I have set your completed emoji to '{emoji}'")

