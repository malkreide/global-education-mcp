"""
Tool-Signatur-Snapshot + Description-Lint.

Behebt zwei Audit-Findings (mcp-audit-skill v1.0.0):

  SEC-022 — Tool-Hash-Pinning gegen Rug-Pull-Angriffe.
            Pro registriertem MCP-Tool wird ein SHA-256 ueber
            (name, description, inputSchema, annotations) gebildet.
            Bei jedem CI-Lauf wird gegen den committeten tools.lock.json
            gediffed; jede Aenderung erfordert einen bewussten Lockfile-
            Update-Commit.

  SEC-015 — Pre-Flight Tool-Poisoning Detection. Heuristische Suche nach
            Prompt-Injection-Markern in den Tool-Descriptions (z.B.
            "ignore previous instructions", "act as system").

Subcommands:
  dump    Snapshot aktueller Signaturen als JSON nach stdout.
  update  Snapshot in tools.lock.json schreiben (bewusst!).
  verify  Snapshot gegen tools.lock.json diffen, exit 1 bei Drift.
  lint    Descriptions auf verdaechtige Token pruefen, exit 1 bei Hit.
  ci      verify + lint (fuer CI-Pipelines).
"""

from __future__ import annotations

import argparse
import asyncio
import difflib
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
LOCKFILE = REPO_ROOT / "tools.lock.json"

# Heuristische Marker fuer Prompt-Injection in Tool-Descriptions.
# Quelle: Anthropic / Simon Willison Tool-Poisoning-Notes 2024-2025.
SUSPICIOUS_PATTERNS: list[tuple[str, str]] = [
    (r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)",
     "Instruction-override-Pattern"),
    (r"\bsystem\s+prompt\b",
     "Direkte Referenz auf System-Prompt"),
    (r"\bact\s+as\s+(?:a\s+|an\s+)?(?:system|admin|root)",
     "Role-elevation-Pattern"),
    (r"\bjail\s*break\b|\bDAN\b\s+mode",
     "Jailbreak-Marker"),
    (r"\b(?:execute|run|eval)\s+(?:the\s+)?(?:following|this)\s+(?:command|code|shell)",
     "Code-Execution-Aufforderung"),
    (r"\bos\.system\b|\bsubprocess\b\s*[.(]|\bshell\s*=\s*True",
     "Shell-Execution-Referenz"),
    (r"cat\s+/etc/(?:passwd|shadow|hosts)|/\.ssh/id_rsa",
     "Sensible Filesystem-Pfade"),
    (r"<\s*assistant\s*>|<\s*system\s*>|<\|im_start\|>",
     "Falsche Rollen-Token"),
]


async def collect_signatures() -> dict[str, Any]:
    """Liest alle registrierten MCP-Tools via FastMCP.list_tools() und
    serialisiert sie deterministisch (sorted keys) plus SHA-256.
    """
    from global_education_mcp.server import mcp

    tools = await mcp.list_tools()
    snapshot: dict[str, Any] = {}
    for tool in tools:
        annotations_dict: Any = None
        if tool.annotations is not None:
            annotations_dict = tool.annotations.model_dump(mode="json", exclude_none=True)
        signature = {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.inputSchema,
            "annotations": annotations_dict,
        }
        canonical = json.dumps(signature, sort_keys=True, ensure_ascii=False)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        snapshot[tool.name] = {"hash": digest, "signature": signature}
    return dict(sorted(snapshot.items()))


def render(snapshot: dict[str, Any]) -> str:
    return json.dumps(snapshot, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def cmd_dump() -> int:
    snapshot = asyncio.run(collect_signatures())
    sys.stdout.write(render(snapshot))
    return 0


def cmd_update() -> int:
    snapshot = asyncio.run(collect_signatures())
    LOCKFILE.write_text(render(snapshot), encoding="utf-8")
    print(f"Wrote {LOCKFILE.relative_to(REPO_ROOT)} ({len(snapshot)} tools).")
    return 0


def cmd_verify() -> int:
    if not LOCKFILE.exists():
        print(
            f"ERROR: {LOCKFILE.relative_to(REPO_ROOT)} fehlt. "
            "Erst-Snapshot via `python scripts/tool_signatures.py update` erzeugen.",
            file=sys.stderr,
        )
        return 1
    current = render(asyncio.run(collect_signatures()))
    expected = LOCKFILE.read_text(encoding="utf-8")
    if current == expected:
        print(f"OK: {LOCKFILE.relative_to(REPO_ROOT)} stimmt mit dem Code ueberein.")
        return 0
    diff = "".join(
        difflib.unified_diff(
            expected.splitlines(keepends=True),
            current.splitlines(keepends=True),
            fromfile=str(LOCKFILE.relative_to(REPO_ROOT)),
            tofile="<live tools>",
        )
    )
    sys.stderr.write(diff)
    sys.stderr.write(
        "\nERROR: Tool-Signaturen haben sich geaendert. "
        "Wenn die Aenderung beabsichtigt ist, fuehre "
        "`python scripts/tool_signatures.py update` aus und committe "
        "den neuen tools.lock.json zusammen mit dem Code-Diff.\n"
    )
    return 1


def cmd_lint() -> int:
    snapshot = asyncio.run(collect_signatures())
    hits: list[tuple[str, str, str]] = []
    for name, entry in snapshot.items():
        description = entry["signature"]["description"] or ""
        for pattern, label in SUSPICIOUS_PATTERNS:
            if re.search(pattern, description, re.IGNORECASE):
                hits.append((name, label, pattern))
    if not hits:
        print(f"OK: keine verdaechtigen Marker in {len(snapshot)} Tool-Descriptions.")
        return 0
    for tool, label, pattern in hits:
        sys.stderr.write(
            f"ERROR: Tool '{tool}' enthaelt verdaechtiges Pattern "
            f"({label}, regex: {pattern!r})\n"
        )
    sys.stderr.write(
        "\nWenn der Treffer ein false positive ist, "
        "passe SUSPICIOUS_PATTERNS in scripts/tool_signatures.py an "
        "und dokumentiere die Ausnahme im Commit-Body.\n"
    )
    return 1


def cmd_ci() -> int:
    rc_verify = cmd_verify()
    rc_lint = cmd_lint()
    return rc_verify or rc_lint


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Tool-Signatur-Snapshot + Description-Lint (SEC-022, SEC-015).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("dump", help="Snapshot als JSON nach stdout.")
    sub.add_parser("update", help="Snapshot in tools.lock.json schreiben.")
    sub.add_parser("verify", help="Snapshot gegen tools.lock.json diffen.")
    sub.add_parser("lint", help="Descriptions auf Prompt-Injection-Marker pruefen.")
    sub.add_parser("ci", help="verify + lint, fuer CI.")
    args = parser.parse_args()
    return {
        "dump": cmd_dump,
        "update": cmd_update,
        "verify": cmd_verify,
        "lint": cmd_lint,
        "ci": cmd_ci,
    }[args.cmd]()


if __name__ == "__main__":
    sys.exit(main())
