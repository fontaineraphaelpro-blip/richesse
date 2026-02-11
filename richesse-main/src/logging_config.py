"""
Central logging configuration used by the app.
"""
import logging
import logging.handlers
from pathlib import Path
from .config import cfg


def setup_logging():
    log_level = getattr(logging, cfg.LOG_LEVEL.upper(), logging.INFO)

    # Ensure log directory exists
    log_path = Path(cfg.LOG_FILE)
    if not log_path.parent.exists():
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    handlers = [
        logging.StreamHandler(),
        logging.handlers.RotatingFileHandler(str(cfg.LOG_FILE), maxBytes=5_000_000, backupCount=3)
    ]

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=handlers,
    )


def get_logger(name: str):
    setup_logging()
    return logging.getLogger(name)
