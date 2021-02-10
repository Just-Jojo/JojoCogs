from .embedder import Embedder


def setup(bot):
    bot.add_cog(Embedder(bot))
