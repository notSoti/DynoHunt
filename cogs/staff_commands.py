import collections
from io import BytesIO
from typing import Optional

import aiohttp
import discord
from asyncache import cached
from cachetools import TTLCache
from discord import app_commands
from discord.ext import commands

import errors
import utils
from bot import DynoHunt


class StaffCommands(commands.Cog):
    def __init__(self, bot: DynoHunt) -> None:
        self.bot = bot

    async def get_all_users(self) -> list[dict]:
        """Get all users from the database."""
        return await utils.DB.get_many(
            self.bot,
            "users",
        )

    async def get_key_stats(self) -> dict[str, int]:
        """Get stats about how many users are on each key.

        Returns:
            dict: Key numbers mapped to count of users on that key
        """
        users = await utils.DB.get_many(self.bot, "users")
        stats = collections.Counter(str(user.get("key_to_find", 1)) for user in users)
        return dict(stats)

    async def get_key_completion_times(self) -> dict[str, float]:
        """Calculate average time spent on each key in minutes.

        Returns:
            dict: Key numbers mapped to average completion time in minutes
        """
        users = await utils.DB.get_many(self.bot, "users")
        key_times: dict[str, list[float]] = collections.defaultdict(list)

        for user in users:
            timestamps: dict = user.get("key_completion_timestamps", {})
            sorted_keys = sorted(
                timestamps.keys(), key=lambda x: int(x) if x != "-1" else float("inf")
            )

            for i in range(len(sorted_keys) - 1):
                current_key: int = sorted_keys[i]
                next_key: int = sorted_keys[i + 1]
                time_diff: int = (
                    timestamps[next_key] - timestamps[current_key]
                ) / 60  # Convert to minutes
                key_times[current_key].append(time_diff)

        return {
            key: sum(times) / len(times) if times else 0
            for key, times in key_times.items()
        }

    @cached(
        cache=TTLCache(maxsize=10, ttl=1800),
        key=lambda self, stats: str(sorted(stats.items())),
    )
    async def build_graph(self, stats: dict) -> BytesIO:
        """Generate a graph of the stats.

        Args:
            stats (dict): The stats to graph

        Returns:
            BytesIO: Graph image as a byte stream
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://quickchart.io/chart",
                json=stats,
            ) as response:
                if response.status != 200:
                    raise Exception(f"Failed to generate graph: {response.status}")

                data = await response.read()
                return BytesIO(data)

    @app_commands.command(
        name="stats",
        description="Get the global or user stats for the current hunt.",
    )
    @app_commands.checks.cooldown(1, 7, key=lambda i: (i.user.id))
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(
        user="User to get stats for.",
    )
    async def _stats(
        self,
        interaction: discord.Interaction,
        user: Optional[discord.User] = None,
    ) -> None:
        """Get the global or user stats for the hunt."""
        await interaction.response.defer(thinking=True)
        embed = discord.Embed(
            color=discord.Color.blue(),
            url="https://discord.com",  # needed for multi image embed
            timestamp=discord.utils.utcnow(),
        )
        if not user:
            embed.set_author(
                name="Global Hunt Stats",
            )

            all_users = await self.get_all_users()
            if not all_users:
                raise errors.Error("No users found in the database.")
            embed.add_field(
                name="Total Users",
                value=f"{len(all_users)} users",
            )
            users_with_progress = len(
                [user for user in all_users if user.get("key_to_find") != 1]
            )
            embed.add_field(
                name="Users that made progress",
                value=(
                    f"{users_with_progress} users "
                    f"({users_with_progress / len(all_users) * 100:.0f}%)"
                ),
            )
            embed.add_field(
                name="Total Key Guesses",
                value=f"{sum(user.get('total_attempts', 0) for user in all_users)} guesses",
            )
            embed.add_field(
                name="Total Finished Users",
                value=f"{len([user for user in all_users if user.get('completed')])} users",
            )
            embed.add_field(
                name="Potential Cheaters",
                value=f"{len([user for user in all_users if user.get('flagged')])} users",
            )
            stats = await self.get_key_stats()
            sorted_stats = {
                k: stats[k]
                for k in sorted(
                    stats.keys(), key=lambda x: int(x) if x != "-1" else float("inf")
                )
            }
            completed_users = len([user for user in all_users if user.get("completed")])
            if "-1" in sorted_stats:
                sorted_stats["-1"] -= completed_users
            sorted_stats["completed"] = completed_users
            display_stats = {
                ("Decoding" if k == "-1" else "Completed" if k == "completed" else k): v
                for k, v in sorted_stats.items()
            }
            embed.add_field(
                name="Users per Key",
                value="\n".join(
                    f"{k}: {v} users"
                    if k in ["Decoding", "Completed"]
                    else f"Key {k}: {v} users"
                    for k, v in display_stats.items()
                ),
            )

            stats_image_bytes = await self.build_graph(
                stats={
                    "chart": {
                        "type": "bar",
                        "data": {
                            "labels": [
                                (
                                    "Decoding"
                                    if k == "-1"
                                    else "Completed"
                                    if k == "completed"
                                    else f"Key {k}"
                                )
                                for k in sorted_stats.keys()
                            ],
                            "datasets": [
                                {
                                    "label": "Users on each key",
                                    "data": list(sorted_stats.values()),
                                },
                            ],
                        },
                    },
                    "width": 800,
                    "height": 400,
                }
            )
            embed.set_image(url="attachment://stats.png")
            stats_image_bytes.seek(0)

            completion_times = await self.get_key_completion_times()
            sorted_keys = sorted(
                completion_times.keys(),
                key=lambda x: int(x) if x != "-1" else float("inf"),
            )

            # Format labels with arrows and calculate times
            times = []
            formatted_labels = []
            for i in range(len(sorted_keys) - 1):
                times.append(completion_times[sorted_keys[i]])
                current_key = (
                    "Finished" if sorted_keys[i] == "-1" else f"Key {sorted_keys[i]}"
                )
                next_key = (
                    "Finished"
                    if sorted_keys[i + 1] == "-1"
                    else f"Key {sorted_keys[i + 1]}"
                )
                formatted_labels.append(f"{current_key} → {next_key}")

            time_stats_image_bytes = await self.build_graph(
                stats={
                    "chart": {
                        "type": "bar",
                        "data": {
                            "labels": formatted_labels,
                            "datasets": [
                                {
                                    "label": "Average Time Spent (minutes)",
                                    "data": times,
                                    "backgroundColor": "rgba(54, 162, 235, 0.5)",
                                    "borderColor": "rgb(54, 162, 235)",
                                    "borderWidth": 1,
                                },
                            ],
                        },
                        "options": {
                            "scales": {
                                "y": {
                                    "beginAtZero": False,
                                    "title": {"display": True, "text": "Minutes"},
                                }
                            },
                            "plugins": {
                                "title": {
                                    "display": True,
                                    "text": "Global Average Time Spent Per Key",
                                }
                            },
                        },
                    },
                    "width": 1000,
                    "height": 600,
                }
            )
            temp_embed = embed.copy()
            temp_embed.set_image(url="attachment://time_stats.png")
            time_stats_image_bytes.seek(0)

            return await interaction.followup.send(
                embeds=[embed, temp_embed],
                files=[
                    discord.File(stats_image_bytes, filename="stats.png"),
                    discord.File(time_stats_image_bytes, filename="time_stats.png"),
                ],
            )

        user_stats = await utils.User.get_user(self.bot, user.id)
        if not user_stats:
            raise errors.Error("User not found in the database.")

        embed.set_author(
            name=f"@{str(user)}",
            icon_url=user.avatar,
        )
        embed.add_field(
            name="Next Key",
            value=f"{user_stats.get('key_to_find') if user_stats.get('key_to_find') != -1 else 'Finished'}",
            inline=True,
        )
        embed.add_field(
            name="Started At",
            value=f"<t:{user_stats.get('created_at')}:F> (<t:{user_stats.get('created_at')}:R>)",
            inline=True,
        )
        embed.add_field(
            name="Key Completion Times",
            value="\n".join(
                [
                    f"Key {key}: <t:{time}:F> (<t:{time}:R>)"
                    if key != "-1"
                    else f"Finished: <t:{time}:F> (<t:{time}:R>)"
                    for key, time in user_stats.get(
                        "key_completion_timestamps", {}
                    ).items()
                ]
            ),
            inline=False,
        )
        if user_stats.get("flagged"):
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
            text=(
                f"Total attempts: {user_stats.get('total_attempts', 0)} | "
                f"Wrong Order Attempts: {user_stats.get('wrong_order_correct_guesses', 0)}"
            ),
        )

        user_stats = await utils.User.get_user(self.bot, user.id)
        timestamps = user_stats.get("key_completion_timestamps", {})
        sorted_keys = sorted(
            timestamps.keys(), key=lambda x: int(x) if x != "-1" else float("inf")
        )

        # Calculate time differences in minutes and format for display
        times = []
        formatted_labels = []
        for i in range(len(sorted_keys) - 1):
            time_diff = (
                timestamps[sorted_keys[i + 1]] - timestamps[sorted_keys[i]]
            ) / 60
            times.append(time_diff)

            # Format label to show which keys were involved
            current_key = (
                "Finished" if sorted_keys[i] == "-1" else f"Key {sorted_keys[i]}"
            )
            next_key = (
                "Finished"
                if sorted_keys[i + 1] == "-1"
                else f"Key {sorted_keys[i + 1]}"
            )
            formatted_labels.append(f"{current_key} → {next_key}")

        graph_image_bytes = await self.build_graph(
            stats={
                "chart": {
                    "type": "bar",
                    "data": {
                        "labels": formatted_labels,
                        "datasets": [
                            {
                                "label": "Time Spent (minutes)",
                                "data": times,
                                "backgroundColor": "rgba(54, 162, 235, 0.5)",
                                "borderColor": "rgb(54, 162, 235)",
                                "borderWidth": 1,
                            },
                        ],
                    },
                    "options": {
                        "scales": {
                            "y": {
                                "beginAtZero": False,
                                "title": {"display": True, "text": "Minutes"},
                            }
                        },
                        "plugins": {
                            "title": {
                                "display": True,
                                "text": f"{user.name}'s Time Spent Per Key",
                            }
                        },
                    },
                },
                "width": 1000,
                "height": 600,
            }
        )
        embed.set_image(url="attachment://user_time_graph.png")
        graph_image_bytes.seek(0)

        await interaction.followup.send(
            embed=embed,
            file=discord.File(graph_image_bytes, filename="user_time_graph.png"),
        )


async def setup(bot: DynoHunt) -> None:
    await bot.add_cog(StaffCommands(bot))
