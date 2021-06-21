# Copyright (c) 2021 - Jojo#7791
# Licensed under MIT

import logging
from typing import Callable, Literal, Optional

import discord
from pycipher import pycipher
from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_list

log = logging.getLogger("red.JojoCogs.depypher")

_caesar = pycipher.Caesar(key=4)
_atbash = pycipher.Atbash()
_vigenere = pycipher.Vigenere
_porta = pycipher.Porta


async def convert_case(original: str, new: str) -> str:
    """Convert a string's casing to be the same as the original"""
    ret = ""
    for index, letter in enumerate(original):
        if not letter.isalpha():
            ret += letter
            _ = list(new)  # type:ignore
            _.insert(index, letter)
            new = "".join(_)
            continue
        if letter.isupper():
            ret += new[index].upper()
        else:
            ret += new[index].lower()
    return ret


class Depypher(commands.Cog):
    """GIRPNWXRQHTLRYCGWQTQHHKVVAXRWCEILSJQRPTYHVH!

    (hint, use `[p]devigenere depypher <this docstring>` to find out what it means!)
    """

    __authors__ = ["Jojo#7791"]
    __version__ = "1.0.0"

    def format_help_for_context(self, ctx: commands.Context):
        pre = super().format_help_for_context(ctx)
        plural = "s" if len(self.__authors__) > 1 else ""
        return (
            f"{pre}\n"
            f"Author{plural}: {humanize_list(self.__authors__)}\n"
            f"Version: `{self.__version__}`"
        )

    @commands.command()
    async def caesar(self, ctx, *, to_cipher: str):
        """IRGVCTX E QIWWEKI AMXL E GEIWEV GMTLIV
        (hint, use `[p]deceaser <this docstring>` to find out what it means!)
        """
        await self._process_message(
            ctx, _caesar.encipher(string=to_cipher, keep_punct=True), to_cipher
        )

    @commands.command()
    async def decaesar(self, ctx, *, cipher: str):
        """Decrypt a message with Caesar"""
        await self._process_message(
            ctx, _caesar.decipher(string=cipher, keep_punct=True), cipher
        )

    @commands.command()
    async def atbash(self, ctx, *, cipher: str):
        """VMXIBKG Z NVHHZTV DRGS ZGYZHS
        (hint, use `[p]deatbash <this docstring>` to find out what it means!)
        """
        await self._process_message(
            ctx, _atbash.encipher(string=cipher, keep_punct=True), cipher
        )

    @commands.command()
    async def deatbash(self, ctx, *, cipher: str):
        """Decipher a message encrypted with Atbash"""
        await self._process_message(
            ctx, _atbash.decipher(string=cipher, keep_punct=True), cipher
        )

    @commands.command()
    async def vigenere(self, ctx, keyword: str, *, cipher: str):
        """HREZNWXUEOVQHTJIYZRWOLKGECGXZMVYYZXBAQIB
        (hint, use `[p]devigenere decrypt <this docstring>` to find out what it means!)
        """
        await self._process_message(ctx, _vigenere(key=keyword).encipher(cipher), cipher)

    @commands.command()
    async def devigenere(self, ctx, keyword: str, *, cipher: str):
        """Decipher a message encrypted in Vigenere with a keyword"""
        await self._process_message(ctx, _vigenere(key=keyword).decipher(cipher), cipher)

    @commands.command()
    async def porta(self, ctx, keyword: str, *, cipher: str):
        """SLQJMIKOOSKGUPSHWLTMQSAAJHUYWAVZF
        (hint, use `[p]deporta decrypt <this docstring>` to find out what it means!)
        """
        await self._process_message(
            ctx, _porta(key=keyword).encipher(string=cipher), cipher
        )

    @commands.command()
    async def deporta(self, ctx, keyword: str, *, cipher: str):
        """Decrypt a message with the Porta cipher!"""
        await self._process_message(
            ctx, _porta(key=keyword).decipher(string=cipher), cipher
        )

    @staticmethod
    async def _process_message(
        ctx: commands.Context, msg: str, original: str
    ) -> discord.Message:
        processed = await convert_case(original, msg)
        return await ctx.send(processed)

    async def red_delete_data_for_user(
        self,
        *,
        requester: Literal["discord_deleted_user", "owner", "user", "user_strict"],
        user_id: int,
    ) -> None:
        return
