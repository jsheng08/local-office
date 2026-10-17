---
type: decision
tags: [decision, adr]
related:
  project: PRJ-SPL
updated: 2026-10-15
synthetic: true
---
# ADR-003: IC number masking

- **Status:** proposed (needs PM and security review)
- **Date:** 2026-10-15

## Context
Brief v2 §8 requires: mask on all screens, encrypt at rest, keep at most 90 days, capture [[PDPA]] consent in-app before collecting. Due before [[UAT]] on 2026-12-15.

## Decision
Proposed: show only the last four digits everywhere; the full number is decrypted only server-side for COD verification with an audit entry; a scheduled job purges records after 90 days; the app presents a consent screen before the field can be filled. Never share ICs in chat or email.

## Consequences
- Needs [[Arjun Pillai]] (key management, purge job) and [[Priya Nair]] (backend) and [[Muhammad Haziq]] (consent screen).
- Not implemented; this is a design proposal.
- See [[RISK-001 PDPA IC handling]].

Links: [[SPL Brief v2 Changes]], [[IC Number]]
