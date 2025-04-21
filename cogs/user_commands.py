from time import strftime, time
from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands

import config
import errors
import utils
from bot import DynoHunt


class UserCommands(commands.Cog):
    """Utility commands for the bot."""

    def __init__(self, bot: DynoHunt):
        self.bot = bot

    def average_time_between_keys(self, user_data: dict) -> str:
        """Calculate the average time between keys."""
        timestamps = user_data.get("key_completion_timestamps", [])
        if len(timestamps) < 2:
            return "N/A"

        sorted_timestamps = sorted(int(timestamp) for timestamp in timestamps.values())
        total_time = sum(
            sorted_timestamps[i + 1] - sorted_timestamps[i]
            for i in range(len(sorted_timestamps) - 1)
        )
        average_minutes = total_time / (len(sorted_timestamps) - 1) / 60

        if average_minutes < 60:
            return f"{average_minutes:.2f} minutes"
        elif average_minutes < 1440:  # Less than 24 hours
            return f"{average_minutes / 60:.2f} hours"
        else:
            return f"{average_minutes / 1440:.2f} days"

    def find_longest_key_time(self, user_data: dict) -> tuple[str, int]:
        """Calculate which key took the longest time to find.

        Returns:
            tuple[str, int]: A tuple containing the key number and time taken in seconds
        """
        timestamps = user_data.get("key_completion_timestamps", {})
        if len(timestamps) < 2:
            return None, 0

        # Convert to sorted list of (key, timestamp) pairs
        sorted_items = sorted(
            [(k, int(v)) for k, v in timestamps.items() if k != "-1"],
            key=lambda x: int(x[1]),
        )

        longest_time = 0
        longest_key = None
        prev_timestamp = user_data.get("created_at")

        # Compare each timestamp with the previous one
        for key, timestamp in sorted_items:
            time_taken = timestamp - prev_timestamp
            if time_taken > longest_time:
                longest_time = time_taken
                longest_key = key
            prev_timestamp = timestamp

        return longest_key, longest_time

    def _format_found_items(
        self,
        user_data: dict,
        item_type: Literal["value", "code"],
    ) -> str:
        """Format found keys or codes for display."""
        items_found = []
        for key, key_data in config.KEYS.items():
            if key == "-1" or str(key) not in user_data.get(
                "key_completion_timestamps", {}
            ):
                continue

            item_value = key_data.get(item_type.lower())
            items_found.append(
                f"{'Key' if item_type == 'value' else 'From Key'} {key}: **{item_value}**"
            )

        return "\n".join(items_found)

    def calculate_completion_time(self, start_time: int, end_time: int) -> str:
        """Calculate the total time taken between two timestamps.

        Args:
            start_time (int): Starting timestamp
            end_time (int): Ending timestamp

        Returns:
            str: Formatted time string with days, hours, and minutes
        """
        total_time = end_time - start_time
        days = total_time // 86400
        hours = (total_time % 86400) // 3600
        minutes = (total_time % 3600) // 60

        time_parts = []
        if days > 0:
            time_parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours > 0:
            time_parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0:
            time_parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")

        return ", ".join(time_parts)

    @app_commands.command(
        name="help",
        description="Learn how to play the hunt.",
    )
    @app_commands.checks.cooldown(1, 6, key=lambda i: (i.user.id))
    @app_commands.dm_only()
    async def _help(self, interaction: discord.Interaction):
        """Get help with the hunt."""
        embed = discord.Embed(
            title=f"Dyno Hunt {strftime('%Y')}! <a:DynoGlitch:866473520326377472>",
            description=(
                "Welcome to this year's Dyno Hunt!\n\n"
                "This is an exciting scavenger hunt where you'll solve clues to discover hidden keys "
                "throughout the Dyno community. Each key is unique and will unlock the next part of your adventure. "
                "Simply send your guesses here in our DM channel.\n\n"
                "Ready to begin your quest? Get your first clue with the "
                f"{await self.bot.get_app_command('clue', 'mention')} command!"
            ),
            color=discord.Color.blue(),
        )
        embed.add_field(
            name="How to Play",
            value=(
                "1. Read the clue carefully.\n"
                "2. Solve the clue to find the key. "
                "Keys only contain lowercase letters a-z (no spaces, numbers, or special characters). "
                "Example key: `sixstars`\n"
                "3. Send your answer here in this DM channel.\n"
                "4. If correct, you'll get the next clue! If wrong, you can try again.\n"
                "Remember: Keys must be found in the correct order.\n\n"
                "Type `/` to see available commands and track your progress!\n"
                f"Visit <#{config.EVENTS_CHANNEL_ID}> for more details. Good hunting!"
            ),
            inline=False,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="progress",
        description="See your current progress in the hunt.",
    )
    @app_commands.checks.cooldown(1, 6, key=lambda i: (i.user.id))
    @app_commands.dm_only()
    async def _progress(self, interaction: discord.Interaction):
        """Check your progress in the hunt."""
        if int(time()) > config.END_TIME_TIMESTAMP:
            raise errors.Error(
                "The hunt is over! Check back next year for more clues and keys!"
            )
        user_data = await utils.User.get_user(self.bot, interaction.user.id)
        if not user_data:
            return await interaction.response.send_message(
                (
                    f"You haven't started the hunt yet! Use "
                    f"{await self.bot.get_app_command('clue', 'mention')} to get your first clue."
                ),
                ephemeral=True,
            )

        if not user_data.get("key_completion_timestamps"):
            return await interaction.response.send_message(
                (
                    f"You haven't found any keys yet! Use "
                    f"{await self.bot.get_app_command('clue', 'mention')} to get your first clue."
                ),
                ephemeral=True,
            )

        embed = discord.Embed(
            title="Your Progress",
            description="Here's your progress in the hunt so far:",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_author(
            name=f"@{str(interaction.user)}",
            icon_url=interaction.user.avatar,
        )
        embed.set_footer(
            text=(
                f"You've found {len(user_data.get('key_completion_timestamps'))} "
                f"out of {len(config.KEYS) - 1} keys"
            ),
        )

        keys_resp = self._format_found_items(user_data, "value")
        embed.add_field(
            name="Keys Found",
            value=keys_resp,
            inline=False,
        )

        # Check if the current hunt is using codes
        if config.KEYS.get("1", {}).get("code"):
            codes_resp = self._format_found_items(user_data, "code")
            embed.add_field(
                name="Codes Found",
                value=codes_resp,
                inline=False,
            )

        if user_data.get("completed", False):
            embed.set_footer(
                text=f"You've found all {len(config.KEYS) - 1} keys, and decoded the final message!",
            )
        elif len(user_data.get("key_completion_timestamps")) == len(config.KEYS) - 1:
            embed.set_footer(
                text=f"You've found all {len(config.KEYS) - 1} keys! Time to decode them!",
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="clue",
        description="Get a hint for your next key.",
    )
    @app_commands.checks.cooldown(1, 6, key=lambda i: (i.user.id))
    @app_commands.dm_only()
    async def _clue(self, interaction: discord.Interaction):
        """Get the clue for your next key."""
        if int(time()) > config.END_TIME_TIMESTAMP:
            raise errors.Error(
                "This year's hunt is over! Check back next year for more clues and keys!"
            )
        user_data = await utils.User.get_user(self.bot, interaction.user.id)
        if not user_data:
            user_data = await utils.User.create_user(self.bot, interaction.user.id)

        if user_data.get("completed", False):
            return await interaction.response.send_message(
                "You've already completed the hunt! Thanks for participating!",
                ephemeral=True,
            )

        embed = discord.Embed(
            title="Clue",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow(),
        )
        if user_data.get("key_to_find") == -1:
            embed.description = (
                "You've found all the keys! Here's your final clue to decode them:"
            )
        else:
            embed.set_footer(
                text="Once you find the key, send it here to unlock the next clue!",
            )
            embed.description = "Here's your clue for the next key:"

        embed.description += (
            f"\n> {await utils.User.get_clue(self.bot, interaction.user.id)}"
        )
        embed.set_author(
            name=f"@{str(interaction.user)}",
            icon_url=interaction.user.avatar,
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="my-stats",
        description="See your stats in the hunt.",
    )
    @app_commands.checks.cooldown(1, 10, key=lambda i: (i.user.id))
    @app_commands.dm_only()
    async def _my_stats(self, interaction: discord.Interaction):
        """Get your stats in the hunt."""
        if int(time()) < config.END_TIME_TIMESTAMP:
            raise errors.Error(
                "The hunt is still ongoing! Check back after it ends to see your stats!"
            )

        user_data = await utils.User.get_user(self.bot, interaction.user.id)
        if not user_data:
            raise errors.Error("You didn't participate in this year's hunt.")

        embed = discord.Embed(
            title="Your Stats",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_author(
            name=f"@{str(interaction.user)}",
            icon_url=interaction.user.avatar,
        )

        # Analyze the user's performance
        total_attempts = user_data.get("total_attempts", 0)
        keys_found = len(user_data.get("key_completion_timestamps", {}))
        if user_data.get("key_to_find") == -1:
            keys_found -= 1
        total_keys = len(config.KEYS) - 1
        completion_rate = (keys_found / total_keys) * 100
        avg_time = self.average_time_between_keys(user_data)

        # Find the key that took longest
        longest_key, longest_time = self.find_longest_key_time(user_data)
        longest_key_msg = ""
        if longest_key and longest_time > 0 and user_data.get("completed"):
            time_str = self.calculate_completion_time(0, longest_time)
            longest_key_msg = f"\nKey {longest_key} was your biggest challenge, taking **{time_str}** to solve!"

        # Generate performance messages
        attempt_msg = (
            "You showed incredible persistence"
            if total_attempts >= 30
            else "You demonstrated great determination"
            if total_attempts >= 20
            else "You put in a solid effort"
            if total_attempts >= 10
            else "You displayed remarkable precision"
            if total_attempts < 10 and keys_found > 0
            else "You began your journey"
        )

        progress_msg = (
            "and successfully conquered the entire hunt! 🏆"
            if completion_rate == 100
            else "and made exceptional progress through the hunt! 🌟"
            if completion_rate >= 75
            else "and made significant headway in the hunt! 💫"
            if completion_rate >= 50
            else "and ventured well into the hunt! ✨"
            if completion_rate >= 25
            else "but only scratched the surface! 🌱"
            if completion_rate > 0
            else "but you couldn't find any keys! 🔑"
        )

        time_msg = ""
        if avg_time != "N/A":
            if "minutes" in avg_time:
                time_msg = "You blazed through these keys at lightning speed! ⚡"
            elif "hours" in avg_time:
                time_msg = "You maintained a steady and consistent pace!"
            else:
                time_msg = "You took a methodical approach to solving each key..."

        embed.description = (
            f"Here's how you did in {strftime('%Y')}'s Dyno Hunt...\n\n"
            f"{attempt_msg} with **{total_attempts}** attempts {progress_msg}\n\n"
            f"You discovered **{keys_found}** out of {total_keys} keys!{longest_key_msg}\n"
            f"\nYour adventure began on <t:{user_data.get('created_at')}:F>"
        )

        if user_data.get("completed"):
            completion_timestamp = user_data.get("key_completion_timestamps").get("-1")
            time_str = self.calculate_completion_time(
                user_data.get("created_at"), completion_timestamp
            )
            embed.description += (
                f" and you triumphantly finished on <t:{completion_timestamp}:F>.\n"
                f"Total time to complete: **{time_str}**!"
            )
            embed.set_footer(
                text=(
                    "Congratulations on completing the hunt! We hope you enjoyed it!"
                ),
            )

        if avg_time != "N/A":
            embed.description += (
                f"\n\nOn average, you spent **{avg_time}** between keys. {time_msg}"
            )

        await interaction.response.send_message(embed=embed)


async def setup(bot: DynoHunt):
    """Add the cog to the bot."""
    await bot.add_cog(UserCommands(bot))
