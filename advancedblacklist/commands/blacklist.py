# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import pagify

from ..abc import ABMixin  # type:ignore
from .utils import (add_to_blacklist, edit_reason, get_blacklist,
                    in_blacklist, remove_from_blacklist)

__all__ = ["Blacklist"]


class Blacklist(ABMixin):
    """Commands for the blacklist side of the cog"""

    @commands.group(name="blacklist", aliases=["blocklist"])
    @commands.is_owner()
    async def blacklist(self, ctx: commands.Context):
        """Manage [botname]'s blacklist"""
        pass

    @blacklist.command(name="add")
    async def blacklist_add(
        self, ctx: commands.Context, users: commands.Greedy[discord.User], *, reason: str = None
    ):
        """Add users to the blacklist.

        **Arguments**
            - `users` The users to add to the blacklist. These cannot be bots.
            - `reason` The reason for adding these users to the blacklist. This is optional.
        """
        if not users:
            raise commands.UserInputError
        for user in users:
            if user.bot:
                return await ctx.send("You cannot add bots to the blacklist.")
            elif await self.bot.is_owner(user):
                return await ctx.send("You cannot add a bot owner to the blacklist.")

        reason = reason or "No reason provided."
        await add_to_blacklist(self.bot, users, reason)
        that = "that user" if len(users) == 1 else "those users"
        await ctx.send(f"Done. Added {that} to the blacklist.")

    @blacklist.command(name="remove", aliases=["del", "delete", "rm"], require_var_positional=True)
    async def blacklist_remove(self, ctx: commands.Context, *users: discord.User):
        """Remove users from the blacklist.

        **Arguments**
            - `users` The users to remove from the blacklist.
        """
        if not await get_blacklist(self.bot):
            return await ctx.send("There are no users in the blacklist.")
        await remove_from_blacklist(self.bot, users)
        that = "that user" if len(users) == 1 else "those users"
        await ctx.send(f"Done. Removed {that} from the blacklist.")

    @blacklist.command(name="reason")
    async def blacklist_reason(self, ctx: commands.Context, user: discord.User, *, reason: str):
        """Edit the reason for a user in the blacklist.

        **Arguments**
            - `user` The user to edit the reason of.
        """
        if user.bot:
            return await ctx.send("That user is a bot.")
        elif await self.bot.is_owner(user):
            return await ctx.send("That user is a bot owner.")
        elif not await in_blacklist(self.bot, user.id, ctx.guild):
            return await ctx.send("That user is not in the blacklist.")
        try:
            await edit_reason(self.bot, user, reason, False)
        except KeyError:
            return await ctx.send("That user was not in the blacklist.")
        await ctx.send("Done. Edited the reason for that user.")

    @blacklist.command(name="list")
    async def blacklist_list(self, ctx: commands.Context):
        """List the users in the blacklist."""
        if not (bl := await get_blacklist(self.bot)):
            return await ctx.send("There are no users in the blacklist.")
        msg = "Blacklisted Users:"
        for key, value in bl.items():
            name = u.name if (u := self._get_user(ctx, key)) else "Unknown User"
            msg += f"\n\t- [{key}] {name}: {value}"
        await ctx.send_interactive(pagify(msg, page_length=1800), "yml")

    @commands.group(name="localblacklist", aliases=["localblocklist"])
    @commands.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    async def local_blacklist(self, ctx: commands.Context):
        """Manage the local blacklist for your guild."""
        pass

    @local_blacklist.command(name="add")
    async def local_blacklist_add(
        self, ctx: commands.Context, members: commands.Greedy[discord.Member], *, reason: str = None
    ):
        """Add users to the local blacklist

        **Arguments**
            - `members` The users to add to the local blacklist. These cannot be bots
            - `reason` The reason for adding these members to the blacklist. This is optional
        """
        if not members:
            raise commands.UserInputError
        for user in members:
            if user.bot:
                return await ctx.send("You cannot add bots to the local blacklist.")
            elif await self.bot.is_owner(user):
                return await ctx.send("You cannot add a bot owner to the local blacklist.")
            elif user.id == ctx.guild.owner_id:
                return await ctx.send("You cannot add the guild owner to the local blacklist.")
            elif ctx.author == user:
                return await ctx.send("You cannot add yourself to the local blacklist.")
        reason = reason or "No reason provided."
        await add_to_blacklist(self.bot, members, reason, guild=ctx.guild)
        that = "that member" if len(members) == 1 else "those members"
        await ctx.send(f"Done. Added {that} to the local blacklist.")

    @local_blacklist.command(
        name="remove", aliases=["del", "delete", "rm"], require_var_positional=True
    )
    async def local_blacklist_remove(self, ctx: commands.Context, *users: discord.Member):
        """Remove users from the local blacklist.

        **Arguments**
            - `users` The users to remove from the local blacklist.
        """
        if not await get_blacklist(self.bot, ctx.guild):
            return await ctx.send("There are no users in the local blacklist.")
        await remove_from_blacklist(self.bot, users, guild=ctx.guild)
        that = "that user" if len(users) == 1 else "those users"
        await ctx.send(f"Done. Removed {that} from the local blacklist.")

    @local_blacklist.command(name="reason")
    async def local_blacklist_reason(
        self, ctx: commands.Context, member: discord.Member, *, reason: str
    ):
        """Edit the reason for a member in the local blacklist.

        **Arguments**
            - `member` The member to edit the reason of. This cannot be a bot.
            - `reason` The reason for blacklisting the member.
        """
        if await self.bot.is_owner(member):
            return await ctx.send("That member is a bot owner.")
        elif ctx.guild.owner_id == member.id:
            return await ctx.send("That member is the guild owner.")
        elif member.bot:
            return await ctx.send("That member is a bot.")
        elif not await in_blacklist(self.bot, member.id, ctx.guild):
            return await ctx.send("That member is not locally blacklisted.")
        try:
            await edit_reason(self.bot, member, reason, False, guild=ctx.guild)
        except KeyError:
            return await ctx.send("That member was not in the local blacklist.")
        await ctx.send("The reason for that member has been edited.")

    @local_blacklist.command(name="list")
    async def local_blacklist_list(self, ctx: commands.Context):
        """List the users in the local blacklist."""
        if not (bl := await get_blacklist(self.bot, ctx.guild)):
            return await ctx.send("There are no members in the local blacklist.")
        msg = "Locally Blacklisted Members:"
        for key, value in bl.items():
            name = u.name if (u := ctx.guild.get_member(int(key))) else "Unknown or Deleted Member"
            msg += f"\n\t- [{key}] {name}: {value}"
        await ctx.send_interactive(pagify(msg, page_length=1800), "yml")
