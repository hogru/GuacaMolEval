# coding=utf-8
import contextlib
import inspect
import logging
import sys
import warnings
from functools import partialmethod
from os import PathLike
from pathlib import Path
from types import FrameType
from typing import Any, Optional, Union, Final, Iterable

from loguru import logger


DEFAULT_CONSOLE_FORMAT: Final[
    str
] = "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
DEFAULT_FILE_FORMAT: Final[str] = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | <level>{level: <8}</level> | "
    "{name}:{function}:{line} - <level>{message}</level>"
)

DEFAULT_LOG_LEVEL: Final[int] = logging.INFO
SIGNS_FOR_ROOT_DIR: Final[tuple[str, ...]] = (
    ".git",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
)


def guess_project_root_dir(
        caller_file_path: Optional[Union[PathLike, str]] = None,
        signs_for_root_dir: Iterable[str] = SIGNS_FOR_ROOT_DIR,
) -> Path:
    """Guess the project´s root directory.

    Traverses the directory from the caller´s directory toward the root directory.
    The first directory that contains one of the signs for the root directory becomes the root directory.
    If no such directory is found, the caller´s directory is returned.

    Args:
        caller_file_path: the path to the caller´s file, defaults to None, i.e. use the caller´s file.
        signs_for_root_dir: the signs for the root directory, defaults to SIGNS_FOR_ROOT_DIR.

    Returns:
        The project´s root directory.
    """

    caller_file_path = (
        Path(inspect.stack()[1].filename).resolve()
        if caller_file_path is None
        else Path(caller_file_path).resolve()
    )
    directory = caller_file_path
    while (directory != directory.parent) and (directory := directory.parent):
        if any(directory.joinpath(sign).exists() for sign in signs_for_root_dir):
            return directory

    return caller_file_path.parent


# Code taken from https://github.com/Delgan/loguru#entirely-compatible-with-standard-logging
# Type annotations are my own
class _InterceptHandler(logging.Handler):
    """Intercept standard logging messages and forward them to loguru."""

    # noinspection PyMissingOrEmptyDocstring
    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists.
        level: Union[int, str]
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame: Optional[FrameType]
        depth: int
        # noinspection PyProtectedMember
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
        )


def _show_warning(message: str, *_: Any, **__: Any) -> None:
    """Redirect warnings to loguru."""
    logger.warning(message)


def configure_logging(
        log_level: int = logging.INFO,
        *,
        console_format: Optional[str] = None,
        file_format: Optional[str] = None,
        file_log_level: Optional[int] = None,
        log_dir: Optional[Union[PathLike, str]] = None,
        log_file: Optional[Union[PathLike, str]] = None,
        rotation: str = "1 day",
        retention: str = "7 days",
) -> None:
    """Configure logging.

    Args:
        log_level: the log level to use, defaults to logging.INFO.
        console_format: the format to use for the console, defaults to None, i.e. use the default format.
        file_format: the format to use for the file, defaults to None, i.e. use the default format.
        file_log_level: the log level to use for the file, defaults to None, i.e. use the console log level.
        log_dir: the directory to use for the log file, defaults to None, i.e. use <project root>/logs.
        log_file: the name of the log file, defaults to None, i.e. use <caller name>.log.
        rotation: the rotation to use for the log file, defaults to "1 day".
        retention: the retention to use for the log file, defaults to "7 days".
    """

    # Allow for separate log levels for console and file logging
    console_log_level = log_level
    file_log_level = console_log_level if file_log_level is None else file_log_level

    console_format = (
        DEFAULT_CONSOLE_FORMAT if console_format is None else str(console_format)
    )
    file_format = DEFAULT_FILE_FORMAT if file_format is None else str(file_format)

    # Determine log file path
    # To be changed with python version ≥ 3.11: A list of FrameInfo objects is returned.
    caller_file_path = Path(inspect.stack()[1].filename).resolve()
    if log_dir is None:
        log_dir = guess_project_root_dir(caller_file_path=caller_file_path) / "logs"
    else:
        log_dir = Path(log_dir).resolve()
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    if log_file is None:
        log_file = Path(f"{str(caller_file_path.stem)}.log")

    log_file = log_dir / log_file

    # Remove all previously added handlers
    logger.remove()

    # Allow for logging of headers, add log level
    with contextlib.suppress(TypeError):
        logger.level("HEADING", no=21, color="<red><BLACK><bold>")
        logger.__class__.heading = partialmethod(logger.__class__.log, "HEADING")  # type: ignore

    # Add console handler
    logger.add(sys.stderr, level=console_log_level, format=console_format)

    # Add file handler
    logger.add(
            sink=log_file,
            rotation=rotation,
            retention=retention,
            level=file_log_level,
            format=file_format,
            enqueue=True,
            backtrace=True,
            diagnose=True,
            colorize=False,
    )

    # Redirect warnings to logger
    warnings.showwarning = _show_warning  # type: ignore

    # Intercept logging messages from other libraries
    logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)

    logger.debug(
            f"Logging with log level {file_log_level} to {log_file} with rotation {rotation} and retention {retention}"
    )
