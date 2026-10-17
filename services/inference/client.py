"""Local Nemotron inference client (vLLM OpenAI-compatible API). No hosted fallback, no mock data."""
import base64
import copy
import json
import logging
import time
from typing import List, Optional, Tuple, Type

import httpx
from pydantic import BaseModel, ValidationError

from services.inference.routing import resolve

log = logging.getLogger("local_office.inference")


class InferenceError(Exception):
    def __init__(self, use_case: str, model: str, reason: str):
        super().__init__("%s (%s): %s" % (use_case, model, reason))
        self.use_case = use_case
        self.model = model
        self.reason = reason


def _image_mime(data: bytes) -> str:
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return "image/png"


def _attach_images(messages: List[dict], images: Optional[List[bytes]]) -> List[dict]:
    msgs = copy.deepcopy(messages)
    if not images:
        return msgs
    idx = None
    for i in range(len(msgs) - 1, -1, -1):
        if msgs[i].get("role") == "user":
            idx = i
            break
    if idx is None:
        msgs.append({"role": "user", "content": []})
        idx = len(msgs) - 1
    content = msgs[idx].get("content")
    if isinstance(content, str):
        parts = [{"type": "text", "text": content}]
    elif isinstance(content, list):
        parts = list(content)
    else:
        parts = []
    for img in images:
        b64 = base64.b64encode(img).decode("ascii")
        parts.append({"type": "image_url",
                      "image_url": {"url": "data:%s;base64,%s" % (_image_mime(img), b64)}})
    msgs[idx]["content"] = parts
    return msgs


def _extract_text(message: dict) -> Optional[str]:
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        if "</think>" in content:
            content = content.split("</think>")[-1]
        return content.strip() or None
    # Fallback: reasoning leaked despite enable_thinking=false; only accept text after </think>.
    for key in ("reasoning", "reasoning_content"):
        r = message.get(key)
        if isinstance(r, str) and "</think>" in r:
            tail = r.split("</think>")[-1].strip()
            if tail:
                return tail
    return None


def _post(use_case: str, cfg: dict, payload: dict) -> Tuple[str, dict]:
    """POST once to /chat/completions with 1 transport-level retry. Returns (text, meta)."""
    url = cfg["base_url"].rstrip("/") + "/chat/completions"
    last_reason = "unknown"
    for attempt in (1, 2):
        t0 = time.monotonic()
        try:
            with httpx.Client(timeout=cfg["timeout_s"]) as c:
                resp = c.post(url, json=payload)
            latency_s = time.monotonic() - t0
            if resp.status_code != 200:
                last_reason = "HTTP %d: %s" % (resp.status_code, resp.text[:300])
                log.warning("inference %s attempt %d failed: %s", use_case, attempt, last_reason)
                continue
            try:
                body = resp.json()
            except ValueError:
                last_reason = "invalid JSON from server"
                continue
            choices = body.get("choices") or []
            if not choices:
                last_reason = "no choices in response"
                continue
            text = _extract_text(choices[0].get("message") or {})
            if text is None:
                last_reason = "empty content (finish_reason=%s)" % choices[0].get("finish_reason")
                continue
            usage = body.get("usage") or {}
            ct = int(usage.get("completion_tokens") or 0)
            meta = {
                "use_case": use_case,
                "model": cfg["name"],
                "endpoint": cfg["base_url"],
                "latency_ms": int(round(latency_s * 1000)),
                "completion_tokens": ct,
                "prompt_tokens": int(usage.get("prompt_tokens") or 0),
                "tok_per_s": round(ct / latency_s, 1) if latency_s > 0 else None,
                "attempts": attempt,
            }
            return text, meta
        except httpx.TimeoutException:
            last_reason = "timeout after %.0fs" % cfg["timeout_s"]
        except httpx.HTTPError as e:
            last_reason = "connection error: %s" % e.__class__.__name__
        log.warning("inference %s attempt %d failed: %s", use_case, attempt, last_reason)
    raise InferenceError(use_case, cfg["name"], last_reason)


def _base_payload(cfg: dict, messages: List[dict], max_tokens: int) -> dict:
    return {
        "model": cfg["name"],
        "messages": messages,
        "temperature": 0,
        "max_tokens": max_tokens,
        "chat_template_kwargs": {"enable_thinking": False},
    }


def chat_text(use_case: str, messages: List[dict], max_tokens: int = 800) -> Tuple[str, dict]:
    try:
        cfg = resolve(use_case)
    except KeyError as e:
        raise InferenceError(use_case, "none", str(e))
    return _post(use_case, cfg, _base_payload(cfg, copy.deepcopy(messages), max_tokens))


def _strip_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else ""
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    return t.strip()


def chat_json(use_case: str, messages: List[dict], schema: Type[BaseModel],
              images: Optional[List[bytes]] = None, max_tokens: int = 2000) -> Tuple[BaseModel, dict]:
    try:
        cfg = resolve(use_case)
    except KeyError as e:
        raise InferenceError(use_case, "none", str(e))
    msgs = _attach_images(messages, images)
    response_format = {"type": "json_schema",
                       "json_schema": {"name": schema.__name__, "schema": schema.model_json_schema()}}
    last_err = ""
    total_attempts = 0
    for validation_try in (1, 2):
        payload = _base_payload(cfg, msgs, max_tokens)
        payload["response_format"] = response_format
        text, meta = _post(use_case, cfg, payload)
        total_attempts += meta["attempts"]
        try:
            obj = schema.model_validate_json(_strip_fences(text))
            meta["attempts"] = total_attempts
            return obj, meta
        except ValidationError as e:
            last_err = str(e)[:1500]
            log.warning("inference %s schema validation failed (try %d): %s",
                        use_case, validation_try, last_err[:200])
            msgs = msgs + [
                {"role": "assistant", "content": text},
                {"role": "user", "content": "Your previous output failed schema validation:\n"
                 + last_err + "\nReturn only corrected JSON matching the schema."},
            ]
    raise InferenceError(use_case, cfg["name"], "schema validation failed after retry: " + last_err[:500])
