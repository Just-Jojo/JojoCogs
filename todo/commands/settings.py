# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from redbot.core import commands

from ..abc import TodoMixin


class Settings(TodoMixin):
    """Commands for todo's settings"""

    @staticmethod
    def _get_enabled_status(value: bool) -> str:
        """An internal function to get an enabled status based off a bool"""
        return "enabled" if value else "disabled"

    @commands.group(name="todoset", aliases=["todosettings"])
    async def todo_settings(self, ctx: commands.Context):
        """Commands for configuring your todo list"""
        pass

    @todo_settings.command(name="markdown", aliases=["md", "codeblock"])
    async def todo_use_markdown(self, ctx: commands.Context, value: bool):
        """Set your todo list to use markdown blocks

        This will look something like this
        **Jojo's todos**
        ```md
        1. Blah blah
        2. Blah blah blah
        3. aaaaaaaaaaaaaaaaaaa
        ```
        **Arguments**
            - `value` Whether markdown should be used or not
        """
        current = await self.cache.get_user_setting(ctx.author, "use_markdown")
        if current == value:
            currently = "currently" if value else "not currently"
            return await ctx.send(f"Markdown blocks are {currently} enabled")
        await self.cache.set_user_setting(ctx.author, "use_markdown", value)
        await ctx.send(f"Markdown blocks are now {self._get_enabled_status(value)}")

    @todo_settings.command(name="embeds", aliases=["embed"])
    async def todo_use_embeds(self, ctx: commands.Context, value: bool):
        """Set your todo list to use embeds

        **NOTE** embeds will *only* be used if possible in the current channel

        **Arguments**
            - `value` Whether to use embeds or not
        """
        current = await self.cache.get_user_setting(ctx.author, "use_embeds")
        if current == value:
            currently = "currently" if value else "not currently"
            return await ctx.send(f"Embeds are {currently} enabled")
        await self.cache.set_user_setting(ctx.author, "use_embeds", value)
        await ctx.send(f"Embeds are now {self._get_enabled_status(value)}")
