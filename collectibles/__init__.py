import json
import pathlib

from redbot.core.bot import Red

from .collectibles import Collectibles

with open(pathlib.Path(__file__).parent / "info.json") as fp:
    __red_end_user_data_statement__ = json.load(fp)


def setup(bot: Red):
    bot.add_cog(Collectibles(bot))
