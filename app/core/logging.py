import logging
from pathlib import Path

from app.core.config import get_settings


def configure_logging() -> None:
    settings = get_settings()
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    log_path = Path(settings.app_log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handlers.append(logging.FileHandler(log_path, encoding="utf-8"))
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=handlers,
    )

    access_logger = logging.getLogger("access")
    access_logger.setLevel(logging.INFO)
    access_logger.propagate = False
    access_handler = logging.FileHandler(settings.access_log_path, encoding="utf-8")
    access_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    access_logger.handlers = [access_handler]

    audit_logger = logging.getLogger("audit")
    audit_logger.setLevel(logging.INFO)
    audit_logger.propagate = False
    audit_handler = logging.FileHandler(settings.audit_log_path, encoding="utf-8")
    audit_handler.setFormatter(logging.Formatter("%(message)s"))
    audit_logger.handlers = [audit_handler]
