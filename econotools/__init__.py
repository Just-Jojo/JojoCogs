from .economy_tools import EconomyTools
# from .jojo_eco import JojoEconomy


def setup(bot):
    bot.add_cog(EconomyTools(bot))
    # bot.add_cog(JojoEconomy(bot))
