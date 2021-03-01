from .todo import ToDo
from redbot.core.bot import Red


def setup(bot: Red):
    bot.add_cog(ToDo(bot))
