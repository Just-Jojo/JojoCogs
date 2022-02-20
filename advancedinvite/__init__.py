from discord import version_info
import json
import pathlib

from redbot.core.bot import Red
from redbot.core.errors import CogLoadError

from .advanced_invite import AdvancedInvite


if version_info.major != 2:
    raise CogLoadError(
        "This cog requires discord.py 2.0. "
        "Please use the regular branch instead (<https://github.com/Just-Jojo/JojoCogs/tree/master>)"
    )


with open(pathlib.Path(__file__).parent / "info.json") as fp:
    __red_end_user_data_statement__ = json.load(fp)["end_user_data_statement"]


async def setup(bot: Red):
    bot.add_cog(AdvancedInvite(bot))
