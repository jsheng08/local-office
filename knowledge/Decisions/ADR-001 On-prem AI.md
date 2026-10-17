---
type: decision
tags: [decision, adr]
related:
  scope: firm-wide
updated: 2026-09-20
synthetic: true
---
# ADR-001: On-prem AI

- **Status:** accepted
- **Date:** 2026-09-20

## Context
Client briefs carry NDAs, personal-data requirements and our own budget and staff data. Policy SEC-1 forbids uploading client documents to public AI tools.

## Decision
Run generative AI only on the office ATOM with local NVIDIA Nemotron. No hosted-AI fallback.

## Consequences
- Briefs never leave the office ([[How the office helper uses this vault]]).
- Throughput is bounded by one machine; we state measured speed rather than promising it.
- Offline operation must be verified before we claim it.

Links: [[Sinar Pantai Logistics]], [[RISK-006 Prompt injection in client documents]]
