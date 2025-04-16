from time import strftime
from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands

import config
import utils
from bot import DynoHunt


class UserCommands(commands.Cog):
    """Utility commands for the bot."""

    def __init__(self, bot: DynoHunt):
        self.bot = bot

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
                f"{await self.bot.get_command('clue', 'mention')} command!"
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


async def setup(bot: DynoHunt):
    """Add the cog to the bot."""
    await bot.add_cog(UserCommands(bot))
