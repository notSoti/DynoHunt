import logging
import sys


class ColorFormatter(logging.Formatter):
    RESET_SEQ = "\033[0m"
    COLORS = {
        "DEBUG": "\033[92m",  # Green
        "INFO": "\033[94m",  # Blue
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[91m",  # Red
        "CRITICAL": "\033[91m",  # Red
        "NAME": "\033[95m",  # Purple
    }

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET_SEQ)
        record.name = f"{self.COLORS['NAME']}{record.name}{self.RESET_SEQ}"
        record.levelname = f"{color}{record.levelname}{self.RESET_SEQ}"
        record.msg = f"{color}{record.msg}{self.RESET_SEQ}"
        return super().format(record)


def get_logger():
    """Get the logger for the bot."""
    logger = logging.getLogger("discord")
    logger.setLevel(logging.INFO)

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    stream = sys.stdout if sys.stdout.isatty() else sys.stderr
    stream_logger = logging.StreamHandler(stream)

    stream_logger.setLevel(logging.INFO)

    stream_logger.setFormatter(
        ColorFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
        )
    )
    logger.addHandler(stream_logger)
    return logger


logger = get_logger()
