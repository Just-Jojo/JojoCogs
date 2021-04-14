"""
MIT License

Copyright (c) 2021 Jojo#7711

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import discord
from redbot.core import commands

from .abc import ToDoMixin


def get_toggle(setting: bool) -> str:
    return "enabled" if setting else "disabled"


class Settings(ToDoMixin):
    """Settings for todo!"""

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
        await self._toggler(
            ctx, toggle, "use_embeds", msg, already_set
        )  # TODO _toggler method

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
        msg = f"Private lists are now {toggled}"
        already_set = f"Private lists are already {toggled}"
        await self._toggler(ctx, toggle, "private", msg, already_set)

    @todo_set.command(aliases=["settings"])
    async def showsettings(self, ctx):
        """Show your settings"""
        conf = self.config.user(ctx.author)
        settings = {
            "Markdown blocks": get_toggle(await conf.use_md()).capitalize(),
            "Embeds": get_toggle(await conf.use_embeds()).capitalize(),
            "Private lists": get_toggle(await conf.private()).capitalize(),
            "Autosorting": get_toggle(await conf.autosort()).capitalize(),
            "Reverse sorting": get_toggle(await conf.reverse_sort()).capitalize(),
            "Combined lists": get_toggle(await conf.combined_lists()).capitalize(),
            "Extra details": get_toggle(await conf.detailed_pop()).capitalize(),
        }
        if await ctx.embed_requested():
            embed = discord.Embed(
                title=f"{ctx.author.name}'s todo settings",
                colour=await ctx.embed_colour(),
            )
            [
                embed.add_field(name=key, value=value, inline=True)
                for key, value in settings.items()
            ]
            kwargs = {"embed": embed}
        else:
            msg = f"**{ctx.author.name}'s todo settings**"
            msg += "\n".join(f"**{key}:** `{value}`" for key, value in settings.items())
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
