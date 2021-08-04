from .core import CmdLogger


def setup(bot):
    bot.add_cog(CmdLogger(bot))