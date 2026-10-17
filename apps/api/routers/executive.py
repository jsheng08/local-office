from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from services.agents.executive.variance import VarianceDataError, run_variance
from services.inference.client import InferenceError
from services.security.audit import record
from services.security.auth import require

router = APIRouter(prefix="/api")


@router.get("/executive/variance")
def executive_variance(month: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}$"),
                       user: dict = Depends(require("exec:view"))):
    resource = "variance:%s" % (month or "latest")
    try:
        result = run_variance(month)
    except VarianceDataError as e:
        record(user, "executive.variance", resource, "error", detail={"reason": str(e)})
        raise HTTPException(status_code=404, detail=str(e))
    except InferenceError as e:
        record(user, "executive.variance", resource, "error",
               detail={"reason": e.reason, "model": e.model})
        raise
    call = result["meta"]["calls"][0]
    record(user, "executive.variance", "variance:%s" % result["month"], "ok", meta=call,
           detail={"rows": len(result["rows"]),
                   "flagged": sum(1 for r in result["rows"] if r["flagged"]),
                   "unverified_numbers": result["unverified_numbers"]})
    return result
