# Copyright (c) 2025 - Amy (jojo7791)
# Licensed under MIT

from __future__ import annotations

from typing import Final, Tuple

from redbot.core.bot import Red
from redbot.core.errors import CogLoadError
from redbot.core.utils import get_end_user_data_statement

from .core import SimpleTag

__all__: Final[Tuple[str, ...]] = ("__red_end_user_data_statement__", "setup")


__red_end_user_data_statement__ = get_end_user_data_statement(__file__)


async def setup(bot: Red) -> None:
    if bot.get_cog("CustomCommands"):
        raise CogLoadError("Cannot have CustomCommands loaded")
    await bot.add_cog(SimpleTag(bot))
