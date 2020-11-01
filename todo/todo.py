from redbot.core import commands, checks, Config
import discord
import logging

log = logging.getLogger("red.jojo.todo")


class ToDo(commands.Cog):
    """A simple todo list for discord"""
    _default_global_settings = {
        "DM": True
    }

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, 19924714009, force_registration=True)
        self.config.register_guild(**self._default_global_settings)
        self.config.register_user(
            todo={
                "ToDo": "Create a ToDo reminder"
            }
        )

    @commands.group()
    @commands.guild_only()
    @checks.guildowner()
    async def todoset(self, ctx):
        """The base settings command for the ToDo cog"""

    @todoset.command()
    async def dm(self, ctx, toggle: bool = None):
        """Toggles the dm setting
        will default to True if not specified"""
        if toggle is None:
            return await ctx.send("I can't set it to `None`!")
        old = await self.check_dm(ctx)
        if toggle == old:
            msg = "That is the same setting!\nSilly goose"
        else:
            await self.config.guild(ctx.guild).set_raw("DM", value=toggle)
            msg = "Set the DM status to `{}`\n\n`True meaning I will dm the user, False meaning I will send it to the server`".format(
                toggle)
        await ctx.send(msg)

    @commands.group()
    async def todo(self, ctx):
        """Base ToDo command"""

    @todo.command()
    async def add(self, ctx, title, *, description):
        """Add a ToDo to your list"""
        await self.config.user(ctx.author).todo.set_raw(title, value=description)
        await ctx.send("Added `{0}` to your ToDo list under the title `{1}`.".format(description, title))

    @todo.command(aliases=["del", ])
    async def remove(self, ctx, *, reminder: str = None):
        """Remove a ToDo reminder"""
        toogle = False if isinstance(ctx.channel, discord.DMChannel) else await self.check_dm(ctx)
        if reminder is None:
            todos = await self.get_todos(ctx, ctx.author)
            if toogle is False:
                await ctx.send(todos)
            else:
                try:
                    return await ctx.author.send(todos)
                except discord.Forbidden:
                    return await ctx.send("I could not send you the message!\n{}".format(todos))

        await self.config.user(ctx.author).todo.clear_raw(reminder)
        await ctx.send("I have removed `{}` from your ToDo list".format(reminder))

    @todo.command(name="list")
    async def _list(self, ctx):
        todo_list = self.readable_dict(await self.config.user(ctx.author).todo.get_raw())
        if isinstance(ctx.channel, discord.abc.GuildChannel):
            toggle = await self.check_dm(ctx)
        else:
            toggle = False
        if toggle is True:
            try:
                return await ctx.author.send(todo_list)
            except discord.Forbidden:
                return await ctx.send("I could not dm you the message!")
        await ctx.send(todo_list)

    def readable_dict(self, dictionary: dict, numbered: bool = False) -> str:
        readable = []
        for num, (key, item) in enumerate(dictionary.items()):
            if numbered is True:
                string_version = "{0}. {1}: {2}".format(num, key, item)
            else:
                string_version = "{0}: {1}".format(key, item)
            readable.append(string_version)
        return "\n".join(readable)

    async def check_dm(self, ctx) -> bool:
        toogle: bool = await self.config.guild(ctx.guild).get_raw("DM")
        return toogle

    async def get_todos(self, ctx: commands.Context, author: discord.Member) -> str:
        todos = await self.config.user(author).todo.get_raw()
        return self.readable_dict(todos, True)
