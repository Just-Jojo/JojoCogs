"""
MIT License

Copyright (c) 2020-2021 Jojo#7711

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

from pycipher import pycipher
from redbot.core import commands

_caesar = pycipher.Caesar(key=4)
_atbash = pycipher.Atbash()
_vigenere = pycipher.Vigenere
_porta = pycipher.Porta


class Depypher(commands.Cog):
    """GIRPNWXRQHTLRYCGWQTQHHKVVAXRWCEILSJQRPTYHVH!

    (hint, use `[p]devigenere depypher <this docstring>` to find out what it means!)
    """

    @commands.command()
    async def caesar(self, ctx, *, to_cipher: str):
        """IRGVCTX E QIWWEKI AMXL E GEIWEV GMTLIV
        (hint, use `[p]deceaser <this docstring>` to find out what it means!)
        """
        await ctx.send(_caesar.encipher(string=to_cipher, keep_punct=True))

    @commands.command()
    async def decaesar(self, ctx, *, cipher: str):
        """Decrypt a message with Caesar"""
        await ctx.send(_caesar.decipher(string=cipher, keep_punct=True))

    @commands.command()
    async def atbash(self, ctx, *, cipher: str):
        """VMXIBKG Z NVHHZTV DRGS ZGYZHS
        (hint, use `[p]deatbash <this docstring>` to find out what it means!)
        """
        await ctx.send(_atbash.encipher(string=cipher, keep_punct=True))

    @commands.command()
    async def deatbash(self, ctx, *, cipher: str):
        """Decipher a message encrypted with Atbash"""
        await ctx.send(_atbash.decipher(string=cipher, keep_punct=True))

    @commands.command()
    async def vigenere(self, ctx, keyword: str, *, cipher: str):
        """HREZNWXUEOVQHTJIYZRWOLKGECGXZMVYYZXBAQIB
        (hint, use `[p]devigenere decrypt <this docstring>` to find out what it means!)
        """
        await ctx.send(_vigenere(key=keyword).encipher(cipher))

    @commands.command()
    async def devigenere(self, ctx, keyword: str, *, cipher: str):
        """Decipher a message encrypted in Vigenere with a keyword"""
        await ctx.send(_vigenere(key=keyword).decipher(cipher))

    @commands.command()
    async def porta(self, ctx, keyword: str, *, cipher: str):
        """SLQJMIKOOSKGUPSHWLTMQSAAJHUYWAVZF
        (hint, use `[p]deporta decrypt <this docstring>` to find out what it means!)
        """
        await ctx.send(_porta(key=keyword).encipher(string=cipher))

    @commands.command()
    async def deporta(self, ctx, keyword: str, *, cipher: str):
        """Decrypt a message with the Porta cipher!"""
        await ctx.send(_porta(key=keyword).decipher(string=cipher))

    async def red_delete_data_for_user(self, *, requester, user_id):
        """Nothing to delete"""
        return
