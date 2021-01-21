from redbot.core import commands

from typing import *
import discord


class Version(commands.Cog):
    __version__ = "1.0.1"

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def version(self, ctx: commands.Context, cog_name: str):
        """
        Get a cog's version (if any)

        *Note, you must have the proper capitalization for cogs, this uses PascalCase

        Example:
        `[p]version Version`, `[p]version JojoStore`
        """
        cog: commands.Cog = self.bot.get_cog(cog_name)
        if not cog:
            await ctx.send(
                f"I could not find a cog by the name of `{cog_name}`!\n"
                f"Use `{ctx.clean_prefix}help` to find all of the cogs I have!"
            )
            return
        if hasattr(cog, "version") and any([isinstance(cog.version, typ) for typ in (int, str)]):
            await ctx.send(f"`{cog.qualified_name}` version `{cog.version}`")
        elif hasattr(cog, "__version__"):
            await ctx.send(f"`{cog.qualified_name}` version `{cog.__version__}`")
        else:
            await ctx.send(f"`{cog.qualified_name}` does not have a version!")
