# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import json
from pathlib import Path

from redbot.core.bot import Red

from .core import AdvancedBlacklist

with open(Path(__file__).parent / "info.json") as fp:
    __red_end_user_data_statement__ = json.load(fp)["end_user_data_statement"]


async def setup(bot: Red) -> None:
    c = await AdvancedBlacklist.init(bot)
    bot.add_cog(c)
