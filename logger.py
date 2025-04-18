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

    # INFO and DEBUG
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.addFilter(lambda record: record.levelno <= logging.INFO)

    # WARNING, ERROR, and CRITICAL
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)

    formatter = ColorFormatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
    )
    stdout_handler.setFormatter(formatter)
    stderr_handler.setFormatter(formatter)

    logger.addHandler(stdout_handler)
    logger.addHandler(stderr_handler)
    return logger


logger = get_logger()
