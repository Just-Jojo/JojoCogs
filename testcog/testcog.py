from redbot.core import commands
from redbot.core.utils import menus
import discord
import asyncio


class TestCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def pages(self, ctx):
        x = {"Test": 34, "Vanguards": 30, "Vanesrseguards": 30, "Vangersuards": 30, "Vanserguards": 30, "Vangdgesuards": 30, "Vanguargdds": 30, "Vangzuards": 30,
             "Vnguards": 30, "Vangusards": 30, "Vangfuards": 30, "Vandguards": 30, "Vangauards": 30, "Vangguards": 30, "Vangeuards": 30}
        embeds = []
        counts = 0
        embed = discord.Embed(title="Store")
        for key, value in x.items():
            if counts == 25:
                embed.add_field(name=key, value=value, inline=False)
                embeds.append(embed)
                embed = discord.Embed(title="Store")
                counts = 0
            else:
                embed.add_field(name=key, value=value, inline=False)
                counts += 1
        msg = await ctx.send(embed=embeds[0])
        c = menus.DEFAULT_CONTROLS if len(embeds) > 1 else {
            "\N{CROSS MARK}": menus.close_menu}
        asyncio.create_task(menus.menu(ctx, embeds, c, message=msg))
        menus.start_adding_reactions(msg, c.keys())
