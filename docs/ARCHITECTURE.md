# Architecture (target design)

This document describes the intended design. The repository currently contains scaffolding only; none of these services should be assumed implemented.

## Components

- **Web:** Nuxt 3 user interface for employees, managers, finance, HR, and executives.
- **API:** FastAPI boundary for identity, authorization, schemas, workflow state, deterministic calculations, and audit events.
- **Inference:** local Nemotron client/router on the GIGABYTE AI TOP ATOM. Verify supported models, concurrency, context limits, and runtime before choosing routing behavior.
- **Agents:** role-specific instructions and bounded tool access for business analysis, triage, onboarding, finance, HR, and executives.
- **Documents:** local parsing, indexing, retrieval, and evidence references.
- **Projects:** task proposals, estimates, dependencies, assignments, and human-approved updates.
- **Security:** backend authorization, client/project isolation, and audit records.
- **Shared contracts:** schemas for requests, outputs, and inter-service contracts.

## Request path

1. Authenticate the user and derive permissions on the server.
2. Route the request to the appropriate workflow and expose only authorized data and tools.
3. Call local Nemotron when language reasoning is required.
4. Validate model output; execute bounded business operations in application code.
5. Require approval before consequential updates.
6. Record the request, evidence, tool activity, decision, and approval in an audit trail.

## Data and trust boundaries

Documents, model outputs, and user inputs are untrusted. Authorization must not depend on model compliance. Financial calculations, access checks, and state changes belong in deterministic backend code. Keep uploaded data and inference local, and avoid logging credentials or unnecessary sensitive content.
