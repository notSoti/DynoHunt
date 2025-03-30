from discord import app_commands


class NotTheAuthor(Exception):
    """Raised when a user is interacting with an interaction that is not theirs."""


class Error(app_commands.AppCommandError):
    """Base class for exceptions in this module."""
