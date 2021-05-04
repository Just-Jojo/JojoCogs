# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

from typing import List, Union

import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import box

from .abc import ToDoMixin

_examples = {
    "todos": (
        "1. Finish my essay\n"
        "2. Write a script for turning off my lights :D\n"
        "3. Theater practice"
    ),
    "completed": "1. Get a puppy :)\n2. JavaScript for my website!",
}
_check_mark = "\N{WHITE HEAVY CHECK MARK}"


class Examples(ToDoMixin):
    """Example commands"""

    @commands.group()
    async def todo(self, ctx):
        pass

    @todo.command()
    async def example(self, ctx):
        """Get an example of what your todo list would look like"""
        conf = await self._get_user_config(ctx.author)
        md = conf.get("use_md", True)
        embedded = conf.get("use_embeds", True)
        private = conf.get("private", False)
        combined = conf.get("combined_lists", False)
        act_todos = list(_examples.values())
        channel = await self._get_destination(ctx)

        if md:
            if combined:
                pre = "\n\N{WHITE HEAVY CHECK MARK} Completed\n".join(act_todos)
                act_todos = box(pre, "md")
            else:
                act_todos = [box(x, "md") for x in act_todos]
        elif combined:
            # The reason I have an elif is because if md and combined are true it will
            # combine the lists with markdown
            # I don't want it to do that, then recombine the string right after
            # so elif is needed
            act_todos = "\n\N{WHITE HEAVY CHECK MARK} Completed\n".join(act_todos)

        if (not private and await ctx.embed_requested() and embedded) or (
            private and embedded
        ):
            if not combined:
                return await self._handle_not_combined(ctx, channel, private, act_todos)
            embed = (
                discord.Embed(title="Todos", colour=await ctx.embed_colour())
            ).set_footer(text="Page 1/1")
            embed.description = act_todos
            return await channel.send(
                "Here's what your todo list would look like", embed=embed
            )

        if combined:
            msg = (
                "Here's what your todo list would look like\n" + act_todos + "\nPage 1/1"
            )
        else:
            msg = "Here's what your todo list would look like\n" + act_todos[0]
            msg += (
                "\nAnd here's what your completed list would look like\n" + act_todos[1]
            )
        await channel.send(msg)

    async def _handle_not_combined(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel,
        private: bool,
        todos: List[str],
    ):
        """Very good method name Jojo!"""
        todo_embed = (
            discord.Embed(
                title="Todos", description=todos[0], colour=await ctx.embed_colour()
            )
        ).set_footer(text="Page 1/1")
        completed_embed = (
            discord.Embed(
                title="Completed todos",
                description=todos[1],
                colour=await ctx.embed_colour(),
            )
        ).set_footer(text="Page 1/1")
        bundled = [
            ["Here is what your todo list would look like", todo_embed],
            ["And here is what your completed list would look like", completed_embed],
        ]
        await self._send_multiple(channel, bundled)

    async def _send_multiple(
        self, channel: discord.TextChannel, content: List[List[Union[str, discord.Embed]]]
    ):
        [await channel.send(content=msg, embed=embed) for msg, embed in content]
