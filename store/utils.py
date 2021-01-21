import discord

from redbot.core import commands, Config
from redbot.core.bot import Red
from redbot.vendored.discord.ext import menus
import typing

__all__ = ["JojoMenu", "LargeMenu", "NoGuild"]


class MenuMixin:
    """Menu mixin

    Adds :func:`send_initial_message`, :func:`on_exit` or X button, and :func:`index_parser`
    """
    index: int
    pages: list
    current_page: typing.Union[discord.Embed, str]
    message: discord.Message

    def index_parser(self, forwards: bool, skip: bool):
        """Adds/Subtracts an amount from the index based on variables

        Parameters
        ----------
        forwards: :class:`bool`
            If True, this will increase the index by the amount
            Otherwise it will descrease
        skip: :class:`bool`
            If True it will set the amount to 5
            Otherwise it will set it to 1
        """
        page_len = len(self.pages) - 1  # Index starts at 0
        if skip is True:
            amount = 5
        else:
            amount = 1
        if forwards is True:
            self.index += amount
            if self.index > page_len:
                self.index = page_len
        else:
            self.index -= amount
            if self.index < 0:
                self.index = 0
        self.current_page = self.pages[self.index]

    async def on_exit(self, payload):
        """|coro|

        Currently the only method you need to implement yourself

        Type
        ----
        This method should be a :class:`Button` and should have the button decorator
        """
        raise NotImplementedError

    async def send_initial_message(self, ctx: commands.Context, channel: discord.TextChannel):
        if ctx.guild is None or channel is None:
            channel = ctx.channel  # This is handy
        if isinstance(self.current_page, discord.Embed):
            return await channel.send(embed=self.current_page)
        else:
            return await channel.send(content=self.current_page)

    async def message_send(self):
        if isinstance(self.current_page, discord.Embed):
            return await self.message.edit(embed=self.current_page)
        else:
            return await self.message.edit(content=self.current_page)


class StoreMenu(MenuMixin, menus.Menu):
    """A Menu for the store as I'd rather use this than Red's
    """

    def __init__(
        self, pages: list, timeout: float = 30.0, remove_reactions: bool = True,
        delete_message_after: bool = False
    ):
        self.pages = pages
        self.index = 0
        self.current_page = self.pages[0]
        super().__init__(timeout=timeout, delete_message_after=delete_message_after,
                         clear_reactions_after=remove_reactions)

    @menus.button("\N{LEFTWARDS BLACK ARROW}")
    async def on_left(self, payload):
        self.index_parser(forwards=False, skip=False)
        await self.message_send()

    @menus.button("\N{CROSS MARK}")
    async def on_exit(self, payload):
        self.stop()
        await self.message.delete()

    @menus.button("\N{BLACK RIGHTWARDS ARROW}")
    async def on_right(self, payload):
        self.index_parser(forwards=True, skip=False)
        await self.message_send()


class LargeMenu(MenuMixin, menus.Menu):
    """A larger menu"""

    def __init__(
        self, pages: list, timeout: float = 30.0, remove_reactions: bool = True,
        delete_message_after: bool = False
    ):
        self.index = 0
        self.pages = pages
        self.current_page = self.pages[0]
        super().__init__(timeout=timeout, delete_message_after=delete_message_after,
                         clear_reactions_after=remove_reactions)

    @menus.button("\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}")
    async def on_far_left(self, payload):
        self.index_parser(forwards=False, skip=True)
        await self.message_send()

    @menus.button("\N{LEFTWARDS BLACK ARROW}")
    async def on_left(self, payload):
        self.index_parser(forwards=False, skip=False)
        await self.message_send()

    @menus.button("\N{CROSS MARK}")
    async def on_exit(self, payload):
        self.stop()
        await self.message.delete()

    @menus.button("\N{BLACK RIGHTWARDS ARROW}")
    async def on_right(self, payload):
        self.index_parser(forwards=True, skip=False)
        await self.message_send()

    @menus.button("\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}")
    async def on_far_right(self, payload):
        self.index_parser(forwards=True, skip=True)
        await self.message_send()
