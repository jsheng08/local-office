---
type: decision
tags: [decision, adr]
related:
  project: PRJ-SPL
updated: 2026-10-09
synthetic: true
---
# ADR-002: OTP provider

- **Status:** accepted
- **Date:** 2026-10-09

## Context
The driver app needs a one-time password at login, and customers receive SMS notifications (§4). Options: a global messaging API versus a Malaysia-based SMS gateway.

## Decision
Use a Malaysia-based SMS gateway for OTPs and customer SMS; WhatsApp stays a separate channel for notifications only. Vendor name is still to be chosen by [[Priya Nair]] with [[Arjun Pillai]]'s security checklist.

## Consequences
- Local delivery routes, local sender IDs, easier to keep message content in Malaysia.
- OTP messages contain no [[IC Number]] or other personal identifiers (policy SEC-4).
- [[Wong Kah Seng]] reuses the same gateway for KLN-2 reminders.

Links: [[PRJ-SPL Driver and Dispatch Portal]], [[PRJ-KLN Klinik Appointment App]]
