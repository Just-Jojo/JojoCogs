# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import json
from pathlib import Path

from redbot.core.bot import Red

from .core import AdvancedLog

with open(Path(__file__).parent / "info.json") as fp:
    __red_end_user_data_statement__ = json.load(fp)["end_user_data_statement"]


def setup(bot: Red):
    bot.add_cog(AdvancedLog(bot))
