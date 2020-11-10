import asyncio
import contextlib
from typing import Literal

import discord
from redbot.core import Config, commands
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.predicates import MessagePredicate, ReactionPredicate

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

    async def red_delete_data_for_user(
        self,
        requester: Literal["discord", "owner", "user", "user_strict"],
        user_id: int
    ) -> None:
        """Nothing to delete"""
        return

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
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def suggest(self, ctx):
        """Add a suggestion for the bot"""

        author = ctx.author
        channel = await self.config.get_raw("channel")
        if channel is None:
            return await ctx.send("There is no suggestion channel!")
        try:
            await author.send("Please input the suggestion you have\nTime out is `20` seconds")
            await ctx.send("DM'd you :D")
        except discord.Forbidden:
            await ctx.send("I couldn't dm you!")

        while True:
            try:
                message: discord.Message = await ctx.bot.wait_for('message', timeout=20)
            except asyncio.TimeoutError:
                return await author.send("Timed out.")
            if message.author == author and isinstance(message.channel, discord.DMChannel):
                channel = self.bot.get_channel(channel)
                emb = Embed.create(
                    self, ctx, title="Suggestion from {}".format(ctx.author.name), description=message.content,
                    footer="Suggestions designed by Jojo", footer_url=ctx.me.avatar_url, thumbnail=author.avatar_url
                )
                msg = await author.send("Does this look good to you?", embed=emb)
                start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
                pred = ReactionPredicate.yes_or_no(msg, ctx.author)
                try:
                    await ctx.bot.wait_for("reaction_add", check=pred, timeout=10)
                except asyncio.TimeoutError:
                    return await author.send("Okay!")
                await msg.delete()
                if pred.result:
                    await author.send("Your suggestion was added. Thank you for helping keep {} alive!".format(ctx.me.name))
                    return await channel.send(embed=emb)
                else:
                    return await author.send("Cancled the suggestion!\nYou can always suggest something later")
