import logging
from datetime import datetime, timezone
import discord
from redbot.core.utils import mod
from redbot.core import commands, Config, modlog
import contextlib

log = logging.getLogger('red.jojo.jojomod')


class JojoMod(commands.Cog):
    """
    Kick and ban function :D
    """
    default_guild_settings = {
        'dm_kickban': False
    }

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, 604890389779, force_registration=True)
        self.config.register_guild(**self.default_guild_settings)

    @staticmethod
    async def reinvite_logic(ctx: commands.Context) -> str:
        pass

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(kick_members=True)
    @commands.admin_or_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str):
        """Basic kick command
        """

        if member == ctx.author:
            return await ctx.send("Listen, I can't kick you. Stop bothering me! >:|")
        elif ctx.guild.me.top_role <= member.top_role or member == ctx.guild.owner:
            return await ctx.send("Due to hierarchy things I can't kick 'em\nGo bother someone else now")
        audit = mod.get_audit_reason(ctx.author, reason)
        toogle = await self.config.guild(ctx.guild).get_raw("dm_kickban")

        if toogle is True:
            with contextlib.suppress(discord.HTTPException):
                embed = discord.Embed(
                    title="**You have been kicked from {}.**".format(ctx.guild))
                embed.add_field(
                    name="**Reason**",
                    value=reason if reason else "No reason was given.",
                    inline=False
                )
                await member.send(embed=embed)
        try:
            await ctx.guild.kick(member, reason=audit)
            log.info("{}({}) was kicked by {}({})".format(
                member, member.id, ctx.author, ctx.author.id))
        except discord.Forbidden:
            await ctx.send("I'm not allowed to do that. Maybe change my perms and we can talk later >:|")
        except Exception as _:
            log.exception(
                "{}({}) attempted to kick {}({}) but an error occurred".format(
                    ctx.author, ctx.author.id, member, member.id)
            )
        else:
            case_type = "kick"
            await modlog.create_case(
                self.bot,
                ctx.guild,
                ctx.message.created_at.replace(tzinfo=timezone.utc),
                case_type,
                member,
                ctx.author,
                reason,
                until=None,
                channel=None)
            await ctx.send("Done. That felt pretty good. Let's go get some ice cream now")
