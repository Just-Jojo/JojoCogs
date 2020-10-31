import logging
from datetime import datetime
import discord
from redbot.core.utils import mod
from redbot.core import commands, Config, modlog

log = logging.getLogger('red.jojo.jojomod')


class JojoMod(commands.Cog):
    """
    Kick and ban function :D
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(kick_members=True)
    @commands.admin_or_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str):
        """Basic kick command
        """

        if member == ctx.author:
            return await ctx.send("Listen, I can't kick you. Stop bothering me! >:|")
        elif ctx.guild.me.top_role <= member.top_role or member == ctx.guild_owner:
            return await ctx.send("Due to hierarchy things I can't kick 'em\nGo bother someone else now")
        audit = mod.get_audit_reason(ctx.author, reason)

        try:
            await ctx.guild.kick(member, audit)
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
            await modlog.create_case(self.bot, ctx.guild, datetime.now, case_type, member, ctx.author, reason, until=None, channel=None)
            await ctx.send("Done. That felt pretty good. Let's go get some ice cream now")
