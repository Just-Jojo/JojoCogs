# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from redbot.core.bot import Red

from .core import AdvancedLog


def setup(bot: Red):
    bot.add_cog(AdvancedLog(bot))
