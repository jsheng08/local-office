"""Requirements -> Kanban primary workflow (B2)."""
import copy
import re
import time
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing_extensions import Literal

from services.agents.business_analyst.agent import extract, verify_citations
from services.agents.triage.agent import apply_triage, triage
from services.documents.chunk import chunk_paragraphs, sha256_text
from services.documents.diff import diff_paragraphs
from services.projects import store
from services.security.audit import record
from services.security.auth import check_project, require

router = APIRouter(prefix="/api")

DEMO_DIR = Path(__file__).resolve().parents[3] / "data" / "demo"
_DEMO_RE = re.compile(r"^requirements_v\d+\.md$")
MAX_TEXT = 60000


class AnalyzeBody(BaseModel):
    demo_file: Optional[str] = None
    text: Optional[str] = None


class DecisionBody(BaseModel):
    decision: Literal["approve", "reject"]
    note: Optional[str] = None


def _load_text(body: AnalyzeBody) -> str:
    if body.demo_file:
        name = body.demo_file
        if not _DEMO_RE.match(name) or "/" in name or "\\" in name:
            raise HTTPException(400, "demo_file must be a file like requirements_v1.md")
        path = DEMO_DIR / name
        if not path.is_file():
            raise HTTPException(404, "demo file not found: %s" % name)
        return path.read_text(encoding="utf-8")
    if body.text and body.text.strip():
        if len(body.text) > MAX_TEXT:
            raise HTTPException(413, "document too large")
        return body.text
    raise HTTPException(400, "provide demo_file or text")


def _paragraphs(text: str) -> List[Dict[str, str]]:
    paras = chunk_paragraphs(text)
    if not paras:
        raise HTTPException(422, "no §N. paragraphs found in document")
    return paras


def _meta(calls: List[dict]) -> dict:
    return {"calls": calls, "total_latency_ms": int(sum(c.get("latency_ms", 0) or 0 for c in calls))}


def _snap(r: Optional[Dict]) -> Optional[Dict]:
    if not r:
        return None
    t = r.get("triage") or {}
    return {"priority": r.get("priority"), "low": t.get("low"), "likely": t.get("likely"),
            "high": t.get("high"), "pert": t.get("pert"),
            "recommended_staff": [s.get("name") for s in r.get("recommended_staff", [])]}


def _norm(s: str) -> str:
    return " ".join((s or "").lower().split())


def _audit_error(user, action, resource, exc):
    try:
        record(user, action, resource, "error", detail={"error": type(exc).__name__})
    except Exception:
        pass


@router.get("/projects")
def list_projects(user: dict = Depends(require("project:view"))):
    allowed = user.get("projects", [])
    return [p for p in store.load_projects() if "*" in allowed or p["id"] in allowed]


@router.post("/projects/{pid}/requirements/analyze")
def analyze(pid: str, body: AnalyzeBody, user: dict = Depends(require("req:analyze"))):
    check_project(user, pid)
    text = _load_text(body)
    paras = _paragraphs(text)
    resource = "project:%s/requirements" % pid
    try:
        ext, m1 = extract(paras)
        by_id, m2 = triage(ext["requirements"], ext["ambiguities"])
    except Exception as exc:
        _audit_error(user, "requirements.analyze", resource, exc)
        raise
    reqs = ext["requirements"]
    apply_triage(reqs, by_id)
    meta = _meta([m1, m2])
    run_id, cs_id = store.new_id("run"), store.new_id("cs")
    store.save_run({"id": run_id, "project_id": pid, "kind": "analyze", "doc_sha256": sha256_text(text),
                    "demo_file": body.demo_file, "paragraphs": paras, "requirements": reqs,
                    "ambiguities": ext["ambiguities"], "created_by": user.get("username"), "created_at": time.time()})
    changes = [{"req_id": r["id"], "title": r["title"], "change": "added", "before": None,
                "after": _snap(r), "reason": "new requirement"} for r in reqs]
    store.save_change_set({"id": cs_id, "project_id": pid, "run_id": run_id, "kind": "analyze",
                           "status": "pending", "requirements": reqs, "changes": changes,
                           "created_by": user.get("username"), "created_at": time.time()})
    unverified = sum(1 for r in reqs for c in r["citations"] if c["status"] == "unverified")
    record(user, "requirements.analyze", resource, "pending", meta=meta,
           detail={"run_id": run_id, "change_set_id": cs_id, "doc_sha256": sha256_text(text),
                   "paragraphs": len(paras), "requirements": len(reqs), "ambiguities": len(ext["ambiguities"]),
                   "ignored_instructions": len(ext["ignored_instructions"]), "unverified_citations": unverified})
    return {"run_id": run_id, "change_set_id": cs_id, "status": "pending", "paragraphs": paras,
            "requirements": reqs, "ambiguities": ext["ambiguities"],
            "ignored_instructions": ext["ignored_instructions"], "meta": meta}


def drop_removed(reqs: List[Dict], pdiff: List[Dict]) -> List[Dict]:
    """Deterministic: a requirement whose citations all point at removed paragraphs is removed."""
    removed = {d["id"] for d in pdiff if d["change"] == "removed"}
    return [r for r in reqs if not r.get("citations")
            or not all(c["paragraph_id"] in removed for c in r["citations"])]


def stabilize(old_reqs: List[Dict], new_reqs: List[Dict], pdiff: List[Dict],
              paras: List[Dict[str, str]]) -> List[Dict]:
    """Deterministic guard against model drift between runs.
    - A previous requirement whose source paragraphs were all removed stays removed.
    - A requirement whose cited source paragraphs are all unchanged (before and after) keeps its
      previous content, so priorities only move when the client's text actually moved."""
    status = {d["id"]: d["change"] for d in pdiff}
    old_map = {r["id"]: r for r in old_reqs}
    gone = {r["id"] for r in old_reqs
            if r.get("citations") and all(status.get(c["paragraph_id"]) == "removed" for c in r["citations"])}
    out = []
    for r in new_reqs:
        if r["id"] in gone:
            continue
        o = old_map.get(r["id"])
        cites = [c["paragraph_id"] for c in r.get("citations", [])] + \
                [c["paragraph_id"] for c in (o or {}).get("citations", [])]
        if o is not None and cites and all(status.get(pid) == "equal" for pid in cites):
            keep = copy.deepcopy(o)
            verify_citations(keep, paras)
            out.append(keep)
        else:
            out.append(r)
    return out


def _paras_of(r: Dict) -> set:
    return {c["paragraph_id"] for c in r.get("citations", [])}


def reconcile_ids(old_reqs: List[Dict], new_reqs: List[Dict]) -> List[Dict]:
    """The model sometimes reuses an old id for an unrelated requirement. Treat an id whose
    cited paragraphs share nothing with the old requirement of that id as a new requirement:
    re-key it to the old requirement citing the same paragraphs, else to a fresh id."""
    old_map = {r["id"]: r for r in old_reqs}
    taken = set()
    out = []
    for r in new_reqs:
        o = old_map.get(r["id"])
        if o is not None and not (_paras_of(o) & _paras_of(r)):
            r = dict(r, id="")
        out.append(r)
        if r["id"]:
            taken.add(r["id"])
    nums = [int(i[1:]) for i in list(old_map) + list(taken) if i[1:].isdigit()]
    next_n = max(nums or [0]) + 1
    for r in out:
        if r["id"]:
            continue
        match = next((o["id"] for o in old_reqs
                      if o["id"] not in taken and _paras_of(o) & _paras_of(r)), None)
        if match is None:
            match = "R%d" % next_n
            next_n += 1
        r["id"] = match
        taken.add(match)
    return out


def classify_changes(old_reqs: List[Dict], new_reqs: List[Dict], pdiff: List[Dict]) -> List[Dict]:
    changed_paras = {d["id"] for d in pdiff if d["change"] in ("changed", "added", "removed")}
    old_map = {r["id"]: r for r in old_reqs}
    new_map = {r["id"]: r for r in new_reqs}
    out = []
    for r in new_reqs:
        o = old_map.get(r["id"])
        if o is None:
            out.append({"req_id": r["id"], "title": r["title"], "change": "added", "before": None,
                        "after": _snap(r), "reason": "new requirement"})
            continue
        reasons = []
        if o.get("priority") != r.get("priority"):
            reasons.append("priority %s→%s" % (o.get("priority"), r.get("priority")))
        cited = sorted({c["paragraph_id"] for c in r.get("citations", [])} & changed_paras)
        if cited:
            reasons.append("cites changed %s" % ", ".join(cited))
        out.append({"req_id": r["id"], "title": r["title"],
                    "change": "modified" if reasons else "unchanged",
                    "before": _snap(o), "after": _snap(r),
                    "reason": "; ".join(reasons) if reasons else "no change"})
    for o in old_reqs:
        if o["id"] not in new_map:
            out.append({"req_id": o["id"], "title": o["title"], "change": "removed", "before": _snap(o),
                        "after": None, "reason": "no longer in document"})
    return out


@router.post("/projects/{pid}/requirements/reanalyze")
def reanalyze(pid: str, body: AnalyzeBody, user: dict = Depends(require("req:analyze"))):
    check_project(user, pid)
    prev = store.get_last_run(pid)
    if not prev:
        raise HTTPException(409, "no previous analysis for this project; run analyze first")
    text = _load_text(body)
    paras = _paragraphs(text)
    pdiff = diff_paragraphs(prev["paragraphs"], paras)
    resource = "project:%s/requirements" % pid
    calls = []
    try:
        ext, m1 = extract(paras, previous=prev["requirements"])
        calls.append(m1)
        reids = reconcile_ids(prev["requirements"], drop_removed(ext["requirements"], pdiff))
        new_reqs = stabilize(prev["requirements"], reids, pdiff, paras)
        ext["requirements"] = new_reqs
        old_map = {r["id"]: r for r in prev["requirements"]}
        changed_paras = {d["id"] for d in pdiff if d["change"] != "equal"}
        to_triage = []
        for r in new_reqs:
            o = old_map.get(r["id"])
            affected = (o is None or o.get("priority") != r.get("priority")
                        or any(c["paragraph_id"] in changed_paras for c in r["citations"]))
            if affected or not o.get("triage") or o["triage"].get("pert") is None:
                to_triage.append(r)
            else:
                r["triage"] = o["triage"]
                r["recommended_staff"] = o.get("recommended_staff", [])
        if to_triage:
            by_id, m2 = triage(to_triage, ext["ambiguities"], all_ids=[r["id"] for r in new_reqs],
                               max_tokens=1500)
            calls.append(m2)
            apply_triage(to_triage, by_id)
    except Exception as exc:
        _audit_error(user, "requirements.reanalyze", resource, exc)
        raise
    changes = classify_changes(prev["requirements"], new_reqs, pdiff)
    meta = _meta(calls)
    run_id, cs_id = store.new_id("run"), store.new_id("cs")
    store.save_run({"id": run_id, "project_id": pid, "kind": "reanalyze", "doc_sha256": sha256_text(text),
                    "demo_file": body.demo_file, "paragraphs": paras, "requirements": new_reqs,
                    "ambiguities": ext["ambiguities"], "previous_run_id": prev["id"],
                    "created_by": user.get("username"), "created_at": time.time()})
    store.save_change_set({"id": cs_id, "project_id": pid, "run_id": run_id, "kind": "reanalyze",
                           "status": "pending", "requirements": new_reqs, "changes": changes,
                           "created_by": user.get("username"), "created_at": time.time()})
    counts = {}
    for c in changes:
        counts[c["change"]] = counts.get(c["change"], 0) + 1
    record(user, "requirements.reanalyze", resource, "pending", meta=meta,
           detail={"run_id": run_id, "previous_run_id": prev["id"], "change_set_id": cs_id,
                   "doc_sha256": sha256_text(text), "changes": counts,
                   "retriaged": len(to_triage), "ignored_instructions": len(ext["ignored_instructions"])})
    return {"run_id": run_id, "change_set_id": cs_id, "status": "pending", "paragraph_diff": pdiff,
            "changes": changes, "requirements": new_reqs,
            "ignored_instructions": ext["ignored_instructions"], "meta": meta}


@router.post("/change_sets/{cs_id}/decision")
def decide(cs_id: str, body: DecisionBody, user: dict = Depends(require("proposal:approve"))):
    cs = store.get_change_set(cs_id)
    if cs is None:
        raise HTTPException(404, "change set not found")
    check_project(user, cs["project_id"])
    resource = "change_set:%s" % cs_id
    try:
        res = store.decide_change_set(cs_id, body.decision, user, body.note)
    except ValueError as exc:
        record(user, "change_set.decision", resource, "denied", detail={"reason": str(exc)})
        raise HTTPException(409, str(exc))
    status = res["change_set"]["status"]
    record(user, "change_set.decision", resource, "ok",
           detail={"decision": body.decision, "status": status, "project_id": cs["project_id"],
                   "run_id": cs.get("run_id"), "board_items": len(res["board"]),
                   "note_present": bool(body.note)})
    return {"change_set_id": cs_id, "status": status, "board": res["board"]}
