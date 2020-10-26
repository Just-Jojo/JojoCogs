from redbot.core import commands, Config
import discord


class SwearCount(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, 2839686154, force_registration=True)
        self.config.register_user(
            swearcount=0
        )

    async def listener(self, message):
        if type(message.author) != discord.Member:
            return
        if type(message.channel) != discord.TextChannel:
            return
        if message.author.bot:
            return
        if not message.content[0] in await self.bot.get_prefix(message):
            counts = ["fuck", "shit", "frik", "fudge"]
            if counts in message.content():
                await message.channel.send("{} you swore! That's a point for you!".format(message.author.mention))
                old = await self.config.user(message.author).swearcount.get_raw()
                await self.config.user(message.author).swearcount.set_raw(old + 1)
        else:
            await self.bot.process_commands(message)
