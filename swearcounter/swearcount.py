from redbot.core import commands, Config
import discord
import logging

log = logging.getLogger("red.jojo.swearcount")


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
    async def swearcount(self, ctx, user: discord.Member = None):
        if ctx.guild.id != 696461072101539961:
            return
        if user is None:
            user = ctx.author
        leaderboard = await self.config.user(user).get_raw("swearcount")
        await ctx.send(leaderboard)

    @swearcount.command(name="board")
    async def lb(self, ctx):
        if ctx.guild.id != 696461072101539961:
            return
        original = await self.config.all_users()
        users = sorted(
            original.items(),
            key=lambda x: x[1]['swearcount'], reverse=True
        )
        actual_users = []
        for user in users:
            name = ctx.guild.get_member(user[0]).display_name
            amount = user[1]["swearcount"]
            actual_users.append("**{}**: {}".format(name, amount))
        sending = "\n".join(actual_users)
        await ctx.send("**Swear count leaderboard**\nHow to read: `User, swear score`\n\n{}\n\n*note: Score is based on the times this user has sworn".format(sending))
