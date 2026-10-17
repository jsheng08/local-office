import hashlib

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from services.agents.onboarding.qa import ask
from services.inference.client import InferenceError
from services.security.audit import record
from services.security.auth import require

router = APIRouter(prefix="/api")


class Question(BaseModel):
    question: str


@router.post("/onboarding/ask")
def onboarding_ask(body: Question, user: dict = Depends(require("onboarding:ask"))):
    q = (body.question or "").strip()
    if not q:
        raise HTTPException(status_code=400, detail="question is required")
    qhash = hashlib.sha256(q.encode("utf-8")).hexdigest()[:16]
    try:
        result = ask(user, q)
    except InferenceError as e:
        record(user, "onboarding.ask", "question:%s" % qhash, "error",
               detail={"reason": e.reason, "model": e.model})
        raise
    record(user, "onboarding.ask", "question:%s" % qhash,
           "ok" if result["status"] == "answered" else "pending",
           meta=result["meta"]["calls"][0],
           detail={"status": result["status"],
                   "escalated_to": "hr" if result["status"] == "escalate" else None,
                   "citations": [c["section_id"] for c in result["citations"]],
                   "dropped_citations": result["dropped_citations"],
                   "forced_escalation": result["forced_escalation"],
                   "sections_considered": result["sections_considered"]})
    return result
