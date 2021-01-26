import discord

from redbot.core import commands, Config
from redbot.core.bot import Red  # Want to have Red for typing hinting

import logging
perm = discord.Permissions

log = logging.getLogger("red.Jojo-Cogs.invite")


def is_public():
    """Custom check for if the invite is public or not"""
    async def pred(ctx: commands.Context):
        bot: Red = ctx.bot
        if await bot.is_owner(ctx.author):
            return True  # Owners are special
        conf: Config = bot.get_cog("Invite").conf  # Just get the config
        if await conf.public():
            return True
        return False
    return commands.check(pred)


class Invite(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, 1325634653215432165, True)
        self.config.register_global(perms=0, public=True)

    def cog_unload(self):
        global OLDINVITE
        if OLDINVITE:
            try:
                self.bot.remove_command("invite")
            except Exception as e:
                log.error(e)
            finally:
                self.bot.add_command(OLDINVITE)

    async def get_invite(self) -> str:
        app_info = await self.bot.application_info()
        perms_int = await self.config.perms()
        return discord.utils.oauth_url(app_info.id, permissions=perm(perms_int))

    @commands.group(invoke_without_command=True)
    @is_public()
    async def invite(self, ctx):
        """Get the invite for the bot!"""
        invite = await self.get_invite()
        invite_embed = {
            "title": f"{self.bot.user.name}'s Invite url",
            "description": f"Here is the [invite link]({invite}) for the bot!",
            "footer": {
                "text": f"{self.bot.user.name} invite",
                "icon_url": str(self.bot.user.avatar_url)
            },
            "color": 0x00ffff
        }
        embed = discord.Embed.from_dict(invite_embed)
        await ctx.send(embed=embed)

    @invite.command()
    @commands.is_owner()
    async def setperms(self, ctx, permissions: int):
        await self.config.perms.set(permissions)
        await ctx.tick()

    @invite.command()
    @commands.is_owner()
    async def public(self, ctx, state: bool):
        await self.config.public.set(state)
        await ctx.tick()


OLDINVITE: commands.Command


def setup(bot: Red):
    global OLDINVITE
    OLDINVITE = bot.get_command("invite")
    if OLDINVITE:
        bot.remove_command("invite")
    bot.add_cog(Invite(bot))
