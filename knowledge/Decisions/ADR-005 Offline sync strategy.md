---
type: decision
tags: [decision, adr]
related:
  project: PRJ-SPL
updated: 2026-10-13
synthetic: true
---
# ADR-005: Offline sync strategy

- **Status:** accepted
- **Date:** 2026-10-13

## Context
§7: rural East Coast routes lose coverage; no delivery record may be lost.

## Decision
Store each [[POD]] event in a local queue with a unique id; sync oldest first with retry; the server de-duplicates by id and acknowledges before the app deletes anything.

## Consequences
- No lost records, safe retries.
- Photos upload after the record, so a delivery can show "proof pending" for a while.
- Tested in airplane mode on 2026-10-15 ([[2026-10-15 SPL Standup]]).

Links: [[ADR-004 Flutter for driver app]]
