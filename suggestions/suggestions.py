from redbot.core import commands, Config
import discord


class Suggestions(commands.Cog):
    default_global = {
        "channel": None
    }

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 41989963, force_registration=True)
        self.config.register_global(
            **self.default_global
        )

    @commands.command()
    @commands.is_owner()
    async def suggestionset(self, ctx, channel: discord.TextChannel):
        """Set up the suggestion channel"""
        msg = await ctx.send("Would you like to set up the suggest channel as {}?".format(channel.mention))
        mass = await self.bot.wait_for("message", check=lambda message: message.author == ctx.author)
        if mass.content[0] == "y":
            await self.config.set_raw("channel", value=channel)
        else:
            await msg.edit(content="Canceled!")
