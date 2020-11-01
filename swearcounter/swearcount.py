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
                for count in counts:
                    if count in message.content.lower():
                        old = await self.config.user(message.author).get_raw("swearcount")
                        await self.config.user(message.author).set_raw("swearcount", value=old + 1)
                        counting = await self.config.user(message.author).get_raw("swearcount")
                        if counting >= 10:
                            swear_role = message.guild.get_role(
                                771515693921206363)
                            if not swear_role in message.author.roles:
                                await message.author.add_roles(swear_role)
                        await message.channel.send("{} you swore! That's a point for you!".format(message.author.mention))
        except IndexError:
            pass

    @commands.group(aliases=["swear", ], invoke_without_command=True)
    async def swearcount(self, ctx):
        if ctx.guild.id != 696461072101539961:
            return
        leaderboard = await self.config.user(ctx.author).get_raw("swearcount")
        await ctx.send(leaderboard)

    @swearcount.command(name="board")
    async def lb(self, ctx):
        if ctx.guild.id != 696461072101539961:
            return
        leaderboard = await self.config.all_users()
        leader = []
        for item in sorted(leaderboard.items(), key=lambda p: p[1]):
            leader.append("**{0}** {1}".format(*item))
        await ctx.send("\n".join(leader))
