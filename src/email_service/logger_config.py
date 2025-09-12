# src/email_service/logger_config.py
import logging
import os
from logging.handlers import TimedRotatingFileHandler
from dotenv import load_dotenv

load_dotenv()

ENV = os.getenv("ENVIRONMENT", "development").lower()
LOG_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

def get_logger(name: str, level=logging.INFO):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # avoid duplicate handlers in re-imports

    logger.setLevel(level)

    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")

    if ENV == "development":
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(fmt)
        logger.addHandler(ch)
    else:
        # production -> file with daily rotation
        fh = TimedRotatingFileHandler(
            filename=os.path.join(LOG_DIR, f"{name}.log"),
            when="midnight",
            backupCount=14,
            encoding="utf-8"
        )
        fh.setLevel(level)
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger
