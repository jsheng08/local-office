from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from services.agents.finance.claims import (ClaimError, decide_claim, list_claims, load_demo_file,
                                            submit_claim, validate_upload, MAX_UPLOAD_BYTES)
from services.inference.client import InferenceError
from services.security.audit import record
from services.security.auth import require

router = APIRouter(prefix="/api")


class Decision(BaseModel):
    decision: str
    note: Optional[str] = None


@router.post("/finance/claims")
def create_claim(file: Optional[UploadFile] = File(None), demo_file: Optional[str] = Form(None),
                 user: dict = Depends(require("claim:submit"))):
    try:
        if file is not None:
            data = validate_upload(file.file.read(MAX_UPLOAD_BYTES + 1))
            source = "upload:%s" % (file.filename or "receipt")[:100]
        elif demo_file:
            data = load_demo_file(demo_file)
            source = "demo:%s" % demo_file
        else:
            raise ClaimError(400, "provide multipart 'file' or form field 'demo_file'")
    except ClaimError as e:
        record(user, "finance.claim.submit", "claim:new", "error", detail={"reason": e.detail})
        raise HTTPException(status_code=e.status, detail=e.detail)
    try:
        claim = submit_claim(user, data, source)
    except InferenceError as e:
        record(user, "finance.claim.submit", "claim:new", "error",
               detail={"reason": e.reason, "model": e.model, "source": source})
        raise
    record(user, "finance.claim.submit", "claim:%s" % claim["claim_id"], "pending",
           meta=claim["meta"]["calls"][0],
           detail={"file_sha256": claim["file_sha256"], "source": source,
                   "total_amount": claim["extracted"]["total_amount"],
                   "category": claim["extracted"]["category"],
                   "failed_checks": [c["detail"] for c in claim["policy_checks"] if not c["passed"]],
                   "route_to": "finance"})
    return claim


@router.get("/finance/claims")
def get_claims(user: dict = Depends(require("claim:submit"))):
    claims = list_claims(user)
    record(user, "finance.claim.list", "claims", "ok", detail={"count": len(claims)})
    return claims


@router.post("/finance/claims/{claim_id}/decision")
def claim_decision(claim_id: str, body: Decision, user: dict = Depends(require("claim:decide"))):
    try:
        claim = decide_claim(user, claim_id, body.decision, body.note)
    except ClaimError as e:
        record(user, "finance.claim.decide", "claim:%s" % claim_id,
               "denied" if e.status == 403 else "error", detail={"reason": e.detail})
        raise HTTPException(status_code=e.status, detail=e.detail)
    record(user, "finance.claim.decide", "claim:%s" % claim_id, "ok",
           detail={"status": claim["status"], "payment_executed": False})
    return claim
