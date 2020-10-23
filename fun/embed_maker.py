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
        JOJOBOTURL = "https://cdn.discordapp.com/avatars/730061145490325644/e19579cefc7ff5695a0a2878c31c4588.png?size=1024"
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
            footer = "Jojo's embed maker"
        if footer_url is None:
            footer_url = JOJOBOTURL
        data.set_footer(text=footer, icon_url=footer_url)
        return data
