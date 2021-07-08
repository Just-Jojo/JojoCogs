# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from datetime import datetime
from enum import Enum
from typing import Union

import discord
from redbot.core import commands

from ..abc import TodoMixin
from ..utils import timestamp_format


class PresetsEnum(Enum):
    minimal = {
        "combine_lists": False,
        "extra_details": False,
        "pretty_todos": False,
        "number_todos": False,
        "use_markdown": False,
        "use_timestamps": False,
    }
    pretty = {
        "combine_lists": True,
        "extra_details": True,
        "pretty_todos": True,
        "number_todos": True,
        "use_markdown": True,
        "use_timestamps": True,
    }


class PresetConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, arg: str):
        if arg.lower() not in ("pretty", "minimal"):
            raise commands.BadArgument(
                f'Argument must be "minimal" or "pretty" not "{arg}"'
            )
        if arg.lower() == "pretty":
            return PresetsEnum.pretty
        return PresetsEnum.minimal


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
        enabled = self._get_enabled_status(value)
        if current == value:
            return await ctx.send(f"Markdown blocks are already {enabled}")
        await self.cache.set_user_setting(ctx.author, "use_markdown", value)
        await ctx.send(f"Markdown blocks are now {enabled}")

    @todo_settings.command(name="embeds", aliases=["embed"])
    async def todo_use_embeds(self, ctx: commands.Context, value: bool):
        """Set your todo list to use embeds

        **NOTE** embeds will *only* be used if possible in the current channel

        **Arguments**
            - `value` Whether to use embeds or not
        """
        current = await self.cache.get_user_setting(ctx.author, "use_embeds")
        enabled = self._get_enabled_status(value)
        if current == value:
            return await ctx.send(f"Embeds are already {enabled}")
        await self.cache.set_user_setting(ctx.author, "use_embeds", value)
        await ctx.send(f"Embeds are now {enabled}")

    @todo_settings.command(name="number", aliases=["index"])
    async def todo_number_todos(self, ctx: commands.Context, value: bool):
        """Set your todo list to index todos whilst listing them

        \u200b
        **Arguments**
            - `value` Whether to index todos or not
        """
        current = await self.cache.get_user_setting(ctx.author, "number_todos")
        if current == value:
            do_do_not = "" if value else "do not "
            return await ctx.send(f"Todo lists already {do_do_not}index todos")
        now_no_longer = "now" if value else "no longer"
        await ctx.send(f"Todo will {now_no_longer} index todos")
        await self.cache.set_user_setting(ctx.author, "number_todos", value)

    @todo_settings.command(name="colour")
    async def todo_colour(
        self, ctx: commands.Context, colour: Union[discord.Colour, None]
    ):
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

    @todo_settings.command(name="timestamps", aliases=["timestamp", "ts"])
    async def todo_use_timestamps(self, ctx: commands.Context, value: bool):
        """Set whether todo should use timestamps

        **NOTE** this will only be in effect if the message is not embedded. This might also be removed at a later date

        **Arguments**
            - `value` Whether to enable timestamps
        """
        current = await self.cache.get_user_setting(ctx.author, "use_timestamps")
        if current == value:
            currently = "" if value else "does not "
            s = "s" if value else ""
            return await ctx.send(f"Todo already {current}use{s} timestamps")
        enabled = self._get_enabled_status(value)
        await ctx.send(f"Timestamps are now {enabled}")
        await self.cache.set_user_setting(ctx.author, "use_timestamps", value)

    @todo_settings.command(name="combine", aliases=["combined"])
    async def todo_combined(self, ctx: commands.Context, value: bool):
        """Combine your todo list with your completed list

        **NOTE** this will only be in effect if you have completed todos

        **Arguments**
            - `value` Whether to combine your lists or not
        """
        current = await self.cache.get_user_setting(ctx.author, "combine_lists")
        enabled = self._get_enabled_status(value)
        if current == value:
            return await ctx.send(f"Combined lists are already {enabled}")
        await ctx.send(f"Combined lists are now {enabled}")
        await self.cache.set_user_setting(ctx.author, "combine_lists", value)

    @todo_settings.command(name="pretty")
    async def todo_pretty(self, ctx: commands.Context, value: bool):
        """Have your todo list look pretty

        This will set it to use emojis such as ✅ and 🟩

        **Arguments**
            - `value` Whether pretty should be enabled
        """
        current = await self.cache.get_user_setting(ctx.author, "pretty_todos")
        enabled = self._get_enabled_status(value)
        if current == value:
            return await ctx.send(f"Pretty todos are already {enabled}")
        await ctx.send(f"Pretty todos are now {enabled}")
        await self.cache.set_user_setting(ctx.author, "pretty_todos", value)

    @todo_settings.command(name="details")
    async def todo_extra_details(self, ctx: commands.Context, value: bool):
        """Have your todo list send you extra details.

        This may be removed at a later date

        **Arguments**
            - `value` Whether you should recieve extra details
        """
        current = await self.cache.get_user_setting(ctx.author, "extra_details")
        enabled = self._get_enabled_status(value)
        if current == value:
            return await ctx.send(f"Extra details are already {enabled}")
        await ctx.send(f"Extra details are now {enabled}")
        await self.cache.set_user_setting(ctx.author, "extra_details", value)

    @todo_settings.command(name="preset")
    async def preset(self, ctx: commands.Context, preset: PresetConverter):
        """Set you settings to a preset

        Current presets are `minimal` and `pretty`

        **Arguments**
            - `preset` The preset for your settings. Must be either `minimal` or `pretty` as of right now.
        """
        data = preset.value  # type:ignore
        old_settings = await self.cache.get_user_item(ctx.author, "user_settings")
        old_settings.update(data)
        await self.cache.set_user_item(ctx.author, "user_settings", old_settings)
        await ctx.send(f'Done. Your settings are now set to the preset "{preset.name}"')

    @todo_settings.command(name="autosort")
    async def todo_autosort(self, ctx: commands.Context, value: bool):
        """Set your todo list to auto sort

        **NOTE** This command won't autosort your todos. Use `[p]todo sort` to sort your todos

        **Arguments**
            - `value` Whether your todo list should auto sort
        """

        current = await self.cache.get_user_setting(ctx.author, "autosorting")
        enabled = self._get_enabled_status(value)
        if current == value:
            return await ctx.send(f"Autosorting is already {enabled}")
        await self.cache.set_user_setting(ctx.author, "autosorting", value)
        await ctx.send(f"Autosorting is now {enabled}")

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
                settings_dict["Colour"] = (
                    hex(value).replace("0x", "#") if value is not None else "Bot colour"
                )
                continue
            if key in ("private", "reverse_sort"):
                continue
            key = key.replace("_", " ").capitalize()
            settings_dict[key] = self._get_enabled_status(value).capitalize()

        msg = "\n".join(f"**{k}** {v}" for k, v in settings_dict.items())
        title = f"{ctx.author.name}'s todo settings"
        if await ctx.embed_requested():
            colour = (
                k
                if (k := user_settings["colour"]) is not None
                else await ctx.embed_colour()
            )
            embed = discord.Embed(
                title=title, description=msg, colour=colour, timestamp=datetime.utcnow()
            )
            kwargs = {"embed": embed, "content": None}
        else:
            msg = f"**{title}**\n\n{msg}\n{timestamp_format()}"
            kwargs = {"embed": None, "content": msg}
        await ctx.send(**kwargs)
