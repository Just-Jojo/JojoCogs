# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import logging

import aiohttp
import discord
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_list

from .utils import APIError

log = logging.getLogger("red.JojoCogs.ducks")
duck_image_api = "https://random-d.uk/api/v2"


class Ducks(commands.Cog):
    """Ducks! Who could ask for more?"""

    __author__ = ["Jojo#7791"]
    __version__ = "0.1.2"

    def __init__(self, bot: Red):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def format_help_for_context(self, ctx: commands.Context):
        pre_processed = super().format_help_for_context(ctx)
        plural = "s" if len(self.__author__) > 1 else ""
        return (
            f"{pre_processed}\n"
            f"Author{plural}: `{humanize_list(self.__author__)}`\n"
            f"Version: `{self.__version__}`"
        )

    async def red_delete_data_for_user(self, *args):
        # This cog does not store data
        return

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    async def _get_response(self):
        async with self.session.get(f"{duck_image_api}/random") as re:
            if re.status != 200:
                raise APIError()
            return (await re.json())["url"]

    @commands.command()
    async def ducks(self, ctx: commands.Context):
        """Get a random duck image!"""
        async with ctx.typing():
            try:
                url = await self._get_response()
            except APIError as e:
                return await ctx.send(str(e))
        kwargs = {"content": url}
        if await ctx.embed_requested():
            embed = discord.Embed(title="Ducks!", colour=await ctx.embed_colour())
            embed.set_image(url=url)
            embed.set_footer(text="Ducks!")
            kwargs = {"embed": embed}
        await ctx.send(**kwargs)

    @commands.command()
    async def duckshttp(self, ctx: commands.Context, code: int):
        """Get a duck http status code"""
        valid_codes = []
