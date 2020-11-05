from redbot.core import commands, Config
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.predicates import ReactionPredicate, MessagePredicate
import discord
import asyncio
import contextlib
from .embed import Embed


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
            message = "Would you like to set the suggestion channel as {}?".format(
                channel.mention)
            can_react = ctx.channel.permissions_for(ctx.me).add_reactions
            if not can_react:
                message += " (y/n)"
            question = await ctx.send(message)
            if can_react:
                start_adding_reactions(
                    question, ReactionPredicate.YES_OR_NO_EMOJIS
                )
                pred = ReactionPredicate.yes_or_no(question, ctx.author)
                event = "reaction_add"
            else:
                pred = MessagePredicate.yes_or_no(ctx)
                event = "message"
            try:
                await ctx.bot.wait_for(event, check=pred, timeout=30)
            except asyncio.TimeoutError:
                return await question.delete()

            if not pred.result:
                if can_react:
                    with contextlib.suppress(discord.Forbidden):
                        await question.clear_reactions()
                return await ctx.send("Okay! :D")
            else:
                if can_react:
                    with contextlib.suppress(discord.Forbidden):
                        await question.clear_reactions()
            await self.config.set_raw("channel", value=channel.id)
            await question.edit(content="Done! Set up {} as the suggestion channel!".format(channel.mention))

        else:
            message = "Would you like to remove the channel?"
            can_react = ctx.channel.permissions_for(ctx.me).add_reactions
            if not can_react:
                message += " (y/n)"
            question = await ctx.send(message)
            if can_react:
                start_adding_reactions(
                    question, ReactionPredicate.YES_OR_NO_EMOJIS)
                pred = ReactionPredicate.yes_or_no(question, ctx.author)
                event = "reaction_add"
            else:
                pred = MessagePredicate.yes_or_no(ctx)
                event = "message"
            try:
                await ctx.bot.wait_for(event, check=pred, timeout=30)
            except asyncio.TimeoutError:
                return await question.delete()

            if not pred.result:
                if can_react:
                    with contextlib.suppress(discord.Forbidden):
                        await question.clear_reactions()
                return await ctx.send("Okay! :D")
            else:
                if can_react:
                    with contextlib.suppress(discord.Forbidden):
                        await question.clear_reactions()
            await self.config.clear_raw("channel")
            await question.edit(content="Done!")

    @commands.command()
    @commands.is_owner()
    async def test(self, ctx, *, suggestion: str):
        if not isinstance(ctx.channel, discord.DMChannel):
            return await ctx.send("This command only works in dms!")
        channel = await self.config.get_raw("channel")
        if channel is None:
            return await ctx.send("This bot's owner has not set up a suggestion box!")
        channel = bot.get_channel(channel)

        # Now for the embed
        emb = Embed.create(
            ctx, title="Suggestion from {}".format(ctx.author.name), description=suggestion
        )
        await channel.send(embed=emb)
