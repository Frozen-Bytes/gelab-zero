"""
UTILS/LOGGER.PY
This is the central logging utility for the entire project.
It ensures that every component speaks to the same output streams
in a consistent format.
"""

import logging
import os
import time
from datetime import datetime


def setup_logger(name: str):
    """
    Creates and configures a logger instance with console and file handlers.

    Args:
        name (str): The module name for the logger.

    Returns:
        logging.Logger: A configured logger object.
    """

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    date_folder = datetime.now().strftime("%Y-%m-%d")
    log_dir = os.path.join("data", "outputs", "logs", date_folder)
    os.makedirs(log_dir, exist_ok=True)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    timestamp = int(time.time() * 1000)
    file_name = os.path.join(log_dir, f"sim_{timestamp}.log")
    file_handler = logging.FileHandler(file_name, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger
