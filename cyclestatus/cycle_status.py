# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import asyncio
import logging
import random
import re
from datetime import datetime
from itertools import cycle
from typing import List, Optional

import discord
from discord.ext import tasks
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_list, pagify
from redbot.core.utils.predicates import MessagePredicate

from .menus import Menu, Pages, PositiveInt

log = logging.getLogger("red.JojoCogs.cyclestatus")
_config_structure = {
    "global": {
        "statuses": [],
        "use_help": True,
        "next_iter": 0,
        "toggled": True,  # Toggle if the status should be cycled or not
        "random": False,
    },
}

_bot_guild_var = r"{bot_guild_count}"
_bot_member_var = r"{bot_member_count}"
_bot_prefix_var = r"{bot_prefix}"


class CycleStatus(commands.Cog):
    """Automatically change the status of your bot every minute"""

    __authors__ = ["Jojo#7791"]
    __version__ = "1.0.8"
    # These people have suggested something for this cog!
    __suggesters__ = ["ItzXenonUnity | Lou#2369", "StormyGalaxy#1297"]

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, 115849, True)
        self.config.register_global(**_config_structure["global"])
        self.task: asyncio.Task = self.bot.loop.create_task(self.init())
        self.toggled: Optional[bool] = None
        self.random: Optional[bool] = None
        self.last_random: Optional[int] = None

    async def init(self):
        await self.bot.wait_until_red_ready()
        self.main_task.start()
        self.toggled = await self.config.toggled()
        self.random = await self.config.random()

    def cog_unload(self):
        self.task.cancel()
        self.main_task.cancel()

    def format_help_for_context(self, ctx: commands.Context):
        pre = super().format_help_for_context(ctx)
        plural = "s" if len(self.__authors__) > 1 else ""
        return (
            f"{pre}\n"
            f"Author{plural}: `{humanize_list(self.__authors__)}`\n"
            f"Version: `{self.__version__}`\n"
            f"People who have put in suggestions: `{humanize_list(self.__suggesters__)}`"
        )

    @commands.group()
    @commands.is_owner()
    async def status(self, ctx):
        """Commands working with the status"""
        pass

    @status.command()
    @commands.check(lambda ctx: ctx.cog.random is False)
    async def forcenext(self, ctx):
        """Force the next status to display on the bot"""
        nl = await self.config.next_iter()
        status = (statuses := await self.config.statuses())[nl]
        await self.config.next_iter.set(nl + 1 if nl < len(statuses) else 0)
        await self._status_add(status, await self.config.use_help())
        await ctx.tick()

    @status.command(name="usehelp")
    async def status_set(self, ctx, toggle: bool = None):
        """Change whether the status should have ` | [p]help`

        \u200b
        **Arguments**
            - `toggle` Whether help should be used or not.
        """
        if toggle is None:
            msg = f"Added help is {'enabled' if await self.config.use_help() else 'disabled'}"
            return await ctx.send(msg)
        await self.config.use_help.set(toggle)
        await ctx.tick()

    @status.command(name="add")
    async def status_add(self, ctx, *, status: str):
        """Add a status to the list

        Put `{bot_guild_count}` or `{bot_member_count}` in your message to have the user count and guild count of your bot! You can also put `{bot_prefix}` in your message to have the bot's prefix be displayed (eg. `{bot_prefix}ping`)

        **Arguments**
            - `status` The status to add to the cycle.
        """
        async with self.config.statuses() as s:
            s.append(status)
        await ctx.tick()

    @status.command(name="remove", aliases=["del", "rm", "delete"])
    async def status_remove(self, ctx, num: PositiveInt = None):  # type:ignore
        """Remove a status from the list

        \u200b
        **Arguments**
            - `num` The index of the status you want to remove.
        """
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

    @status.command(name="random")
    async def status_random(self, ctx: commands.Context, value: bool):
        """Have the bot cycle to a random status

        \u200b
        **Arguments**
            - `value` Whether to have random statuses be enabled or not
        """

        if value == self.random:
            enabled = "enabled" if value else "disabled"
            return await ctx.send(f"Random statuses are already {enabled}")
        self.random = value
        await self.config.random.set(value)
        now_no_longer = "now" if value else "no longer"
        await ctx.send(f"Statuses will {now_no_longer} be random")

    @status.command(name="toggle")
    async def status_toggle(self, ctx: commands.Context, value: bool):
        """Toggle whether the status should be cycled.

        This is handy for if you want to keep your statuses but don't want them displayed at the moment

        **Arguments**
            - `value` Whether to toggle cycling statues
        """
        if value == self.toggled:
            enabled = "enabled" if value else "disabled"
            return await ctx.send(f"Cycling statuses is already {enabled}")
        self.toggled = value
        await self.config.toggled.set(value)
        now_not = "now" if value else "not"
        await ctx.send(f"I will {now_not} cycle statuses")

    @status.command(name="settings")
    async def status_settings(self, ctx: commands.Context):
        """Show your current settings for the cycle status cog"""
        settings = {
            "Randomized statuses?": "Enabled" if self.random else "Disabled",
            "Toggled?": "Yes" if self.toggled else "No",
            "Statuses?": f"See `{ctx.clean_prefix}status list`",
        }
        title = "Your Cycle Status settings"
        kwargs = {
            "content": f"**{title}**\n\n"
            + "\n".join(f"**{k}** {v}" for k, v in settings.items())
        }
        if await ctx.embed_requested():
            embed = discord.Embed(
                title=title, colour=await ctx.embed_colour(), timestamp=datetime.utcnow()
            )
            [embed.add_field(name=k, value=v, inline=False) for k, v in settings.items()]
            kwargs = {"embed": embed}
        await ctx.send(**kwargs)

    @tasks.loop(minutes=1)
    async def main_task(self):
        if not (statuses := await self.config.statuses()) or not self.toggled:
            return
        if self.random:
            if self.last_random is not None and len(statuses) > 1:
                statuses.pop(self.last_random)  # Remove that last picked one
            msg = random.choice(statuses)
        else:
            try:
                # So, sometimes this gets larger than the list of the statuses
                # so, if this raises an `IndexError` we need to reset the next iter
                msg = statuses[(nl := await self.config.next_iter())]
            except IndexError:
                nl = 0  # Hard reset
                msg = statuses[0]
        await self._status_add(msg, await self.config.use_help())
        if not self.random:
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

    async def _status_add(self, status: str, use_help: bool) -> None:
        status = status.replace(_bot_guild_var, str(len(self.bot.guilds))).replace(
            _bot_member_var, str(len(self.bot.users))
        )

        prefix = (await self.bot.get_valid_prefixes())[0]
        prefix = re.sub(rf"<@!?{self.bot.user.id}>", f"@{self.bot.user.name}", prefix)

        status = status.replace(_bot_prefix_var, prefix)

        if use_help:
            status += f" | {prefix}help"
        game = discord.Game(name=status)
        await self.bot.change_presence(activity=game)
