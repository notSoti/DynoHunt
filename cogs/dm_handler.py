from time import strftime, time

import discord
from discord.ext import commands

import config
import utils
from bot import DynoHunt


class HowToPlayView(discord.ui.View):
    """A view that displays information on how to play the game."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="How to Play",
        style=discord.ButtonStyle.secondary,
        custom_id="button:how_to_play",
    )
    async def how_to_play(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """Displays information on how to play the game."""
        embed = discord.Embed(
            title=f"Dyno Hunt {strftime('%Y')}!",
            description=(
                "Welcome to this year's Dyno Hunt! This is a scavenger hunt "
                "where you must find keys to progress through the clues. "
                "Each key is a word or phrase that you must find and enter to progress to the next clue. "
                "You can enter your guesses here in this DM channel."
            ),
            color=discord.Color.blue(),
        )
        embed.add_field(
            name="How to Play",
            value=(
                "1. Read the clue provided.\n"
                "2. Use the clue to find the key. "
                "All keys will only contain lowercase letters A-Z with **no spaces**. "
                "An example key is `sixstars`\n"
                "3. Send the key **here** in this DM channel.\n"
                "4. If you're correct, you'll receive the next clue! "
                "Otherwise, I'll tell you so. Also keep in mind, you have to find the keys in the correct order!\n"
                "Additionally, you can use a few slash commands here to keep track of your progress! "
                "Just type `/` here to see all available commands.\n"
                f"For more information, check out <#{config.EVENTS_CHANNEL_ID}>; good luck!"
            ),
            inline=False,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class DMHandler(commands.Cog):
    """Cog for handling user activity in a guild."""

    def __init__(self, bot: DynoHunt):
        self.bot = bot
        self.cd_mapping = commands.CooldownMapping.from_cooldown(
            2, 5, commands.BucketType.user
        )
        self.persistent_view = HowToPlayView()

    async def cog_load(self):
        self.bot.add_view(self.persistent_view)

    async def cog_unload(self):
        self.persistent_view.stop()

    def cleanup_message(self, message_content: discord.Message) -> str:
        """Cleans up a message by removing common prefixes, codeblocks and strings.

        Args:
            message (discord.Message): The message to clean up.

        Returns:
            str: The cleaned up message.
        """
        common_chars = [".", ",", "!", "?", "-", "/", ">", "`", '"', "'"]
        for char in common_chars:
            message_content = message_content.replace(char, "")
        return message_content.lower()

    async def is_sus(self, user_id: int) -> bool:
        """Check if user is solving keys too quickly or guessing keys in wrong order.

        Args:
            user_id (int): Discord user ID to check

        Returns:
            bool: True if user is progressing suspiciously fast or guessing out of order
        """
        user = await utils.User.get_user(self.bot, user_id)
        if not user:
            return False

        if user.get("key_completion_timestamps"):
            timestamps = user.get("key_completion_timestamps", {})
            completion_times = sorted(timestamps.values())

            for i in range(1, len(completion_times)):
                time_diff = completion_times[i] - completion_times[i - 1]
                if time_diff < 180:
                    return True

        wrong_order_guesses = user.get("wrong_order_correct_guesses", 0)
        if wrong_order_guesses > 6:
            return True

        return False

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Listens for messages and key guesses in DMs and processes them.

        Args:
            message (discord.Message): The message object received.
        """

        if message.guild is not None or message.author.bot or not message.content:
            return
        if len(message.content) == 1 or len(message.content) >= 100:
            return

        cooldown = self.cd_mapping.get_bucket(message)
        if cooldown.update_rate_limit():
            return

        if int(time()) < config.START_TIME_TIMESTAMP:
            return
        if int(time()) > config.END_TIME_TIMESTAMP:
            return await message.reply(
                "The hunt has ended. Thanks for participating!",
                allowed_mentions=discord.AllowedMentions.none(),
            )

        message.content = self.cleanup_message(message.content)

        user = await utils.User.get_user(self.bot, message.author.id)
        if not user:
            user = await utils.User.create_user(self.bot, message.author.id)

        if await utils.User.has_finished(self.bot, message.author.id):
            return await message.reply(
                "You've already completed the hunt! Thanks for participating!",
                allowed_mentions=discord.AllowedMentions.none(),
            )

        async with message.channel.typing():
            await utils.User.increment_attempts(self.bot, message.author.id)

            # If the user has found the final key, send the decoding instructions
            # and the final code (from this last guess)
            if user.get("key_to_find") == -1:
                return await message.reply(
                    (
                        "Congratulations! You've found all of the keys! "
                        "Here's your final clue:\n"
                        f"> {await utils.User.get_clue(self.bot, message.author.id)}"
                    ),
                    allowed_mentions=discord.AllowedMentions.none(),
                )

            # Check if the guess is correct
            if message.content == await utils.User.get_key(self.bot, message.author.id):
                user = await utils.User.advance_user(self.bot, message.author.id)
                await message.reply(
                    (
                        "Correct! This key's code is "
                        f"***{await utils.User.get_code(self.bot, message.author.id)}***! "
                        "Here's your next clue:\n> "
                        f"{await utils.User.get_clue(self.bot, message.author.id)}\n"
                    ),
                    allowed_mentions=discord.AllowedMentions.none(),
                    view=HowToPlayView(),
                )
                self.bot.dispatch("key_found", message)

            else:
                if flagged := message.content in [
                    key["value"]
                    for key in config.KEYS.values()
                    if isinstance(key, dict) and "value" in key
                ]:
                    await utils.User.increment_wrong_order_guesses(
                        self.bot, message.author.id
                    )
                await message.reply(
                    (
                        "That's not the correct key or that's not your **next** key! "
                        "Here's your current clue again:\n"
                        f"> {await utils.User.get_clue(self.bot, message.author.id)}"
                    ),
                    allowed_mentions=discord.AllowedMentions.none(),
                    view=HowToPlayView(),
                )
                self.bot.dispatch(
                    "key_guess", message
                ) if not flagged else self.bot.dispatch("key_guess", message, True)

        if await self.is_sus(message.author.id):
            await utils.User.set_flag(self.bot, message.author.id, True)


async def setup(bot: DynoHunt):
    """Adds the cog to the bot."""
    await bot.add_cog(DMHandler(bot))
