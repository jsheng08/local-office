"""Append-only, hash-chained audit log (JSONL). Stores ids/hashes, never document text."""
import hashlib
import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
AUDIT_PATH = ROOT / "data" / "runtime" / "audit.jsonl"
GENESIS = "0" * 64

_lock = threading.Lock()
_last_hash: Optional[str] = None


def _canonical(entry: dict) -> bytes:
    body = {k: v for k, v in entry.items() if k != "hash"}
    return json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _load_last_hash() -> str:
    if not AUDIT_PATH.exists():
        return GENESIS
    last = GENESIS
    with AUDIT_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    last = json.loads(line).get("hash", last)
                except ValueError:
                    pass
    return last


def _user_ref(user: Optional[dict]) -> Optional[dict]:
    if not user:
        return None
    return {"username": user.get("username"), "role": user.get("role"), "staff_id": user.get("staff_id")}


def record(user: Optional[dict], action: str, resource: str, outcome: str,
           meta: Optional[dict] = None, detail: Optional[dict] = None) -> dict:
    global _last_hash
    with _lock:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        if _last_hash is None:
            _last_hash = _load_last_hash()
        entry = {
            "id": uuid.uuid4().hex[:12],
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "user": _user_ref(user),
            "action": action,
            "resource": resource,
            "outcome": outcome,
            "meta": meta,
            "detail": detail,
            "prev_hash": _last_hash,
        }
        entry["hash"] = hashlib.sha256(_canonical(entry)).hexdigest()
        with AUDIT_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")
        _last_hash = entry["hash"]
        return entry


def read(limit: int = 200) -> Tuple[List[dict], bool]:
    """Return (newest-first entries, chain_valid). Verifies the full chain."""
    with _lock:
        if not AUDIT_PATH.exists():
            return [], True
        entries: List[dict] = []
        valid = True
        prev = GENESIS
        with AUDIT_PATH.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                except ValueError:
                    valid = False
                    continue
                if e.get("prev_hash") != prev or hashlib.sha256(_canonical(e)).hexdigest() != e.get("hash"):
                    valid = False
                prev = e.get("hash", "")
                entries.append(e)
    entries.reverse()
    return entries[:limit], valid
