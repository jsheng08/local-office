# Shared build contracts (frozen — all builders code against these)

Python 3.9 (`.venv/`, already has fastapi, uvicorn, httpx, pydantic 2, python-multipart). Use `Optional[...]`/`List[...]`, never `X | Y`, no `match`. Run from repo root: `.venv/bin/uvicorn apps.api.main:app --port 8000`. All packages already have `__init__.py`. Do not `pip install` anything without need. Do not commit.

Models via SSH tunnel (already running): `lightning` http://localhost:9000/v1, `omni` http://localhost:9001/v1 (vision), `nano` http://localhost:9006/v1. No hosted fallback, no mock responses anywhere (CLAUDE.md).

## services/inference/client.py (owner B1)

```python
class InferenceError(Exception): ...          # .use_case, .model, .reason
def chat_json(use_case: str, messages: List[dict], schema: Type[BaseModel],
              images: Optional[List[bytes]] = None, max_tokens: int = 2000) -> Tuple[BaseModel, dict]
def chat_text(use_case: str, messages: List[dict], max_tokens: int = 800) -> Tuple[str, dict]
```
- Use cases (services/inference/routing.py `ROUTES`): `requirements_extract`, `triage`, `executive_explain` → lightning; `onboarding_qa` → nano; `receipt_extract` → omni.
- Always `temperature: 0`, `chat_template_kwargs: {"enable_thinking": False}`; chat_json sends `response_format={"type":"json_schema","json_schema":{"name":schema.__name__,"schema":schema.model_json_schema()}}`, validates with `schema.model_validate_json`, retries once with the validation error appended, then raises InferenceError. Timeouts: 90 s (omni 120 s).
- `images`: raw PNG/JPEG bytes; client appends them as `image_url` data-URL parts to the LAST user message.
- `meta` dict: `{"use_case","model","endpoint","latency_ms","completion_tokens","prompt_tokens","tok_per_s","attempts"}` (all measured, from vLLM `usage`).
- AI endpoints return `"meta": {"calls": [meta, ...], "total_latency_ms": int}`.

## services/security/auth.py (owner B1)

Users from `data/demo/users.json` (array of `{username, display_name, staff_id, role, projects[]}`; projects may contain `"*"` = all).
```python
def current_user(x_demo_user: Optional[str] = Header(None)) -> dict   # 401 if missing/unknown
def require(perm: str)            # returns a FastAPI dependency -> user dict; 403 + audited denial
def check_project(user: dict, project_id: str) -> None   # 403 + audited denial
```
ROLE_PERMS:
- analyst: project:view, req:analyze, onboarding:ask, claim:submit
- pm: project:view, req:analyze, proposal:approve, onboarding:ask, claim:submit, audit:view
- employee: project:view, onboarding:ask, claim:submit
- finance: onboarding:ask, claim:submit, claim:decide, exec:view, audit:view
- hr: onboarding:ask, staff:view
- exec: project:view, exec:view, onboarding:ask, audit:view

## services/security/audit.py (owner B1)

```python
def record(user: Optional[dict], action: str, resource: str, outcome: str,
           meta: Optional[dict] = None, detail: Optional[dict] = None) -> dict
def read(limit: int = 200) -> Tuple[List[dict], bool]      # (newest first, chain_valid)
```
Append-only hash-chained JSONL at `data/runtime/audit.jsonl` (`prev_hash`, `hash`=sha256). Store hashes/ids, not document text. Outcomes: `ok`, `denied`, `error`, `pending`.

## apps/api/main.py (owner B1)

Imports router modules `apps.api.routers.{system,requirements,onboarding,finance,executive}` each exposing `router = APIRouter(prefix="/api")`; a failed import is logged, not fatal. Exception handler: InferenceError → HTTP 502 `{"error":"local_inference_failed","detail":...,"use_case":...,"model":...}`. Mounts `apps/web` as static at `/` (html=True) LAST.

## Endpoints

| Owner | Method path | Perm | Request | Response |
|---|---|---|---|---|
| B1 | GET /api/health | none | – | `{models:[{name,model_id,base_url,ok,latency_ms,max_model_len,error}], host:"EMARQUE-DGX-J (DGX Spark) via SSH tunnel", hosted_fallback:false}` |
| B1 | GET /api/users | none | – | users list (for the switcher) |
| B1 | GET /api/me | any | – | user |
| B1 | GET /api/audit | audit:view | – | `{entries, chain_valid}` |
| B2 | GET /api/projects | project:view | – | projects the user can access (from projects.json + approved board state) |
| B2 | POST /api/projects/{pid}/requirements/analyze | req:analyze + check_project | JSON `{demo_file?: "requirements_v1.md", text?: str}` | `{run_id, change_set_id, status:"pending", paragraphs:[{id,text}], requirements:[Req], ambiguities:[{id,question,paragraph_id,quote}], ignored_instructions:[{paragraph_id,quote}], meta}` |
| B2 | POST /api/projects/{pid}/requirements/reanalyze | req:analyze + check_project | same as analyze (v2) | `{run_id, change_set_id, status:"pending", paragraph_diff:[{id,change:"added"\|"removed"\|"changed"\|"equal"}], changes:[{req_id,title,change:"added"\|"removed"\|"modified"\|"unchanged",before:Snap\|null,after:Snap\|null,reason}], requirements:[Req], ignored_instructions, meta}` |
| B2 | POST /api/change_sets/{id}/decision | proposal:approve | `{decision:"approve"\|"reject", note?}` | `{change_set_id, status:"applied"\|"rejected", board:[Req]}` |
| B3 | POST /api/onboarding/ask | onboarding:ask | `{question}` | `{status:"answered"\|"escalate", answer, citations:[{section_id,doc,title}], sections_considered:int, meta}` |
| B3 | POST /api/finance/claims | claim:submit | multipart `file` OR form field `demo_file` (e.g. `receipt_grab_001.png`) | `{claim_id, extracted:{vendor,date,currency,total_amount,category,confidence}, policy_checks:[{rule,passed,detail}], status:"pending_approval", route_to:"finance", meta}` |
| B3 | GET /api/finance/claims | claim:submit | – | claims (own; finance sees all) |
| B3 | POST /api/finance/claims/{id}/decision | claim:decide | `{decision:"approve"\|"reject", note?}` | claim (status `approved_by_finance` / `rejected`; no payment is executed by the system) |
| B3 | GET /api/executive/variance?month=2026-09 | exec:view | – | `{month, rows:[{project_id,cost_centre,category,budget_myr,actual_myr,variance_myr,variance_pct,flagged}], totals, narrative:{summary, drivers:[{item,explanation}]}, unverified_numbers:[str], meta}` |

`Req` = `{id, title, statement, priority:"must"|"should"|"could"|"wont", type, citations:[{paragraph_id, quote, status:"verified"|"relocated"|"unverified"}], story:{as_a,i_want,so_that}, acceptance_criteria:[str], triage:{low,likely,high,pert,confidence,assumptions,depends_on,required_skills}, recommended_staff:[{staff_id,name,score,reason}], approvable:bool}`
`Snap` = `{priority, low, likely, high, pert, recommended_staff:[names]}`

Errors: 401/403 `{"detail": "..."}` from FastAPI; 502 for inference failures (above). The UI shows these verbatim.

## Demo data (owner B5) — `data/demo/`

- `requirements_v1.md`, `requirements_v2.md`: one paragraph per block, each block starting with `§N.` at line start (e.g. `§4. Customer notifications: ...`). Header lines before §1 are ignored by the chunker. v2 removed paragraph stays as `§6. [REMOVED – deferred to Phase 2] ...`.
- `staff.json`: `[{id,name,role,skills[],weekly_capacity_h,allocated_h,projects[],hourly_cost_myr}]`
- `projects.json`: `[{id,name,client,status,budget_myr,start,deadline,kanban:[...]}]` — PRJ-SPL kanban starts `[]` (populated by approved analysis); PRJ-KLN has 3 items.
- `users.json`: see auth.
- `policies/{leave,expense_claims,it_security}.md`: sections `## LV-1 Title`, `## EX-2 Title`, `## SEC-4 Title`. Optional frontmatter line `audience: all`.
- `receipts/receipt_grab_001.png` (+ `.txt` twin), `receipts/receipt_002.txt`
- `finance.csv`: `month,project_id,cost_centre,category,budget_myr,actual_myr`; `budget.json`.

Runtime state goes in `data/runtime/` (gitignored).
