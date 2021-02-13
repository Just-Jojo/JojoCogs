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
