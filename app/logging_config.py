import logging
import logging.handlers
import os
from app.config import Config

def setup_logging():
    os.makedirs("logs", exist_ok=True)
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, Config.LOG_LEVEL, logging.INFO))

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Rotating file handler
    fh = logging.handlers.RotatingFileHandler("logs/app.log", maxBytes=10485760, backupCount=5)
    fh.setFormatter(formatter)

    # Error file handler
    efh = logging.handlers.RotatingFileHandler("logs/errors.log", maxBytes=10485760, backupCount=5)
    efh.setLevel(logging.ERROR)
    efh.setFormatter(formatter)

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(efh)
    logger.addHandler(ch)

# Import Config here to avoid circular import
