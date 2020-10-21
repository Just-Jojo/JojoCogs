from redbot.core import commands, checks, Config
import discord


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
    @checks.admin()
    async def todoset(self, ctx):
        """The base settings command for the ToDo cog"""

    @todoset.command()
    @checks.admin()
    async def dm(self, ctx, toggle: bool = True):
        """Toggles the dm setting
        will default to True if not specified"""
        await self.config.guild(ctx.guild).DM.set_raw(value=toggle)
        await ctx.send("Set the dm status to `{}`".format(toggle))

    @commands.group()
    async def todo(self, ctx):
        """Base ToDo command"""

    @todo.command()
    async def add(self, ctx, title, *, description):
        """Add a ToDo to your list"""
        await self.config.user(ctx.author).todo.set_raw(title, value=description)
        await ctx.send("Added `{0}` to your ToDo list under the title `{1}`.".format(description, title))

    @todo.command(aliases=["del", ])
    async def remove(self, ctx, number: int = None):
        if number is None:
            todo_list = self.readable_dict(await self.config.user(ctx.author).todo.get_raw(), True)
            return await ctx.send("Here are all of the ToDo reminders you have: {0}\nTo remove one, please type `[p]todo remove|del <number>`".format(todo_list))
        await self.config.user(ctx.author).todo.clear_raw(number)
        await ctx.send("Sucessfully removed that ToDo reminder.")

    @todo.command(name="list")
    async def _list(self, ctx):
        todo_list = await self.config.user(ctx.author).todo.get_raw()
        toggle = await self.config.guild(ctx.guild).get_raw("DM")
        readable_todo = self.readable_dict(todo_list)
        if toggle is True:
            await self.whisper(ctx, user=ctx.author, msg=readable_todo)
        else:
            await ctx.send(readable_todo)

    def readable_dict(self, dictionary: dict, numbered: bool = False):
        num = 0
        readable = []
        for key, item in dictionary.items():
            if numbered is True:
                string_version = "{0}. {1}: {2}".format(num, key, item)
                num += 1
            else:
                string_version = "{0}: {1}".format(key, item)
            readable.append(string_version)
        return "\n".join(readable)

    async def whisper(self, ctx, user: discord.Member, msg: str = ""):
        try:
            await user.send(msg)
        except discord.Forbidden:
            return await ctx.send("I cannot dm that user.")
