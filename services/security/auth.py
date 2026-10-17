"""Demo identity (X-Demo-User header) and backend-enforced role/project permissions."""
import json
import threading
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import Depends, Header, HTTPException

from services.security import audit

ROOT = Path(__file__).resolve().parents[2]
USERS_PATH = ROOT / "data" / "demo" / "users.json"

ROLE_PERMS: Dict[str, set] = {
    "analyst": {"project:view", "req:analyze", "demo:reset", "staff:directory", "onboarding:ask"},
    "pm": {"project:view", "req:analyze", "demo:reset", "proposal:approve", "staff:directory", "onboarding:ask", "audit:view"},
    "employee": {"project:view", "staff:directory", "onboarding:ask"},
    "finance": {"staff:directory", "onboarding:ask", "exec:view", "audit:view"},
    "hr": {"staff:directory", "onboarding:ask", "staff:view"},
    "exec": {"project:view", "exec:view", "staff:directory", "onboarding:ask", "audit:view"},
}

_lock = threading.Lock()
_cache: Dict[str, object] = {"mtime": None, "users": []}


def load_users() -> List[dict]:
    """Lazily load users.json (reloads if the file changes). Missing file -> empty list."""
    with _lock:
        try:
            mtime = USERS_PATH.stat().st_mtime
        except OSError:
            _cache["mtime"], _cache["users"] = None, []
            return []
        if _cache["mtime"] != mtime:
            try:
                data = json.loads(USERS_PATH.read_text(encoding="utf-8"))
                _cache["users"] = data if isinstance(data, list) else []
            except ValueError:
                _cache["users"] = []
            _cache["mtime"] = mtime
        return list(_cache["users"])  # type: ignore


def get_user(username: str) -> Optional[dict]:
    for u in load_users():
        if u.get("username") == username:
            return dict(u)
    return None


def has_perm(user: dict, perm: str) -> bool:
    return perm in ROLE_PERMS.get(user.get("role", ""), set())


def current_user(x_demo_user: Optional[str] = Header(None)) -> dict:
    if not x_demo_user:
        raise HTTPException(status_code=401, detail="missing X-Demo-User header")
    user = get_user(x_demo_user.strip())
    if user is None:
        audit.record(None, "auth", "user:%s" % x_demo_user[:64], "denied", detail={"reason": "unknown user"})
        raise HTTPException(status_code=401, detail="unknown user")
    user["permissions"] = sorted(ROLE_PERMS.get(user.get("role", ""), set()))
    return user


def require(perm: str):
    def _dep(user: dict = Depends(current_user)) -> dict:
        if not has_perm(user, perm):
            audit.record(user, "authorize", "perm:%s" % perm, "denied",
                         detail={"reason": "role %s lacks %s" % (user.get("role"), perm)})
            raise HTTPException(status_code=403, detail="role '%s' lacks permission '%s'" % (user.get("role"), perm))
        return user
    return _dep


def check_project(user: dict, project_id: str) -> None:
    projects = user.get("projects") or []
    if "*" in projects or project_id in projects:
        return
    audit.record(user, "authorize", "project:%s" % project_id, "denied",
                 detail={"reason": "not assigned to project"})
    raise HTTPException(status_code=403, detail="user '%s' has no access to project '%s'" % (user.get("username"), project_id))
