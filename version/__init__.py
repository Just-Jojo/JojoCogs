from .version import Version


def setup(bot):
    bot.add_cog(Version(bot))
