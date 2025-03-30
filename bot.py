import asyncio
import hashlib
from datetime import timedelta
from os import urandom
from time import time
from typing import Optional, Union

from motor.motor_asyncio import AsyncIOMotorClient
import config
import errors
import discord
from asyncache import cached
from cachetools import LRUCache, TTLCache
from discord.app_commands import AppCommand
from discord.ext import commands

import logger
from cogs import EXTENSIONS
# from cogs.dm_handler import HowToPlayView
# from views import BaseView

logger = logger.get_logger()


class DynoHunt(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.prefix = config.PREFIX
        self.launch_time = int(time())

    @cached(cache=LRUCache(maxsize=1))
    async def fetch_app_commands(self) -> list[dict[str, Union[str, list[str]]]]:
        """Fetch and cache all application commands.

        Returns:
            list[dict[str, Union[str, list[str]]]]: The list of application commands.
        """
        logger.info("Fetching application commands")
        application_commands = []
        fetched_commands: list[AppCommand] = await self.tree.fetch_commands()

        for command in fetched_commands:
            children = []
            for option in command.options:
                if option.type == discord.AppCommandOptionType.subcommand:
                    children.append(option.name)
            application_commands.append(
                {
                    "name": command.name,
                    "id": command.id,
                    "description": command.description,
                    "mention": command.mention,
                    "children": children,
                }
            )

        for command in application_commands[:]:
            if command["children"]:
                parent: dict = application_commands.pop(
                    application_commands.index(command)
                )
                for child in command["children"]:
                    application_commands.append(
                        {
                            "name": f"{parent['name']} {child}",
                            "id": parent["id"],
                            "description": parent["description"],
                            "mention": f"</{parent['name']} {child}:{parent['id']}>",
                            "children": [],
                        }
                    )

        return application_commands

    async def get_app_command(
        self, name: str, attribute: Optional[str] = None
    ) -> Optional[Union[dict[str, str], str]]:
        """Get an application command by name.

        Args:
            name (str): The name of the application command.

        Returns:
            Optional[Union[dict[str, str], str]]: The command dict or the attribute of the command.
        """
        for command in await self.fetch_app_commands():
            if command["name"] == name:
                return command if attribute is None else command.get(attribute)

    @cached(cache=TTLCache(maxsize=1, ttl=6 * 60 * 60))
    async def fetch_application_emojis(self) -> list[discord.Emoji]:
        """Override the fetch_application_emojis method to cache the emojis.

        Returns:
            list[Emoji]: The list of emojis.
        """
        logger.info("Fetching application emojis")
        return await super().fetch_application_emojis()

    async def get_app_emoji(self, name: str) -> str:
        """Get the emoji for the bot.

        Args:
            name (str): The name of the emoji.

        Returns:
            str: The requested emoji or "❓" if not found.
        """
        emoji = discord.utils.get(await self.fetch_application_emojis(), name=name)
        if emoji is None:
            logger.warning(f"App emoji {name} not found")
            return "❓"
        return str(emoji)

    async def setup_hook(self) -> None:
        """Hook to setup the bot."""
        self.db = AsyncIOMotorClient(config.MONGO_URI)

        extensions = EXTENSIONS
        for extension in extensions:
            try:
                await self.load_extension(extension)
            except commands.ExtensionAlreadyLoaded:
                logger.warning(f"Extension already loaded: {extension}")
            except commands.ExtensionNotFound:
                logger.error(f"Extension not found: {extension}")
            except commands.NoEntryPointError:
                logger.error(f"Extension has no setup function: {extension}")
            # except commands.ExtensionFailed as e:
            #     logger.error(f"Failed to load extension {extension}: {e}")
            finally:
                logger.debug(f"Loaded extension {extension}")

    async def on_ready(self) -> None:
        """Event to run when the bot is ready."""
        path = "./tree.hash"
        tree_hash = await get_tree_hash(self.tree)
        # Create the file if it does not exist
        with open(path, "a+b") as fp:
            pass
        with open(path, "r+b") as fp:
            data = fp.read()
            if data != tree_hash:
                await self.tree.sync()
                logger.info("Tree hash has changed, syncing...")
                fp.seek(0)
                fp.write(tree_hash)
                fp.truncate()
            else:
                logger.info("Tree hash has not changed, not syncing.")

        await self.change_presence(activity=discord.CustomActivity(name="🐰"))
        logger.info(f"{self.user} is online")

    async def on_interaction(self, interaction: discord.Interaction) -> None:
        """Interactions handler.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
        if interaction.type is not discord.InteractionType.application_command:
            return

        # await update_stat(bot, "commands_used")
        # await update_most_used_commands(bot, interaction.command.name)

        logger.debug(
            (
                f"{interaction.user} ({interaction.user.id}) used the "
                f"{interaction.command.name} application command"
            )
        )

    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError,
    ) -> None:
        """Error handler for application commands.

        Args:
            interaction (discord.Interaction): The interaction object.
            error (discord.app_commands.AppCommandError): The error object.
        """
        error_embed = discord.Embed(
            color=discord.Color.brand_red(),
            title="Error!",
            timestamp=discord.utils.utcnow(),
        )
        emoji = await self.get_app_emoji("error")

        if isinstance(error, discord.app_commands.MissingRole):
            error_embed.description = (
                f"{emoji} You are not allowed to use this command."
            )

        elif isinstance(error, discord.app_commands.MissingPermissions):
            error_embed.description = (
                f"{emoji} You are missing the required permissions to use this command."
            )

        # elif isinstance(error, errors.NotTheAuthor):
        #     error_embed.description = (
        #         f"{emoji} Only the author of the interaction can use this."
        #     )

        else:
            error_embed.description = f"{emoji} {str(error)}"

        log = f"UserID: {interaction.user.id} - Command: {interaction.command.name}: {error}"

        logger.error(log)
        try:
            await interaction.response.send_message(
                embed=error_embed, ephemeral=True, delete_after=15
            )
        except discord.InteractionResponded:
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ) -> None:
        """Error handler for prefix commands.

        Args:
            ctx (commands.Context): The context object.
            error (commands.CommandError): The error object.
        """
        error_embed = discord.Embed(
            color=discord.Color.brand_red(),
            title="Error!",
            timestamp=discord.utils.utcnow(),
        )
        error_embed.description = f"{await self.get_app_emoji('error')} {error}"
        emoji = await self.get_app_emoji("error")

        if isinstance(error, commands.CommandInvokeError):
            error = error.original
            error_embed.description = f"{emoji} {str(error)}"
            ctx.command.reset_cooldown(ctx)

        elif isinstance(error, commands.CommandNotFound):
            return

        elif isinstance(error, commands.MissingRequiredArgument):
            help_command = self.get_command("help")
            return await ctx.invoke(help_command, command=ctx.command.qualified_name)

        elif isinstance(error, commands.MissingRole):
            error_embed.description = (
                f"{emoji} You are not allowed to use this command."
            )

        elif isinstance(error, commands.NotOwner):
            return

        elif isinstance(error, commands.BadArgument):
            error_embed.description = f"{emoji} {error}"
            ctx.command.reset_cooldown(ctx)

        elif isinstance(error, commands.MissingPermissions):
            error_embed.description = (
                f"{emoji} You are missing the required permissions to use this command."
            )

        elif isinstance(error, commands.CommandOnCooldown):
            now = discord.utils.utcnow()
            cooldown = now + timedelta(seconds=error.retry_after)
            cooldown = discord.utils.format_dt(cooldown, "R")
            error_embed.description = (
                f"{emoji} The {ctx.command} command is on "
                f"cooldown, you can use it again {cooldown}."
            )
            error = f"The {ctx.command} application command is on cooldown."

        elif error.original and isinstance(error.original, errors.Error):
            error_embed.description = f"{emoji} {error.original}"
            ctx.command.reset_cooldown(ctx)

        # elif error.original and isinstance(error.original, errors.NotTheAuthor):
        #     error_embed.description = (
        #         f"{emoji} Only the author of the interaction can use this."
        #     )

        else:
            error_embed.description = f"{emoji} {error}"

        logger.error(f"UserID: {ctx.author.id} - Command: {ctx.command}: {error}")

        try:
            await ctx.reply(embed=error_embed, delete_after=15)
        except (discord.Forbidden, discord.HTTPException):
            pass


async def get_tree_hash(tree: discord.app_commands.CommandTree) -> bytes:
    """Generate a hash of the command tree."""
    coms = sorted(tree._get_all_commands(guild=None), key=lambda n: n.qualified_name)
    payload = [c.to_dict(tree) for c in coms]
    return hashlib.sha256(str(payload).encode()).digest()


async def get_prefix(bot: DynoHunt, message: discord.Message) -> str:
    """Get the prefix for the bot.

    Args:
        message (discord.Message): The message object.

    Returns:
        str: The prefix for the bot.
    """
    fake_prefix = urandom(8).hex()
    if message.guild is None or isinstance(message.author, discord.User):
        return fake_prefix
    if message.author.id == bot.owner_id:
        prefix = bot.prefix
        return commands.when_mentioned_or(prefix, prefix.capitalize())(bot, message)
    return fake_prefix


async def main() -> None:
    bot = DynoHunt(
        intents=discord.Intents(
            dm_messages=True,
            guilds=True,
            members=True,  # Required for the on_member_update event
        ),
        command_prefix=[],
        allowed_mentions=discord.AllowedMentions(
            roles=False, users=False, everyone=False
        ),
        # case_insensitive=True,
        # strip_after_prefix=True,
        owner_id=config.APP_OWNER_ID,
        # description="Put your amazing detective skills to work as you explore all things related to Dyno to find clues and coded messages for a chance to win some prizes!",
        status="online",
        # help_command=None,
    )
    await bot.start(config.APP_TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
