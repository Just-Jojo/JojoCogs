from .calculations import Calculations
from redbot.core.bot import Red


def setup(bot: Red):
    bot.add_cog(Calculations(bot))
