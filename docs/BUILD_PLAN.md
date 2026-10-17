# 1-hour build plan (hackathon, 2026-10-17)

Merged from 5 planning passes. This is a plan, not a report of working software.

## Decisions (resolved where the planners disagreed)

- **Stack:** FastAPI on the `.venv` that already exists (Python 3.9, fastapi/uvicorn/httpx/pydantic/python-multipart installed). Frontend is static `apps/web/{index.html,app.js,styles.css}`: vanilla JS, no CDN, served by FastAPI at `/`. Nuxt is deferred; the README must say so.
- **Models** (verified, see `MODEL_CONFIGURATION.md`), reached through the SSH tunnel on the Mac:

  | Use case | Model | URL |
  |---|---|---|
  | Requirements extraction, v2 re-analysis, triage, executive explanation | `lightning` | `localhost:9000` |
  | Onboarding Q&A | `nano` | `localhost:9006` |
  | Receipt image extraction | `omni` | `localhost:9001` (image input **not yet smoke-tested**: do this first) |

- **Inference client contract** (frozen): `chat_json(use_case, messages, schema: Type[BaseModel], images=None) -> (obj, meta)`.
  - Always sends `enable_thinking: false` and `response_format=json_schema`, with temperature 0.
  - Timeout is 60 s, or 90 s for omni.
  - On malformed JSON it retries once with the validation error appended, then raises `InferenceError`, which the API returns as a 502.
  - `meta` holds `{model, endpoint, latency_ms, completion_tokens, tok_per_s}`.
  - **There is no mock path.**
- **Auth:** the `X-Demo-User` header is looked up in `data/demo/users.json`, and a `require(perm)` dependency checks it, along with `check_project`. Denials are audited. This is labelled "demo identity, not authentication".
- **Storage:**
  - State: JSON at `data/runtime/state.json`.
  - Audit: append-only, hash-chained JSONL at `data/runtime/audit.jsonl`. It stores hashes, not document text.
- **Demo data:** the data spec is the single source of truth for names, limits and IDs.
  - Firm: Teratai Digital. Client: Sinar Pantai Logistics. Projects: PRJ-SPL and PRJ-KLN.
  - Users: aisyah (analyst), daniel (pm/approver), haziq (employee), farah (new joiner), suresh (finance), hana (hr), siti (exec).
  - Expense limits come from `policies/expense_claims.md`.

## Primary workflow (P0): requirements → Kanban

1. **Deterministic:** chunk the doc into paragraphs §1..§n.
2. **lightning L1:** extract requirements with `{paragraph_id, quote}` citations, ambiguities, stories, acceptance criteria and `ignored_instructions`. The prompt says document text is untrusted.
3. **Deterministic:** verify each quote is a substring of its cited paragraph and mark it verified, relocated or unverified. Unverified items can't be approved.
4. **lightning L2:** estimate effort low/likely/high with assumptions, `depends_on` and required skills. It must not name people.
5. **Deterministic:**
   - Compute PERT and enforce low ≤ likely ≤ high.
   - Drop dependency ids that don't exist.
   - Rank staff in code: skill overlap × available hours.
6. **v2:**
   - difflib paragraph diff.
   - L1 again, reusing requirement ids.
   - Requirement diff (added, removed, modified).
   - L2 only for affected items.
   - A before/after priority table, saved as a change set with status `pending`.
7. A human (PM role) approves. Only then is the Kanban board written, and an audit row is added.

## Secondary workflows, in priority order (cut from the bottom)

1. **Executive variance:**
   - Python computes budget vs actual from `finance.csv` and flags variances over 10%.
   - lightning explains them.
   - A regex check flags any number in the explanation that isn't in the computed table.
2. **Expense claim:**
   - omni extracts fields from the receipt PNG.
   - Python applies the policy limits with `Decimal`.
   - The claim is set to `pending_approval` and routed to finance. There is no pay action.
3. **Onboarding Q&A:**
   - Policies are filtered by role in code, then stuffed into context for nano.
   - Answers cite section ids; any id that wasn't sent is rejected.
   - If the policies don't cover the question, the answer is "escalate to HR".
4. **Bounded tool-calling agent:** cut unless 20+ minutes remain.

## Work split (no file overlap)

| Builder | Owns |
|---|---|
| B1 integration | `services/inference/*`, `services/security/*`, `apps/api/main.py`, `apps/api/routers/system.py` (`/api/health`, `/api/me`, `/api/audit`), `scripts/run.sh` |
| B2 P0 | `services/documents`, `services/agents/{business_analyst,triage}`, `services/projects`, `apps/api/routers/requirements.py` |
| B3 secondary | `services/agents/{executive,finance,onboarding}`, `apps/api/routers/{executive,finance,onboarding}.py` |
| B4 frontend | `apps/web/*` |
| B5 data | `data/demo/*`, `scripts/make_receipt.py` (PIL is available) |

## Timeline

| Time | Step |
|---|---|
| T+0–5 | Freeze contracts. Smoke-test omni with an image. |
| T+5–35 | Build in parallel. B1 ships the client and auth by T+12. |
| T+35 | Requirements flow working end to end. |
| T+42 | Secondary flows wired; cut whatever fails. |
| T+50 | Rehearse. curl the wrong role and expect 403. Warm up each model. |
| T+55 | Docs: mark each feature implemented, tested or not done. |

## Demo safety

- **Proving it is offline:** do NOT turn off the hotspot, because it carries the Mac↔DGX link. Two options:
  - Delete the default route on both machines, so the on-link 172.20.10.x traffic survives, and show a public `curl` failing. Rehearse this first.
  - Run `watch nvidia-smi` plus the vLLM log on the DGX during a live call.
- **If a call fails:** show the real error and never fake output. Cap `max_tokens` at about 800 for v2 and secondary calls.
