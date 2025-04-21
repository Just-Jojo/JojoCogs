# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import json
from pathlib import Path

from redbot.core.bot import Red

from .core import AdvancedBlacklist

with open(Path(__file__).parent / "info.json") as fp:
    __red_end_user_data_statement__ = json.load(fp)["end_user_data_statement"]


async def setup(bot: Red) -> None:
    advanced_blacklist = await AdvancedBlacklist.init(bot)
    # Instead of having the normal cog loading, this will need to patch
    # some commands in the bot, therefore we need to initialize the cog before adding it
    # to the bot
    await bot.add_cog(advanced_blacklist)
