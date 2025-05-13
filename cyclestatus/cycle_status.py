# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from __future__ import annotations

import asyncio
import enum
import logging
import random
import re

try:
    from datetime import datetime, UTC as DatetimeUTC

    def get_datetime():
        return datetime.now(DatetimeUTC)

except ImportError:
    from datetime import datetime

    def get_datetime():
        return datetime.utcnow()


from typing import Final, List, Optional, Iterable, Dict, Union, TYPE_CHECKING

import discord
from discord.ext import tasks
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_list, humanize_number, pagify
from redbot.core.utils.predicates import MessagePredicate

from .menus import Menu, Page, PositiveInt

__all__ = ["CycleStatus"]

log = logging.getLogger("red.JojoCogs.cyclestatus")
_config_structure: Dict[str, Dict[str, Union[list, int, str, bool]]] = {
    "global": {
        "statuses": [],
        "use_help": True,
        "next_iter": 0,
        "toggled": True,  # Toggle if the status should be cycled or not
        "random": False,
        "status_type": 0,  # int, the value corresponds with a `discord.ActivityType` value
        "status_mode": "online",  # str, the value that corresponds with a `discord.Status` value
        "show_bots": False,
    },
}

_bot_guild_var: Final[str] = r"{bot_guild_count}"
_bot_member_var: Final[str] = r"{bot_member_count}"
_bot_prefix_var: Final[str] = r"{bot_prefix}"


def humanize_enum_vals(e: enum.Enum) -> str:
    return humanize_list(
        list(map(lambda c: f"`{c.name.replace('_', ' ')}`", e))  # type:ignore
    )


def _get_non_bot_users(users: Iterable[discord.User]) -> int:
    actual = [user for user in users if not user.bot]
    return len(actual)


def _enabled(val: bool) -> str:
    return "enabled" if val else "disabled"


class ActivityType(enum.Enum):
    """Copy of `discord.ActivityType` minus `unknown`"""

    playing = 0
    listening = 2
    watching = 3
    custom = 4
    competing = 5

    def __int__(self):
        return self.value


if TYPE_CHECKING:
    ActivityConverter = ActivityType
else:

    class ActivityConverter(commands.Converter):
        async def convert(self, ctx: commands.Context, arg: str) -> ActivityType:
            arg = arg.lower()
            ret = getattr(ActivityType, arg, None)
            if not ret:
                raise commands.BadArgument(
                    f"The argument must be one of the following: "
                    f"{humanize_enum_vals(ActivityType)}"
                )
            return ret


class Status(enum.Enum):
    online = "online"
    idle = "idle"
    do_not_disturb = dnd = "dnd"

    def __str__(self) -> str:
        return self.value


if TYPE_CHECKING:
    StatusConverter = Status
else:

    class StatusConverter(commands.Converter):
        async def convert(self, ctx: commands.Context, arg: str) -> Status:
            arg = arg.lower().replace(" ", "_")
            try:
                return Status(arg)
            except ValueError:
                raise commands.BadArgument(
                    f"The argument must be one of the following: {humanize_enum_vals(Status)}"
                )


# TODO(Amy) Since I'm starting to work on cogs again, maybe add the ability
# to change the amount of time the bot cycles status
class CycleStatus(commands.Cog):
    """Automatically change the status of your bot every minute"""

    __authors__: Final[List[str]] = ["Jojo#7791"]
    # These people have suggested something for this cog!
    __suggesters__: Final[List[str]] = ["ItzXenonUnity | Lou#2369", "StormyGalaxy#1297"]
    __version__: Final[str] = "1.0.17"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, 115849, True)
        self.config.register_global(**_config_structure["global"])
        self.toggled: Optional[bool] = None
        self.random: Optional[bool] = None
        self.last_random: Optional[int] = None
        self.main_task.start()

    async def cog_load(self) -> None:
        self.toggled = await self.config.toggled()
        self.random = await self.config.random()

    async def cog_unload(self) -> None:
        self.main_task.cancel()

    async def red_delete_data_for_user(self, *, requester: str, user_id: int) -> None:
        """Nothing to delete"""

        return

    async def red_get_data_for_user(self, *, user_id: int) -> dict:
        """Nothing to return"""

        return {}

    def format_help_for_context(self, ctx: commands.Context) -> str:
        pre = super().format_help_for_context(ctx)
        plural = "s" if len(self.__authors__) > 1 else ""
        return (
            f"{pre}\n"
            f"Author{plural}: `{humanize_list(self.__authors__)}`\n"
            f"Version: `{self.__version__}`\n"
            f"People who have put in suggestions: `{humanize_list(self.__suggesters__)}`"
        )

    @commands.command(name="cyclestatusversion", aliases=["csversion"], hidden=True)
    async def cycle_status_version(self, ctx: commands.Context):
        """Get the version of Cycle Status that [botname] is running"""

        await ctx.send(
            f"Cycle Status, Version `{self.__version__}`. Made with :heart: by Jojo#7791"
        )

    @commands.group(name="cyclestatus", aliases=["cstatus"])
    @commands.is_owner()
    async def status(self, ctx: commands.Context):
        """Commands working with cycling statuses"""

        pass

    @status.command(name="type")
    async def status_type(self, ctx: commands.Context, status: ActivityConverter):
        """Change the status type of [botname]

        **Arguments**
            - `status` The status type. Valid types are
            `playing, listening, watching, custom, and competing`
        """

        await self.config.status_type.set(status.value)
        await ctx.send(f"Done, set the status type to `{status.name}`.")

    @status.command(name="mode")
    async def status_mode(self, ctx: commands.Context, mode: StatusConverter):
        """Change the status mode of [botname]

        **Arguments**
            - `mode` The mode type. Valid types are:
            `online, idle, dnd, and do not disturb`
        """

        await self.config.status_mode.set(mode.value)
        await ctx.send(f"Done, set the status mode to `{mode.value}`.")

    @status.command()
    @commands.check(lambda ctx: ctx.cog.random is False)  # type:ignore
    async def forcenext(self, ctx: commands.Context) -> None:
        """Force the next status to display on the bot"""

        nl = await self.config.next_iter()
        statuses = await self.config.statuses()
        if not statuses:
            await ctx.send("There are no statuses")
            return
        if len(statuses) == 1:
            await ctx.tick()
            await self._status_add(statuses[0], await self.config.use_help())
            return
        try:
            status = statuses[nl]
        except IndexError:
            status = statuses[0]
            nl = 0
        await self.config.next_iter.set(nl + 1 if nl < len(statuses) else 0)
        await self._status_add(status, await self.config.use_help())
        await ctx.tick()

    @status.command(name="usehelp")
    async def status_set(self, ctx: commands.Context, toggle: Optional[bool] = None) -> None:
        """Change whether the status should have ` | [p]help`

        **Arguments**
            - `toggle` Whether help should be used or not.
        """

        if toggle is None:
            msg = f"Added help is {_enabled(await self.config.use_help())}"
            await ctx.send(msg)
            return
        await self.config.use_help.set(toggle)
        await ctx.tick()

    @status.command(name="add")
    async def status_add(self, ctx: commands.Context, *, status: str):
        """Add a status to the list

        Put `{bot_guild_count}` or `{bot_member_count}` in your message
        to have the user count and guild count of your bot
        If `showbots` is enabled it will include bots in the user count.

        You can also put `{bot_prefix}` in your message to have the
        bot's prefix be displayed (eg. `{bot_prefix}ping`)

        **Arguments**
            - `status` The status to add to the cycle.
        """

        if len(status) > 100:
            await ctx.send("Statuses cannot be longer than 100 characters.")
            return
        async with self.config.statuses() as s:
            s.append(status)
        await ctx.tick()

    @status.command(name="remove", aliases=["del", "rm", "delete"])
    async def status_remove(self, ctx: commands.Context, num: Optional[PositiveInt] = None):
        """Remove a status from the list

        **Arguments**
            - `num` The index of the status you want to remove.
        """

        if num is None:
            await self._status_list(ctx)
            return
        num -= 1
        async with self.config.statuses() as sts:
            if num >= len(sts):
                return await ctx.send("You don't have that many statuses, silly")
            del sts[num]
        await ctx.tick()

    @status.command(name="list")
    async def status_list(self, ctx: commands.Context) -> None:
        """List the available statuses"""

        await self._status_list(ctx)

    async def _status_list(self, ctx: commands.Context) -> None:
        if not (status := await self.config.statuses()):
            await ctx.send("There are no statuses")
            return
        await self._show_statuses(ctx=ctx, statuses=status)

    @status.command(name="clear")
    async def status_clear(self, ctx: commands.Context) -> None:
        """Clear all of the statuses"""

        msg = await ctx.send("Would you like to clear all of your statuses? (y/n)")
        pred = MessagePredicate.yes_or_no()
        try:
            await self.bot.wait_for("message", check=pred)
        except asyncio.TimeoutError:
            pass
        await msg.delete()
        if not pred.result:
            await ctx.send("Okay! I won't remove your statuses.")
            return

        await self.config.statuses.set([])
        await self.bot.change_presence()
        await ctx.tick()

    @status.command(name="random")
    async def status_random(self, ctx: commands.Context, value: bool) -> None:
        """Have the bot cycle to a random status

        **Arguments**
            - `value` Whether to have random statuses be enabled or not
        """

        if value == self.random:
            await ctx.send(f"Random statuses are already {_enabled(value)}")
            return
        self.random = value
        await self.config.random.set(value)
        now_no_longer = "now" if value else "no longer"
        await ctx.send(f"Statuses will {now_no_longer} be random.")

    @status.command(name="toggle")
    async def status_toggle(self, ctx: commands.Context, value: Optional[bool]) -> None:
        """Toggle whether the status should be cycled.

        This is handy for if you want to keep your statuses
        but don't want them displayed at the moment

        **Arguments**
            - `value` Whether to toggle cycling statues
        """

        if value is None:
            await ctx.send(f"Cycling Statuses is {'enabled' if self.toggled else 'disabled'}")
            return
        if value == self.toggled:
            await ctx.send(f"Cycling statuses is already {_enabled(value)}")
            return
        self.toggled = value
        await self.config.toggled.set(value)
        now_not = "now" if value else "not"
        await ctx.send(f"I will {now_not} cycle statuses.")

    @status.command(name="showbots", aliases=["bots"])
    async def status_show_bots(self, ctx: commands.Context, toggle: bool) -> None:
        r"""Toggle whether to show bots in the member count in statuses

        **Arguments**
            \- `toggle`Whether or not to show bots in the member count (defaults to False)
        """

        old = await self.config.show_bots()
        enabled = _enabled(toggle)
        if old == toggle:
            await ctx.send(f"Showing bots is already {enabled}.")
            return
        await self.config.show_bots.set(toggle)
        await ctx.send(f"Show bots in the user count is now {enabled}.")

    @status.command(name="settings")
    async def status_settings(self, ctx: commands.Context) -> None:
        """Show your current settings for the cycle status cog"""
        settings = {
            "Randomized statuses?": "Enabled" if self.random else "Disabled",
            "Toggled?": "Yes" if self.toggled else "No",
            "Statuses?": f"See `{ctx.clean_prefix}cyclestatus list`",
            "Status Type?": ActivityType(await self.config.status_type()).name,
            "Show bots?": await self.config.show_bots(),
        }
        title = "Your Cycle Status settings"
        if await ctx.embed_requested():
            embed = discord.Embed(
                title=title, colour=await ctx.embed_colour(), timestamp=get_datetime()
            )
            [embed.add_field(name=k, value=v, inline=False) for k, v in settings.items()]
            await ctx.send(embed=embed)
            return
        await ctx.send(f"**{title}**\n\n" + "\n".join(f"**{k}** {v}" for k, v in settings.items()))

    @tasks.loop(minutes=1)
    async def main_task(self) -> None:
        msg: str
        nl: int = 0
        statuses = await self.config.statuses()
        if not statuses or not self.toggled:
            return
        if self.random:
            if self.last_random is not None and len(statuses) > 1:
                statuses.pop(self.last_random)  # Remove that last picked one
            msg = random.choice(statuses)
            self.last_random = statuses.index(msg)
        else:
            nl = await self.config.next_iter()  # northernlion, holy shit
            try:
                # So, sometimes this gets larger than the list of the statuses
                # so, if this raises an `IndexError` we need to reset the next iter
                msg = statuses[nl]
            except IndexError:
                nl = 0  # Hard reset
                msg = statuses[0]
        await self._status_add(msg, await self.config.use_help())
        if not self.random:
            nl = 0 if len(statuses) - 1 == nl else nl + 1
            await self.config.next_iter.set(nl)

    @main_task.before_loop
    async def main_task_before_loop(self) -> None:
        await self.bot.wait_until_red_ready()

    async def _num_lists(self, data: List[str]) -> List[str]:
        """|coro|

        Return a list of numbered items
        """
        return [f"{num}. {d}" for num, d in enumerate(data, 1)]

    async def _show_statuses(self, ctx: commands.Context, statuses: List[str]) -> None:
        source = Page(
            list(pagify("\n".join(await self._num_lists(statuses)), page_length=400)),
            title="Statuses",
        )
        await Menu(source=source, bot=self.bot, ctx=ctx).start()

    async def _status_add(self, status: str, use_help: bool) -> None:
        status = status.replace(_bot_guild_var, humanize_number(len(self.bot.guilds)))
        if await self.config.show_bots():
            members = len(self.bot.users)
        else:
            members = _get_non_bot_users(self.bot.users)
        status = status.replace(_bot_member_var, humanize_number(members))

        prefix = (await self.bot.get_valid_prefixes())[0]
        if TYPE_CHECKING:
            assert self.bot.user is not None, "mypy"
        prefix = re.sub(rf"<@!?{self.bot.user.id}>", f"@{self.bot.user.name}", prefix)

        status = status.replace(_bot_prefix_var, prefix)

        if use_help:
            status += f" | {prefix}help"

        # For some reason using `discord.Activity(type=discord.ActivityType.custom)`
        # will result in the bot not changing its status
        # So I'm gonna use this until I figure out something better lmao
        game: discord.BaseActivity
        status_type = await self.config.status_type()

        if status_type == 4:
            game = discord.CustomActivity(name=status)
        else:
            game = discord.Activity(type=status_type, name=status)
        await self.bot.change_presence(activity=game, status=await self.config.status_mode())
