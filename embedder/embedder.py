"""MIT License

Copyright (c) 2020 Jojo#7711

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
SOFTWARE."""

from redbot.core import commands, Config
import discord

import logging
from . import parsers
from typing import Optional, Literal  # *

log = logging.getLogger("red.jojo.embedmaker")


class Embedder(commands.Cog):
    """
    An embed maker for Red.
    This mostly exists because I couldn't find a better first/third party cog

    Create an embed from text or from a json file (upload a json file with the command)
    """

    __version__ = "1.0.0"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 12535235231231231, True)
        self.config.register_global(embeds={})
        self.config.register_guild(embeds={}, defaults=False)
        # `Embeds` is dict(name: str, embed: discord.Embed)

    async def red_delete_data_for_user(
        self,
        requester: Literal["discord", "owner", "user", "user_strict"],
        user_id: int
    ) -> None:
        """Nothing to delete."""
        return

    @commands.group()
    @commands.admin()
    async def setembed(self, ctx):
        """Base setter command for embeds"""

    @setembed.command()
    async def usedefault(self, ctx, state: bool):
        await self.config.guild(ctx.guild).set_raw("defaults", value=state)
        await ctx.tick()

    @commands.group()
    async def embed(self, ctx):
        """Basic embed command"""

    @embed.group(name="global")
    @commands.is_owner()
    async def glob(self, ctx):
        """Base global command"""

    @glob.command(name="upload")
    async def _upload(self, ctx, name):
        """Upload a global embed"""
        await self.upload_embed_parser(ctx, name, True)

    @glob.command(name="create")  # Pesky already-defined errors
    async def _create(self, ctx, name: str, title: str, *, description):
        """Create a global embed"""
        await self.create_embed(ctx, name, title, description, True)

    @glob.command(name="remove", aliases=("del", "delete"))
    async def _remove(self, ctx, embed: str):
        """Remove a global embed"""
        embeds = await self.config.get_raw('embeds')
        if embed not in embeds.keys():
            await ctx.send("Hm, that embed doesn't seem to exist!")
            return
        del embeds[embed]
        await self.config.set_raw("embeds", value=embeds)
        await ctx.tick()

    @embed.group(invoke_without_command=True)
    async def drop(self, ctx, channel: Optional[discord.TextChannel], name: str):
        """Send an embed from the given title"""
        embeds = await self.config.guild(ctx.guild).get_raw("embeds")
        try:
            embed = embeds[name]
        except KeyError:
            await ctx.send("Hm, that embed does not seem to exist")
            return
        channel = channel or ctx.channel
        await channel.send(embed=discord.Embed.from_dict(embed))

    @drop.command(name="global")
    async def _global(self, ctx, channel: Optional[discord.TextChannel], name: str):
        """Drop a global embed"""
        embeds = await self.config.get_raw("embeds")
        try:
            embed = embeds[name]
        except KeyError:
            await ctx.send("Hm, that embed doesn't seem to exist")
            return
        channel = channel or ctx.channel
        await channel.send(embed=discord.Embed.from_dict(embed))

    @embed.command()
    @commands.mod_or_permissions(embed_links=True)
    async def create(self, ctx, name: str, title: str, *, description: str = None):
        """Create a simple embed"""
        await self.create_embed(ctx, name, title, description, False)

    @embed.group(invoke_without_command=True)
    @commands.mod_or_permissions(embed_links=True)
    async def store(self, ctx, name: str, title: str, *, description: str):
        """Store a simple embed by a name
        Example:
        `[p]embed store rules \"Demaratus support server rules\" Be nice
        Don't steal other's code`"""
        embeds = await self.config.guild(ctx.guild).get_raw("embeds")
        if name in embeds.keys():  # Do this **before** creating the embed
            await ctx.send(f"An embed with the name {name} has already been created!")
            return
        embed = discord.Embed(title=title, description=description)
        embeds[name] = embed.to_dict()
        await self.config.guild(ctx.guild).set_raw("embeds", value=embeds)
        await ctx.send(embed=embed)

    @store.command()
    async def msg(self, ctx, name: str, message: int):
        """Store an embed from a message"""
        embeds = await self.config.guild(ctx.guild).get_raw("embeds")
        if name in embeds.keys():
            await ctx.send(f"An embed with the name `{name}` already exists!")
            return
        try:
            msg: discord.Message = await ctx.fetch_message(message)
        except discord.NotFound:
            await ctx.send("Hm, I couldn't seem to find that message")
            return
        if len(msg.embeds) < 1:
            await ctx.send("That message doesn't seem to have any embeds!")
            return
        await ctx.send(embed=msg.embeds[0])
        embeds[name] = msg.embeds[0].to_dict()
        await self.config.guild(ctx.guild).set_raw('embeds', value=embeds)

    @embed.command()
    @commands.mod_or_permissions(embed_links=True)
    async def upload(self, ctx, name: str):
        """Store an embed from a JSON file"""
        await self.upload_embed_parser(ctx, name, False)

    @embed.command()
    async def uploadnostore(self, ctx, channel: discord.TextChannel = None):
        """Upload an embed from a file without storing it"""
        channel = channel or ctx.channel
        em = await parsers.parse_embed(ctx.message.attachments)
        if type(em) == str:
            await ctx.send(
                f"Couldn't create an embed from that file!"
                f" ```py\n{em}```"
            )
            return
        elif type(em) == None:
            await ctx.send("That's not a `json` file")
            return
        await ctx.send(embed=em)

    @embed.command(name="list")
    async def _list(self, ctx, guild_specific: bool = True):
        """List all of the available embeds"""
        embs = await self.embed_lister(ctx, guild_specific)
        log.info(embs)
        if not embs:
            msg = "There are no embeds yet!" if guild_specific is False else f"{ctx.guild.name} doesn't have any embeds!"
            await ctx.send(msg)
            return
        embed = discord.Embed()
        embed.title = f"{ctx.guild.name} Embeds" if guild_specific else f"{ctx.me.name} Embeds"
        embed.add_field(name="Embeds", value=", ".join(embs))
        await ctx.send(embed=embed)

    @embed.command(aliases=("del", "delete"))
    @commands.mod_or_permissions(embed_links=True)
    async def remove(self, ctx, embed: str):
        """Delete a stored embed"""
        embeds = await self.config.guild(ctx.guild).get_raw("embeds")
        if not embed in embeds.keys():
            await ctx.send("Hm, that embed doesn't seem to exist")
            return
        del embeds[embed]
        await self.config.guild(ctx.guild).set_raw('embeds', value=embeds)
        await ctx.tick()

    async def embed_lister(self, ctx: commands.Context, global_guild: bool) -> list:
        if global_guild:
            embeds = await self.config.guild(ctx.guild).get_raw("embeds")
            if len(list(embeds.keys())) > 0:
                return list(embeds.keys())
            return None
        embeds = await self.config.get_raw('embeds')
        if len(list(embeds.keys())) > 0:
            return list(embeds.keys())
        return None

    def default_embed(self, ctx: commands.Context = None):
        embed = discord.Embed()
        if ctx:
            embed.colour = ctx.embed_color
        else:
            embed.colour = 0x00ffff
        return embed  # This was shorter than I thought...

    async def upload_embed_parser(
        self, ctx: commands.Context, name: str, glob: bool = False
    ):
        if glob:
            embeds = await self.config.get_raw("embeds")
        else:
            embeds = await self.config.guild(ctx.guild).get_raw("embeds")

        if name in embeds.keys():
            await ctx.send(f"An embed with the name {name} already exists!")
            return

        if len(ctx.message.attachments) < 1:
            await ctx.send("You need to have a `json` file uploaded when using this command!")
            return
        parsed = await parsers.parse_embed(ctx.message.attachments)
        if parsed == None:
            await ctx.send("The type of a file for embeds needs to end with `.json`!")
            return
        elif type(parsed) == str:
            await ctx.send(parsed)
            return
        await ctx.send(embed=parsed)
        embeds[name] = parsed.to_dict()
        if glob:
            await self.config.set_raw('embeds', value=embeds)
            return
        await self.config.guild(ctx.guild).set_raw("embeds", value=embeds)

    async def create_embed(self, ctx: commands.Context, name: str, title: str, description: str, glob: bool):
        """Create an embed that's either global or guild"""
        if glob:
            embeds = await self.config.get_raw("embeds")
        else:
            embeds = await self.config.guild(ctx.guild).get_raw("embeds")

        if name in embeds.keys():
            await ctx.send(f"An embed with the name `{name}` already exists!")
            return

        embed = self.default_embed()
        embed.title = title
        embed.description = description
        log.info(embed)

        await ctx.send(embed=embed)
        embeds[name] = embed.to_dict()
        if glob:
            await self.config.set_raw("embeds", value=embeds)
            return
        await self.config.guild(ctx.guild).set_raw("embeds", value=embeds)
