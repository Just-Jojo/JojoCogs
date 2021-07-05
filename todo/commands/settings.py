# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import discord
from redbot.core import commands
from datetime import datetime

from ..abc import TodoMixin
from ..utils import timestamp_format

from typing import Union



class Settings(TodoMixin):
    """Commands for todo's settings"""

    @staticmethod
    def _get_enabled_status(value: bool) -> str:
        """An internal function to get an enabled status based off a bool"""
        return "enabled" if value else "disabled"

    @commands.group(name="todoset", aliases=["todosettings"])
    async def todo_settings(self, ctx: commands.Context):
        """Commands for configuring your todo list"""
        # await ctx.invoke(self.todo_show_settings) # TODO Decide on this

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

    @todo_settings.command(name="number", aliases=["index"])
    async def todo_number_todos(self, ctx: commands.Context, value: bool):
        """Set your todo list to index todos whilst listing them

        \u200b
        **Arguments**
            - `value` Whether to index todos or not
        """
        current = await self.cache.get_user_setting(ctx.author, "number_todos")
        if current == value:
            do_do_not = "" if value else "do not"
            return await ctx.send(f"Todo lists already {do_do_not} index todos")
        await self.cache.set_user_setting(ctx.author, "number_todos", value)
        now_no_longer = "now" if value else "no longer"
        await ctx.send(f"Todo will {now_no_longer} index todos")

    @todo_settings.command(name="colour")
    async def todo_colour(self, ctx: commands.Context, colour: Union[discord.Colour, None]):
        """Set the colour of your todo list's embeds

        **NOTE** this will only work if you have embeds enabled and the bot can embed links in the channel

        **Arguments**
            - `colour` The colour you would like the embed to be. Type `None` to set it to the bot's default embed colour
        """
        if colour is not None:
            msg = f"Set the colour to `{colour}`"
            colour = colour.value
        else:
            msg = "Reset the colour to the bot's default embed colour"
        await ctx.send(msg)
        await self.cache.set_user_setting(ctx.author, "colour", colour)

    @todo_settings.command(name="showsettings")
    async def todo_show_settings(self, ctx: commands.Context):
        """Show your todo settings
        
        This will list the following:
            - `indexed todos`
            - `colour`
            - `embedded`
            - `markdown`
            - `autosort`
            - `combined lists`
            - `pretty todos`
            - `timestamps`
            - `extra details`
        """
        user_settings = await self.cache.get_user_item(ctx.author, "user_settings")
        settings_dict = {}
        for key, value in user_settings.items():
            if key == "colour":
                settings_dict["Colour"] = hex(value).replace("0x", "#") if value is not None else "Bot colour"
                continue
            if key in ("private", "reverse_sort"):
                continue
            key = key.replace("_", " ").capitalize()
            settings_dict[key] = self._get_enabled_status(value).capitalize()
        msg = "\n".join(f"**{k}** {v}" for k, v in settings_dict.items())
        title = f"{ctx.author.name}'s todo settings"
        if await ctx.embed_requested():
            colour = k if (k := user_settings["colour"]) is not None else await ctx.embed_colour()
            embed = discord.Embed(
                title=title, description=msg, colour=colour, timestamp=datetime.utcnow()
            )
            kwargs = {"embed": embed, "content": None}
        else:
            msg = f"**{title}**\n\n{msg}\n{timestamp_format()}"
            kwargs = {"embed": None, "content": msg}
        await ctx.send(**kwargs)
