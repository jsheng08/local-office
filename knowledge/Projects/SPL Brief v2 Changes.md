---
type: project
tags: [requirements, spl, change, v2]
related:
  project: PRJ-SPL
  document: requirements_v2
updated: 2026-10-17
synthetic: true
---
# SPL Brief v2: what changed (dated 2026-10-14)

Arrived by email Tuesday 2026-10-13 at 6 pm as a draft, discussed in [[2026-10-14 SPL Client Call]], formally dated 2026-10-14. Compare with [[SPL Brief v1]].

| Section | v1 | v2 | Why it hurts |
|---|---|---|---|
| §6 KPI reports | in scope | **removed, deferred to Phase 2** | small saving, but no price reduction offered |
| §8 IC handling | should-have | **must-have**: mask on all screens, encrypt at rest, retain max 90 days, in-app PDPA consent before collection, **done before UAT 2026-12-15** | needs security work, see [[RISK-001 PDPA IC handling]], [[ADR-003 IC number masking]] |
| §9 go-live | 2027-02-06 | **2027-01-15** | three weeks earlier, [[RISK-003 Go-live pulled to 15 Jan]] |
| §11 e-invoicing | absent | **[[LHDN MyInvois]] integration for COD receipts, mandatory by 2027-01-01** | brand new integration, [[RISK-002 MyInvois deadline]] |
| §10 budget | RM 480,000 ceiling | **same ceiling** | extra work with no extra money, [[RISK-004 Labour overrun]] |

## Reading
- Net effect: more work, less time, same ceiling.
- Any extra work beyond the ceiling needs SPL management approval (§10). Raise it through the [[Change Request Process]]; [[Daniel Tan]] approves before anything goes to the client.
- Staffing suggestions (for the PM to decide, not decided): PDPA work suits [[Arjun Pillai]] and [[Priya Nair]]; MyInvois suits [[Wong Kah Seng]].

Project: [[PRJ-SPL Driver and Dispatch Portal]].
