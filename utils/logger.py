# logger.py
import logging
from logging import Logger
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

def get_logger(name: str, 
               level: int = logging.DEBUG,
               fmt: str = "%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
               datefmt: str = "%Y-%m-%d %H:%M:%S") -> Logger:
    """
    Returns a logger that writes to logs/<name>.log.

    - name:      logger name (and the log filename).
    - level:     minimum level to capture (default DEBUG).
    - fmt:       log line format.
    - datefmt:   timestamp format in log lines.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # If we've already set up this logger, don’t add another handler
    if any(isinstance(h, logging.FileHandler) and h.baseFilename.endswith(f"{name}.log")
           for h in logger.handlers):
        return logger

    log_path = LOG_DIR / f"{name}.log"
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(level)

    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
    fh.setFormatter(formatter)

    logger.addHandler(fh)
    # Optional: also log to console
    # ch = logging.StreamHandler()
    # ch.setLevel(level)
    # ch.setFormatter(formatter)
    # logger.addHandler(ch)

    return logger
