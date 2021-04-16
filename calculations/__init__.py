from redbot.core.bot import Red

from .calculations import Calculations


def setup(bot: Red):
    bot.add_cog(Calculations(bot))
