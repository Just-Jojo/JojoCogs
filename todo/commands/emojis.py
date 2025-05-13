# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from typing import Optional, Union, TYPE_CHECKING

import discord

try:
    from emoji.unicode_codes import UNICODE_EMOJI_ENGLISH
except ImportError:
    from emoji import EMOJI_DATA as UNICODE_EMOJI_ENGLISH
from redbot.core import commands

from ..abc import TodoMixin

__all__ = ["Emojis"]


async def pretty(ctx: commands.Context) -> bool:
    if TYPE_CHECKING:
        assert ctx.cog is not None and isinstance(ctx.cog, TodoMixin)
    return await ctx.cog.cache.get_user_setting(ctx.author, "pretty_todos")


class EmojiConverter(commands.EmojiConverter):
    async def convert(
        self, ctx: commands.Context, arg: str
    ) -> Union[str, discord.Emoji]:  # type:ignore
        arg = arg.strip()
        return arg if arg in UNICODE_EMOJI_ENGLISH.keys() else await super().convert(ctx, arg)


class Emojis(TodoMixin):
    """Emojis for todo... fun"""

    @commands.group(name="todoset")
    async def todo_settings(self, *args): ...

    @todo_settings.group(name="categoryemojis", aliases=["catemojis"])
    async def category_emoji(self, ctx: commands.Context):
        """Set your category emojis"""
        pass

    @category_emoji.command(name="todoemoji", aliases=["temoji"])
    async def category_todo_emoji(
        self, ctx: commands.Context, reset: Optional[bool], emoji: Optional[EmojiConverter] = None
    ):
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
        elif not emoji:
            return await ctx.send_help()
        use_md = await self.cache.get_user_setting(ctx.author, "use_markdown")
        if use_md:
            return await ctx.send("You can't use custom emojis while having markdown enabled")
        act_emoji = str(emoji)
        await self.cache.set_user_setting(ctx.author, "todo_category_emoji", act_emoji)
        return await ctx.send(f"Your todo category emoji has been set to '{act_emoji}'.")

    @category_emoji.command(name="completedemoji", aliases=["cemoji"])
    async def category_completed_emoji(
        self, ctx: commands.Context, reset: Optional[bool], emoji: Optional[EmojiConverter] = None
    ):
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
        elif not emoji:
            return await ctx.send_help()
        use_md = await self.cache.get_user_setting(ctx.author, "use_markdown")
        if use_md:
            return await ctx.send("You can't use custom emojis while having markdown enabled")
        act_emoji = str(emoji)
        await self.cache.set_user_setting(ctx.author, "completed_category_emoji", act_emoji)
        return await ctx.send(f"Your completed category emoji has been set to '{act_emoji}'.")

    @commands.check(pretty)
    @todo_settings.command(name="todoemoji", aliases=("temoji",))
    async def todo_emoji(
        self, ctx: commands.Context, reset: Optional[bool], emoji: EmojiConverter = None
    ):
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
        elif not emoji:
            return await ctx.send_help()
        use_md = await self.cache.get_user_setting(ctx.author, "use_markdown")
        if use_md:
            return await ctx.send("You can't have custom emojis while markdown is enabled")
        act_emoji = str(emoji)
        await self.cache.set_user_setting(ctx.author, "todo_emoji", act_emoji)
        return await ctx.send(f"I have set your todo emoji to '{act_emoji}'")

    @commands.check(pretty)
    @todo_settings.command(name="completeemoji", aliases=("cemoji",))
    async def todo_complete_emoji(
        self, ctx: commands.Context, reset: Optional[bool], emoji: EmojiConverter = None
    ):
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
        elif not emoji:
            return await ctx.send_help()
        use_md = await self.cache.get_user_setting(ctx.author, "use_markdown")
        if use_md:
            return await ctx.send("You can't have custom emojis while markdown is enabled")
        act_emoji = str(emoji)
        await self.cache.set_user_setting(ctx.author, "completed_emoji", act_emoji)
        return await ctx.send(f"I have set your completed emoji to '{act_emoji}'")
