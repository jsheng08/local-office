"""Local JSON state for runs, change sets and approved Kanban boards."""
import copy
import json
import threading
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / "data" / "runtime" / "state.json"
PROJECTS_PATH = ROOT / "data" / "demo" / "projects.json"
_LOCK = threading.RLock()


def _empty() -> Dict:
    return {"runs": {}, "change_sets": {}, "boards": {}, "last_run": {}}


def _load() -> Dict:
    if not STATE_PATH.exists():
        return _empty()
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (ValueError, OSError):
        return _empty()
    base = _empty()
    base.update(data)
    return base


def _save(state: Dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_PATH.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)
    tmp.replace(STATE_PATH)


def new_id(prefix: str) -> str:
    return "%s-%s" % (prefix, uuid.uuid4().hex[:8])


def save_run(run: Dict) -> None:
    with _LOCK:
        st = _load()
        st["runs"][run["id"]] = run
        st["last_run"][run["project_id"]] = run["id"]
        _save(st)


def get_last_run(project_id: str) -> Optional[Dict]:
    with _LOCK:
        st = _load()
        rid = st["last_run"].get(project_id)
        return copy.deepcopy(st["runs"].get(rid)) if rid else None


def save_change_set(cs: Dict) -> None:
    with _LOCK:
        st = _load()
        st["change_sets"][cs["id"]] = cs
        _save(st)


def get_change_set(cs_id: str) -> Optional[Dict]:
    with _LOCK:
        return copy.deepcopy(_load()["change_sets"].get(cs_id))


def decide_change_set(cs_id: str, decision: str, user: Dict, note: Optional[str]) -> Dict:
    """Apply/reject a pending change set atomically. Board only changes on approve."""
    with _LOCK:
        st = _load()
        cs = st["change_sets"].get(cs_id)
        if cs is None:
            raise KeyError(cs_id)
        if cs["status"] != "pending":
            raise ValueError("change set is already %s" % cs["status"])
        cs["status"] = "applied" if decision == "approve" else "rejected"
        cs["decided_by"] = user.get("username")
        cs["decided_at"] = time.time()
        cs["note"] = note
        if decision == "approve":
            st["boards"][cs["project_id"]] = [r for r in cs["requirements"] if r.get("approvable", True)]
        board = st["boards"].get(cs["project_id"], [])
        _save(st)
        return {"change_set": copy.deepcopy(cs), "board": copy.deepcopy(board)}


def get_board(project_id: str) -> List[Dict]:
    with _LOCK:
        return copy.deepcopy(_load()["boards"].get(project_id, []))


def load_projects() -> List[Dict]:
    with open(PROJECTS_PATH, encoding="utf-8") as f:
        projects = json.load(f)
    with _LOCK:
        boards = _load()["boards"]
    for p in projects:
        board = boards.get(p["id"], [])
        p["approved_requirements"] = board
        if board:
            base = [k for k in p.get("kanban", []) if not k.get("from_analysis")]
            p["kanban"] = base + [kanban_item(r) for r in board]
    return projects


def kanban_item(r: Dict) -> Dict:
    t = r.get("triage") or {}
    cites = ", ".join(c["paragraph_id"] for c in r.get("citations", []))
    return {"id": r["id"], "title": r["title"], "priority": r.get("priority"), "status": "todo",
            "estimate_h": t.get("pert"), "assignee": None,  # staff assignment is a separate human decision
            "suggested_staff": [s.get("staff_id") for s in r.get("recommended_staff", [])],
            "source_ref": "brief " + cites if cites else None, "approved": True, "from_analysis": True}
