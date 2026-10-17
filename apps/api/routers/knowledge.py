import hashlib

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from services.agents.knowledge.kb import ask
from services.inference.client import InferenceError
from services.security.audit import record
from services.security.auth import require

router = APIRouter(prefix="/api")


class Question(BaseModel):
    question: str


@router.post("/knowledge/ask")
def knowledge_ask(body: Question, user: dict = Depends(require("staff:directory"))):
    q = (body.question or "").strip()
    if not q:
        raise HTTPException(status_code=400, detail="question is required")
    qhash = hashlib.sha256(q.encode("utf-8")).hexdigest()[:16]
    try:
        result = ask(user, q)
    except InferenceError as e:
        record(user, "knowledge.ask", "question:%s" % qhash, "error", detail={"reason": e.reason, "model": e.model})
        raise
    record(user, "knowledge.ask", "question:%s" % qhash, "ok" if result["status"] == "answered" else "pending",
           meta=result["meta"]["calls"][0],
           detail={"status": result["status"], "citations": [c["id"] for c in result["citations"]],
                   "dropped_citations": result["dropped_citations"], "notes_visible": result["notes_visible"]})
    return result
