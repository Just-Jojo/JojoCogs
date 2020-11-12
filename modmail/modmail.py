from typing import Literal

import discord
from redbot.core import Config, commands
from redbot.core.utils.predicates import MessagePredicate


class ModMail(commands.Cog):
    """This cog allows you to see any dms your bot receives"""

    default_global = {
        "Channel": None
    }

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, 12386760762, force_registration=True)
        self.config.register_global(**self.default_global)

    async def red_delete_data_for_user(
        self,
        requester: Literal["discord", "owner", "user", "user_strict"],
        user_id: int
    ) -> None:
        """Nothing to delete"""
        return

    @commands.Cog.listener()
    async def on_message(self, message):
        if not isinstance(message.channel, discord.DMChannel):
            return
        if message.author.bot:
            return
        app = await self.bot.application_info()
        if message.author.id == app.owner.id:
            return
        channel = self.bot.get_channel(await self.config.get_raw("Channel"))
        if not message.content[0] in await self.bot.get_prefix(message) and channel is not None:
            emb = Embed.create(self, message, title="Mod Mail 📬",
                               description=message.content)
            await channel.send(embed=emb)

    @commands.command()
    @commands.is_owner()
    async def modmail(self, ctx, toggle: discord.TextChannel = None):
        """Enable/disable the Mod mail"""

        if toggle is None:
            await ctx.send("Would you like to disable the Mod Mail? (y/n)")
            try:
                pred = MessagePredicate.yes_or_no(ctx)
                await ctx.bot.wait_for("message", check=pred)
                if pred.result is True:
                    message = "Removed the Mod Mail channel"
                else:
                    message = "Canceled the removal of the Mod Mail channel"
            except TimeoutError:
                message = "Canceled the removal of the Mod Mail channel"
            return await ctx.send(message)
        await self.config.set_raw("Channel", value=toggle.id)
        await ctx.send("Channel changed to {}".format(toggle.mention))

class Embed:
    def __init__(self, bot):
        self.bot = bot

    def create(self, message, title="", description="", image: str = None, thumbnail: str = None) -> discord.Embed:
        """A modified version of JJW's embed maker to suit the `on_message` listener"""

        data = discord.Embed(title=title, color=discord.Color.dark_magenta())
        if description is not None:
            if len(description) <= 1500:
                data.description = description
        data.set_author(name=message.author.display_name,
                        icon_url=message.author.avatar_url)
        if image is not None:
            data.set_image(url=image)
        if thumbnail is not None:
            data.set_thumbnail(url=thumbnail)
        data.set_footer(text="{0.name} modmail".format(
            self.bot.user), icon_url=self.bot.user.avatar_url)
        return data
