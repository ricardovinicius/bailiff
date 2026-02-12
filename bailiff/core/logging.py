import logging
import sys
from textual.logging import TextualHandler

def setup_logging(level: int = logging.DEBUG, log_file: str | None = None) -> None:
    """
    Configure the logging system.
    Silences third-party libraries and redirects logs safely to avoid TUI corruption.
    """
    if log_file:
        handler = logging.FileHandler(log_file)
    else:
        handler = TextualHandler()

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    handler.setFormatter(formatter)
    handler.setLevel(level)

    bailiff_logger = logging.getLogger("bailiff")
    bailiff_logger.setLevel(level)
    bailiff_logger.propagate = False  
    
    if not bailiff_logger.handlers:
        bailiff_logger.addHandler(handler)

    root = logging.getLogger()
    root.handlers.clear()       
    root.addHandler(handler)    
    root.setLevel(logging.WARNING) 