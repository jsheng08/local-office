---
type: decision
tags: [decision, adr]
related:
  project: PRJ-SPL
updated: 2026-10-02
synthetic: true
---
# ADR-004: Flutter for driver app

- **Status:** accepted
- **Date:** 2026-10-02

## Context
Drivers use mixed low-end Android phones; we need one codebase, camera and signature capture, maps and offline storage.

## Decision
Build the driver app in Flutter, owned by [[Muhammad Haziq]].

## Consequences
- Fast iteration and good offline libraries.
- Only one mobile specialist on the team ([[Muhammad Haziq]]), so bus factor is one.

Links: [[ADR-005 Offline sync strategy]], [[POD]]
