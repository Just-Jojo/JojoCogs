"""
MIT License

Copyright (c) 2020 jack1142

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

This project bundles font from Noto family (https://www.google.com/get/noto/) which is distributed under the SIL Open Font License.
Copy of this license can be found in NotoSans-LICENSE.txt file in the pillowsend/data/fonts folder of this repository.
"""
import discord
from discord.abc import Messageable

from redbot.core import commands, Config
from redbot.core.commands import Context
from redbot.core.bot import Red
from functools import wraps

real_send = Messageable.send
CONFIG = Config.get_conf(None, 348964231348679, True, "CanadianSend")
CONFIG.register_global(toggle=False, double=True)


@wraps(real_send)
async def send(
    self,
    content=None,
    *,
    tts=False,
    embed=None,
    file=None,
    files=None,
    delete_after=None,
    nonce=None,
    allowed_mentions=None,
) -> discord.Message:
    content = str(content) if content is not None else None
    if content:
        if len(content) > 1995:
            await real_send(self, "Eh?")
        else:
            content = content.replace("about", "aboot")  # haha aboot go brr
            if await CONFIG.double():
                content = f"Eh, {content}"
            if content.endswith((".", "!", "?")):
                content += " Eh?"
            elif content.endswith((" ", "\n", "```")):
                content += "Eh?"
            else:
                content += ", eh?"
    else:
        content = "Eh?"
    return await real_send(
        self,
        content=content,
        tts=tts,
        embed=embed,
        file=file,
        files=files,
        delete_after=delete_after,
        nonce=nonce,
        allowed_mentions=allowed_mentions,
    )


class CanadianSend(commands.Cog):
    __author__ = ["jack1142 (Jackenmen#6607)", "Jojo#7791"]

    def __init__(self, bot: Red):
        self.bot = bot

    def cog_unload(self):
        setattr(Messageable, "send", real_send)

    async def initalize(self):
        toggle = await CONFIG.toggle()
        if toggle:
            setattr(Messageable, "send", send)

    @commands.group(invoke_without_command=True)
    @commands.is_owner()
    async def canadiansend(self, ctx, toggle: bool):
        """Toggle CanadianSend because why not?"""
        if toggle:
            setattr(Messageable, "send", send)
        else:
            setattr(Messageable, "send", real_send)
        await ctx.tick()
        await CONFIG.toggle.set(toggle)

    @canadiansend.command()
    async def double(self, ctx, toggle: bool):
        """Double, eh?, eh?"""
        await CONFIG.double.set(toggle)
        await ctx.tick()

    @commands.command()
    async def canadiancredits(self, ctx):
        """Credits for Jack because without SmileySend I wouldn't have this"""
        description = (
            "Thanks to Jack over at Red"
            " for giving me the tools to make this!"
            "\nYou can check Jack's smileysend out at their [repo](https://github.com/jack1142/WeirdUnsupportedCogsOfJack)"
        )
        embed = discord.Embed(
            title="Canadian Send Credits!",
            description=description,
            colour=await ctx.embed_colour(),
        )
        await ctx.send(embed=embed)
