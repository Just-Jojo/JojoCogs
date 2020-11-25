#pylint: disable=unused-variable
import logging
import random
from typing import Literal
import asyncio

import discord
from redbot.core import Config, commands
from redbot.core.utils import menus
from redbot.core.utils.chat_formatting import pagify

log = logging.getLogger('red.jojo.mjolnir')


class Mjolnir(commands.Cog):
    default_user = {
        "times_lifted": 0
    }
    default_guild = {
        "drop_rate": 100
    }

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, 15034742, force_registration=True)
        self.config.register_user(**self.default_user)
        self.config.register_guild(**self.default_guild)
        self.embed = Embed(self.bot)

    async def red_delete_data_for_user(
        self,
        requester: Literal["discord", "owner", "user", "user_strict"],
        user_id: int
    ) -> None:
        await self.config.user_from_id(user_id).clear()

    @commands.command()
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def trylift(self, ctx):
        """Try to lift Thor's mighty hammer"""
        trylift_error = [
            "You tried your best but still lost. Fear not! There is still hope!",
            "If you wish for the power of a god, you better be worthy of it",
            "No luck just yet, try again!",
            "You'll get it! Just keep trying! I believe in you"
        ]
        rate = await self.config.guild(ctx.guild).get_raw("drop_rate")
        trylift_result = random.randint(1, rate)
        if trylift_result == rate:
            old = await self.config.user(ctx.author).get_raw('times_lifted')
            msg = "The sky opens up and a bolt of lightning strikes the ground\nYou are worthy. Hail, son of Odin"
            if rate >= 50:
                await self.config.user(ctx.author).set_raw("times_lifted", value=old + 1)
                log.info("{}({}) has lifted mjolnir".format(
                    ctx.author.name, ctx.author.id)
                )
            else:
                log.info(
                    "{} has lifted the hammer but because the drop rate was so low I will not be adding it to the leaderboard".format(
                        ctx.author.name)
                )
        else:
            msg = random.choice(trylift_error)
        await ctx.send(msg)

    @commands.command()
    @commands.mod_or_permissions(manage_guild=True)
    async def rates(self, ctx, number: int = None):
        """
        Adjust the chance for lifting Mjolnir

        *Note that if the chance for lifting it is below 50 anyone who lifts it will not be added to the leaderboard"""

        if number is not None:
            await self.config.guild(ctx.guild).set_raw("drop_rate", value=number)
            await ctx.send("The chance of lifting Mjolnir is now `{}`".format(number))
        else:
            rate = await self.config.guild(ctx.guild).get_raw("drop_rate")
            await ctx.send("The chance for lifting Mjolnir is `1/{}`".format(rate))

    @commands.command()
    async def liftedboard(self, ctx):
        """Get the leaderboard for the people who have lifted Thor's hammer"""

        board = await self.config.all_users()
        users = sorted(
            board.items(), key=lambda x: x[1]["times_lifted"], reverse=True
        )
        sen = []
        for user in users:
            name = self.bot.get_user(user[0]).name
            amount = user[1]["times_lifted"]
            sen.append("**{}** {}".format(name, amount))
        if len(sen) > 0:
            paged = pagify(text=(sending := "\n".join(sen)), page_length=1500)
            embeds = []
            for page in paged:
                embed = await self.embed.create(ctx, title="Worthy leaderboard")
                embed.add_field(name="Liftedboard", value=page)
                embeds.append(embed)
            controls = menus.DEFAULT_CONTROLS if len(embeds) > 1 else {
                "\N{CROSS MARK}": menus.close_menu
            }
            asyncio.create_task(
                menus.menu(
                    ctx, embeds, controls, message=(msg := await ctx.send(embed=embeds[0])),
                    timeout=20
                )
            )
            menus.start_adding_reactions(msg, controls)
        else:
            await ctx.send("No one has lifted Thor's hammer yet!")


class Embed:
    def __init__(self, bot):
        self.bot = bot

    async def create(
        self, ctx: commands.Context, title: str = None, description: str = None,
        image: str = None, thumbnail: str = None, footer: str = None, footer_url: str = None,
        color: discord.Colour = None
    ) -> discord.Embed:
        data = discord.Embed()
        if title:
            data.title = title
        if description:
            data.description = description

        if color:
            data.colour = color
        else:
            if isinstance(ctx.channel, discord.TextChannel):
                data.colour = ctx.author.colour
            else:
                data.colour = await ctx.embed_colour()

        if thumbnail:
            data.set_thumbnail(url=thumbnail)
        if image:
            data.set_image(url=image)

        if not footer:
            footer = "{} embed maker".format(ctx.me.name)
        if not footer_url:
            footer_url = ctx.me.avatar_url
        data.set_footer(text=footer, icon_url=footer_url)

        return data
