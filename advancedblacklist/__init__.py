# Copyright (c) 2021 - Amy (jojo7791)
# Licensed under MIT

import json
import pathlib

from redbot.core.bot import Red

from .core import AdvancedBlacklist


with open(pathlib.Path(__file__).parent / "info.json") as fp:
    __red_end_user_data_statement__ = json.load(fp)["end_user_data_statement"]

del pathlib, json, fp


async def setup(bot: Red) -> None:
    cog = await AdvancedBlacklist.async_init(bot)
    await bot.add_cog(cog)
