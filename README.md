# Closed Office

**One ATOM. One Private AI. Your Entire Office.**

Closed Office is a proposed private AI operating layer for consulting firms and software houses. It aims to turn confidential client requirements into actionable project work and support employees across onboarding, project management, finance, HR, and executive operations.

> **Project status:** This repository currently contains project guidance and a proposed structure. Application services and workflows have not yet been implemented. The architecture below is a target, not a claim about working software.

## Why local AI

Closed Office is designed to run NVIDIA Nemotron inference on the GIGABYTE AI TOP ATOM (DGX Spark platform, 128 GB unified memory). Keeping inference on organization-operated hardware can help keep sensitive HR, finance, client, project, and security data within the organization's controlled environment. The core workflows should remain available without public internet when their local dependencies are available.

There is no hosted LLM fallback. Hardware, model, and runtime compatibility must be verified before claiming a workflow runs locally. Local deployment does not by itself provide security; access controls, storage protections, auditing, and operational controls remain necessary.

## Product workflows

1. **Requirements to delivery plan:** analyze client notes and documents, extract requirements with source references, identify ambiguities, propose stories and acceptance criteria, estimate work with uncertainty, and recommend dependencies and priorities. A person reviews proposed changes before they affect approved plans.
2. **Employee onboarding:** answer policy questions from authorized local documents, guide onboarding, and escalate unanswered questions.
3. **Expense claims and finance:** interpret receipts and policy documents, prepare claims or draft invoices and purchase orders, and route them for approval. Deterministic backend code applies financial rules; the AI does not approve or transfer funds.
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

The folders are scaffolding. Each service needs an implementation, configuration, and verification before it can be described as functional.

## Development priorities

- **P0:** verify local Nemotron inference; ingest documents; extract cited requirements; propose Kanban tasks; estimate and triage; re-evaluate priorities when new documents arrive.
- **P1:** onboarding and expense claim workflows; executive financial reporting grounded in actual records.
- **P2:** invoice and purchase-order drafting; advanced capacity planning; carefully scoped device/security workflows.

Prioritize one complete, evidence-backed local-AI workflow over a collection of unfinished features.

## Setup

There is no runnable application or dependency manifest in this initial scaffold yet. Start implementation by selecting and documenting the local inference runtime and model available on the ATOM, then add reproducible setup instructions here. Never silently substitute mock responses or a hosted model for local inference.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Demonstration plan](docs/DEMO.md)
- [Security requirements](docs/SECURITY.md)
- [Model configuration](docs/MODEL_CONFIGURATION.md)
- [Claude Code guidance](CLAUDE.md)

## Hackathon judging focus

The working assumptions from the project brief are AI capability (25%), local AI on ATOM (25%), impact and feasibility (20%), technical implementation (15%), and pitch/demo (15%). Validate these against the official event materials before using them as final criteria.
