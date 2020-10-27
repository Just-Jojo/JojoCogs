from redbot.core import commands, Config
import discord


class SwearCount(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, 55550120145, force_registration=True)
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
        if message.guild.id != 696461072101539961:
            return
        try:
            if not message.content[0] in await self.bot.get_prefix(message):
                counts = ["fuck", "shit", "frik", "fudge", "frick"]
                if message.content.lower() in counts:
                    await message.channel.send("{} you swore! That's a point for you!".format(message.author.mention))
                    old = await self.config.user(message.author).get_raw("swearcount")
                    await self.config.user(message.author).set_raw("swearcount", value=old + 1)
        except IndexError:
            pass

    @commands.command()
    async def swearcount(self, ctx):
        leaderboard = await self.config.user(ctx.author).get_raw("swearcount")
        await ctx.send(leaderboard)
