"""System endpoints: model health, demo users, current user, audit log."""
import time
from typing import List

import httpx
from fastapi import APIRouter, Depends

from services.inference.routing import MODELS
from services.security import audit
from services.security.auth import current_user, load_users, require

router = APIRouter(prefix="/api")

HOST = "EMARQUE-DGX-J (DGX Spark) via SSH tunnel"


def _probe(cfg: dict) -> dict:
    out = {"name": cfg["name"], "model_id": None, "base_url": cfg["base_url"], "ok": False,
           "latency_ms": None, "max_model_len": None, "root": None, "error": None}
    t0 = time.monotonic()
    try:
        with httpx.Client(timeout=5.0) as c:
            r = c.get(cfg["base_url"].rstrip("/") + "/models")
        out["latency_ms"] = int(round((time.monotonic() - t0) * 1000))
        if r.status_code != 200:
            out["error"] = "HTTP %d" % r.status_code
            return out
        data = (r.json() or {}).get("data") or []
        if not data:
            out["error"] = "no models listed"
            return out
        m = data[0]
        out.update(model_id=m.get("id"), root=m.get("root"), max_model_len=m.get("max_model_len"), ok=True)
    except httpx.TimeoutException:
        out["error"] = "timeout (5s)"
    except httpx.HTTPError as e:
        out["error"] = "unreachable: %s" % e.__class__.__name__
    except ValueError:
        out["error"] = "invalid JSON"
    return out


@router.get("/health")
def health() -> dict:
    models: List[dict] = [_probe(cfg) for cfg in MODELS.values()]
    return {"models": models, "host": HOST, "hosted_fallback": False}


@router.get("/users")
def users() -> List[dict]:
    return [{k: u.get(k) for k in ("username", "display_name", "staff_id", "role", "projects")}
            for u in load_users()]


@router.get("/me")
def me(user: dict = Depends(current_user)) -> dict:
    return user


@router.get("/audit")
def audit_log(limit: int = 200, user: dict = Depends(require("audit:view"))) -> dict:
    entries, valid = audit.read(limit=max(1, min(limit, 1000)))
    return {"entries": entries, "chain_valid": valid}
