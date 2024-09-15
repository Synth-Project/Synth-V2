import io
import sys
from loguru import logger

info_logger = io.StringIO()
debug_logger = io.StringIO()
error_logger = io.StringIO()


def console_logging_setup():
    format_info = "<blue>{time:HH:mm:ss.SS}</blue> | [<bold><u><yellow>{extra[source]}</yellow></u></bold>]: <green>{message}</green>"
    format_debug = "<blue>{time:HH:mm:ss.SS}</blue> | [<bold><u><yellow>{extra[source]}</yellow></u></bold>]: <blue>{message}</blue>"
    format_error = "<blue>{time:HH:mm:ss.SS}</blue> | <red>{message}</red>"

    logger.remove()

    logger.add(
        sink=sys.stdout,
        colorize=True,
        format=format_debug,
        level="DEBUG",
        filter=lambda record: record["level"].name == "DEBUG"
        and record["extra"].get("source") is not None,
    )

    logger.add(
        sink=sys.stdout,
        colorize=True,
        format=format_info,
        level="INFO",
        filter=lambda record: record["level"].name == "INFO"
        and record["extra"].get("source") is not None,
    )
    logger.add(sink=sys.stdout, colorize=True, format=format_error, level="ERROR")


def string_logging_setup():
    format_info = "{time:HH:mm:ss.SS} | {extra[source]}: {message}"
    format_debug = "{time:HH:mm:ss.SS} | [{extra[source]}]: {message}"
    format_error = "{time:HH:mm:ss.SS} | {message}"

    logger.add(
        sink=debug_logger,
        colorize=True,
        format=format_debug,
        level="DEBUG",
        filter=lambda record: record["level"].name == "DEBUG"
        and record["extra"].get("source") is not None,
    )

    logger.add(
        sink=info_logger,
        colorize=True,
        format=format_info,
        level="INFO",
        filter=lambda record: record["level"].name == "INFO"
        and record["extra"].get("source") is not None,
    )
    logger.add(sink=error_logger, colorize=True, format=format_error, level="ERROR")


console_logging_setup()
string_logging_setup()
