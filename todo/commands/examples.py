"""
MIT License

Copyright (c) 2021 Jojo#7711

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

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
        """This actually allows me to make a subcommand without actually having it(?)

        It works is what I'm saying"""
        pass

    @todo.command()
    async def example(self, ctx):
        """See some examples of how to use todo!"""
        use_md = await self.config.user(ctx.author).use_md()
        use_embeds = await self.config.user(ctx.author).use_embeds()
        combined = await self.config.user(ctx.author).combined_lists()
        msg = "Here is an example of how your todo list would look like"
        act_todos = box(_examples["todos"], "md") if use_md else _examples["todos"]
        embed = False

        if use_embeds and await ctx.embed_requested():
            todo_embed = discord.Embed(
                title="Todo example",
                colour=await ctx.embed_colour(),
                description=act_todos,
            )
            todo_embed.set_footer(text="Page 1/1")
            if not combined:
                completed_embed = discord.Embed(
                    title="Completed todo example",
                    colour=await ctx.embed_colour(),
                    description=box(_examples["completed"], "md")
                    if use_md
                    else _examples["completed"],
                )
                completed_embed.set_footer(text="Page 1/1")
                return await self._send_embedded_completed_todo(
                    ctx, todo_embed, completed_embed
                )
            to_add = f"\n{_check_mark} Completed todos\n{_examples['completed']}"
            if use_md:
                todo_embed.description = todo_embed.description[:-4] + f"{to_add}```"
            else:
                todo_embed.description += to_add
            embed = True
        else:
            msg += f"\n\n**Todo Example**\n{act_todos}"
            completed = _examples["completed"]
            if combined:
                if use_md:
                    msg = msg[:-4]
                    completed += "```"
                msg += f"\n{_check_mark} Completed todos\n{completed}"
            else:
                if use_md:
                    completed = box(completed, "md")
                msg += (
                    f"\nAnd here's what your completed list would look like\n{completed}"
                )
            msg += "\nPage 1/1"
        kwargs = {"content": msg}
        if embed:
            kwargs["embed"] = todo_embed
        await ctx.send(**kwargs)

    async def _send_embedded_completed_todo(
        self,
        ctx: commands.Context,
        todo_embed: discord.Embed,
        completed_embed: discord.Embed,
    ):
        msgs = [
            {
                "content": "This is what your todo list would look like",
                "embed": todo_embed,
            },
            {
                "content": "And this is what your completed list would look like",
                "embed": completed_embed,
            },
        ]
        [await ctx.send(**k) for k in msgs]
