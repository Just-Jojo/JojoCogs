# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from datetime import datetime
from typing import Dict, Optional, Union

import discord
from redbot.core import commands

from .abc import ToDoMixin
from ..utils import PresetConverter # type:ignore


def get_toggle(setting: bool) -> str:
    return "enabled" if setting else "disabled"


class Settings(ToDoMixin):
    """Settings for todo!"""

    _embed_title = "{0.author.name}'s settings"

    @commands.group("todoset")
    async def todo_set(self, ctx):
        """Configure how you would like your todo lists to look like

        I am always looking for new ways to customize your lists
        If you have an idea use `[p]todo suggestions` and follow the instructions :D
        """
        pass

    @todo_set.command(usage="<use embeds>", aliases=["useembeds"])
    async def embed(self, ctx, toggle: bool):
        """Set your list to be embedded"""
        toggled = get_toggle(toggle)
        msg = f"Embeds are now {toggled}"
        already_set = f"Embeds are already {toggled}"
        await self._toggler(ctx, toggle, "use_embeds", msg, already_set)

    @todo_set.command(usage="<use markdown blocks>", aliases=["usemd"])
    async def md(self, ctx, toggle: bool):
        """Set your lists to use markdown blocks"""
        toggled = get_toggle(toggle)
        msg = f"Markdown is now {toggled}"
        already_set = f"Markdown is already {toggled}"
        await self._toggler(ctx, toggle, "use_md", msg, already_set)

    @todo_set.command(usage="<autosort todo lists>", aliases=["doautosort"])
    async def autosort(self, ctx, toggle: bool):
        """Set your list to autosort"""
        toggled = get_toggle(toggle)
        msg = f"Autosorting is now {toggled}"
        already_set = f"Autosorting is already {toggled}"
        await self._toggler(ctx, toggle, "autosort", msg, already_set)

    @todo_set.command(usage="<combine lists>")
    async def combine(self, ctx, toggle: bool):
        """Set your lists to be combined"""
        toggled = get_toggle(toggle)
        msg = f"Combined lists are now {toggled}"
        already_set = f"Combined lists are already {toggled}"
        await self._toggler(ctx, toggle, "combined_lists", msg, already_set)

    @todo_set.command(usage="<show timestamp>")
    async def timestamp(self, ctx, toggle: bool):
        """Toggle for Discord timestamps to be shown in `[p]todo add`."""
        toggled = get_toggle(toggle)
        msg = f"Timestamps are now {toggled}."
        already_set = f"Timestamps are already {toggled}."
        await self._toggler(ctx, toggle, "timestamp", msg, already_set)

    @todo_set.command(usage="<give more details>")
    async def details(self, ctx, toggle: bool):
        """Set your lists to give you extra details when adding and removing them"""
        toggled = get_toggle(toggle)
        msg = f"Extra details is now {toggled}"
        already_set = f"Extra details is already {toggled}"
        await self._toggler(ctx, toggle, "detailed_pop", msg, already_set)

    @todo_set.command()
    async def private(self, ctx, toggle: bool):
        """Set your lists to be private"""
        toggled = get_toggle(toggle)
        msg = (
            f"Private lists are now {toggled} "
            "(note, you will need to have the bot able to "
            "dm you otherwise this will not work)"
        )
        already_set = f"Private lists are already {toggled}"
        await self._toggler(ctx, toggle, "private", msg, already_set)

    @todo_set.command(aliases=["color"])
    async def colour(self, ctx, color: discord.Colour = None):
        """Set the colour of your embeds"""
        msg: str
        if color is None:
            msg = "The embed colour is now reset (it will be the bot's embed colour)"
        else:
            msg = f"The embed colour is now {color}"
            color = color.value
        await ctx.send(msg)
        await self.config.user(ctx.author).colour.set(color)
        await self.update_cache(user_id=ctx.author.id)

    @todo_set.command(name="preset")
    async def todoset_preset(self, ctx: commands.Context, preset: PresetConverter):
        """Set your todo settings to a preset

        **Types**
        - >   preset: Choose either \"minimal\" or \"fancy\""""
        conf = await self._get_user_config(ctx.author)
        for key, value in preset.items():
            conf[key] = value # type:ignore
        await self.config.user(ctx.author).set(conf)
        await ctx.tick()

    @todo_set.command(aliases=["settings"])
    async def showsettings(self, ctx):
        """Show your settings"""
        conf = await self._get_user_config(ctx.author)
        embedded = conf["use_embeds"]
        private = conf["private"]
        settings = {
            "Markdown blocks": get_toggle(conf["use_md"]).capitalize(),
            "Embeds": get_toggle(embedded).capitalize(),
            "Private lists": get_toggle(private).capitalize(),
            "Autosorting": get_toggle(conf["autosort"]).capitalize(),
            "Reverse sorting": get_toggle(conf["reverse_sort"]).capitalize(),
            "Combined lists": get_toggle(conf["combined_lists"]).capitalize(),
            "Extra details": get_toggle(conf["detailed_pop"]).capitalize(),
            "Colour": conf["colour"] or "Bot's embed colour",
            "Non embed timestamps": get_toggle(conf["timestamp"]).capitalize(),
        }
        if private:
            return await self._private_send_settings(
                ctx, use_embed=embedded, settings=settings, timestamp=conf.get("timestamp", True)
            )
        if await ctx.embed_requested() and embedded:
            embed = discord.Embed(
                title=self._embed_title.format(ctx),
                colour=conf["colour"] or await ctx.embed_colour(),
                timestamp = datetime.utcnow(),
            )
            [
                embed.add_field(name=key, value=value, inline=True)
                for key, value in settings.items()
            ]
            kwargs = {"embed": embed}
        else:
            humanized_settings = "\n".join(
                f"**{key}** {value}" for key, value in settings.items()
            )
            msg = (
                f"{self._embed_title.format(ctx)}\n\n"
                f"{humanized_settings}"
            )
            if conf.get("timestamp", True):
                msg += f"\n<t:{int(datetime.now().timestamp())}>"
            kwargs = {"content": msg}
        await ctx.send(**kwargs)

    async def _toggler(
        self, ctx: commands.Context, toggle: bool, key: str, msg: str, already_set: str
    ):
        """DRY basically"""
        setting = await self.config.user(ctx.author).get_raw(key)
        if setting == toggle:
            return await ctx.send(content=already_set)
        await ctx.send(content=msg)
        await self.config.user(ctx.author).set_raw(key, value=toggle)
        await self.update_cache(user_id=ctx.author.id)

    async def _private_send_settings(
        self, ctx: commands.Context, use_embed: bool, settings: Dict[str, str], timestamp: bool
    ):
        """I never said I was good at naming methods"""
        title = self._embed_title.format(ctx)
        humanized_settings = "\n".join(
            f"**{key}** {value}" for key, value in settings.items()
        )
        if use_embed:
            embed: discord.Embed = discord.Embed(
                title=title, colour=await ctx.embed_colour(), timestamp=datetime.utcnow()
            )
            [
                embed.add_field(name=key, value=value, inline=True)
                for key, value in settings.items()
            ]
            kwargs = {"embed": embed}
        else:
            kwargs = {"content": f"{title}\n\n{humanized_settings}"}
            if timestamp:
                kwargs["content"] += f"\n<t:{int(datetime.now().timestamp())}>"
        try:
            await ctx.author.send(**kwargs)
        except discord.Forbidden:
            await ctx.send(
                "I can't dm you! If you would like to use private lists, please allow me to dm you"
            )
            await self.config.user(ctx.author).private.set(False)
        else:
            return
        if await ctx.embed_requested() and embed:
            await ctx.send(**kwargs)
        else:
            await ctx.send(content=f"{title}\n\n{humanized_settings}")
