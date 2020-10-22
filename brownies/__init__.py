from .brownie import Brownie


def setup(bot):
    bot.add_cog(Brownie(bot))
