import discord
from redbot.core import commands


class Embed:
    def __init__(self, bot):
        self.bot = bot

    def create(
        self, ctx: commands.Context, title: str = "", description: str = "", thumbnail: str = None, footer: str = None,
        footer_url: str = None
    ) -> discord.Embed:
        data = discord.Embed(
            title=title, description=description, color=ctx.author.color
        )
        if thumbnail:
            data.set_thumbnail(url=thumbnail)
        data.set_footer(
            text=footer if footer is not None else ctx.author.name,
            icon_url=footer_url if footer_url is not None else ctx.author.icon_url
        )
        return data
