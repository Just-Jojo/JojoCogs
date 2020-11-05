from redbot.core import commands, Config
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.predicates import ReactionPredicate, MessagePredicate
import discord
import asyncio
import contextlib


class Suggestions(commands.Cog):
    default_global = {
        "channel": None
    }

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 41989963, force_registration=True)
        self.config.register_global(
            **self.default_global
        )

    @commands.command()
    @commands.is_owner()
    async def suggestset(self, ctx, channel: discord.TextChannel = None):
        """Set up the suggestion channel"""
        if channel is not None:
            msg = await ctx.send("Would you like to set up the suggest channel as {}? `y/n`".format(channel.mention))
            mass = await self.bot.wait_for("message", check=lambda message: message.author == ctx.author)
            if mass.content[0].lower() == "y":
                await self.config.set_raw("channel", value=channel.id)
                await msg.edit(content="Added {} as the suggestion channel".format(channel.mention))
            else:
                await msg.edit(content="Canceled!")
        else:
            msg = await ctx.send("Would you like to remove the suggestion channel? `y/n`")
            mass = await self.bot.wait_for("message", check=lambda message: message.author == ctx.author)
            if mass.content[0].lower() == "y":
                await self.config.clear_raw("channel")
                await msg.edit(content="Removed the channel!")
            else:
                await msg.edit(content="Okay, I'll cancel the removal")

    @commands.command()
    @commands.is_owner()
    async def test(self, ctx):
        msg = await ctx.send("Test")
        pred = ReactionPredicate.yes_or_no(msg, ctx.author)
        start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
        try:
            await ctx.bot.wait_for("reaction_add", check=pred, timeout=20)
        except asyncio.TimeoutError:
            await msg.delete()
            return
        if not pred.result:
            await msg.delete()
            return
        else:
            with contextlib.suppress(discord.Forbidden):
                await msg.clear_reactions()
        await ctx.send("Done")
