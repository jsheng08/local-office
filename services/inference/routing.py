"""Use-case -> local Nemotron endpoint routing (all served by vLLM on the ATOM via SSH tunnel)."""
import os
from typing import Dict

MODELS: Dict[str, dict] = {
    "lightning": {
        "name": "lightning",
        "base_url": os.environ.get("LO_LIGHTNING_URL", "http://localhost:9000/v1"),
        "timeout_s": 90.0,
    },
    "omni": {
        "name": "omni",
        "base_url": os.environ.get("LO_OMNI_URL", "http://localhost:9001/v1"),
        "timeout_s": 120.0,
    },
    "nano": {
        "name": "nano",
        "base_url": os.environ.get("LO_NANO_URL", "http://localhost:9006/v1"),
        "timeout_s": 90.0,
    },
}

ROUTES: Dict[str, str] = {
    "requirements_extract": "lightning",
    "triage": "lightning",
    "executive_explain": "lightning",
    "onboarding_qa": "nano",
    "receipt_extract": "omni",
}


def resolve(use_case: str) -> dict:
    """Return the model config for a use case. Unknown use cases are an error (no silent default)."""
    if use_case not in ROUTES:
        raise KeyError("unknown inference use_case: %s" % use_case)
    return MODELS[ROUTES[use_case]]
