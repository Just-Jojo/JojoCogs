from redbot.core import commands, Config
import discord


class SwearCount(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, 2839686154, force_registration=True)
        self.config.register_global(
            blocked=[]
        )
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
            counts = ["fuck", "shit", "frik", "fudge", "frick"]
            if message.content.lower() in counts:
                await message.channel.send("{} you swore! That's a point for you!".format(message.author.mention))
                old = await self.config.user(message.author).get_raw("swearcount")
                await self.config.user(message.author).set_raw("swearcount", value=old + 1)

    @commands.command()
    async def swearcount(self, ctx):
        leaderboard = await self.config.user(ctx.author).get_raw("swearcount")
        await ctx.send(leaderboard)

    @commands.command()
    @commands.mod_or_permissions(manage_guild=True)
    async def stop(self, ctx):
        guild = ctx.guild
        if guild in await self.config.blocked.get_raw():
            return await ctx.send("Your guild is already in the blocklist!")
        await self.config.blocked.set_raw(value=guild)
        await ctx.send("Your guild has now been put in the block list")

    @commands.command()
    @commands.mod_or_permissions(manage_guild=True)
    async def start(self, ctx):
        guild = ctx.guild
        blocked = await self.config.blocked.get_raw()
        if guild not in blocked:
            return await ctx.send("Your guild is not in the blocklist")
        await self.config.blocked.clear_raw(guild)
        await ctx.send("Removed your guild from the blocklist!")
