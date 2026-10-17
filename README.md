# Local Office

**One ATOM. One Private AI. Your Entire Office.**

Local Office is a proposed private AI operating layer for consulting firms and software houses. It aims to turn confidential client requirements into actionable project work and support employees across onboarding, project management, finance, HR, and executive operations.

> **Project status:** The hackathon application now has a Nuxt console and FastAPI services. On 2026-10-17 the deterministic unit tests and 6 live API tests passed, and the requirements workflow was clicked through in the Nuxt UI against live local Nemotron. Operation without public internet remains pending verification. See the scoped status table below.

## Why local AI

A consulting firm's most useful AI input is also what it is least free to send to a cloud API:

- **Client NDAs and data-processing terms.** Many restrict sharing client material with third-party processors or require the client's consent first. A PM with a brief at 6 pm can't get that consent before tomorrow's call.
- **Personal data in the briefs themselves.** The demo brief asks for IC-number handling for COD customers. Material like this is subject to Malaysia's PDPA, and keeping processing on firm-operated hardware avoids adding another processor to the chain.
- **The firm's own confidential delivery data.** Budgets, actuals, rates and the staff roster are what make an estimate useful, and they're commercially sensitive.

Local Office runs NVIDIA Nemotron on the GIGABYTE AI TOP ATOM (DGX Spark platform, 128 GB unified memory) with **no hosted LLM fallback**. The 128 GB of unified memory is what lets a large mixture-of-experts model sit on one desk-side box in the office instead of in a data centre; the model actually served is reported by `/api/health` and recorded in [docs/MODEL_CONFIGURATION.md](docs/MODEL_CONFIGURATION.md).

What this does not claim: running locally is not by itself PDPA compliance, and it is not security. Access control, storage protection, auditing and operational controls are still needed, and this prototype uses demo identity rather than real authentication. Operation without public internet is claimed only after it has been tested (see the status table).

## Product workflows

1. **Requirements to delivery plan:** analyze client notes and documents, extract requirements with source references, identify ambiguities, propose stories and acceptance criteria, estimate work with uncertainty, and recommend dependencies and priorities. A person reviews proposed changes before they affect approved plans.
2. **Employee onboarding:** answer policy questions from authorized local documents, guide onboarding, and escalate unanswered questions.
3. **Finance:** draft invoices and purchase orders from authorized records and route them for approval (not implemented). Deterministic backend code applies financial rules; the AI does not approve or transfer funds. Receipt scanning is intentionally out of scope (excluded by the hackathon rules).
4. **HR capacity planning:** analyze workload and capacity for planning. Estimated hours alone must not be treated as an employee performance score.
5. **Executive reporting:** explain budgets, P&L, and variances using authorized financial records. Arithmetic comes from deterministic code; the AI must not invent figures.
6. **Security operations:** explore authorized device inventory and security workflows only after their scope and safeguards are designed. Device monitoring is not implemented by this scaffold.

## Target architecture

The web application is a Nuxt 3 frontend and the API is a FastAPI backend. The API enforces authentication, role and project access, validates agent tool calls, and records consequential actions. A local inference service routes requests to compatible Nemotron model(s); the number of models and their capacity must be established on the target ATOM rather than assumed. Document, project, and security services provide bounded business operations. Shared schemas define API and agent contracts.

```text
Employee / administrator
          |
    Nuxt 3 web app
          |
   FastAPI application ------ Local database and document storage
          |
 Authentication, authorization, audit, deterministic business rules
          |
 Agent router and bounded tools
          |
 Local Nemotron inference on GIGABYTE AI TOP ATOM
```

## Proposed repository layout

```text
apps/
  web/                         Nuxt 3 frontend
  api/                         FastAPI backend
services/
  inference/                   Nemotron client and model routing
  agents/                       business_analyst, triage, onboarding,
                                finance, hr, executive
  documents/                    parsing, indexing, retrieval
  projects/                     Kanban, estimates, assignments
  security/                     authorization and audit
packages/shared/                schemas and contracts
data/demo/                      synthetic demonstration documents only
tests/                           unit, integration, and offline checks
scripts/                         inference, demo seed, and offline checks
docs/                            architecture, demo, security, model setup
```

The layout includes implemented services and planned areas. The status table records what this verification pass actually exercised.

## Development priorities

- **P0:** verify local Nemotron inference; ingest documents; extract cited requirements; propose Kanban tasks; estimate and triage; re-evaluate priorities when new documents arrive.
- **P1:** onboarding workflow; executive financial reporting grounded in actual records.
- **P2:** invoice and purchase-order drafting; advanced capacity planning; carefully scoped device/security workflows.

Prioritize one complete, evidence-backed local-AI workflow over a collection of unfinished features.

## Setup

Run these commands from the repository root on the Mac. The backend uses the existing Python 3.9 `.venv` (FastAPI, uvicorn, httpx, Pydantic 2, python-multipart). The DGX must already be serving the local Nemotron models; SSH alias `Hackathonnode` must work. No model download or hosted fallback is part of startup.

1. Open the SSH tunnel in one terminal and leave it running:

   ```bash
   ssh -N -o ServerAliveInterval=15 -o ExitOnForwardFailure=yes \
     -L 9000:127.0.0.1:9000 -L 9001:127.0.0.1:9001 \
     -L 9006:127.0.0.1:9006 Hackathonnode
   ```

2. Start the backend in another terminal:

   ```bash
   .venv/bin/uvicorn apps.api.main:app --port 8000
   ```

   Alternatively, `scripts/run.sh` checks/creates the tunnel and starts this backend. Use it instead of steps 1–2; it does not start Nuxt. Do not start another backend if one is already listening on port 8000.

3. Start the Nuxt frontend in a third terminal:

   ```bash
   cd apps/web
   npm install && npm run dev
   ```

   Open <http://localhost:3000>. Nuxt proxies `/api` to `http://127.0.0.1:8000`; the API is directly available at <http://127.0.0.1:8000/api/health>. Install frontend dependencies while internet is available, then retain `node_modules` for the offline demo. No dependencies were installed during this verification pass. The Nuxt install/build/browser flow has not been verified here.

4. Verify the existing services from the repository root:

   ```bash
   scripts/check_inference.sh
   .venv/bin/python -m unittest discover -s tests -t . -v
   LIVE=1 .venv/bin/python -m unittest tests.integration.test_api_live -v
   scripts/check_offline.sh
   ```

   Unit tests never call models. Live tests call the running backend and real models, and append audit records; they do not start/stop services. `check_inference.sh` prints served model roots and one measured Lightning completion with thinking disabled. `check_offline.sh` reports routes and public HTTPS reachability on both hosts, then calls each local model. It never changes networking. Both scripts use `.venv/bin/python` by default (`PYTHON` can override it).

The user switcher sends `X-Demo-User`; this is **demo identity, not production authentication**. Users come from [data/demo/users.json](data/demo/users.json):

| Username | Display name | Role | Projects |
|---|---|---|---|
| aisyah | Aisyah Rahman (Business Analyst) | analyst | PRJ-SPL |
| daniel | Daniel Tan (Project Manager) | pm | PRJ-SPL, PRJ-KLN |
| haziq | Muhammad Haziq (Mobile Developer) | employee | PRJ-SPL |
| farah | Farah Aziz (New Joiner) | employee | none |
| suresh | Suresh Kumar (Finance) | finance | all |
| hana | Hana Lee (HR) | hr | none |
| siti | Siti Hajar (Executive) | exec | all |

## Status

Evidence from this verification pass on 2026-10-17; a live API test is not a browser demonstration. “Implemented” below is limited to behavior exercised by these tests.

| Workflow | Implemented | Tested (unit) | Demonstrated live |
|---|---|---|---|
| Requirements v1 → approval → v2 → approval | Implemented | Deterministic diff/citation logic not unit-tested | Nuxt UI on live Lightning (2026-10-17): v1 analysis with §6 injection listed as ignored, analyst approval 403, PM approval, v2 before/after (§8 should→must, e-invoicing added, KPI reports removed); v1/v2 each ~22–38 s |
| Document upload and demo pack | UTF-8/PDF extraction; local Omni image route; metadata-only upload audit; generated PDF/MD/PNG pack in `demo_uploads/` | PDF §id round trips, text numbering, limits, permission/project denials and audit metadata; full discovery: 30 tests, 22 passed, 8 skipped, 0 failures/errors | PNG generated and visually inspected; Omni OCR and upload UI pending live verification |
| Staff directory, leave and approved board | Authenticated directory excludes rates; inclusive leave windows (`LO_TODAY` override); triage excludes staff on leave; project-scoped board read | All 7 demo users, leave boundaries, ranking exclusion, board project denial | pending verification |
| Onboarding | Implemented: leave answer API | Tested: section parsing and role filtering; citation rejection/escalation skipped (no pure helper) | Live API: answered with leave citations; UI pending verification |
| Executive variance | Implemented: September variance API | Tested: RM 9,400 / 18.1% labour overrun; invented RM 200,000 flagged | Live API: Siti 200, `unverified_numbers == []`; UI pending verification |
| Role permissions | Implemented: tested denials | Tested: analyst cannot approve; HR cannot view executive data | Live API: Haziq/Hana executive 403; Aisyah approval 403 |
| Audit | Implemented: isolated hash-chain storage | Tested: chaining, ordering, altered/deleted entries, full-chain verification with a result limit | pending verification |
| Local inference | Implemented: served endpoints answer | pending verification | Three model roots listed; real text answers from Lightning, Omni, Nano |
| HR capacity, invoice/PO drafting, device/security operations | pending verification | pending verification | pending verification |
| Operation without public internet | pending verification | pending verification | pending verification |

Exact results (after removing the expense-claim scenario and its tests): default discovery (`-s tests -t .`) runs the remaining unit tests with 0 failures; the earlier pass with finance tests ran **23 tests: 15 passed, 0 failed, 8 skipped** (6 opt-in live checks plus the 2 unit skips). `LIVE=1` integration discovery ran **6 tests: 6 passed, 0 failed, 0 skipped**. There were no test errors. Citation filtering and forced escalation live inside `ask()` after inference, so the unit suite explicitly skips those two checks rather than mocking a model answer.

The reporting scripts completed successfully. Lightning's one-call measurement was **0.131293 s** (a warm text call, not a throughput benchmark). All three local models answered. Both machines could reach `https://huggingface.co`, and both had an IPv4 default gateway of `172.20.10.1` (the Mac route needed a read outside the sandbox). This run does **not** establish offline operation. See [the rehearsal checklist](docs/DEMO.md) before making that claim.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Demonstration plan](docs/DEMO.md)
- [Security requirements](docs/SECURITY.md)
- [Model configuration](docs/MODEL_CONFIGURATION.md)
- [Claude Code guidance](CLAUDE.md)

## Hackathon judging focus

The working assumptions from the project brief are AI capability (25%), local AI on ATOM (25%), impact and feasibility (20%), technical implementation (15%), and pitch/demo (15%). Validate these against the official event materials before using them as final criteria.
