import discord
from validator_collection import validators
import requests


class EmbedDescriptionError(Exception):
    pass


class Embed:
    def __init__(self, bot):
        self.bot = bot

    def create(self, ctx, title="", description="", image: str = None, thumbnail: str = None,
               footer_url: str = None, footer: str = None) -> discord.Embed:
        if isinstance(ctx.message.channel, discord.abc.GuildChannel):
            color = ctx.message.author.color
        data = discord.Embed(title=title, color=color)
        if description is not None:
            if len(description) <= 1500:
                data.description = description
            else:
                raise EmbedDescriptionError
        data.set_author(name=ctx.author.display_name,
                        icon_url=ctx.author.avatar_url)
        if image is not None:
            validators.url(image)
            code = requests.get(image).status_code
            if code == 200:
                data.set_image(url=image)
            else:
                pass
        if thumbnail is not None:
            validators.url(thumbnail)
            code = requests.get(thumbnail).status_code
            if code == 200:
                data.set_thumbnail(url=thumbnail)
            else:
                pass
        if footer is None:
            footer = "{0.name}'s Embed Maker".format(self.bot.user)
        if footer_url is None:
            footer_url = self.bot.user.avatar_url
        data.set_footer(text=footer, icon_url=footer_url)
        return data
