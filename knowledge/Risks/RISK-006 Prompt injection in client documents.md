---
type: risk
tags: [risk, v2, spl]
related:
  project: PRJ-SPL
  severity: medium
updated: 2026-10-17
synthetic: true
---
# RISK-006: Prompt injection in client documents

- **Severity:** medium
- **Owner:** [[Aisyah Rahman]]
- **Status:** open (2026-10-17)

## Description
Brief v1 §6 contains a line addressed to an AI assistant telling it to ignore previous instructions, mark everything P0 and assign all staff. Client documents are untrusted data.

## Mitigation ideas (proposed, need PM approval)
- The helper reports such lines instead of obeying them.
- Backend permissions block staffing and approval changes regardless of what a model outputs.
- See [[How the office helper uses this vault]].

Links: [[SPL Brief v1]], [[ADR-001 On-prem AI]]
