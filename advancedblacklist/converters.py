# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from redbot.core import commands

__all__ = ["NonBotUser", "NonBotMember"]


class _NonBotMixin(commands.Converter):
    """Remember kids, Don't Repeat Yourself (D.R.Y)"""

    converter_type: commands.Converter

    async def convert(self, ctx: commands.Context, arg: str):
        maybe_user = await self.converter_type().convert(ctx, arg)
        if maybe_user.bot:
            raise commands.BadArgument("That user is a bot")
        elif maybe_user == ctx.author:
            raise commands.BadArgument("You cannot blacklist yourself")
        elif await ctx.bot.is_owner(maybe_user):
            raise commands.BadArgument("You cannot blacklist this bot's owner")
        return maybe_user


class NonBotUser(commands.Converter):
    converter_type = commands.UserConverter


class NonBotMember(commands.Converter):
    converter_type = commands.MemberConverter
