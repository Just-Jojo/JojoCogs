from redbot.core import commands, Config
from redbot.core.bot import Red
import discord
from discord.utils import get
from datetime import datetime


class DM(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, 12312321352454, True)
        self.config.register_global(channel=None)

    @commands.is_owner()
    @commands.command()
    async def setchannel(self, ctx, channel: discord.TextChannel):
        await self.config.set_raw("channel", value=channel.id)
        await ctx.tick()

    @commands.Cog.listener("on_message_without_command")
    async def on_dm(self, msg):
        if msg.guild:
            return
        if (channel := await self.config.get_raw("channel")) :
            channel = await self.bot.fetch_channel(channel)
            embed = await self._format_embed(msg=msg)
            embed.colour = await self.bot.get_embed_colour(channel)
            await channel.send(embed=embed)

    async def _format_embed(self, msg: discord.Message):
        embed = discord.Embed(
            title=f"DM From {msg.author} ({msg.author.id})",
            description=msg.content,
        )
        embed.set_thumbnail(url=msg.author.avatar_url)
        embed.timestamp = datetime.utcnow()
        return embed


def setup(bot: Red):
    bot.add_cog(DM(bot))
