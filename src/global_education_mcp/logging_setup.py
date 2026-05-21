"""
Strukturiertes JSON-Logging fuer global-education-mcp.

Behebt Audit-Finding OBS-003 (Structured Logging mit RFC 5424
Severity-Stufen). Schreibt JSON-Objekte auf STDERR — stdout bleibt
reserviert fuer das MCP-stdio-Protokoll (siehe OBS-004).

Format pro Log-Zeile (eine JSON-Zeile, kein Pretty-Print):

    {"ts":"2026-05-21T10:00:00Z","level":"info","logger":"global_education_mcp.server",
     "msg":"tool_call","tool":"uis_get_education_data","duration_ms":482,"status":"ok",
     "indicator":"LR.AG15T99","country":"CHE"}

`level` ist RFC-5424-konform (debug/info/notice/warning/error/critical).
Aktivierung via `configure_logging()` in main() oder LOG_LEVEL env var.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from typing import Any

# RFC 5424 Severities, gemappt auf Python-Logging-Levels.
# Python-Logging kennt kein 'notice' nativ — wir bilden es auf 25 ab.
NOTICE = 25
logging.addLevelName(NOTICE, "NOTICE")

_RFC5424_NAMES = {
    logging.DEBUG: "debug",
    logging.INFO: "info",
    NOTICE: "notice",
    logging.WARNING: "warning",
    logging.ERROR: "error",
    logging.CRITICAL: "critical",
}


class JSONFormatter(logging.Formatter):
    """Eine Zeile JSON pro Log-Record. Extra-Felder via
    `logger.info("msg", extra={"extra_fields": {...}})`."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": _RFC5424_NAMES.get(record.levelno, record.levelname.lower()),
            "logger": record.name,
            "msg": record.getMessage(),
        }
        extra_fields = getattr(record, "extra_fields", None)
        if isinstance(extra_fields, dict):
            for k, v in extra_fields.items():
                if k not in payload:  # nicht ueberschreiben
                    payload[k] = v
        if record.exc_info:
            payload["exc_type"] = record.exc_info[0].__name__ if record.exc_info[0] else None
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(level: str | int | None = None) -> None:
    """Setzt einen JSON-Handler auf STDERR auf dem Root-Logger.

    `level` akzeptiert Strings wie "INFO" oder Python-Level-Konstanten.
    Wenn None: LOG_LEVEL env var (Default INFO).

    Idempotent — wiederholte Aufrufe ersetzen den Handler.
    """
    if level is None:
        level = os.environ.get("LOG_LEVEL", "INFO")
    if isinstance(level, str):
        level = logging.getLevelName(level.upper())
        if not isinstance(level, int):
            level = logging.INFO

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JSONFormatter())

    root = logging.getLogger()
    # Vorhandene Handler entfernen, damit kein Doppel-Output entsteht.
    for h in list(root.handlers):
        root.removeHandler(h)
    root.addHandler(handler)
    root.setLevel(level)
