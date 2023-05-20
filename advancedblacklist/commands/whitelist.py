# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import asyncio
import logging
from typing import Union

import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import box, pagify
from redbot.core.utils.predicates import MessagePredicate

from ..abc import ABMixin  # type:ignore
from .utils import (
    add_to_whitelist,
    clear_whitelist,
    edit_reason,
    get_whitelist,
    in_whitelist,
    remove_from_whitelist,
)

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

    @whitelist.command(name="clear")
    async def whitelist_clear(self, ctx: commands.Context, confirm: bool = False):
        """Clear the whitelist"""
        if not confirm:
            await ctx.send("Would you like to clear the whitelist?(y/n)")
            pred = MessagePredicate.yes_or_no(ctx)
            try:
                await self.bot.wait_for("message", check=pred, timeout=10.0)
            except asyncio.TimeoutError:
                pass
            if not pred.result:
                return await ctx.send("Okay, I won't clear the whitelist.")
        await clear_whitelist(self.bot)
        await ctx.send("Cleared the whitelist.")

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
        members_or_roles: commands.Greedy[Union[discord.Member, discord.Role]],
        *,
        reason: str = None,
    ):
        """Add members and roles to the local whitelist.

        This will disallow anyone not in the local whitelist or not in a role in the local whitelist from using [botname].

        Note, if you are an admin you must add yourself to the localwhitelist as to not lock yourself out of [botname].

        **Arguments**
            - `members_or_roles` The members/roles to add to the whitelist. Members cannot be bots.
            - `reason` The reason for adding these members/roles to the whitelist. This argument is optional.
        """
        if not members_or_roles:
            raise commands.UserInputError
        for user in members_or_roles:
            if isinstance(user, discord.Member) and user.bot:
                return await ctx.send("You cannot locally whitelist a bot.")
        reason = reason or "No reason provided."
        members = {u.id for u in members_or_roles}
        if not (ctx.guild.owner_id == ctx.author.id or await self.bot.is_owner(ctx.author)):
            # We need to make sure to not lock an admin out of the bot
            # This is a toned down version of the cog creator's method for this check
            # https://github.com/Cog-Creators/Red-DiscordBot/blob/V3/develop/redbot/core/core_commands.py#L4521-#L4532
            current = set((await get_whitelist(self.bot, ctx.guild)).keys())
            maybe_new = current.union(members_or_roles)
            check = {ctx.author.id}
            if check.isdisjoint(maybe_new):
                return await ctx.send(
                    "I can't add those members to the local "
                    "whitelist as it would lock you from using this bot."
                )
        await add_to_whitelist(self.bot, members_or_roles, reason, guild=ctx.guild)
        that = "that member/role" if len(members) == 1 else "those members/roles"
        await ctx.send(f"Done. Added {that} to the local whitelist.")

    @local_whitelist.command(name="remove", aliases=["del", "delete"], require_var_positional=True)
    async def local_whitelist_remove(
        self, ctx: commands.Context, *member_or_roles: Union[discord.Member, discord.Role]
    ):
        """Remove members/roles from the local whitelist

        **Arguments**
            - `members` The members/roles to remove from the local whitelist.
        """
        if not await get_whitelist(self.bot, ctx.guild):
            return await ctx.send("There are no members or roles in the local whitelist.")
        await remove_from_whitelist(self.bot, set(member_or_roles), guild=ctx.guild)
        that = "that member/role" if len(member_or_roles) == 1 else "those members/roles"
        await ctx.send(f"Done. Removed {that} from the local whitelist.")

    @local_whitelist.command(name="reason")
    async def local_whitelist_reason(
        self,
        ctx: commands.Context,
        member_or_role: Union[discord.Member, discord.Role],
        *,
        reason: str,
    ):
        """Edit the reason for a locally whitelisted member/role

        **Arguments**
            - `member_or_role` The member/role to edit the reason of. Members cannot be a bot.
            - `reason` The new reason for locally whitelisting the member/role.
        """
        if isinstance(member_or_role, discord.Member) and member_or_role.bot:
            return await ctx.send("That member is a bot.")
        elif not await in_whitelist(self.bot, member_or_role.id, ctx.guild):
            return await ctx.send("That member/role is not whitelisted.")
        try:
            await edit_reason(self.bot, member_or_role, reason, True)
        except KeyError:
            return await ctx.send("That member/role was not in the local blacklist.")
        await ctx.send("Done. The reason for that member/role has been updated.")

    @local_whitelist.command(name="clear")
    async def local_whitelist_clear(self, ctx: commands.Context, confirm: bool = False):
        """Clear the local whitelist"""
        if not confirm:
            await ctx.send("Would you like to clear the local whitelist? (y/n)")
            pred = MessagePredicate.yes_or_no(ctx)
            try:
                await self.bot.wait_for("message", check=pred, timeout=10.0)
            except asyncio.TimeoutError:
                pass
            if not pred.result:
                return await ctx.send("Okay, I won't clear the local whitelist.")
        await clear_whitelist(self.bot, ctx.guild)
        await ctx.send("Cleared the local whitelist.")

    @local_whitelist.command(name="list")
    async def local_whitelist_list(self, ctx: commands.Context):
        """List the locally whitelisted members/roles"""
        if not (wl := await get_whitelist(self.bot, ctx.guild)):
            return await ctx.send("There are no locally allowed members or roles.")
        msg = "Locally Allowed Members/Roles:"
        for uid, reason in wl.items():
            name = (
                u.name
                if (u := ctx.guild.get_member(int(uid)))
                else r.name
                if (r := ctx.guild.get_role(int(uid)))
                else "Unknown or Deleted Member/Role"
            )
            msg += f"\n\t- [{uid}] {name}: {reason}"
        await ctx.send_interactive(pagify(msg, page_length=1800), "yml")
