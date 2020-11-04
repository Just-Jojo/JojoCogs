from .suggestions import Suggestions


def setup(bot):
    bot.add_cog(Suggestions(bot))
