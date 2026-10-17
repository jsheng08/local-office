"""Paragraph-level diff by paragraph id."""
from typing import List, Dict


def _is_removed(text: str) -> bool:
    return "[REMOVED" in (text or "").upper()


def _norm(t: str) -> str:
    return " ".join((t or "").split())


def diff_paragraphs(old: List[Dict[str, str]], new: List[Dict[str, str]]) -> List[Dict[str, str]]:
    old_map = {p["id"]: p["text"] for p in old}
    new_map = {p["id"]: p["text"] for p in new}
    order = [p["id"] for p in new] + [p["id"] for p in old if p["id"] not in new_map]
    out = []
    for pid in order:
        o = old_map.get(pid)
        n = new_map.get(pid)
        if o is None:
            change = "removed" if _is_removed(n) else "added"
        elif n is None or (_is_removed(n) and not _is_removed(o)):
            change = "removed"
        elif _norm(o) == _norm(n):
            change = "equal"
        else:
            change = "changed"
        out.append({"id": pid, "change": change})
    return out
