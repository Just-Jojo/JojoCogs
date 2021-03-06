# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import asyncio
import logging
import re
from itertools import cycle
from typing import List

import discord
from discord.ext import tasks
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import pagify
from redbot.core.utils.predicates import MessagePredicate
from jojo_utils import Menu

from .menus import Pages

log = logging.getLogger("red.JojoCogs.cyclestatus")
_config_structure = {
    "global": {
        "statuses": [],
        "use_help": True,
        "next_iter": 0,
    },
}


def positive_int(arg: str) -> int:
    try:
        ret = int(arg)
    except ValueError:
        raise commands.BadArgument(message=f"{arg} is not an int")
    if ret < 1:
        raise commands.BadArgument(message=f"'{arg}' is not positive")
    return ret


class CycleStatus(commands.Cog):
    """Automatically change the status of your bot every minute"""

    __version__ = "1.0.1"
    __author__ = ["Jojo#7791"]

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, 115849, True)
        self.config.register_global(**_config_structure["global"])
        self.task: asyncio.Task = self.bot.loop.create_task(self.init())

    async def init(self):
        await self.bot.wait_until_red_ready()
        self.main_task.start()

    def cog_unload(self):
        if not self.task.done():
            self.task.cancel()
            return  # Worst case :/
        self.main_task.cancel()

    def format_help_for_context(self, ctx: commands.Context):
        return (
            f"{super().format_help_for_context(ctx)}"
            f"\nVersion `{self.__version__}`"
            f"\nAuthor(s) `{', '.join(self.__author__)}`"
        )

    @commands.group()
    @commands.is_owner()
    async def status(self, ctx):
        """Commands working with the status"""
        pass

    @status.command(name="usehelp")
    async def status_set(self, ctx, toggle: bool = None):
        """Change whether the status should have ` | [p]help`"""
        if toggle is None:
            msg = f"Added help is {'enabled' if await self.config.use_help() else 'disabled'}"
            return await ctx.send(msg)
        await self.config.use_help.set(toggle)
        await ctx.tick()

    @status.command(name="add")
    async def status_add(self, ctx, *, status: str):
        """Add a status to the list"""
        async with self.config.statuses() as s:
            s.append(status)
        await ctx.tick()

    @status.command(name="remove", aliases=["del", "rm", "delete"])
    async def status_remove(self, ctx, num: positive_int = None):
        """Remove a status from the list"""
        if num is None:
            return await ctx.invoke(self.status_list)
        num -= 1
        async with self.config.statuses() as sts:
            if num >= len(sts):
                return await ctx.send("You don't have that many statuses, silly")
            sts.pop(num)
        await ctx.tick()

    @status.command(name="list")
    async def status_list(self, ctx):
        """List the available statuses"""
        if not (status := await self.config.statuses()):
            return await ctx.send("There are no statuses")
        await self._show_statuses(ctx=ctx, statuses=status)

    @status.command(name="clear")
    async def status_clear(self, ctx):
        """Clear all of the statuses"""
        msg = await ctx.send("Would you like to clear all of your statuses? (y/n)")
        pred = MessagePredicate.yes_or_no()
        try:
            await self.bot.wait_for("message", check=pred)
        except asyncio.TimeoutError:
            pred.result = False
        await msg.delete()
        if not pred.result:
            return await ctx.send("Okay! I won't remove your statuses")

        await self.config.statuses.set([])
        await self.bot.change_presence()
        await ctx.tick()

    @tasks.loop(minutes=1)
    async def main_task(self):
        statuses = await self.config.statuses()
        if not statuses:
            return
        try:
            # So, sometimes this gets larger than the list of the statuses
            # so, if this raises an `IndexError` we need to reset the next iter
            msg = statuses[(nl := await self.config.next_iter())]
        except IndexError:
            nl = 0  # Hard reset
            msg = statuses[0]
        if await self.config.use_help():
            prefix = (await self.bot.get_valid_prefixes())[0]
            prefix = re.sub(rf"<@!?{self.bot.user.id}>", f"@{self.bot.user.name}", prefix)
            msg += f" | {prefix}help"
        game = discord.Game(name=msg)
        await self.bot.change_presence(activity=game)
        nl = 0 if len(statuses) - 1 == nl else nl + 1
        await self.config.next_iter.set(nl)

    async def _num_lists(self, data: List[str]) -> List[str]:
        """|coro|

        Return a list of numbered items
        """
        return [f"{num}. {d}" for num, d in enumerate(data, 1)]

    async def _show_statuses(self, ctx: commands.Context, statuses: List[str]) -> None:
        source = Pages(
            list(pagify("\n".join(await self._num_lists(statuses)), page_length=400)),
            title="Statuses",
        )
        await Menu(source=source).start(ctx, channel=ctx.channel)

    async def red_delete_data_for_user(self, *, requester: str, user_id: int) -> None:
        """Nothing to delete"""
        return
