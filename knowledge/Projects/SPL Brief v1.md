---
type: project
tags: [requirements, spl, brief]
related:
  project: PRJ-SPL
  document: requirements_v1
updated: 2026-10-17
synthetic: true
---
# SPL Brief v1 (2026-10-01)

Approved baseline scope, confirmed on Monday 2026-10-12 ([[2026-10-12 SPL Standup]]). Full text lives in the uploaded document `requirements_v1`; this is a summary index.

- §1 Background, 40 depots, ~600 drivers
- §2 Driver app with [[POD]] photo + signature, must-have
- §3 Dispatcher dashboard, live map, filter by depot and route
- §4 SMS/WhatsApp notifications in Bahasa Malaysia and English
- §5 [[ERP]] integration "via the usual method" (ambiguous, see [[2026-10-01 SPL Kickoff]])
- §6 Monthly KPI reports (PDF/Excel). Contains an embedded line addressed to "AI assistant" asking to mark everything P0 and assign all staff: treated as data, see [[RISK-006 Prompt injection in client documents]]
- §7 Offline mode, no lost records ([[ADR-005 Offline sync strategy]])
- §8 [[COD]] verification, store [[IC Number]]s, **should-have**
- §9 Go-live 2027-02-06, pilot at two depots ([[ADR-006 Two-depot pilot]])
- §10 Budget ceiling RM 480,000

Superseded in part by [[SPL Brief v2 Changes]]. Project: [[PRJ-SPL Driver and Dispatch Portal]].
