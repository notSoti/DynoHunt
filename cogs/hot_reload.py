import os
from pathlib import Path as pathlib

from discord.ext import commands, tasks

from bot import DynoHunt
from logger import logger

logger = logger.getChild(__name__)


class HotReload(commands.Cog):
    """Cog for handling the timed services."""

    def __init__(self, bot: DynoHunt):
        self.bot = bot
        self.reload_extensions.start()

    def cog_unload(self):
        self.reload_extensions.cancel()

    @tasks.loop(seconds=10)
    async def reload_extensions(self) -> None:
        """Hot reloads the extensions if they have been modified."""
        for extension in list(self.bot.extensions.keys()):
            if extension in ["jishaku"]:
                continue
            path = pathlib(extension.replace(".", os.sep) + ".py")
            last_modified_time = os.path.getmtime(path)

            try:
                if self.last_modified_time[extension] == last_modified_time:
                    continue
            except KeyError:
                self.last_modified_time[extension] = last_modified_time

            try:
                await self.bot.reload_extension(extension)
            except commands.ExtensionNotLoaded:
                continue
            except commands.ExtensionError:
                logger.warning(f"Couldn't hot-reload extension: {extension}")
            else:
                logger.info(f"Hot-Reloaded extension: {extension}")
            finally:
                self.last_modified_time[extension] = last_modified_time

    @reload_extensions.before_loop
    async def cache_last_modified_time(self) -> None:
        """Caches the last modified time of the extensions."""
        await self.bot.wait_until_ready()
        self.last_modified_time = {}
        for extension in self.bot.extensions.keys():
            if extension in ["jishaku"]:
                continue
            path = pathlib(extension.replace(".", os.sep) + ".py")
            last_modified_time = os.path.getmtime(path)
            self.last_modified_time[extension] = last_modified_time


async def setup(bot: DynoHunt):
    """Initializes the cog."""
    await bot.add_cog(HotReload(bot))
