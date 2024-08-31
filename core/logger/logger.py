import sys

from loguru import logger


def logging_setup():
    format_info = "<blue>{time:HH:mm:ss.SS}</blue> | <green>{message}</green>"
    format_error = "<blue>{time:HH:mm:ss.SS}</blue> | <red>{message}</red>"

    logger.remove()

    logger.add(
        sys.stdout,
        colorize=True,
        format=format_info,
        level="INFO",
        filter=lambda record: record["level"].name != "ERROR",
    )
    logger.add(sys.stdout, colorize=True, format=format_error, level="ERROR")


logging_setup()
