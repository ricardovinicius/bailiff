import logging
import sys


def setup_logging(level: int = logging.DEBUG, log_file: str | None = None) -> None:
    """
    Configure the root bailiff logger.
    If *log_file* is given, logs go to that file; otherwise to stdout.
    Call once at application startup.
    """
    logger = logging.getLogger("bailiff")

    if logger.handlers:
        return

    logger.setLevel(level)
    logger.propagate = False

    if log_file:
        handler = logging.FileHandler(log_file)

        # Redirect root logger to the file too, so third-party libraries
        # (pyannote, speechbrain, diart, etc.) don't leak to the console.
        root = logging.getLogger()
        root.handlers.clear()
        root.addHandler(handler)
        root.setLevel(logging.WARNING)  # only warnings+ from third-party
    else:
        handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
