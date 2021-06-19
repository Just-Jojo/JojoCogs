import json
from pathlib import Path
from redbot.core.bot import Red

from .update import UpdateUtils


with open(Path(__file__).parent / "info.json", "r") as fp:
    __red_end_user_data_statement__ = json.load(fp)


def setup(bot: Red):
    bot.add_cog(UpdateUtils(bot))
