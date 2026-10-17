"""Deterministic paragraph chunking for requirement documents (§N. blocks)."""
import hashlib
import re
from typing import List, Dict

_PARA_RE = re.compile(r"^§\s*(\d+)\.\s*", re.MULTILINE)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def chunk_paragraphs(text: str) -> List[Dict[str, str]]:
    """Split on lines starting with `§N.`; header text before §1 is ignored."""
    matches = list(_PARA_RE.finditer(text or ""))
    out = []  # type: List[Dict[str, str]]
    seen = set()
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = " ".join(text[m.end():end].split())
        pid = "§" + m.group(1)
        if pid in seen:
            continue
        seen.add(pid)
        out.append({"id": pid, "text": body})
    return out
