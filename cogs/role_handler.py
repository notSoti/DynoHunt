import discord
from discord.ext import commands

import config
import utils
from bot import DynoHunt


class RoleHandler(commands.Cog):
    """Cog for handling user activity in a guild."""

    def __init__(self, bot: DynoHunt):
        self.bot = bot
        self.cd_mapping = commands.CooldownMapping.from_cooldown(
            2, 5, commands.BucketType.user
        )

    @commands.Cog.listener()
    async def on_member_update(
        self, before: discord.Member, after: discord.Member
    ) -> None:
        """Listens for hunt champion role updates and finishes the user.

        Args:
            before (discord.Member): The member object before the update.
            after (discord.Member): The member object after the update.
        """

        if before.roles == after.roles:
            return

        if config.HUNT_CHAMPION_ROLE in [role.id for role in after.roles]:
            await utils.User.advance_user(self.bot, after.id)
            self.bot.dispatch("user_finish", after)


async def setup(bot: DynoHunt):
    """Adds the cog to the bot."""
    await bot.add_cog(RoleHandler(bot))
