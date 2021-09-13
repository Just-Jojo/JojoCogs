# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from .advanced_log import AdvancedLog
from redbot.core.bot import Red


def setup(bot: Red):
    bot.add_cog(AdvancedLog(bot))
