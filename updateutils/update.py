# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import asyncio
import asyncio.subprocess as asp
import os
import sys
from datetime import datetime
from pathlib import Path

import aiohttp
import discord
from discord.ext import tasks
from jojo_utils import __version__ as jojoutils_version
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.predicates import MessagePredicate
import logging
from typing import Optional


log = logging.getLogger("red.JojoCogs.updateutils")
VERSION_URL = r"https://raw.githubusercontent.com/Just-Jojo/jojoutils/master/version"


class UpdateUtils(commands.Cog):
    """A developer tool to update Jojo's utils"""

    __authors__ = [
        "Jojo#7791",
    ]
    __version__ = "1.0.1"

    def __init__(self, bot: Red):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        sep = os.path.sep
        # This section is a modified version of Jack's shell's `get_env` function
        # Which is copyrighted under the Apache-2.0 License.
        # https://github.com/jack1142/JackCogs/blob/v3/shell/utils.py#L30
        self.path = Path(sys.executable).resolve()
        self.command = "-m pip install -U git+https://github.com/Just-Jojo/jojoutils.git"
        self.latest_version: Optional[str] = None
        self.update_version.start()

    def format_help_for_context(self, ctx: commands.Context):
        pre = super().format_help_for_context(ctx)
        plural = "s" if len(self.__authors__) > 1 else ""
        return (
            f"{pre}\n"
            f"Author{plural}: {', '.join(self.__authors__)}\n"
            f"Version: {self.__version__}"
        )

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete"""
        return

    async def red_get_data_for_user(self, **kwargs):
        return {}

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())
        self.update_version.cancel()

    async def _update_utils(self):
        process = await asyncio.create_subprocess_shell(
            F"{self.path} {self.command}",
            stdin=asp.PIPE, stderr=asp.STDOUT,
        )
        try:
            out, err = await process.communicate()
        except Exception as e:
            log.error("Error running the command", exc_info=e)
        return out, err

    async def cog_check(self, ctx: commands.Context):
        # Owoner only check
        return await self.bot.is_owner(ctx.author)

    async def _get_version(self):
        async with self.session.get(VERSION_URL) as re:
            self.latest_version = await re.text()

    @commands.group(name="jojoutils")
    async def jojo_utils(self, ctx: commands.Context):
        """Base command for checking/updating Jojo's utils"""
        pass

    @jojo_utils.command(name="check")
    async def jojo_utils_check_updates(self, ctx: commands.Context):
        """Check if you need to update Jojo's utils"""

        description = "You are up to date!"
        if jojoutils_version != self.latest_version:
            description = (
                f"You are out of date! "
                f"You are on version {jojoutils_version} but version {self.latest_version} is available!"
            )
        kwargs = {"content": f"Jojo Utils updater\n\n{description}"}
        if await ctx.embed_requested():
            embed = discord.Embed(
                title="Jojo Utils updater",
                description=description,
                colour=await ctx.embed_colour(),
            )
            embed.set_thumbnail(
                url="https://raw.githubusercontent.com/Just-Jojo/JojoCog-Assets/main/JOJO_COGS.png"
            )
            embed.timestamp = datetime.utcnow()
            kwargs = {"embed": embed}
        await ctx.send(**kwargs)

    @jojo_utils.command(name="version")
    async def jojo_utils_version(self, ctx: commands.Context):
        """Shows the version of the cog and Jojo's utils"""

        data = {
            "Cog Version": self.__version__,
            "Jojo Utils version": jojoutils_version,
            "Latest version on GitHub": self.latest_version,
        }
        kwargs = {
            "content": f"Jojo Utils updater\n\n"
            + "\n".join(f"**{k}** {v}" for k, v in data.items())
        }
        if await ctx.embed_requested():
            embed = discord.Embed(
                title="Jojo Utils updater",
                description="Versions!",
                colour=await ctx.embed_colour(),
            )
            embed.set_thumbnail(
                url="https://raw.githubusercontent.com/Just-Jojo/JojoCog-Assets/main/JOJO_COGS.png"
            )
            [embed.add_field(name=k, value=v, inline=False) for k, v in data.items()]
            embed.timestamp = datetime.utcnow()
            kwargs = {"embed": embed}
        await ctx.send(**kwargs)

    @jojo_utils.command(name="update")
    async def jojo_utils_update(self, ctx: commands.Context):
        """Attempt to update your version of Jojo's utils"""

        if jojoutils_version == self.latest_version:
            await ctx.send("Your version of Jojo's utils is up to date")
            return
        pred = MessagePredicate.yes_or_no(ctx)
        msg = await ctx.send(
            "This is the command that will be ran. Are you okay with this (input y/n)?"
            f"\n\n`{self.path} {self.command}`"
        )
        try:
            msg = await self.bot.wait_for("message", check=pred, timeout=15.0)
        except asyncio.TimeoutError:
            pass
        if not pred.result:
            await ctx.send("That's fine. If you ever want to update you can run that command in your console.")
            return
        try:
            await msg.add_reaction("\N{WHITE HEAVY CHECK MARK}")
        except Exception:
            pass
        async with ctx.typing():
            await self._update_utils()
        await ctx.send("Done. You can now restart your bot to have the changes be put into effect.")

    @tasks.loop(hours=4)
    async def update_version(self):
        await self._get_version()
