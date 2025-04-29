import argparse
import asyncio
import hashlib
from datetime import timedelta
from os import environ
from pathlib import Path
from time import time
from typing import Optional, Union, override

import discord
from asyncache import cached
from cachetools import LRUCache
from discord import app_commands
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient

import config
import errors
import logger
from cogs import EXTENSIONS

logger = logger.get_logger()


class CustomCommandTree(app_commands.CommandTree["DynoHunt"]):
    @override
    async def sync(self, *args, **kwargs):
        await super().sync(*args, **kwargs)
        await self.fetch_app_commands(force=True)

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        """Error handler for application commands.

        Args:
            interaction (discord.Interaction): The interaction object.
            error (app_commands.AppCommandError): The error object.
        """
        error_embed = discord.Embed(
            color=discord.Color.brand_red(),
            title="Error!",
            timestamp=discord.utils.utcnow(),
        )

        if isinstance(error, app_commands.MissingRole):
            error_embed.description = "You are not allowed to use this command."

        elif isinstance(error, app_commands.MissingPermissions):
            error_embed.description = (
                "You are missing the required permissions to use this command."
            )

        elif isinstance(error, app_commands.CommandOnCooldown):
            now = discord.utils.utcnow()
            cooldown = now + timedelta(seconds=error.retry_after)
            cooldown = discord.utils.format_dt(cooldown, "R")
            error_embed.description = (
                f"The {interaction.command.name} command is on "
                f"cooldown, you can use it again {cooldown}."
            )
            error = (
                f"The {interaction.command.name} application command is on cooldown."
            )

        else:
            error_embed.description = f"{str(error)}"

        log = f"UserID: {interaction.user.id} - Command: {interaction.command.name}: {error}"

        logger.error(log)
        try:
            await interaction.response.send_message(
                embed=error_embed, ephemeral=True, delete_after=60
            )
        except discord.InteractionResponded:
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    @cached(cache=LRUCache(maxsize=1))
    async def _cached_fetch_app_commands(
        self,
    ) -> list[dict[str, Union[str, list[str]]]]:
        """Internal method to fetch and cache application commands."""
        logger.info("Fetching application commands")
        application_commands = []
        fetched_commands: list[app_commands.AppCommand] = await self.fetch_commands()

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

    async def fetch_app_commands(
        self, force: bool = False
    ) -> list[dict[str, Union[str, list[str]]]]:
        """Fetch application commands, optionally bypassing cache.

        Args:
            force (bool, optional): Whether to bypass the cache. Defaults to False.

        Returns:
            list[dict[str, Union[str, list[str]]]]: The list of application commands.
        """
        if force:
            return await self._cached_fetch_app_commands.__wrapped__(self)
        return await self._cached_fetch_app_commands()

    async def get_tree_hash(self) -> bytes:
        """Generate a hash of the command tree."""
        coms = sorted(
            self._get_all_commands(guild=None), key=lambda n: n.qualified_name
        )
        payload = [c.to_dict(self) for c in coms]
        return hashlib.sha256(str(payload).encode()).digest()


class DynoHunt(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prefix: str | list[str] = config.args.prefix
        self.launch_time = int(time())

    async def get_app_command(
        self, name: str, attribute: Optional[str] = None
    ) -> Optional[Union[dict[str, str], str]]:
        """Get an application command by name.

        Args:
            name (str): The name of the application command.
            attribute (Optional[str], optional): The attribute of the command to get. Defaults to None.

        Returns:
            Optional[Union[dict[str, str], str]]: The command dict or the attribute of the command.
        """
        for command in await self.tree.fetch_app_commands():
            if command["name"] == name:
                return command if attribute is None else command.get(attribute)

    async def setup_hook(self) -> None:
        """Hook to setup the bot."""
        self.db = AsyncIOMotorClient(config.MONGO_URI)

        extensions = EXTENSIONS

        extensions.append("jishaku")
        environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
        environ["JISHAKU_HIDE"] = "True"
        environ["JISHAKU_NO_UNDERSCORE"] = "True"

        for extension in extensions:
            try:
                await self.load_extension(extension)
                logger.debug(f"Loaded extension {extension}")
            except commands.ExtensionAlreadyLoaded:
                logger.warning(f"Extension already loaded: {extension}")
            except commands.ExtensionNotFound:
                logger.error(f"Extension not found: {extension}")
            except commands.NoEntryPointError:
                logger.error(f"Extension has no setup function: {extension}")
            except commands.ExtensionFailed as e:
                logger.error(f"Failed to load extension {extension}: {e}")

        path = Path("./tree.hash")
        tree_hash = await self.tree.get_tree_hash()
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(tree_hash)
            await self.tree.sync()
            logger.info("Tree hash file created, syncing...")
        else:
            data = path.read_bytes()
            if data != tree_hash:
                await self.tree.sync()
                logger.info("Tree hash has changed, syncing...")
                path.write_bytes(tree_hash)
            else:
                logger.info("Tree hash has not changed, not syncing.")

    async def on_ready(self) -> None:
        """Event to run when the bot is ready."""
        logger.info(f"{self.user} is online with the prefix: {self.prefix}")

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
        error_embed.description = f"{error}"

        if isinstance(error, commands.CommandInvokeError):
            error = error.original
            error_embed.description = f"{str(error)}"
            ctx.command.reset_cooldown(ctx)

        elif isinstance(error, commands.DisabledCommand):
            return

        elif isinstance(error, commands.CommandNotFound):
            return

        elif isinstance(error, commands.MissingRequiredArgument):
            help_command = self.get_command("help")
            if help_command is None:
                return
            return await ctx.invoke(help_command, command=ctx.command.qualified_name)

        elif isinstance(error, commands.MissingRole):
            error_embed.description = "You are not allowed to use this command."

        elif isinstance(error, commands.NotOwner):
            return

        elif isinstance(error, commands.BadArgument):
            error_embed.description = f"{error}"
            ctx.command.reset_cooldown(ctx)

        elif isinstance(error, commands.MissingPermissions):
            error_embed.description = (
                "You are missing the required permissions to use this command."
            )

        elif isinstance(error, commands.CommandOnCooldown):
            now = discord.utils.utcnow()
            cooldown = now + timedelta(seconds=error.retry_after)
            cooldown = discord.utils.format_dt(cooldown, "R")
            error_embed.description = (
                f"The {ctx.command} command is on "
                f"cooldown, you can use it again {cooldown}."
            )
            error = f"The {ctx.command} application command is on cooldown."

        elif isinstance(error, commands.NoPrivateMessage):
            return

        elif isinstance(error, errors.Error):
            error_embed.description = f"{error}"
            ctx.command.reset_cooldown(ctx)

        else:
            error_embed.description = f"{error}"

        logger.error(f"UserID: {ctx.author.id} - Command: {ctx.command}: {error}")

        try:
            await ctx.reply(embed=error_embed, delete_after=60)
        except (discord.Forbidden, discord.HTTPException):
            pass


async def get_prefix(bot: DynoHunt, message: discord.Message) -> list[Optional[str]]:
    """Get the prefix for the bot.

    Args:
        message (discord.Message): The message object.

    Returns:
        str: The prefix for the bot.
    """
    if message.guild is None or isinstance(message.author, discord.User):
        return []
    if message.author.id == bot.owner_id or any(
        role.id in [config.COUNCIL_ROLE, config.COMM_WIZARD_ROLE]
        for role in message.author.roles
    ):
        prefix = bot.prefix
        return commands.when_mentioned_or(*prefix)(bot, message)
    return []


async def main() -> None:
    bot = DynoHunt(
        tree_cls=CustomCommandTree,
        intents=discord.Intents(
            dm_messages=True,
            guild_messages=True,
            message_content=True,
            guilds=True,
            members=True,  # for on_member_update
        ),
        command_prefix=get_prefix,
        allowed_mentions=discord.AllowedMentions(
            roles=False, users=False, everyone=False
        ),
        case_insensitive=True,
        strip_after_prefix=True,
        owner_id=config.APP_OWNER_ID,
        status="online",
        activity=discord.CustomActivity(name="🔎 DM me to get started with the hunt!"),
        help_command=None,
    )
    await bot.start(config.APP_TOKEN)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dyno Hunt Bot")
    parser.add_argument(
        "--prefix",
        help="Set the bot prefix. If not set, there will be no prefix.",
        type=str,
        default=[],
    )
    parser.add_argument(
        "--dev",
        help="Run the bot in development mode",
        action="store_true",
    )
    args = parser.parse_args()

    config.args = args
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
