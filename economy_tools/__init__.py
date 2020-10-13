from .economy_tools import EconomyTools


def setup(bot):
    bot.add_cog(EconomyTools(bot))
