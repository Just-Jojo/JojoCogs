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

    async def whisper(self, ctx, user: discord.Member, msg: str = ""):
        try:
            await user.send(msg)
        except discord.Forbidden:
            return await ctx.send("I cannot dm that user.")

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

    @todo.command(name="list")
    async def _list(self, ctx):
        todo_list = await self.config.user(ctx.author).todo.get_raw()
        if await self.config.guild(ctx.guild).DM is True:
            await self.whisper(ctx, user=ctx.author, msg=todo_list)
        else:
            await ctx.send(todo_list)
