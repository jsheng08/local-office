"""Authenticated, explicitly allowlisted staff directory (no financial rates)."""
from fastapi import APIRouter, Depends
from services.agents.triage.agent import active_leave, load_staff
from services.security.auth import require

router = APIRouter(prefix="/api")


@router.get("/staff")
def list_staff(user: dict = Depends(require("staff:directory"))):
    leave = active_leave()
    fields = ("id", "name", "role", "projects", "weekly_capacity_h", "allocated_h")
    return [dict({key: row.get(key) for key in fields}, on_leave=leave.get(row["id"]))
            for row in load_staff()]
