"""Application-wide logging configuration.

Call ``get_logger(__name__)`` from any module to get a logger that writes
to both the console and logs/app.log, per Section 6.2.9 of the assessment
brief ("Logging: Application-wide, using the logging module").
"""

import logging
import os
import sys

# Make src/config importable whether this file is run as part of the
# package or executed directly during quick testing.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402

_configured = False


def _configure_root_logger() -> None:
    global _configured
    if _configured:
        return

    os.makedirs(config.LOGS_DIR, exist_ok=True)

    root = logging.getLogger("ems")
    root.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(config.LOG_FILE_PATH, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # keep the console quiet by default
    console_handler.setFormatter(formatter)

    root.addHandler(file_handler)
    root.addHandler(console_handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a logger under the 'ems' namespace, configured on first use."""
    _configure_root_logger()
    return logging.getLogger(f"ems.{name}")
