from .mjolnir import Mjolnir


def setup(bot):
    bot.add_cog(Mjolnir(bot))
