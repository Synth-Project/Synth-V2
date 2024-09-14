import sys
from loguru import logger


def logging_setup():
    format_info = "<blue>{time:HH:mm:ss.SS}</blue> | [<bold><u><yellow>{extra[source]}</yellow></u></bold>]: <green>{message}</green>"
    format_debug = "<blue>{time:HH:mm:ss.SS}</blue> | [<bold><u><yellow>{extra[source]}</yellow></u></bold>]: <blue>{message}</blue>"
    format_error = "<blue>{time:HH:mm:ss.SS}</blue> | <red>{message}</red>"

    logger.remove()

    logger.add(
        sys.stdout,
        colorize=True,
        format=format_debug,
        level="DEBUG",
        filter=lambda record: record["level"].name == "DEBUG"
        and record["extra"].get("source") is not None,
    )

    logger.add(
        sys.stdout,
        colorize=True,
        format=format_info,
        level="INFO",
        filter=lambda record: record["level"].name == "INFO"
        and record["extra"].get("source") is not None,
    )
    logger.add(sys.stdout, colorize=True, format=format_error, level="ERROR")


logging_setup()
