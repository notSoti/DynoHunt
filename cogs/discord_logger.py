from typing import Optional

import discord
from discord.ext import commands

import config
import utils
from bot import DynoHunt
from logger import logger

logger = logger.getChild(__name__)


class UserStats(discord.ui.View):
    """A view that displays user stats."""

    def __init__(self, user_id: int):
        super().__init__(timeout=None)
        self.user_id = user_id

    @discord.ui.button(
        label="User Stats",
        style=discord.ButtonStyle.secondary,
        custom_id="button:user_stats",
    )
    async def user_stats(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Displays user stats."""
        user = interaction.client.get_user(self.user_id)
        if not user:
            try:
                user = await interaction.client.fetch_user(self.user_id)
            except discord.NotFound:
                return await interaction.response.send_message(
                    "User not found.", ephemeral=True
                )
            except discord.HTTPException as e:
                return await interaction.response.send_message(
                    f"Failed to fetch user: {e}", ephemeral=True
                )
        embed = discord.Embed(
            title=f"User Stats for {user.mention}",
            color=discord.Color.blue(),
        )
        embed.set_author(
            name=f"@{user}",
            icon_url=user.avatar,
        )
        user_data = await utils.User.get_user(interaction.client, self.user_id)
        if not user_data:
            return await interaction.response.send_message(
                "User not found in the database.", ephemeral=True
            )
        if user:
            next_key = user_data.get("key_to_find")
            embed.add_field(
                name="Keys Found",
                value=f"{next_key - 1 if next_key != -1 else len(config.KEYS) - 1}/{len(config.KEYS) - 1}",
                inline=False,
            )
            embed.add_field(
                name="Started At",
                value=f"<t:{user_data.get('created_at')}:F> (<t:{user_data.get('created_at')}:R>)",
                inline=False,
            )
            if user_data.get("key_completion_timestamps"):
                embed.add_field(
                    name="Key Completion Times",
                    value="\n".join(
                        [
                            f"Key {key}: <t:{time}:F> (<t:{time}:R>)"
                            if key != "-1"
                            else f"Finished: <t:{time}:F> (<t:{time}:R>)"
                            for key, time in user_data.get(
                                "key_completion_timestamps", {}
                            ).items()
                        ]
                    ),
                    inline=False,
                )
            if user_data.get("flagged"):
                embed.add_field(
                    name="⚠️ Potential Cheating",
                    value=(
                        "This user has been flagged for potential cheating due to getting keys too quickly "
                        "or getting multiple keys in the wrong order. "
                        "Please further review their progress and verify if they are cheating."
                    ),
                    inline=False,
                )
            embed.set_footer(
                text=f"Total attempts: {user_data.get('total_attempts', 0)}"
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class DiscordLogger(commands.Cog):
    """Cog for sending messages to the bot's log channel."""

    def __init__(self, bot: DynoHunt):
        self.bot = bot
        self.persistent_view = UserStats(config.APP_OWNER_ID)

    async def cog_load(self):
        self.bot.add_view(self.persistent_view)

    async def cog_unload(self):
        self.persistent_view.stop()

    @commands.Cog.listener()
    async def on_key_guess(
        self, message: discord.Message, wrong_key: Optional[bool] = False
    ) -> None:
        """Listens for guess attempts and logs them.

        Args:
            message (discord.Message): The message object received.
            wrong_key (bool, optional): Whether the guess was a key out of order. Defaults to False.
        """

        if not config.LOGS_CHANNEL_ID:
            return

        logging_channel = self.bot.get_channel(config.LOGS_CHANNEL_ID)
        if not logging_channel:
            return logger.warning("Could not find the logging channel.")

        embed = discord.Embed(
            title="Guess Attempt",
            description=message.content,
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow(),
        )
        if wrong_key:
            embed.add_field(
                name="⚠️ Wrong Key",
                value="This key was guessed out of order.",
                inline=False,
            )
        embed.set_author(
            name=f"@{message.author}",
            icon_url=message.author.avatar,
        )
        embed.set_footer(
            text=f"User ID: {message.author.id} | Message ID: {message.id}"
        )

        try:
            await logging_channel.send(embed=embed, view=UserStats(message.author.id))
        except discord.Forbidden:
            logger.error("Missing permissions to send messages to the logging channel.")
        except discord.HTTPException as e:
            logger.error(f"Failed to send message to the logging channel: {e}")

    @commands.Cog.listener()
    async def on_key_found(self, message: discord.Message) -> None:
        """Listens for key finds and logs them.

        Args:
            message (discord.Message): The message object received.
        """

        if not config.LOGS_CHANNEL_ID:
            return

        logging_channel = self.bot.get_channel(config.LOGS_CHANNEL_ID)
        if not logging_channel:
            return logger.warning("Could not find the logging channel.")

        user = await utils.User.get_user(self.bot, message.author.id)
        next_key = user.get("key_to_find")
        embed = discord.Embed(
            title=f"Key Found: {next_key - 1 if next_key != -1 else len(config.KEYS) - 1}/{len(config.KEYS) - 1}",
            description=message.content,
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_author(
            name=f"@{message.author}",
            icon_url=message.author.avatar,
        )
        embed.set_footer(
            text=f"User ID: {message.author.id} | Message ID: {message.id}"
        )

        try:
            await logging_channel.send(embed=embed, view=UserStats(message.author.id))
        except discord.Forbidden:
            logger.error("Missing permissions to send messages to the logging channel.")
        except discord.HTTPException as e:
            logger.error(f"Failed to send message to the logging channel: {e}")

    @commands.Cog.listener()
    async def on_user_finish(self, user: discord.User) -> None:
        """Listens for user finishes and logs them.

        Args:
            message (discord.Message): The message object received.
        """

        if not config.LOGS_CHANNEL_ID:
            return

        logging_channel = self.bot.get_channel(config.LOGS_CHANNEL_ID)
        if not logging_channel:
            return logger.warning("Could not find the logging channel.")

        embed = discord.Embed(
            title="User Finished",
            description=f"{user.mention} has finished the hunt!",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_author(
            name=f"@{str(user)}",
            icon_url=user.avatar,
        )
        embed.set_footer(text=f"User ID: {user.id}")

        try:
            await logging_channel.send(embed=embed, view=UserStats(user.id))
        except discord.Forbidden:
            logger.error("Missing permissions to send messages to the logging channel.")
        except discord.HTTPException as e:
            logger.error(f"Failed to send message to the logging channel: {e}")


async def setup(bot: DynoHunt):
    """Adds the cog to the bot."""
    await bot.add_cog(DiscordLogger(bot))
