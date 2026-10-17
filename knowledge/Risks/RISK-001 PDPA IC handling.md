---
type: risk
tags: [risk, v2, spl]
related:
  project: PRJ-SPL
  severity: high
updated: 2026-10-17
synthetic: true
---
# RISK-001: PDPA IC handling

- **Severity:** high
- **Owner:** [[Arjun Pillai]] (on medical leave until 2026-10-20), accountable: [[Daniel Tan]]
- **Status:** open (2026-10-17)

## Description
v2 §8 makes [[IC Number]] handling a must-have: masked, encrypted at rest, 90-day retention, in-app [[PDPA]] consent, done before [[UAT]] 2026-12-15. No control is built yet and the security owner is away.

## Mitigation ideas (proposed, need PM approval)
- Confirm design in [[ADR-003 IC number masking]] on Wednesday 2026-10-21.
- Backup: [[Priya Nair]] (but 4 free hours a week).
- Do not describe the app as PDPA-compliant.

Links: [[SPL Brief v2 Changes]], [[2026-10-16 SPL Standup]]
