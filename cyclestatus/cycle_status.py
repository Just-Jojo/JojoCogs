import discord
from discord.ext import tasks

from redbot.core import commands, Config
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_list, box

from itertools import cycle

import logging

log = logging.getLogger("red.JojoCogs.cyclestatus")

_config_structure = {"statuses": [], "type": "game", "help": True}


class CycleStatus(commands.Cog):
    __version__ = "0.1.1"
    __author__ = ["Jojo#7791"]

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, 3213546583213654, True)
        self.config.register_global(**_config_structure)
        self.removed = False

    async def init(self):
        await self._update_status()
        self.update_status.start()

    def cog_unload(self):
        self.update_status.cancel()

    @tasks.loop(minutes=10)
    async def _update_status(self):
        stats = await self.config.statuses()
        if not len(stats):
            self.cy = None
            if self.removed is False:
                await self.bot.change_presence()
                self.removed = True
        else:
            self.cy = cycle(stats)
            if self.removed:
                self.removed = False

    @commands.group()
    async def status(self, ctx):
        """Base command for Status options"""

    @status.group(name="set", invoke_without_command=True)
    async def status_set(self, ctx, ac_type: str):
        """Set the type of the status activity!"""
        ac_type = ac_type.lower()
        if ac_type not in ("game", "watching", "listening"):
            return await ctx.send("That wasn't a valid type!")
        await ctx.tick()
        await self.config.type.set(ac_type)

    @status_set.command(name="help")
    async def status_set_help(self, ctx, toggle: bool):
        if (s := await self.config.help()) == toggle:
            await ctx.send(f"Help was already {'enabled' if toggle else 'disabled'}")
        else:
            await ctx.tick()
            await self.config.help.set(toggle)

    @status.command(name="add")
    async def status_add(self, ctx, *, status: str):
        async with self.config.statuses() as stat:
            stat.append(status)
        await ctx.tick()
        await self.update_status()

    @status.command(name="remove", aliases=["del", "delete"])
    async def status_remove(self, ctx, *indexes: int):
        if not len(indexes):
            msg = await self.config.statuses()
            msg = "\n".join([f"{num}. {x}" for num, x in enumerate(msg, 1)])
            return await ctx.send(box(msg, "md"))
        (indexes := [i - 1 for i in indexes]).sort(reverse=True)
        async with self.config.statuses() as stat:
            for index in indexes:
                try:
                    stat.pop(index)
                except IndexError:
                    pass
        await ctx.tick()

    @status.command(name="list")
    async def status_list(self, ctx):
        msg = await self.config.statuses()
        msg = "\n".join([f"{num}. {x}" for num, x in enumerate(msg, 1)])
        await ctx.send(box(msg, "md"))

    @tasks.loop(minutes=5)
    async def update_status(self):
        if self.cy is None:
            pass
        else:
            add_help = await self.config.help()
            game_type = await self.config.type()
            msg = next(self.cy)
            if add_help:
                prefix = await self.bot.get_valid_prefixes()
                for p in prefix:
                    if not p == self.bot.user.mention:
                        prefix = p
                        break
                if isinstance(prefix, list):
                    prefix = "@me "
                msg += f" | {prefix}help"
            if game_type == "game":
                ac = discord.Game(name=msg)
            elif game_type == "listening":
                ac = discord.Activity(name=msg, type=discord.ActivityType.listening)
            else:
                ac = discord.Activity(name=msg, type=discord.ActivityType.watching)
            await self.bot.change_presence(activity=ac)

    async def cog_check(self, ctx: commands.Context):
        return await self.bot.is_owner(ctx.author)
