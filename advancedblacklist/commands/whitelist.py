# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import logging

import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import box, pagify

from ..abc import ABMixin  # type:ignore
from .utils import (add_to_whitelist, clear_whitelist, edit_reason,
                    get_whitelist, in_whitelist, remove_from_whitelist)

log = logging.getLogger("red.jojocogs.advancedblacklist.whitelist")


class Whitelist(ABMixin):
    """Mixin for the whitelist related commands"""

    @commands.group(name="whitelist", aliases=("allowlist",))
    @commands.is_owner()
    async def whitelist(self, ctx: commands.Context):
        """Manage [botname]'s whitelist"""
        pass

    @whitelist.command(name="add")
    async def whitelist_add(
        self,
        ctx: commands.Context,
        users: commands.Greedy[discord.User],
        *,
        reason: str = None,
    ):
        """Add a user to the whitelist. These users cannot be bots.

        **Arguments**
            - `users` The users to add to the whitelist.
            - `reason` The reason for adding these users to the whitelist. This argument is optional.
        """
        if not users:
            # This can happen because `commands.Greedy` will try to consume as many arguments as possible
            # However, those can all be invalid args so they will be filtered out... or something
            # Basically: sometimes a `commands.Greedy` argument will give you an empty list
            raise commands.UserInputError
        for user in users:
            if user.bot:
                return await ctx.send("You cannot whitelist a bot.")
        reason = reason or "No reason provided."
        await add_to_whitelist(self.bot, users, reason)
        that = "that user" if len(users) == 1 else "those users"
        await ctx.send(f"Done. Added {that} to the whitelist.")

    @whitelist.command(name="remove", aliases=["del", "delete", "rm"], require_var_positional=True)
    async def whitelist_remove(self, ctx: commands.Context, *users: discord.User):  # type:ignore
        """Remove users from the whitelist.

        **Arguments**
            - `users` The users to remove from the whitelist.
        """
        if not await get_whitelist(self.bot):
            return await ctx.send("There are no users in the whitelist.")
        await remove_from_whitelist(self.bot, users)

        that = "that user" if len(users) == 1 else "those users"
        await ctx.send(f"Done. Removed {that} from the whitelist.")

    @whitelist.command(name="reason")
    async def whitelist_reason(self, ctx: commands.Context, user: discord.User, *, reason: str):
        """Edit the reason for a whitelisted user."""
        if user.bot:
            return await ctx.send("That user is a bot.")
        elif not await in_whitelist(self.bot, user.id):
            return await ctx.send("That user is not in the whitelist.")
        try:
            await edit_reason(self.bot, user, reason, True)
        except KeyError:
            return await ctx.send("That user was not in the whitelist.")
        await ctx.send("Done. The reason for that user has been updated.")

    @whitelist.command(name="list")
    async def whitelist_list(self, ctx: commands.Context):
        """List the users on [botname]'s whitelist"""
        if not (wt := await get_whitelist(self.bot)):
            return await ctx.send("There are no whitelisted users.")
        msg = "Whitelisted Users:"
        for uid, reason in wt.items():
            user = u.name if (u := self._get_user(ctx, uid)) else "Unknown or Deleted User"
            msg += f"\n\t- [{uid}] {user}: {reason}"
        await ctx.send_interactive(pagify(msg, page_length=1800), "yml")

    @commands.group(name="localwhitelist", aliases=("localallowlist",))
    @commands.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    async def local_whitelist(self, ctx: commands.Context):
        """Manage the local whitelist for your guild."""
        pass

    @local_whitelist.command(name="add")
    async def local_whitelist_add(
        self,
        ctx: commands.Context,
        members: commands.Greedy[discord.Member],
        *,
        reason: str = None,
    ):
        """Add members to the local whitelist.

        This will disallow anyone not on the local whitelist from using [botname].

        Note, if you are an admin you must add yourself to the whitelists as to not lock yourself out of [botname].

        **Arguments**
            - `members` The members to add to the whitelist. They cannot be bots.
            - `reason` The reason for adding these members to the whitelist. This argument is optional.
        """
        if not members:
            raise commands.UserInputError
        for user in members:
            if user.bot:
                return await ctx.send("You cannot locally whitelist a bot.")
        reason = reason or "No reason provided."
        members = {u.id for u in members}
        if not (ctx.guild.owner_id == ctx.author.id or await self.bot.is_owner(ctx.author)):
            # We need to make sure to not lock an admin out of the bot
            # This is a toned down version of the cog creator's method for this check
            # https://github.com/Cog-Creators/Red-DiscordBot/blob/V3/develop/redbot/core/core_commands.py#L4521-#L4532
            current = set((await get_whitelist(self.bot, ctx.guild)).keys())
            maybe_new = current.union(members)
            check = {ctx.author.id}
            if check.isdisjoint(maybe_new):
                return await ctx.send(
                    "I can't add those members to the local "
                    "whitelist as it would lock you from using this bot."
                )
        await add_to_whitelist(self.bot, members, reason, guild=ctx.guild)
        that = "that member" if len(members) == 1 else "those members"
        await ctx.send(f"Done. Added {that} to the local whitelist.")

    @local_whitelist.command(name="remove", aliases=["del", "delete"], require_var_positional=True)
    async def local_whitelist_remove(self, ctx: commands.Context, *members: discord.Member):
        """Remove members from the local whitelist

        **Arguments**
            - `members` The members to remove from the local whitelist.
        """
        if not await get_whitelist(self.bot, ctx.guild):
            return await ctx.send("There are no members in the local whitelist.")
        await remove_from_whitelist(self.bot, set(members), guild=ctx.guild)
        that = "that member" if len(members) == 1 else "those members"
        await ctx.send(f"Done. Removed {that} from the local whitelist.")

    @local_whitelist.command(name="reason")
    async def local_whitelist_reason(
        self, ctx: commands.Context, member: discord.Member, *, reason: str
    ):
        """Edit the reason for a locally whitelisted member"""
        if member.bot:
            return await ctx.send("That member is a bot.")
        elif not await in_whitelist(self.bot, member.id, ctx.guild):
            return await ctx.send("That member is not whitelisted.")
        try:
            await edit_reason(self.bot, member, reason, True)
        except KeyError:
            return await ctx.send("That member was not in the local blacklist.")
        await ctx.send("Done. The reason for that member has been updated.")

    @local_whitelist.command(name="list")
    async def local_whitelist_list(self, ctx: commands.Context):
        """List the locally whitelisted members"""
        if not (wl := await get_whitelist(self.bot, ctx.guild)):
            return await ctx.send("There are no locally allowed members.")
            # TODO At some point it might be wise to add a method as to not rely heavily on the config
            # and to look at the actual value in the wbm config
        msg = "Locally Allowed Members:"
        for uid, reason in wl.items():
            name = u.name if (u := ctx.guild.get_member(int(uid))) else "Unknown or Deleted Member"
            msg += f"\n\t- [{uid}] {name}: {reason}"
        await ctx.send_interactive(pagify(msg, page_length=1800), "yml")
