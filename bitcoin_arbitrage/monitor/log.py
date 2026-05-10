import logging
import os


def _parse_log_level(value: str | None, default: int = logging.INFO) -> int:
    if not value:
        return default
    value = value.strip().upper()
    return getattr(logging, value, default)


def setup_logger(logger_name, log_file='main.log', level: int | None = None) -> logging.Logger:
    logger = logging.getLogger(logger_name)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    effective_level = level if level is not None else logging.INFO
    # Optional override via env var (lets you control logging without importing settings).
    effective_level = _parse_log_level(os.environ.get('LOG_LEVEL'), default=effective_level)

    logger.setLevel(effective_level)
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger
