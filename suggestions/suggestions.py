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
    async def suggestset(self, ctx, channel: discord.TextChannel = None):
        """Set up the suggestion channel"""
        if channel is not None:
            msg = await ctx.send("Would you like to set up the suggest channel as {}? `y/n`".format(channel.mention))
            mass = await self.bot.wait_for("message", check=lambda message: message.author == ctx.author)
            if mass.content[0].lower() == "y":
                await self.config.set_raw("channel", value=channel.id)
                await msg.edit(content="Added {} as the suggestion channel".format(channel.mention))
            else:
                await msg.edit(content="Canceled!")
        else:
            msg = await ctx.send("Would you like to remove the suggestion channel? `y/n`")
            mass = await self.bot.wait_for("message", check=lambda message: message.author == ctx.author)
            if mass.content[0].lower() == "y":
                await self.config.clear_raw("channel")
                await msg.edit("Removed the channel!")
            else:
                await msg.edit("Okay, I'll cancel the removal")
