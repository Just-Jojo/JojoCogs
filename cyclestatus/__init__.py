import json
import pathlib

from redbot.core.bot import Red

from .cycle_status import CycleStatus

with open(pathlib.Path(__file__).parent / "info.json") as fp:
    __red_end_user_data_statement__ = json.load(fp)["end_user_data_statement"]


async def setup(bot: Red):
    await bot.add_cog(CycleStatus(bot))
