import discord
from validator_collection import validators
import requests


class EmbedDescriptionError(Exception):
    pass


class Embed:
    def __init__(self, bot):
        self.bot = bot

    def create(self, message, title="", description="", image: str = None, thumbnail: str = None) -> discord.Embed:
        """A modified version of JJW's embed maker to suit the `on_message` listener"""

        data = discord.Embed(title=title, color=discord.Color.dark_magenta())
        if description is not None:
            if len(description) <= 1500:
                data.description = description
            else:
                raise EmbedDescriptionError
        data.set_author(name=message.author.display_name,
                        icon_url=message.author.avatar_url)
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
        data.set_footer(text="{0.name} modmail".format(
            self.bot.user), icon_url=self.bot.user.avatar_url)
        return data
