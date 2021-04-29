# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import asyncio
import logging
import typing

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box, pagify
from redbot.core.utils.predicates import MessagePredicate
from jojo_utils import positive_int, Menu

from .commands import CompositeMetaclass, Deleting, Examples, Settings
from .utils import TodoPages, todo_positive_int

_config_structure = {
    "todos": [],
    "completed": [],
    "detailed_pop": False,
    "use_md": True,
    "use_embeds": True,
    "autosort": False,
    "reverse_sort": False,
    "combined_lists": False,
    "private": False,
}
_about = (
    "ToDo is a cog designed by Jojo#7791 for keeping track"
    " of tasks for you to do. It provides a simple listing,"
    " adding, and completing for you to work with, and is highly"
    " customizable so you get the best out of it"
)
_comic_link = (
    "https://raw.githubusercontent.com/Just-Jojo/JojoCog-Assets/main/data/todo_comic.jpg"
)


class ToDo(Examples, Settings, Deleting, commands.Cog, metaclass=CompositeMetaclass):
    """A simple and highly customizable todo list for Discord"""

    _no_completed_message = (
        "You don't have any completed todos!"
        " You can complete a todo using `{prefix}todo complete <indexes...>`"
    )
    _no_todo_message = "You don't have any todos! Add one using `{prefix}todo add <todo>`"
    __version__ = "1.2.5"
    __author__ = ["Jojo#7791"]

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            cog_instance=self, identifier=19924714019, force_registration=True
        )
        self.config.register_user(**_config_structure)
        self.log = logging.getLogger("red.JojoCogs.todo")

    def format_help_for_context(self, ctx: commands.Context):
        """Thankie thankie Sinbad"""
        plural = ""
        if len(self.__author__) > 1:
            plural = "s"
        return (
            f"{super().format_help_for_context(ctx)}"
            f"\n\nCurrent Version: `{self.__version__}`"
            f"\nAuthor{plural}: `{', '.join(self.__author__)}`"
        )

    ### Listing commands ###

    @commands.group(invoke_without_command=True)
    async def todo(self, ctx, index: todo_positive_int):
        """Todo commands

        Add a todo to your list and manage your tasks
        """
        act_index = index - 1
        conf = await self._get_user_config(ctx.author)
        todos = conf.get("todos", [])
        if act_index >= len(todos):
            return await ctx.send("You don't have a todo at that index")
        todo = f"{index}. {todos.pop(act_index)}"
        embed = conf.get("use_embeds", True)
        md = conf.get("use_md", True)
        title = f"{ctx.author.name}'s Todos | Todo #{index}"

        if md:
            todo = box(todo, "md")
        if embed and await ctx.embed_requested():
            embed = discord.Embed(
                colour=await ctx.embed_colour(), title=title, description=todo
            )
            kwargs = {"embed": embed}
        else:
            msg = f"{title}\n{todo}"
            kwargs = {"content": msg}
        await ctx.send(**kwargs)

    @todo.group(
        invoke_without_command=True, aliases=["c"], require_var_positional=True
    )  # `c` is easy to type
    async def complete(self, ctx, *indexes: todo_positive_int):
        """Commands having to do with completed todos"""
        if not await self.config.user(ctx.author).todos():
            return await ctx.send(self._no_todo_message.format(prefix=ctx.clean_prefix))
        async with ctx.typing():
            async with self.config.user(ctx.author).todos() as todos:
                async with self.config.user(ctx.author).completed() as completed:
                    indexes = [x - 1 for x in indexes]  # Remove 1 from each item...
                    indexes.sort(reverse=True)  # and sort the list
                    fails, failed, comp, compled = 0, [], 0, []
                    for index in indexes:
                        try:
                            rmd = todos.pop(index)
                        except IndexError:
                            fails += 1
                            failed.append(f"`{index}`")
                        else:
                            comp += 1
                            compled.append(f"`{rmd}`")
                            completed.append(f"{rmd}")
        msg = "Done."
        details = await self.config.user(ctx.author).detailed_pop()
        if comp:
            plural = "" if comp == 1 else "s"
            msg += f"\nCompleted {comp} todo{plural}"
            if details:
                msg += "\n" + "\n".join(compled)
        if fails:
            plural = "" if fails == 1 else "s"
            msg += f"\nFailed to complete {fails} todo{plural}"
            if details:
                msg += "\n" + "\n".join(failed)
        await self._maybe_autosort(ctx)
        if len(msg) > 2000:
            await ctx.send_interactive(pagify(msg))
        else:
            await ctx.send(msg)

    @todo.command()
    async def explain(self, ctx, comic: bool = False):
        """Explain a bit about this cog"""
        if (em := await ctx.embed_requested()) :
            embed = discord.Embed(title="About Todo", colour=await ctx.embed_colour())
            kwargs = {"embed": embed}
        else:
            kwargs = {"content": None}
        if comic:
            if em:
                embed.set_image(url=_comic_link)
            else:
                kwargs["content"] = _comic_link
        else:
            if em:
                embed.description = _about
            else:
                kwargs["content"] = _about
        await ctx.send(**kwargs)

    @todo.command()
    async def suggestions(self, ctx):
        """See how you could add suggestions!"""
        msg = (
            "Thanks for reading this! I made this cog for managing my tasks, "
            "however I realised that this would be helpful for a lot of people "
            "and I added the ability to customize your todo list!\nHowever, "
            "I can add more things, I just don't know what I should add, "
            "you can help by going to my GitHub repo (<https://github.com/Just-Jojo/JojoCogs>), "
            "go to the `issues` tab, click on `Todo suggestions`, and leave a comment! "
            "(here's the issue link <https://github.com/Just-Jojo/JojoCogs/issues/15> :) )"
        )
        if await ctx.embed_requested():
            kwargs = {
                "embed": discord.Embed(
                    title="Todo suggestions",
                    description=msg,
                    colour=await ctx.embed_colour(),
                ),
            }
        else:
            kwargs = {"content": msg}
        await ctx.send(**kwargs)

    @todo.command(name="add")
    async def todo_add(self, ctx, *, todo: str):
        """Add a todo to your list"""
        async with self.config.user(ctx.author).todos() as todos:
            todos.append(todo)

        msg = "Added that as a todo"
        details = await self.config.user(ctx.author).detailed_pop()
        if details:
            msg += f"\n'{discord.utils.escape_markdown(todo)}'"
        await self._maybe_autosort(ctx)
        if len(msg) > 2000:
            await ctx.send_interactive(pagify(msg))
        else:
            await ctx.send(msg)

    @todo.command()
    async def sort(self, ctx):
        """Sort your todos"""
        await ctx.send("Would you like to sort your todos in reverse? (y/n)")
        pred = MessagePredicate.yes_or_no(ctx)
        try:
            await self.bot.wait_for("message", check=pred)
        except asyncio.TimeoutError:
            await ctx.send("Okay, I won't sort your todos in reverse")
            result = False
        else:
            result = pred.result
        await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
        await self.config.user(ctx.author).reverse_sort.set(result)
        async with self.config.user(ctx.author).todos() as todos:
            todos.sort(reverse=result)
        await self.config.user(ctx.author).autosort.set(True)

    @todo.command(name="list")
    async def todo_list(self, ctx):
        """List your current todos!"""
        conf = await self._get_user_config(ctx.author)
        todos = conf.get("todos", [])
        comb = conf.get("combined_lists", False)
        completed = conf.get("completed", [])
        use_md = conf.get("use_md", True)
        use_embeds = conf.get("use_embeds", True)
        private = conf.get("private", True)

        if not todos:
            if comb and completed:
                return await self._complete_list(
                    ctx,
                    completed=completed,
                    use_md=use_md,
                    use_embeds=use_embeds,
                    private=private,
                )
            return await ctx.send(self._no_todo_message.format(prefix=ctx.clean_prefix))

        todos = await self._number_lists(todos)
        if comb and completed:
            if not use_md:
                completed = await self._cross_lists(completed)
            completed = await self._number_lists(completed)
            completed.insert(0, "\N{WHITE HEAVY CHECK MARK} Completed todos")
            todos.extend(completed)
        await self.page_logic(
            ctx, todos, "Todos", use_md=use_md, use_embeds=use_embeds, private=private
        )

    @complete.command(name="sort")
    async def complete_sort(self, ctx):
        """Sort your todos"""
        await ctx.send("Would you like to sort your completed todos in reverse? (y/n)")
        pred = MessagePredicate.yes_or_no(ctx)
        try:
            await self.bot.wait_for("message", check=pred)
        except asyncio.TimeoutError:
            await ctx.send("Okay, I won't sort them in reverse")
            result = False
        else:
            result = pred.result
        await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
        await self.config.user(ctx.author).reverse_sort.set(result)
        async with self.config.user(ctx.author).completed() as todos:
            todos.sort(reverse=result)

    @complete.command(name="list")
    async def complete_list(self, ctx):
        """List your completed todos"""
        conf = await self._get_user_config(ctx.author)
        completed = conf.get("completed", [])
        use_md = conf.get("use_md", True)
        use_embeds = conf.get("use_embeds", True)

        if not completed:
            await ctx.send(self._no_completed_message.format(prefix=ctx.clean_prefix))
        else:
            if not use_md:
                completed = await self._cross_lists(completed)
            completed = await self._number_lists(completed)
            await self.page_logic(
                ctx,
                completed,
                "Completed todos",
                use_md=use_md,
                use_embeds=use_embeds,
                private=conf.get("private", False),
            )

    @todo.command()
    async def version(self, ctx):
        """Check the version of todo"""
        msg = f"ToDo version: `{self.__version__}`"
        await ctx.send(msg)

    ### Utility methods ###

    async def _complete_list(
        self,
        ctx: commands.Context,
        *,
        completed: typing.List[str],
        use_md: bool,
        use_embeds: bool,
        private: bool,
    ):
        if not use_md:
            completed = await self._cross_lists(completed)
        completed = await self._number_lists(completed)
        completed.insert(0, "\N{WHITE HEAVY CHECK MARK} Completed")
        await self.page_logic(
            ctx=ctx,
            data=completed,
            title="Todos",
            use_md=use_md,
            use_embeds=use_embeds,
            private=private,
        )

    async def page_logic(
        self,
        ctx: commands.Context,
        data: list,
        title: str,
        *,
        use_md: bool,
        use_embeds: bool,
        private: bool,
    ):
        data = self._pagified_list(data)
        source = TodoPages(
            data=data,
            use_md=use_md,
            use_embeds=use_embeds,
            title=title,
        )
        await Menu(
            source=source,
            delete_message_after=False,
            clear_reactions_after=True,
            timeout=15.0,
        ).start(
            ctx, channel=await self._get_destination(ctx, private=private), wait=False
        )

    async def _number_lists(self, data: list):
        return [f"{num}. {x}" for num, x in enumerate(data, 1)]

    def _pagified_list(self, data: list):
        return list(pagify("\n".join(data), page_length=500))

    async def _maybe_autosort(self, ctx: commands.Context):
        if not await self.config.user(ctx.author).autosort():
            return
        reverse = await self.config.user(ctx.author).reverse_sort()
        async with self.config.user(ctx.author).todos() as todos:
            todos.sort(reverse=reverse)
        async with self.config.user(ctx.author).completed() as completed:
            completed.sort(reverse=reverse)

    async def _get_destination(self, ctx: commands.Context, *, private: bool):
        if private:
            if ctx.author.dm_channel is None:
                await ctx.author.create_dm()
            return ctx.author.dm_channel
        return ctx.channel

    async def _sort_indexes(self, index: typing.List[int]) -> typing.List[int]:
        index.sort(reverse=True)
        return index

    async def _cross_lists(self, data: list):
        return [f"~~{x}~~" for x in data]

    async def _get_user_config(
        self, user: typing.Union[int, discord.Member, discord.User]
    ) -> dict:
        if isinstance(user, int):
            return await self.config.user_from_id(user).all()
        return await self.config.user(user).all()
