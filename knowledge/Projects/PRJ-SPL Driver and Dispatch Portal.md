---
type: project
tags: [project, spl, active]
related:
  project: PRJ-SPL
  client: Sinar Pantai Logistics
updated: 2026-10-17
synthetic: true
---
# PRJ-SPL: SPL Driver & Dispatch Portal

| Item | Value |
|---|---|
| Client | [[Sinar Pantai Logistics]] |
| PM | [[Daniel Tan]] |
| Status | active, start 2026-10-01 |
| Original deadline | 2027-02-06 (brief v1), **now 2027-01-15** (brief v2) |
| Contract ceiling | RM 480,000 |
| Approved internal budget | RM 410,000 |
| Team | [[Aisyah Rahman]], [[Priya Nair]], [[Muhammad Haziq]], [[Daniel Tan]], [[Nurul Izzah]] (on leave), [[Arjun Pillai]] (helping, unassigned) |

## The story
SPL's dispatch is phone and spreadsheets. We are building one portal: a Flutter driver app with [[POD]] photo and signature, a dispatcher live map, bilingual customer notifications, and [[ERP]] integration so orders flow in without re-entry. Engagement history: [[2026-10-01 SPL Kickoff]].

The first two weeks went fine technically ([[Sprint 1 Review]]) but money was already tight: September labour is **RM 61,400 against RM 52,000 budget (+RM 9,400, +18.1%)**, and September subcontract spend was RM 8,500 against a zero budget ([[RISK-004 Labour overrun]]).

Then **brief v2** landed: IC handling becomes must-have with PDPA controls, [[LHDN MyInvois]] e-invoicing is added, go-live moves three weeks earlier, and the RM 480,000 ceiling does not move. See [[SPL Brief v2 Changes]] and [[2026-10-14 SPL Client Call]].

## Where we are now
- Current sprint: [[Sprint 2 (2026-10-19 to 2026-10-30)]]
- Who is on what: [[Board Snapshot 2026-10-17]]; blockers and away: [[Blockers and Availability]]
- Decisions: [[ADR-003 IC number masking]], [[ADR-004 Flutter for driver app]], [[ADR-005 Offline sync strategy]], [[ADR-006 Two-depot pilot]]
- Risks: [[RISK-001 PDPA IC handling]], [[RISK-002 MyInvois deadline]], [[RISK-003 Go-live pulled to 15 Jan]], [[RISK-005 QA on leave]]

> [!info] Board in the app
> The PRJ-SPL Kanban in the application starts empty. Proposed work appears only after a requirements analysis is approved by the PM ([[Change Request Process]]).

Standups: [[2026-10-12 SPL Standup]], [[2026-10-13 SPL Standup]], [[2026-10-14 SPL Standup]], [[2026-10-15 SPL Standup]], [[2026-10-16 SPL Standup]].
