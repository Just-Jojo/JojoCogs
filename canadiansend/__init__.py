from .canadian_send import CanadianSend


async def setup(bot):
    c = CanadianSend(bot)
    bot.add_cog(c)
    await c.initalize()