import json
import logging
from datetime import datetime, timezone
from typing import Any


audit_logger = logging.getLogger("audit")


def write_audit_event(event_type: str, payload: dict[str, Any]) -> None:
    record = {
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "payload": payload,
    }
    audit_logger.info(json.dumps(record, ensure_ascii=False, sort_keys=True, default=str))
