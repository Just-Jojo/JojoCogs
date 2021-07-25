# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from redbot.core import commands

from ..abc import TodoMixin
from ..utils import NonBotMember


class Managers(TodoMixin):
    """Manage a user's managers for their todo list"""

    @commands.group()
    async def todo(self, *args):
        pass

    @todo.group(name="manager", aliases=["managers"])
    async def todo_mangers(self, ctx: commands.Context):
        """Manage who can manage your todo lists. These people can add and remove from your todo list, so be careful who you grant this to
        """
        pass

    @todo_mangers.command(name="add")
    async def manager_add(self, ctx: commands.Context, user: NonBotMember):
        """Add a user to your todo list managers
        
        This user cannot be a bot. Please be aware that they can add and remove from your todo list and they can view it at any time

        **Arguments**
            - `user` The user you would like to add to your list's managers.
        """
        managers = await self.cache.get_user_item(ctx.author, "managers")
        managers.append(user.id)
        await self.cache.set_user_item(ctx.author, "managers", managers)

        await ctx.send(f"Added {user.name} to your todo list's managers")

    @todo_mangers.command(name="remove", aliases=["del", "delete"])
    async def manager_remove(self, ctx: commands.Context, user: NonBotMember):
        """Remove a user from your list's managers

        This user cannot be a bot

        **Arguments**
            - `user` The user to remove from your managers
        """
        managers = await self.cache.get_user_item(ctx.author, "managers")
        if not managers or user.id not in managers:
            return await ctx.send("That user is not a manager")
        managers.remove(user.id)
        await self.cache.set_user_item(ctx.author, "managers", managers)
        await ctx.send(f"Removed {user.name} from your todo list's managers")

    @todo_mangers.command(name="list")
    async def manager_list(self, ctx: commands.Context):
        """List your todo list's managers"""
        data = await self.cache.get_user_data(ctx.author.id)
        managers = data["managers"]
        settings = data["user_settings"]

        if not managers:
            return await ctx.send(
                (
                    f"You do not have any managers for your todo lists."
                    f" Use `{ctx.clean_prefix}todo manager add` to add a user to your todo list's managers"
                )
            )
        managers = [f"{self._get_user_name(i)} | ({i})" for i in managers]

        await self.page_logic(ctx, managers, f"{ctx.author.name}'s Todo Managers", **settings)

    def _get_user_name(self, user_id: int):
        name = self.bot.get_user(user_id)
        return name.name if name is not None else "Unknown or Deleted User"
