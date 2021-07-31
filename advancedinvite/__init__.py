from .advanced_invite import AdvancedInvite
from redbot.core.bot import Red
import json
import pathlib

with open(pathlib.Path(__file__).parent / "info.json") as fp:
    __red_end_user_data_statement__ = json.load(fp)["end_user_data_statement"]

async def setup(bot: Red):
    bot.add_cog(await AdvancedInvite.init(bot))
