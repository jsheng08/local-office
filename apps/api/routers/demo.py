"""Demo reset: restore the approved v1 baseline recorded from a real local Nemotron run."""
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from services.projects import store
from services.security.audit import record
from services.security.auth import require

router = APIRouter(prefix="/api")
BASELINE = Path(__file__).resolve().parents[3] / "data" / "demo" / "baseline_v1.json"


@router.post("/demo/reset")
def reset(user: dict = Depends(require("demo:reset"))):
    if not BASELINE.is_file():
        raise HTTPException(404, "baseline fixture missing: data/demo/baseline_v1.json")
    fx = json.loads(BASELINE.read_text(encoding="utf-8"))
    prov = fx["_provenance"]
    board = store.reset_to_baseline(fx["run"], fx["change_set"], prov.get("baseline_approver", "daniel"))
    pid = fx["change_set"]["project_id"]
    record(user, "demo.reset", "project:%s" % pid, "ok",
           detail={"baseline_run_id": prov["run_id"], "change_set_id": prov["change_set_id"],
                   "board_items": len(board)})
    return {"project_id": pid, "board": board, "baseline": prov}
