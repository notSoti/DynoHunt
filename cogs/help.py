import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType

import errors
from bot import DynoHunt
from cogs import EXTENSIONS


class Help(commands.Cog):
    def __init__(self, bot: DynoHunt):
        self.bot = bot

    @commands.command(
        name="help",
        description="Get help on a specific command or list all commands.",
        enabled=False,
    )
    @commands.cooldown(1, 5, BucketType.user)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @commands.guild_only()
    async def _help(
        self,
        ctx: commands.Context,
        *,
        command: str = commands.param(
            description="The command to get help on.", default=None
        ),
    ):
        embed = discord.Embed(
            color=discord.Color.random(),
            timestamp=discord.utils.utcnow(),
            title="Help Command",
        )
        embed.set_author(
            name=ctx.author.display_name,
            icon_url=ctx.author.guild_avatar or ctx.author.avatar,
        )
        embed.set_footer(
            text="Arguments in () are optional, while arguments in [] are required."
        )

        all_commands: dict[str, commands.Command] = self.bot.all_commands
        if command:
            command, subcommand = (
                command.lower().split(" ", 1) if " " in command else (command, None)
            )

            if command not in all_commands:
                raise errors.Error("Command not found!")

            command: commands.Command = all_commands[command]

            try:
                if not await command.can_run(ctx):
                    raise errors.Error("Command not found!")
            except commands.CommandError as e:
                raise errors.Error("Command not found!") from e
            if subcommand:
                if command.__class__.__name__ != "Group":
                    raise errors.Error("This command doesn't have any subcommands!")
                subcommand = subcommand.lower()
                for sub in command.commands:
                    if sub.name == subcommand or subcommand in sub.aliases:
                        command: commands.Command = sub
                        break
                else:
                    raise errors.Error("Subcommand not found!")

            embed.title = f"{command.parent.name.capitalize() if subcommand else ''} {command.name.capitalize()} Command"
            embed.description = command.description

            args: dict[str, commands.Parameter] = command.params
            formatted_args = []
            if args:
                value = ""
                for arg in args:
                    value += f"`{arg}` - {args[arg].description}\n"
                    if args[arg].default == args[arg].empty:
                        formatted_args.append(f"[{arg}]")
                    else:
                        formatted_args.append(f"({arg})")
                embed.add_field(
                    name="Arguments",
                    value=value,
                    inline=False,
                )
            embed.add_field(
                name="Usage",
                value=f"{self.bot.prefix}{command.qualified_name} {' '.join(formatted_args)}",
                inline=False,
            )
            if command.__class__.__name__ == "Group":
                value = ""
                for subcommand in command.commands:
                    value += f"`{subcommand.name}` - {subcommand.description}\n"
                embed.add_field(
                    name="Subcommands",
                    value=value,
                    inline=False,
                )
            if command.aliases:
                embed.add_field(
                    name="Aliases",
                    value=", ".join(command.aliases),
                    inline=False,
                )
            if command.cooldown:
                if command.cooldown.rate > 1:
                    cooldown = f"{int(command.cooldown.rate)} times per {int(command.cooldown.per)} seconds"
                else:
                    cooldown = f"{int(command.cooldown.per)} seconds"
                embed.add_field(
                    name="Cooldown",
                    value=cooldown,
                    inline=False,
                )
        else:
            value = ""
            valid_extensions = EXTENSIONS
            for cmd in self.bot.walk_commands():
                if cmd.parent and (
                    cmd.parent.name not in valid_extensions
                    or cmd.parent.name == "jishaku"
                ):
                    continue
                if cmd.hidden:
                    continue
                try:
                    if not await cmd.can_run(ctx):
                        continue
                except commands.CommandError:
                    continue
                value += f"`{self.bot.prefix}{cmd.name}` - {cmd.description}\n"
            embed.description = value
            embed.set_footer(
                text=f"Use {self.bot.prefix}help [command] to learn more about a specific command"
            )

        await ctx.reply(embed=embed, allowed_mentions=discord.AllowedMentions.none())


async def setup(bot: DynoHunt):
    """Setup the cog"""
    await bot.add_cog(Help(bot))
