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
    @commands.guild_only()
    @checks.guildowner()
    async def todoset(self, ctx):
        """The base settings command for the ToDo cog"""

    @todoset.command()
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
        """Remove a ToDo reminder"""
        if isinstance(ctx.channel, discord.abc.GuildChannel):
            toogle = await self.check_dm(ctx)
        else:
            toogle = False
        if number is None:
            todo_list = self.readable_dict(await self.config.user(ctx.author).todo.get_raw(), True)
            msg = "Here are all of the ToDo reminders you have: \n{0}\nTo remove one, please type `[p]todo remove|del <number>`".format(
                todo_list)
            if toogle is True:
                return await ctx.author.send(msg)
            return await ctx.send(msg)
        await self.config.user(ctx.author).todo.clear_raw(number)
        msg = "Sucessfully removed that ToDo reminder."
        if toogle is True:
            return await ctx.author.send(msg)
        await ctx.send(msg)

    @todo.command(name="list")
    async def _list(self, ctx):
        todo_list = self.readable_dict(await self.config.user(ctx.author).todo.get_raw())
        if isinstance(ctx.channel, discord.abc.GuildChannel):
            toggle = await self.config.guild(ctx.guild).get_raw("DM")
        else:
            toggle = False
        if toggle is True:
            return await ctx.author.send(todo_list)
        await ctx.send(todo_list)

    def readable_dict(self, dictionary: dict, numbered: bool = False) -> str:
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

    async def check_dm(self, ctx) -> bool:
        toogle: bool = await self.config.guild(ctx.guild).get_raw("DM")
        return toogle
